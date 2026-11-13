"""DataUpdateCoordinator for Unison Outages."""
import asyncio
import json
import logging
from typing import List

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL, DOMAIN, MAX_STALE_UPDATES, UPDATE_INTERVAL
from .outages import Outage, home_windows, parse_outages

_LOGGER = logging.getLogger(__name__)


class UnisonNzDataUpdateCoordinator(DataUpdateCoordinator[List[Outage]]):
    """Fetches all outages on the Unison network every few minutes."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        self._failures = 0

    def _parse(self, body: bytes) -> List[Outage]:
        outages = parse_outages(json.loads(body))
        lat, lon = self.hass.config.latitude, self.hass.config.longitude
        for outage in outages:
            outage.at_home = bool(home_windows(outage, lat, lon))
        return outages

    async def _async_update_data(self) -> List[Outage]:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                API_URL,
                headers={"Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Unison API returned HTTP {response.status}")
                body = await response.read()
            # The response is ~2 MB (it includes outage area polygons), so parse it off the event loop.
            outages = await self.hass.async_add_executor_job(self._parse, body)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, UpdateFailed) as err:
            self._failures += 1
            # Ride out short API blips with the last good data rather than going unavailable.
            if self.data is not None and self._failures <= MAX_STALE_UPDATES:
                _LOGGER.warning("Unison update failed (%s), keeping last data (%d/%d)", err, self._failures, MAX_STALE_UPDATES)
                return self.data
            raise UpdateFailed(f"Unison update failed: {err}") from err
        self._failures = 0
        return outages
