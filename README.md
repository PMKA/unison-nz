# Unison Outages

A Home Assistant integration for monitoring electricity outages on the Unison Networks distribution network, covering Hawke's Bay, Rotorua, and Taupō.

---

## Regions supported

- Hawke's Bay (Hastings and Napier)
- Rotorua
- Taupō
- All Regions

You can add a separate integration entry for each region if needed.

---

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant.
2. Go to **Integrations**, click the three-dot menu, and choose **Custom repositories**.
3. Add the URL of this repository and set the category to **Integration**.
4. Search for **Unison Outages** and install it.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/unison_nz` folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

---

## Configuration

After installation, add the integration via **Settings > Devices and Services > Add Integration > Unison Outages**.

| Field | Description | Default |
|---|---|---|
| Region | Region to monitor | Rotorua |
| Areas | Optional comma-separated list of suburbs or street names to filter results (e.g. `Hospital Hill, Taradale Road`) | All areas |
| Days of history | How many days of recent/completed outages to include in statistics (0-30) | 7 |
| Days forecast | How far ahead to show scheduled outages (1-90) | 30 |

Duplicate entries for the same region are blocked. Adding a second entry for a different region is fully supported.

Areas and the day ranges can be changed later from the integration's Configure button.

---

## Sensors

Five entities are created per integration entry, grouped under one device.

### At home

These use your Home Assistant home location (Settings, System, General) and the outage areas Unison publishes, so they tell you whether an outage actually covers your house, without needing to set any areas.

- **Power Outage at Home** (`binary_sensor`): on while a current outage covers your home. Attribute `outages` lists them.
- **Next Planned Outage at Home** (`sensor`, timestamp): when the next scheduled outage covering your home starts. Its attributes are the outage object described below.

Every outage object also has `affects_home: true/false`, so the other sensors can be filtered the same way in templates.

### Current Outages

**Entity:** `sensor.current_outages`

State: count of outages currently active in the region.

Attributes:

| Attribute | Description |
|---|---|
| `outages` | List of active outage objects (see below) |
| `customers_affected` | Total customers currently without power |

Active outages include statuses: Active, Partial Restoration, Under Investigation.

---

### Upcoming Outages

**Entity:** `sensor.upcoming_outages`

State: count of scheduled outages starting within the configured forecast window.

Attributes:

| Attribute | Description |
|---|---|
| `outages` | List of scheduled outage objects |
| `customers_affected` | Total customers affected by scheduled outages |

---

### Outage Statistics

**Entity:** `sensor.outage_statistics`

State: total customers currently without power in the region (useful as a dashboard badge).

Attributes:

| Attribute | Description |
|---|---|
| `statistics` | Aggregate stats for outages within the history and forecast window |
| `statistics.total_outages` | Total outage count in window |
| `statistics.total_customers_affected` | Total customers affected across all outages in window |
| `statistics.average_customers_per_outage` | Average customers per outage |
| `statistics.unique_areas_affected` | Number of distinct areas affected |
| `statistics.areas_list` | Sorted list of affected area names |
| `statistics.outage_types.planned` | Count of planned outages |
| `statistics.outage_types.unplanned` | Count of unplanned outages |
| `cancelled_outages` | Details of cancelled outages within the window |

---

### Outage object structure

Each entry in an `outages` list has the following shape:

Times are in New Zealand local time.

```yaml
id: "SP 421000000"
area: "EXAMPLE STREET,SAMPLE ROAD"
reason: "Network Maintenance"
time:
  start: "2026-04-15 09:00"
  end: "2026-04-15 15:00"
  friendly_start: "09:00 AM, 15 Apr"
  friendly_end: "03:00 PM, 15 Apr"
  duration: "6h"
  remaining: "4h 32m"   # null if already ended
  until: null            # null if already started
impact:
  customers: 61
  severity: "low"        # low / medium (>100) / high (>500)
  type: "Planned Outage"
  status: "Scheduled"
location:
  region: "Rotorua"
  coordinates:           # always null: Unison now publishes outage areas instead of a point
    latitude: null
    longitude: null
    radius: null
affects_home: false
```

---

## Updates

Data is refreshed every 5 minutes from the Unison outage API. If an update fails, the last data is kept for up to 30 minutes before the sensors go unavailable.

---

## Requirements

- Home Assistant 2024.12.0 or later

---

## License

MIT, see [LICENSE](LICENSE).

This project is not affiliated with or endorsed by Unison Networks Limited.
