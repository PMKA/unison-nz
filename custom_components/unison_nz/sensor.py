"""Sensor platform for Unison Outages."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_AREAS,
    CONF_FORECAST_DAYS,
    CONF_HISTORY_DAYS,
    CONF_REGION,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_REGION,
    DOMAIN,
)
from .coordinator import UnisonNzDataUpdateCoordinator
from .outages import NZ, Outage, describe, in_days, in_region, is_current, is_upcoming, matches_areas


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: UnisonNzDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        CurrentOutagesSensor(coordinator, entry),
        UpcomingOutagesSensor(coordinator, entry),
        OutageStatsSensor(coordinator, entry),
        NextOutageAtHomeSensor(coordinator, entry),
    ])


class UnisonEntity(CoordinatorEntity[UnisonNzDataUpdateCoordinator]):
    """Shared settings and filtering for one config entry (one region)."""

    def __init__(self, coordinator: UnisonNzDataUpdateCoordinator, entry: ConfigEntry, key: str, name: str) -> None:
        super().__init__(coordinator)
        settings = {**entry.data, **entry.options}
        self._region = settings.get(CONF_REGION, DEFAULT_REGION)
        self._areas = [a.strip().lower() for a in (settings.get(CONF_AREAS) or "").split(",") if a.strip()]
        self._history_days = settings.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS)
        self._forecast_days = settings.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS)
        # Unique IDs match v0.1, so existing entities keep their entity IDs and history.
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_has_entity_name = True
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Unison Networks",
            entry_type=DeviceEntryType.SERVICE,
        )

    def _regional(self) -> List[Outage]:
        return [o for o in self.coordinator.data or [] if in_region(o, self._region)]

    def _filtered(self) -> List[Outage]:
        return [o for o in self._regional() if matches_areas(o, self._areas)]

    def _upcoming(self, now: datetime) -> List[Outage]:
        return [o for o in self._filtered() if is_upcoming(o) and in_days(o.start, now, ahead=self._forecast_days)]


class CurrentOutagesSensor(UnisonEntity, SensorEntity):
    _attr_icon = "mdi:flash-off"
    _attr_native_unit_of_measurement = "outages"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _unrecorded_attributes = frozenset({"outages"})

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "current_outages", "Current Outages")

    @property
    def native_value(self) -> int:
        return sum(1 for o in self._filtered() if is_current(o))

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        now = datetime.now(NZ)
        current = [describe(o, now) for o in self._filtered() if is_current(o)]
        return {"outages": current, "customers_affected": sum(o["impact"]["customers"] for o in current)}


class UpcomingOutagesSensor(UnisonEntity, SensorEntity):
    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "outages"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _unrecorded_attributes = frozenset({"outages"})

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "upcoming_outages", "Upcoming Outages")

    @property
    def native_value(self) -> int:
        return len(self._upcoming(datetime.now(NZ)))

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        now = datetime.now(NZ)
        upcoming = sorted(self._upcoming(now), key=lambda o: o.start or now)
        return {
            "outages": [describe(o, now) for o in upcoming],
            "customers_affected": sum(o.customers for o in upcoming),
        }


class OutageStatsSensor(UnisonEntity, SensorEntity):
    """Customers currently without power, plus statistics over the history/forecast window."""

    _attr_icon = "mdi:chart-box"
    _attr_native_unit_of_measurement = "customers"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _unrecorded_attributes = frozenset({"statistics", "cancelled_outages"})

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "outage_stats", "Outage Statistics")

    @property
    def native_value(self) -> int:
        return sum(o.customers for o in self._filtered() if is_current(o))

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        now = datetime.now(NZ)
        window = [
            o for o in self._filtered()
            if is_current(o)
            or (o.state == "Scheduled" and in_days(o.start, now, ahead=self._forecast_days))
            or in_days(o.end or o.start, now, back=self._history_days)
        ]
        cancelled = [o for o in window if o.status == "Cancelled"]
        areas = sorted({o.area for o in window if o.area})
        customers = sum(o.customers for o in window)
        return {
            "statistics": {
                "total_outages": len(window),
                "total_customers_affected": customers,
                "average_customers_per_outage": round(customers / len(window), 2) if window else 0,
                "unique_areas_affected": len(areas),
                "areas_list": areas,
                "outage_types": {
                    "planned": sum(1 for o in window if o.planned),
                    "unplanned": sum(1 for o in window if not o.planned),
                },
            },
            "cancelled_outages": {
                "count": len(cancelled),
                "outages": [describe(o, now) for o in cancelled],
                "customers_affected": sum(o.customers for o in cancelled),
            },
        }


class NextOutageAtHomeSensor(UnisonEntity, SensorEntity):
    """Start of the next scheduled outage whose area covers Home Assistant's home location."""

    _attr_icon = "mdi:home-lightning-bolt"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "next_outage_at_home", "Next Planned Outage at Home")

    def _next(self) -> Optional[Outage]:
        now = datetime.now(NZ)
        upcoming = [o for o in self._regional() if o.at_home and is_upcoming(o) and o.start and o.start > now]
        return min(upcoming, key=lambda o: o.start, default=None)

    @property
    def native_value(self) -> Optional[datetime]:
        # The outage's overall times, as Unison publishes them; its per-area windows can be odd.
        outage = self._next()
        return outage.start if outage else None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        outage = self._next()
        return describe(outage, datetime.now(NZ)) if outage else {}
