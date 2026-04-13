"""Statistics sensor for Unison Outages."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Any, Dict

from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import STATE_UNKNOWN
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base import UnisonNzBaseSensor

class UnisonNztatsSensor(UnisonNzBaseSensor):
    """Sensor for outage statistics and historical data."""

    def __init__(
        self, 
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        region: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, region)
        self._attr_name = f"Outage Statistics{self._display_region}"
        self._attr_unique_id = f"{entry.entry_id}_outage_stats"
        self._attr_icon = "mdi:chart-box"
        self._attr_native_unit_of_measurement = "customers"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | str:
        """Return total customers currently without power in the region."""
        if self.coordinator.data is None:
            return STATE_UNKNOWN
        nz_now = datetime.now().astimezone(ZoneInfo("Pacific/Auckland"))
        outages = self._filter_outages(nz_now)
        return sum(
            o.get("customersOff", 0)
            for o in outages
            if self._is_current(o, nz_now)
        )

    def _get_cancelled_outages(self, outages, nz_now):
        """Get cancelled outages."""
        return [
            self._format_outage(outage, nz_now)
            for outage in outages
            if outage.get("outageStatus") == "Cancelled"
        ]

    def _calculate_stats(self, outages, nz_now):
        """Calculate outage statistics."""
        if not outages:
            return {}
            
        total_customers = sum(o.get("customersOff", 0) for o in outages)
        areas = set(o.get("areaAffected", "Unknown") for o in outages)
        
        return {
            "total_outages": len(outages),
            "total_customers_affected": total_customers,
            "average_customers_per_outage": round(total_customers / len(outages), 2),
            "unique_areas_affected": len(areas),
            "areas_list": sorted(list(areas)),
            "outage_types": {
                "planned": len([o for o in outages if o.get("outageType", "").startswith("Planned")]),
                "unplanned": len([o for o in outages if o.get("outageType", "").startswith("Unplanned")])
            }
        }

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}

        nz_now = datetime.now().astimezone(ZoneInfo("Pacific/Auckland"))
        history_cutoff = nz_now - timedelta(days=self._history_days)
        forecast_cutoff = nz_now + timedelta(days=self._forecast_days)
        all_outages = self._filter_outages(nz_now)

        def _in_window(o: dict) -> bool:
            state = o.get("outageState", "")
            if state == "Current":
                return True
            if state == "Scheduled":
                ref_raw = o.get("startTime")
                cutoff = forecast_cutoff
            else:  # Recent or other historical state
                ref_raw = o.get("finishTime") or o.get("startTime")
                cutoff = None  # lower bound check
            if not ref_raw:
                return False
            try:
                ref = datetime.fromisoformat(ref_raw)
                if ref.tzinfo is None:
                    ref = ref.replace(tzinfo=ZoneInfo("Pacific/Auckland"))
                if state == "Scheduled":
                    return ref <= cutoff
                return ref >= history_cutoff
            except (ValueError, TypeError):
                return False

        outages = [o for o in all_outages if _in_window(o)]
        cancelled = self._get_cancelled_outages(outages, nz_now)

        return {
            "statistics": self._calculate_stats(outages, nz_now),
            "cancelled_outages": {
                "count": len(cancelled),
                "outages": cancelled,
                "customers_affected": sum(o["impact"]["customers"] for o in cancelled),
            },
            "last_updated": self.coordinator.last_update_success,
        }