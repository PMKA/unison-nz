"""Config flow for Unison Outages."""
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .const import (
    CONF_AREAS,
    CONF_FORECAST_DAYS,
    CONF_HISTORY_DAYS,
    CONF_REGION,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_REGION,
    DOMAIN,
    MAX_FORECAST_DAYS,
    MAX_HISTORY_DAYS,
    MIN_FORECAST_DAYS,
    MIN_HISTORY_DAYS,
    REGIONS,
)


def _settings_schema(current: Dict[str, Any]) -> Dict[Any, Any]:
    """Areas and day ranges, shared by setup and the options flow."""
    return {
        vol.Optional(CONF_AREAS, description={"suggested_value": current.get(CONF_AREAS, "")}): str,
        vol.Required(CONF_HISTORY_DAYS, default=current.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS)): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_HISTORY_DAYS, max=MAX_HISTORY_DAYS)
        ),
        vol.Required(CONF_FORECAST_DAYS, default=current.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS)): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_FORECAST_DAYS, max=MAX_FORECAST_DAYS)
        ),
    }


class UnisonNzConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> ConfigFlowResult:
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_REGION])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=f"Unison Outages - {user_input[CONF_REGION]}", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_REGION, default=DEFAULT_REGION): vol.In(REGIONS), **_settings_schema({})}
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return UnisonNzOptionsFlow()


class UnisonNzOptionsFlow(OptionsFlow):
    """Change areas and day ranges after setup (the region stays fixed per entry)."""

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=vol.Schema(_settings_schema(current)))
