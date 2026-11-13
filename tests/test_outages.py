"""Tests for custom_components/unison_nz/outages.py. Run: python3 -m unittest discover tests"""
import importlib.util
import pathlib
import unittest
from datetime import datetime

_PATH = pathlib.Path(__file__).parents[1] / "custom_components" / "unison_nz" / "outages.py"
_spec = importlib.util.spec_from_file_location("outages", _PATH)
outages = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(outages)

NZ = outages.NZ
# A made-up square of land and a point inside / outside it ([lon, lat]).
SQUARE = [[170.0, -40.0], [170.1, -40.0], [170.1, -40.1], [170.0, -40.1], [170.0, -40.0]]
INSIDE, OUTSIDE = (-40.05, 170.05), (-40.5, 170.5)


def record(**kw):
    base = {
        "outageID": "SP 1", "outageType": "Planned Outage", "outageStatus": "Scheduled", "isPlanned": True,
        "outageState": "Scheduled", "interruptionReason": " Network Upgrades ", "customersOff": 120,
        "areaAffected": "EXAMPLE STREET,SAMPLE ROAD", "networkRegion": "Rotorua",
        "startTime": "2026-11-17T19:30:00+00:00", "finishTime": "2026-11-18T03:30:00+00:00",
        "lastUpdatedTime": "2026-11-10T01:00:00+00:00",
        "outageWindows": [{"type": "Window", "status": "Scheduled", "customers": 100,
                           "startTime": "2026-11-17T20:00:00+00:00", "finishTime": "2026-11-18T02:30:00+00:00",
                           "outageArea": [SQUARE]}],
    }
    base.update(kw)
    return base


class Parse(unittest.TestCase):
    def test_times_are_utc_and_described_in_nz(self):
        o = outages.parse_outages([record()])[0]
        self.assertEqual(o.start.utcoffset().total_seconds(), 0)
        d = outages.describe(o, datetime(2026, 11, 13, 12, 0, tzinfo=NZ))
        # Same shape as v0.1, which automations and dashboards use; 19:30 UTC = 08:30 NZDT next day.
        self.assertEqual(d["time"]["start"], "2026-11-18 08:30")
        self.assertEqual(d["time"]["friendly_start"], "08:30 AM, 18 Nov")
        self.assertEqual(d["time"]["duration"], "8h")
        self.assertEqual(d["time"]["until"], "116h 30m")
        self.assertEqual(d["impact"], {"customers": 120, "severity": "medium", "type": "Planned Outage", "status": "Scheduled"})
        self.assertEqual(d["location"]["region"], "Rotorua")
        self.assertEqual(d["reason"], "Network Upgrades")

    def test_times_without_offset_are_nz(self):
        o = outages.parse_outages([record(startTime="2026-11-18T08:30:00")])[0]
        self.assertEqual(o.start.astimezone(NZ).hour, 8)

    def test_malformed_records_are_skipped_or_defaulted(self):
        got = outages.parse_outages([None, "x", {"outageID": "A", "customersOff": "n/a", "startTime": "bad"}])
        self.assertEqual(len(got), 1)
        self.assertEqual((got[0].customers, got[0].start, got[0].windows), (0, None, []))

    def test_not_a_list_raises(self):
        with self.assertRaises(ValueError):
            outages.parse_outages({"error": "nope"})


class Filters(unittest.TestCase):
    def test_combined_region(self):
        o = outages.parse_outages([record(networkRegion="Napier, Hastings")])[0]
        self.assertTrue(outages.in_region(o, "Hawke's Bay"))
        self.assertFalse(outages.in_region(o, "Rotorua"))
        self.assertTrue(outages.in_region(o, "All Regions"))

    def test_taupo_without_macron(self):
        self.assertTrue(outages.in_region(outages.parse_outages([record(networkRegion="Taupo")])[0], "Taupō"))

    def test_areas(self):
        o = outages.parse_outages([record()])[0]
        self.assertTrue(outages.matches_areas(o, []))
        self.assertTrue(outages.matches_areas(o, ["sample road"]))
        self.assertFalse(outages.matches_areas(o, ["elsewhere"]))

    def test_current_and_upcoming(self):
        cur = outages.parse_outages([record(outageState="Current", outageStatus="Partial Restoration")])[0]
        cancelled = outages.parse_outages([record(outageStatus="Cancelled")])[0]
        self.assertTrue(outages.is_current(cur))
        self.assertTrue(outages.is_upcoming(outages.parse_outages([record()])[0]))
        self.assertFalse(outages.is_upcoming(cancelled))


class Home(unittest.TestCase):
    def test_point_in_area(self):
        o = outages.parse_outages([record()])[0]
        self.assertEqual(len(outages.home_windows(o, *INSIDE)), 1)
        self.assertEqual(outages.home_windows(o, *OUTSIDE), [])

    def test_nested_polygons_are_accepted(self):
        o = outages.parse_outages([record(outageWindows=[{"type": "Window", "status": "Scheduled", "outageArea": [[SQUARE]]}])])[0]
        self.assertEqual(len(outages.home_windows(o, *INSIDE)), 1)


if __name__ == "__main__":
    unittest.main()
