"""Test the Unison Outages config flow."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.unison_nz.const import (
    DOMAIN,
    CONF_REGION,
    CONF_HISTORY_DAYS,
    CONF_FORECAST_DAYS,
)

async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    # Test valid configuration
    with patch(
        "custom_components.unison_nz.config_flow.UnisonNzConfigFlow._async_current_entries",
        return_value=[],
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_REGION: "Rotorua",
                CONF_HISTORY_DAYS: 7,
                CONF_FORECAST_DAYS: 30,
            },
        )
        assert result2["type"] == "create_entry"
        assert result2["title"] == "Unison Outages"
        assert result2["data"] == {
            CONF_REGION: "Rotorua",
            CONF_HISTORY_DAYS: 7,
            CONF_FORECAST_DAYS: 30,
        }

async def test_invalid_days(hass: HomeAssistant) -> None:
    """Test we handle invalid day ranges."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Test invalid history days
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_REGION: "Rotorua",
            CONF_HISTORY_DAYS: 31,  # Too many history days
            CONF_FORECAST_DAYS: 30,
        },
    )
    assert result2["type"] == "form"
    assert result2["errors"]["days_history"] == "invalid_history_days"

    # Test invalid forecast days
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_REGION: "Rotorua",
            CONF_HISTORY_DAYS: 7,
            CONF_FORECAST_DAYS: 91,  # Too many forecast days
        },
    )
    assert result3["type"] == "form"
    assert result3["errors"]["days_forecast"] == "invalid_forecast_days" 