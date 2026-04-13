"""DataUpdateCoordinator for Unison Outages."""
import logging
import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from .const import DOMAIN, API_URL, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

class UnisonOutagesDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Unison outages data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via API."""
        session = async_get_clientsession(self.hass)
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 HomeAssistant",
                "Accept": "application/json",
                "Referer": "https://www.unison.co.nz/outages/",
            }
            async with session.get(
                API_URL,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"API request failed with status {response.status}")
                return await response.json()

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        except Exception as err:
            raise UpdateFailed(f"Error parsing data: {err}")