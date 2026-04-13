"""Upcoming outages sensor."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Any, Dict, List

from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import STATE_UNKNOWN
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base import UnisonNzBaseSensor

class UnisonUpcomingOutagesSensor(UnisonNzBaseSensor):
    """Sensor for upcoming outages."""

    def __init__(
        self, 
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        region: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, region)
        self._attr_name = f"Upcoming Outages{self._display_region}"
        self._attr_unique_id = f"{entry.entry_id}_upcoming_outages"
        self._attr_icon = "mdi:calendar-clock"
        self._attr_native_unit_of_measurement = "outages"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    def _upcoming_in_window(self, outages: List[dict], nz_now: datetime) -> List[dict]:
        """Return upcoming outages whose start time is within the forecast window."""
        cutoff = nz_now + timedelta(days=self._forecast_days)
        result = []
        for o in outages:
            if not self._is_upcoming(o, nz_now):
                continue
            start_raw = o.get("startTime")
            if not start_raw:
                continue
            try:
                start = datetime.fromisoformat(start_raw)
                if start.tzinfo is None:
                    start = start.replace(tzinfo=ZoneInfo("Pacific/Auckland"))
                if start <= cutoff:
                    result.append(o)
            except (ValueError, TypeError):
                continue
        return result

    @property
    def native_value(self) -> int | str:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return STATE_UNKNOWN
        nz_now = datetime.now().astimezone(ZoneInfo("Pacific/Auckland"))
        return len(self._upcoming_in_window(self._filter_outages(nz_now), nz_now))

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}
        nz_now = datetime.now().astimezone(ZoneInfo("Pacific/Auckland"))
        upcoming = [
            self._format_outage(outage, nz_now)
            for outage in self._upcoming_in_window(self._filter_outages(nz_now), nz_now)
        ]
        return {
            "outages": upcoming,
            "customers_affected": sum(o["impact"]["customers"] for o in upcoming),
            "last_updated": self.coordinator.last_update_success,
        }