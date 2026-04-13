"""Tests for Unison Outages sensors."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from custom_components.unison_nz.sensors import (
    UnisonCurrentOutagesSensor,
    UnisonUpcomingOutagesSensor,
    UnisonNztatsSensor,
)

@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = []
    return coordinator

@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.data = {
        "region": "Rotorua",
        "areas": "Owhata, Springfield Road"
    }
    return entry

@pytest.fixture
def sample_outage():
    """Create a sample outage."""
    return {
        "outageID": "TEST123",
        "utilityType": "Electricity",
        "outageType": "Planned - Essential",
        "outageStatus": "Active",
        "outageState": "Current",
        "areaAffected": "Test Area",
        "networkRegion": "Rotorua",
        "startTime": "2024-03-14T09:00:00+13:00",
        "finishTime": "2024-03-14T15:00:00+13:00",
        "latitude": -38.136387,
        "longitude": 176.325317,
        "radius": 500,
        "customersOff": 100,
        "interruptionReason": "Test Reason"
    }

def test_current_outages_sensor(mock_coordinator, mock_config_entry, sample_outage):
    """Test current outages sensor."""
    mock_coordinator.data = [sample_outage]
    sensor = UnisonCurrentOutagesSensor(mock_coordinator, mock_config_entry, "Rotorua")
    
    assert sensor.native_value == 1
    assert len(sensor.extra_state_attributes["outages"]) == 1
    outage = sensor.extra_state_attributes["outages"][0]
    assert outage["id"] == "TEST123"
    assert "coordinates" in outage["location"]
    assert outage["location"]["coordinates"]["latitude"] == -38.136387

def test_upcoming_outages_sensor(mock_coordinator, mock_config_entry, sample_outage):
    """Test upcoming outages sensor."""
    upcoming_outage = sample_outage.copy()
    upcoming_outage["outageState"] = "Scheduled"
    upcoming_outage["outageStatus"] = "Scheduled"
    mock_coordinator.data = [upcoming_outage]
    
    sensor = UnisonUpcomingOutagesSensor(mock_coordinator, mock_config_entry, "Rotorua")
    assert sensor.native_value == 1

def test_stats_sensor(mock_coordinator, mock_config_entry):
    """Test statistics sensor."""
    nz = ZoneInfo("Pacific/Auckland")
    now = datetime.now(nz)
    recent = (now - timedelta(days=2)).isoformat()
    future = (now + timedelta(days=5)).isoformat()
    mock_coordinator.data = [
        {"networkRegion": "Rotorua", "outageState": "Current", "outageStatus": "Active", "customersOff": 100, "areaAffected": "Area A", "startTime": now.isoformat(), "finishTime": future, "outageType": "Planned Outage", "outageID": "1", "latitude": -38.1, "longitude": 176.3, "radius": 500},
        {"networkRegion": "Rotorua", "outageState": "Scheduled", "outageStatus": "Scheduled", "customersOff": 200, "areaAffected": "Area B", "startTime": future, "finishTime": future, "outageType": "Planned Outage", "outageID": "2", "latitude": -38.1, "longitude": 176.3, "radius": 500},
        {"networkRegion": "Rotorua", "outageState": "Recent", "outageStatus": "Cancelled", "customersOff": 300, "areaAffected": "Area C", "startTime": recent, "finishTime": recent, "outageType": "Planned Outage", "outageID": "3", "latitude": -38.1, "longitude": 176.3, "radius": 500},
    ]

    sensor = UnisonNztatsSensor(mock_coordinator, mock_config_entry, "Rotorua")
    assert sensor.native_value == 3

    attributes = sensor.extra_state_attributes
    assert "statistics" in attributes
    assert "cancelled_outages" in attributes
    assert attributes["statistics"]["total_outages"] == 3
    assert attributes["statistics"]["total_customers_affected"] == 600
    assert attributes["cancelled_outages"]["count"] == 1

def test_area_filtering(mock_coordinator, mock_config_entry, sample_outage):
    """Test area filtering."""
    outage = sample_outage.copy()
    outage["areaAffected"] = "Owhata Road"
    mock_coordinator.data = [outage]
    
    sensor = UnisonCurrentOutagesSensor(mock_coordinator, mock_config_entry, "Rotorua")
    assert sensor.native_value == 1

def test_hawkes_bay_region_filtering(mock_coordinator, mock_config_entry):
    """Test Hawke's Bay region filtering."""
    mock_coordinator.data = [
        {"networkRegion": "Hastings", "outageState": "Current", "outageStatus": "Active"},
        {"networkRegion": "Napier", "outageState": "Current", "outageStatus": "Active"},
        {"networkRegion": "Rotorua", "outageState": "Current", "outageStatus": "Active"}
    ]
    
    sensor = UnisonCurrentOutagesSensor(mock_coordinator, mock_config_entry, "Hawke's Bay")
    assert sensor.native_value == 2

def test_outage_formatting(mock_coordinator, mock_config_entry, sample_outage):
    """Test outage formatting."""
    mock_coordinator.data = [sample_outage]
    sensor = UnisonCurrentOutagesSensor(mock_coordinator, mock_config_entry, "Rotorua")
    
    outage = sensor.extra_state_attributes["outages"][0]
    assert "time" in outage
    assert "impact" in outage
    assert "location" in outage
    assert "coordinates" in outage["location"]

def test_severity_calculation(mock_coordinator, mock_config_entry):
    """Test severity calculation."""
    outages = [
        {"networkRegion": "Rotorua", "customersOff": 50},  # low
        {"networkRegion": "Rotorua", "customersOff": 200},  # medium
        {"networkRegion": "Rotorua", "customersOff": 600}   # high
    ]
    
    sensor = UnisonCurrentOutagesSensor(mock_coordinator, mock_config_entry, "Rotorua")
    
    assert sensor._calculate_severity(50) == "low"
    assert sensor._calculate_severity(200) == "medium"
    assert sensor._calculate_severity(600) == "high"

def test_time_formatting(mock_coordinator, mock_config_entry, sample_outage):
    """Test time formatting in outage details."""
    mock_coordinator.data = [sample_outage]
    sensor = UnisonCurrentOutagesSensor(mock_coordinator, mock_config_entry, "Rotorua")
    
    outage = sensor.extra_state_attributes["outages"][0]
    time_info = outage["time"]
    
    assert "friendly_start" in time_info
    assert "friendly_end" in time_info
    assert "duration" in time_info
    assert time_info["friendly_start"].endswith("14 Mar")
    assert time_info["friendly_end"].endswith("14 Mar")

def test_stats_calculations(mock_coordinator, mock_config_entry):
    """Test detailed statistics calculations."""
    nz = ZoneInfo("Pacific/Auckland")
    now = datetime.now(nz)
    future = (now + timedelta(days=3)).isoformat()
    mock_coordinator.data = [
        {
            "networkRegion": "Rotorua",
            "outageState": "Current",
            "outageStatus": "Active",
            "customersOff": 100,
            "outageType": "Planned Outage",
            "areaAffected": "Area 1",
            "startTime": now.isoformat(),
            "finishTime": future,
            "outageID": "1", "latitude": -38.1, "longitude": 176.3, "radius": 500,
        },
        {
            "networkRegion": "Rotorua",
            "outageState": "Current",
            "outageStatus": "Active",
            "customersOff": 200,
            "outageType": "Unplanned Outage",
            "areaAffected": "Area 2",
            "startTime": now.isoformat(),
            "finishTime": future,
            "outageID": "2", "latitude": -38.1, "longitude": 176.3, "radius": 500,
        },
    ]

    sensor = UnisonNztatsSensor(mock_coordinator, mock_config_entry, "Rotorua")
    stats = sensor.extra_state_attributes["statistics"]

    assert stats["average_customers_per_outage"] == 150
    assert stats["unique_areas_affected"] == 2
    assert stats["outage_types"]["planned"] == 1
    assert stats["outage_types"]["unplanned"] == 1
