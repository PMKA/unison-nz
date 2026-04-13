"""Current outages sensor."""
from datetime import datetime
from zoneinfo import ZoneInfo
import logging
from typing import Any, Dict

from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import STATE_UNKNOWN
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base import UnisonOutagesBaseSensor

_LOGGER = logging.getLogger(__name__)

class UnisonCurrentOutagesSensor(UnisonOutagesBaseSensor):
    """Sensor for current outages."""

    def __init__(
        self, 
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        region: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, region)
        self._attr_name = f"Current Outages{self._display_region}"
        self._attr_unique_id = f"{entry.entry_id}_current_outages"
        self._attr_icon = "mdi:flash-off"
        self._attr_native_unit_of_measurement = "outages"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | str:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return STATE_UNKNOWN
        nz_now = datetime.now().astimezone(ZoneInfo("Pacific/Auckland"))
        outages = self._filter_outages(nz_now)
        return len([o for o in outages if self._is_current(o, nz_now)])

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}
        nz_now = datetime.now().astimezone(ZoneInfo("Pacific/Auckland"))
        outages = self._filter_outages(nz_now)
        current = [
            self._format_outage(outage, nz_now)
            for outage in outages
            if self._is_current(outage, nz_now)
        ]
        return {
            "outages": current,
            "customers_affected": sum(o["impact"]["customers"] for o in current),
            "last_updated": self.coordinator.last_update_success
        }