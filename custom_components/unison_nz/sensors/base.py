"""Base sensor for Unison Outages."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging
from typing import Any, List, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.config_entries import ConfigEntry

from ..const import (
    CONF_HISTORY_DAYS,
    CONF_FORECAST_DAYS,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_FORECAST_DAYS,
)

_LOGGER = logging.getLogger(__name__)

class UnisonNzBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Unison Outages sensors."""

    def __init__(
        self, 
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        region: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._region = region
        self._display_region = f" ({region})" if region != "All Regions" else ""
        self._areas = [
            area.lower().strip() 
            for area in entry.data.get("areas", "").split(",") 
            if area.strip()
        ]
        self._history_days = entry.data.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS)
        self._forecast_days = entry.data.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS)

    def _filter_outages(self, nz_now: datetime) -> List[dict[str, Any]]:
        """Filter outages by region and date."""
        if not self.coordinator.data:
            return []
        outages = self.coordinator.data
        if self._region != "All Regions":
            if self._region == "Hawke's Bay":
                outages = [o for o in outages if o.get("networkRegion") in ["Hastings", "Napier"]]
            elif self._region == "Taupō":
                # API returns "Taupo" without macron
                outages = [o for o in outages if o.get("networkRegion") == "Taupo"]
            else:
                outages = [o for o in outages if o.get("networkRegion") == self._region]
        return self._filter_by_area(outages)

    def _filter_by_area(self, outages: List[dict[str, Any]]) -> List[dict[str, Any]]:
        """Filter outages by configured areas."""
        if not self._areas:
            return outages
        
        _LOGGER.debug("Filtering outages by areas: %s", self._areas)
        filtered = []
        for outage in outages:
            area = outage.get("areaAffected", "").lower()
            _LOGGER.debug("Checking area: %s", area)
            area_parts = set(area.replace(',', ' ').split())
            
            for configured_area in self._areas:
                if (configured_area in area or 
                    any(configured_area == part for part in area_parts)):
                    _LOGGER.debug("Match found for %s in %s", configured_area, area)
                    filtered.append(outage)
                    break
        
        return filtered

    def _is_current(self, outage: dict[str, Any], nz_now: datetime) -> bool:
        """Check if outage is current."""
        return (outage.get("outageState") == "Current" and
                outage.get("outageStatus") in ["Active", "Partial Restoration", "Under Investigation"])

    def _is_upcoming(self, outage: dict[str, Any], nz_now: datetime) -> bool:
        """Check if outage is upcoming."""
        return (outage.get("outageState") == "Scheduled" and
                outage.get("outageStatus") not in ["Cancelled", "Completed"])

    def _format_outage(self, outage: dict[str, Any], nz_now: datetime) -> Dict[str, Any]:
        """Format outage information with enhanced details."""
        start_raw = outage.get("startTime")
        end_raw = outage.get("finishTime")  # can be null for under-investigation outages

        start_time = datetime.fromisoformat(start_raw) if start_raw else nz_now
        end_time = datetime.fromisoformat(end_raw) if end_raw else None

        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=ZoneInfo("Pacific/Auckland"))
        if end_time is not None and end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=ZoneInfo("Pacific/Auckland"))

        duration = (end_time - start_time) if end_time else None
        time_remaining = (end_time - nz_now) if end_time and end_time > nz_now else None
        time_until = start_time - nz_now if start_time > nz_now else None
        customers = outage.get("customersOff", 0)

        return {
            "id": outage.get("outageID", "Unknown"),
            "area": outage.get("areaAffected", "Unknown"),
            "reason": outage.get("interruptionReason", "").strip(),
            "time": {
                "start": start_time.strftime("%Y-%m-%d %H:%M"),
                "end": end_time.strftime("%Y-%m-%d %H:%M") if end_time else None,
                "friendly_start": start_time.strftime("%I:%M %p, %d %b"),
                "friendly_end": end_time.strftime("%I:%M %p, %d %b") if end_time else None,
                "duration": self._format_duration(duration) if duration else None,
                "remaining": self._format_duration(time_remaining) if time_remaining else None,
                "until": self._format_duration(time_until) if time_until else None,
            },
            "impact": {
                "customers": customers,
                "severity": self._calculate_severity(customers),
                "type": outage.get("outageType", "Unknown").replace("Planned - ", ""),
                "status": outage.get("outageStatus", "Unknown"),
            },
            "location": {
                "region": outage.get("networkRegion", "") or "Unknown",
                "coordinates": {
                    "latitude": outage.get("latitude"),
                    "longitude": outage.get("longitude"),
                    "radius": outage.get("radius"),
                },
            },
        }

    def _calculate_severity(self, customers: int) -> str:
        """Calculate severity level based on customer impact."""
        if customers > 500:
            return "high"
        elif customers > 100:
            return "medium"
        return "low"

    def _format_duration(self, td: timedelta) -> str:
        """Return a human-readable duration string."""
        total_minutes = max(0, int(td.total_seconds() / 60))
        hours, minutes = divmod(total_minutes, 60)
        if hours == 0:
            return f"{minutes}m"
        if minutes == 0:
            return f"{hours}h"
        return f"{hours}h {minutes}m"

