# Changelog

All notable changes to this project will be documented in this file.

---

## [0.2.1]

### What's Changed

- Added an MIT licence.
- Manifest tidied up so it passes Home Assistant's and HACS's validation, which now run on every push.

---

## [0.2.0]

### What's Fixed

- Unison moved their outage data to a new address in early November, so every sensor went unavailable. The integration now uses the new one.
- Times are shown in New Zealand time. The new data comes in UTC and would otherwise have been 13 hours out.
- Hawke's Bay now includes outages listed under both Napier and Hastings.
- Sensors no longer report "unknown" as a number, which Home Assistant logged as an error.

### What's New

- Power Outage at Home and Next Planned Outage at Home, using your Home Assistant home location and Unison's outage areas.
- Areas and day ranges can be changed after setup.
- A short API outage no longer makes the sensors unavailable straight away (the last data is kept for up to 30 minutes).
- Sensors are grouped under a device, and the long outage lists are no longer stored in the recorder database.

### Notes

- Existing sensors keep their entity IDs and history. The outage attribute format is unchanged, except `location.coordinates`, which is now always empty because Unison no longer provides it.
- The `last_updated` attribute was removed (it was a true/false value, not a time).
- Requires Home Assistant 2024.12 or later.

---

## [0.1.0] — Initial Release - 2026-04-14

### What's New

- Three sensors per integration entry: Current Outages, Upcoming Outages, Outage Statistics.
- Region filtering for Hawke's Bay (Hastings and Napier), Rotorua, Taupō, and All Regions.
- Optional area/street-level filtering within a region.
- Configurable history window (0-30 days) and forecast window (1-90 days).
- Outage attributes include area, reason, times, duration, customers affected, severity, and coordinates.
- Duplicate region entries blocked via unique ID in config flow.
- HACS-compatible repository layout under `custom_components/unison_nz/`.
- Integration icon at 256x256 PNG.

### What's Fixed

- Outages with a null `finishTime` (Under Investigation status) no longer crash the sensor.
- Taupō region filtering now correctly matches the API response which omits the macron.
- `_is_current` now includes Partial Restoration and Under Investigation statuses, not just Active.
- `_is_upcoming` correctly uses `outageState == "Scheduled"` only; the `"Future"` state does not exist in the API.
- Planned/Unplanned outage type counts now use `startswith` to avoid the substring match bug where "Unplanned" was also counted as "Planned".
- History and forecast day settings from config flow are now actually applied to sensor filtering.
- `aiohttp.ClientSession` no longer created manually; uses HA-managed `async_get_clientsession`.
- `timeout` parameter corrected from bare integer to `aiohttp.ClientTimeout`.
- API URL uses the constant from `const.py` rather than a hard-coded string.
