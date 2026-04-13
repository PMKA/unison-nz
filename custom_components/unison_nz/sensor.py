"""Sensor platform for Unison Outages."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_REGION, DEFAULT_REGION
from .sensors import (
    UnisonCurrentOutagesSensor,
    UnisonUpcomingOutagesSensor,
    UnisonNztatsSensor,
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Unison Outages sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    region = entry.data.get(CONF_REGION, DEFAULT_REGION)
    
    sensors = [
        UnisonCurrentOutagesSensor(coordinator, entry, region),
        UnisonUpcomingOutagesSensor(coordinator, entry, region),
        UnisonNztatsSensor(coordinator, entry, region)
    ]
    
    async_add_entities(sensors, True)
