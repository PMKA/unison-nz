# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-04-14

### Added

- Initial release.
- Three sensors per integration entry: Current Outages, Upcoming Outages, Outage Statistics.
- Region filtering for Hawke's Bay (Hastings and Napier), Rotorua, Taupō, and All Regions.
- Optional area/street-level filtering within a region.
- Configurable history window (0-30 days) and forecast window (1-90 days).
- Outage attributes include area, reason, times, duration, customers affected, severity, and coordinates.
- Duplicate region entries blocked via unique ID in config flow.
- HACS-compatible repository layout under `custom_components/unison_outages/`.
- Integration icon at 256x256 PNG.

### Fixed

- Outages with a null `finishTime` (Under Investigation status) no longer crash the sensor.
- Taupō region filtering now correctly matches the API response which omits the macron.
- `_is_current` now includes Partial Restoration and Under Investigation statuses, not just Active.
- `_is_upcoming` correctly uses `outageState == "Scheduled"` only; the `"Future"` state does not exist in the API.
- Planned/Unplanned outage type counts now use `startswith` to avoid the substring match bug where "Unplanned" was also counted as "Planned".
- History and forecast day settings from config flow are now actually applied to sensor filtering.
- `aiohttp.ClientSession` no longer created manually; uses HA-managed `async_get_clientsession`.
- `timeout` parameter corrected from bare integer to `aiohttp.ClientTimeout`.
- API URL uses the constant from `const.py` rather than a hard-coded string.
