"""Tests for TapoBatterySensor.updateTapo robustness."""

from copy import deepcopy
from unittest.mock import MagicMock, AsyncMock

import pytest

from custom_components.tapo_control.sensor import TapoBatterySensor
from homeassistant.const import STATE_UNAVAILABLE

MINIMAL_CAM_DATA = {
    "basic_info": {
        "mac": "B0-19-21-F5-3D-94",
        "device_alias": "Tapo_Camera",
        "device_model": "C410",
        "sw_version": "1.2.1",
        "hw_version": "1.0",
        "battery_percent": 9,
        "battery_charging": "NO",
        "power": "BATTERY",
        "manufacturer_name": "TP-Link",
    },
}


@pytest.fixture
def hass():
    _hass = MagicMock()
    _hass.data = {"tapo_control": {}}
    _hass.config = MagicMock()
    _hass.config.config_dir = "/config"
    return _hass


@pytest.fixture
def config_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "is_klap_device": False,
        "reported_ip_address": "192.168.1.100",
        "media_sync_hours": 24,
    }
    entry.unique_id = "test_unique_id"
    return entry


@pytest.fixture
def entry_dict():
    controller = MagicMock()
    controller.isKLAP = False
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    coordinator.data = {}
    return {
        "controller": controller,
        "coordinator": coordinator,
        "camData": deepcopy(MINIMAL_CAM_DATA),
        "name": "TestCamera",
        "isChild": False,
        "isParent": True,
        "chInfo": None,
        "entities": [],
        "childDevices": [],
        "allControllers": [controller],
        "uuid": "test-uuid",
        "timezoneOffset": 60,
        "refreshEnabled": True,
        "onvifManagement": None,
        "enable_media_sync": False,
        "movement_angle": 15,
        "chime_play_type": 1,
        "chime_play_volume": 15,
        "chime_play_duration": 0,
    }


def test_battery_sensor_normal(entry_dict, hass, config_entry):
    """updateTapo works normally with valid camData."""
    sensor = TapoBatterySensor(entry_dict, hass, config_entry)
    assert sensor._attr_native_value == 9
    sensor.updateTapo(entry_dict["camData"])
    assert sensor._attr_native_value == 9


def test_battery_sensor_none_camdata(entry_dict, hass, config_entry):
    """updateTapo handles None camData gracefully."""
    sensor = TapoBatterySensor(entry_dict, hass, config_entry)
    sensor.updateTapo(None)
    assert sensor._attr_native_value == STATE_UNAVAILABLE


def test_battery_sensor_missing_battery_percent(entry_dict, hass, config_entry):
    """updateTapo handles missing battery_percent key gracefully."""
    sensor = TapoBatterySensor(entry_dict, hass, config_entry)
    camData = deepcopy(entry_dict["camData"])
    del camData["basic_info"]["battery_percent"]
    sensor.updateTapo(camData)
    assert sensor._attr_native_value == STATE_UNAVAILABLE


def test_battery_sensor_missing_basic_info(entry_dict, hass, config_entry):
    """updateTapo handles missing basic_info key gracefully."""
    sensor = TapoBatterySensor(entry_dict, hass, config_entry)
    camData = deepcopy(entry_dict["camData"])
    del camData["basic_info"]
    # Keep other keys so camData is still truthy (realistic scenario)
    camData["motion_detection_enabled"] = {"1": "off"}
    sensor.updateTapo(camData)
    assert sensor._attr_native_value == STATE_UNAVAILABLE
