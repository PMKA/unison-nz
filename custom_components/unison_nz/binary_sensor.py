"""Binary sensor: is there a power outage at home right now."""
from datetime import datetime
from typing import Any, Dict, List

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .outages import NZ, Outage, describe, is_current
from .sensor import UnisonEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([OutageAtHomeSensor(hass.data[DOMAIN][entry.entry_id], entry)])


class OutageAtHomeSensor(UnisonEntity, BinarySensorEntity):
    """On while a current outage's area covers Home Assistant's home location."""

    _attr_icon = "mdi:home-lightning-bolt-outline"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "outage_at_home", "Power Outage at Home")

    def _current(self) -> List[Outage]:
        return [o for o in self._regional() if o.at_home and is_current(o)]

    @property
    def is_on(self) -> bool:
        return bool(self._current())

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        now = datetime.now(NZ)
        return {"outages": [describe(o, now) for o in self._current()]}
