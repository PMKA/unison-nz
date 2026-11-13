"""Parsing and matching of Unison outage data (no Home Assistant imports, so it can be unit tested)."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence
from zoneinfo import ZoneInfo

NZ = ZoneInfo("Pacific/Auckland")

CURRENT_STATUSES = ("Active", "Partial Restoration", "Under Investigation", "Ongoing")
INACTIVE_STATUSES = ("Cancelled", "Completed")

# Regions offered in the config flow -> networkRegion values the API uses. The API can also
# combine them (e.g. "Napier, Hastings") and drops the macron from Taupō.
REGION_NAMES = {
    "Hawke's Bay": ("hastings", "napier"),
    "Rotorua": ("rotorua",),
    "Taupō": ("taupo",),
}

Ring = Sequence[Sequence[float]]  # [[lon, lat], ...]


@dataclass
class Window:
    kind: str
    status: str
    start: Optional[datetime]
    end: Optional[datetime]
    customers: int
    rings: List[Ring] = field(default_factory=list)


@dataclass
class Outage:
    id: str
    state: str
    status: str
    planned: bool
    kind: str
    reason: str
    area: str
    region: str
    customers: int
    start: Optional[datetime]
    end: Optional[datetime]
    updated: Optional[datetime]
    windows: List[Window]
    at_home: bool = False


def _time(value: Any) -> Optional[datetime]:
    """API times are ISO 8601, now in UTC; treat any without an offset as NZ local."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=NZ)


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _rings(area: Any) -> List[Ring]:
    """outageArea is a list of rings ([[lon, lat], ...]); also accept polygons-of-rings."""
    rings: List[Ring] = []
    for item in area or []:
        if item and isinstance(item[0], (list, tuple)) and item[0] and isinstance(item[0][0], (list, tuple)):
            rings.extend(item)
        elif item:
            rings.append(item)
    return rings


def parse_outages(raw: Any) -> List[Outage]:
    """Turn the /api/outages response into Outage records, skipping anything malformed."""
    if not isinstance(raw, list):
        raise ValueError(f"Expected a list of outages, got {type(raw).__name__}")
    outages = []
    for o in raw:
        if not isinstance(o, dict):
            continue
        windows = [
            Window(
                kind=str(w.get("type") or ""),
                status=str(w.get("status") or ""),
                start=_time(w.get("startTime")),
                end=_time(w.get("finishTime")),
                customers=_int(w.get("customers")),
                rings=_rings(w.get("outageArea")),
            )
            for w in o.get("outageWindows") or []
            if isinstance(w, dict)
        ]
        kind = str(o.get("outageType") or "")
        outages.append(Outage(
            id=str(o.get("outageID") or "Unknown"),
            state=str(o.get("outageState") or ""),
            status=str(o.get("outageStatus") or ""),
            planned=bool(o.get("isPlanned", kind.lower().startswith("planned"))),
            kind=kind,
            reason=str(o.get("interruptionReason") or "").strip(),
            area=str(o.get("areaAffected") or ""),
            region=str(o.get("networkRegion") or ""),
            customers=_int(o.get("customersOff")),
            start=_time(o.get("startTime")),
            end=_time(o.get("finishTime")),
            updated=_time(o.get("lastUpdatedTime")),
            windows=windows,
        ))
    return outages


def in_region(outage: Outage, region: str) -> bool:
    names = REGION_NAMES.get(region)
    if not names:  # "All Regions"
        return True
    regions = {r.strip().lower() for r in outage.region.split(",")}
    return any(n in regions for n in names)


def matches_areas(outage: Outage, areas: Sequence[str]) -> bool:
    """True if no areas are configured, or any configured area appears in areaAffected."""
    if not areas:
        return True
    text = outage.area.lower()
    return any(a in text for a in areas)


def is_current(outage: Outage) -> bool:
    return outage.state == "Current" and outage.status not in INACTIVE_STATUSES


def is_upcoming(outage: Outage) -> bool:
    return outage.state == "Scheduled" and outage.status not in INACTIVE_STATUSES


def _inside(lon: float, lat: float, ring: Ring) -> bool:
    """Ray casting point-in-polygon test; ring points are [lon, lat]."""
    hit = False
    for i in range(len(ring)):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[i - 1][0], ring[i - 1][1]
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def home_windows(outage: Outage, lat: float, lon: float) -> List[Window]:
    """The outage's windows whose area contains the given location."""
    return [w for w in outage.windows if any(_inside(lon, lat, r) for r in w.rings)]


def in_days(when: Optional[datetime], now: datetime, back: float = 0, ahead: float = 0) -> bool:
    if when is None:
        return False
    return now - timedelta(days=back) <= when <= now + timedelta(days=ahead)


def duration_text(td: Optional[timedelta]) -> Optional[str]:
    if td is None:
        return None
    minutes = max(0, int(td.total_seconds() // 60))
    hours, minutes = divmod(minutes, 60)
    if not hours:
        return f"{minutes}m"
    return f"{hours}h" if not minutes else f"{hours}h {minutes}m"


def severity(customers: int) -> str:
    if customers > 500:
        return "high"
    return "medium" if customers > 100 else "low"


def describe(outage: Outage, now: datetime) -> Dict[str, Any]:
    """Attribute dict in the same shape as v0.1 (templates rely on it), with times in NZ local time.

    location.coordinates is kept for compatibility but is always empty: the API replaced the
    point and radius with outage area polygons.
    """
    start = outage.start.astimezone(NZ) if outage.start else None
    end = outage.end.astimezone(NZ) if outage.end else None
    return {
        "id": outage.id,
        "area": outage.area or "Unknown",
        "reason": outage.reason,
        "time": {
            "start": start.strftime("%Y-%m-%d %H:%M") if start else None,
            "end": end.strftime("%Y-%m-%d %H:%M") if end else None,
            "friendly_start": start.strftime("%I:%M %p, %d %b") if start else None,
            "friendly_end": end.strftime("%I:%M %p, %d %b") if end else None,
            "duration": duration_text(end - start) if start and end else None,
            "remaining": duration_text(end - now) if end and end > now else None,
            "until": duration_text(start - now) if start and start > now else None,
        },
        "impact": {
            "customers": outage.customers,
            "severity": severity(outage.customers),
            "type": outage.kind or "Unknown",
            "status": outage.status or "Unknown",
        },
        "location": {
            "region": outage.region or "Unknown",
            "coordinates": {"latitude": None, "longitude": None, "radius": None},
        },
        "affects_home": outage.at_home,
    }
