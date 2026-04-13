"""Config flow for Unison Outages integration."""
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_REGION,
    CONF_AREAS,
    CONF_HISTORY_DAYS,
    CONF_FORECAST_DAYS,
    DEFAULT_REGION,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_FORECAST_DAYS,
    MIN_HISTORY_DAYS,
    MAX_HISTORY_DAYS,
    MIN_FORECAST_DAYS,
    MAX_FORECAST_DAYS,
    REGIONS,
)

class UnisonOutagesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Unison Outages."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_REGION])
            self._abort_if_unique_id_configured()

            # Validate days
            if not MIN_HISTORY_DAYS <= user_input[CONF_HISTORY_DAYS] <= MAX_HISTORY_DAYS:
                errors["days_history"] = "invalid_history_days"
            if not MIN_FORECAST_DAYS <= user_input[CONF_FORECAST_DAYS] <= MAX_FORECAST_DAYS:
                errors["days_forecast"] = "invalid_forecast_days"

            if not errors:
                return self.async_create_entry(
                    title=f"Unison Outages - {user_input[CONF_REGION]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_REGION, default=DEFAULT_REGION): vol.In(REGIONS),
                    vol.Optional(CONF_AREAS): str,
                    vol.Required(
                        CONF_HISTORY_DAYS, default=DEFAULT_HISTORY_DAYS
                    ): vol.All(int, vol.Range(min=MIN_HISTORY_DAYS, max=MAX_HISTORY_DAYS)),
                    vol.Required(
                        CONF_FORECAST_DAYS, default=DEFAULT_FORECAST_DAYS
                    ): vol.All(int, vol.Range(min=MIN_FORECAST_DAYS, max=MAX_FORECAST_DAYS)),
                }
            ),
            errors=errors,
        )
