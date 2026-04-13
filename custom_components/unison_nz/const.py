"""Constants for Unison Outages."""
from datetime import timedelta
from typing import Final

DOMAIN = "unison_nz"
API_URL = "https://www.unison.co.nz/api/outage"

# Configuration
CONF_REGION = "region"
CONF_AREAS = "areas"
CONF_HISTORY_DAYS = "days_history"
CONF_FORECAST_DAYS = "days_forecast"

# Defaults
DEFAULT_NAME = "Unison Outages"
DEFAULT_REGION = "Rotorua"
DEFAULT_HISTORY_DAYS = 7
DEFAULT_FORECAST_DAYS = 30

# Limits
MIN_HISTORY_DAYS = 0
MAX_HISTORY_DAYS = 30
MIN_FORECAST_DAYS = 1
MAX_FORECAST_DAYS = 90

# Regions
REGIONS = ["All Regions", "Hawke's Bay", "Rotorua", "Taupō"]

# Update interval
UPDATE_INTERVAL = timedelta(minutes=5)
