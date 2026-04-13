"""Integration tests for Unison Outages sensor."""
import pytest
import aiohttp
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

_LOGGER = logging.getLogger(__name__)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_website():
    """Test fetching data from the actual Unison website."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://www.unison.co.nz/outages/",
    }
    
    async with aiohttp.ClientSession() as session:
        _LOGGER.info("Fetching outage data...")
        async with session.get("https://www.unison.co.nz/api/outage", headers=headers) as response:
            assert response.status == 200, f"API request failed with status {response.status}"
            
            data = await response.json()
            assert isinstance(data, list), "Expected a list of outages"
            
            if data:
                _LOGGER.info(f"Found {len(data)} outages")
                
                # Validate the first outage
                outage = data[0]
                required_fields = [
                    "outageID",
                    "utilityType",
                    "outageType",
                    "outageStatus",
                    "interruptionReason",
                    "areaAffected",
                    "networkRegion",
                    "outageState",
                    "startTime",
                    "finishTime",
                    "latitude",
                    "longitude",
                    "radius",
                    "customersOff"
                ]
                
                for field in required_fields:
                    assert field in outage, f"Missing required field: {field}"
                
                # Validate datetime format
                try:
                    start_time = datetime.fromisoformat(outage["startTime"])
                    finish_time = datetime.fromisoformat(outage["finishTime"])
                    assert start_time.tzinfo is not None, "Start time should have timezone info"
                    assert finish_time.tzinfo is not None, "Finish time should have timezone info"
                    _LOGGER.info(f"Start time (NZ): {start_time.astimezone(ZoneInfo('Pacific/Auckland'))}")
                    _LOGGER.info(f"End time (NZ): {finish_time.astimezone(ZoneInfo('Pacific/Auckland'))}")
                except ValueError as e:
                    assert False, f"Invalid datetime format: {e}"
                
                # Log sample outage details
                _LOGGER.info("\nSample outage details:")
                _LOGGER.info(f"ID: {outage['outageID']}")
                _LOGGER.info(f"Type: {outage['outageType']}")
                _LOGGER.info(f"Status: {outage['outageStatus']}")
                _LOGGER.info(f"Area: {outage['areaAffected']}")
                _LOGGER.info(f"Region: {outage['networkRegion']}")
                _LOGGER.info(f"Customers affected: {outage['customersOff']}")
                
                # Group outages by region
                regions = {}
                for outage in data:
                    region = outage["networkRegion"]
                    if region not in regions:
                        regions[region] = []
                    regions[region].append(outage)
                
                _LOGGER.info("\nOutages by region:")
                for region, outages in regions.items():
                    _LOGGER.info(f"{region}: {len(outages)} outages")
            else:
                _LOGGER.info("No outages found")

        _LOGGER.info("\nTest completed successfully")

@pytest.mark.asyncio
@pytest.mark.integration
async def test_api_response_validation():
    """Test API response validation."""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.unison.co.nz/api/outage") as response:
            data = await response.json()
            
            for outage in data:
                # Validate outage state values
                assert outage["outageState"] in ["Current", "Scheduled", "Recent"]
                assert outage["outageStatus"] in [
                    "Active", "Scheduled", "Cancelled",
                    "Partial Restoration", "Under Investigation", "Completed",
                ]
                
                # Validate location data
                assert isinstance(outage["latitude"], (int, float))
                assert isinstance(outage["longitude"], (int, float))
                assert isinstance(outage["radius"], (int, float))
                
                # Validate timestamps
                start_time = datetime.fromisoformat(outage["startTime"])
                end_time = datetime.fromisoformat(outage["finishTime"])
                assert start_time.tzinfo is not None
                assert end_time.tzinfo is not None

@pytest.mark.asyncio
async def test_outage_states():
    """Test valid outage states and status combinations."""
    valid_states = {
        "Current": ["Active"],
        "Scheduled": ["Scheduled"],
        "Future": ["Scheduled"],
        "Past": ["Cancelled"]
    }
    
    # Add test implementation

@pytest.mark.asyncio
async def test_outage_data_structure():
    """Test outage data structure matches our format."""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.unison.co.nz/api/outage") as response:
            data = await response.json()
            if data:
                outage = data[0]
                # Validate time format
                start_time = datetime.fromisoformat(outage["startTime"])
                assert start_time.tzinfo is not None
                
                # Validate numeric fields
                assert isinstance(outage["customersOff"], (int, float))
                assert isinstance(outage["latitude"], (int, float))
                assert isinstance(outage["longitude"], (int, float))
                
                # Validate string fields
                assert isinstance(outage["outageType"], str)
                assert isinstance(outage["areaAffected"], str)
                assert isinstance(outage["networkRegion"], str)
