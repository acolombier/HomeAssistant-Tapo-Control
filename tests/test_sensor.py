from unittest.mock import MagicMock, AsyncMock
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tapo_control.sensor import (
    TapoRSSISensor,
    TapoLinkTypeSensor,
    TapoSSIDSensor,
    TapoBatterySensor,
    TapoHDDSensor,
    TapoChimeSignalLevel,
    TapoSyncSensor,
)
from custom_components.tapo_control.const import DOMAIN, ENABLE_MEDIA_SYNC


def make_entry(camData=None, **overrides):
    data = camData or {
        "basic_info": {
            "mac": "aa:bb:cc:dd:ee:ff",
            "device_alias": "TestCamera",
            "device_model": "C200",
            "signal_level": "good",
            "battery_percent": 85,
        },
        "connectionInformation": {
            "ssid": "TestWiFi",
            "link_type": "wifi",
            "rssiValue": -45,
        },
        "sdCardData": [
            {"disk_name": "sda", "space": "100GB", "status": "healthy"},
        ],
        "updated": 1000,
    }
    entry = {
        "controller": MagicMock(),
        "coordinator": MagicMock(),
        "camData": data,
        "name": "TestCamera",
        "isChild": False,
        "entities": [],
    }
    entry.update(overrides)
    return entry


class TestTapoRSSISensor:
    def test_updateTapo(self):
        entry = make_entry()
        sensor = TapoRSSISensor(entry, MagicMock(), MagicMock())
        sensor.updateTapo({
            "connectionInformation": {"rssiValue": -45},
        })
        assert sensor._attr_native_value == -45

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        sensor = TapoRSSISensor(entry, MagicMock(), MagicMock())
        sensor.updateTapo({})
        assert sensor._attr_native_value == STATE_UNAVAILABLE

    def test_updateTapo_missing_key(self):
        entry = make_entry()
        sensor = TapoRSSISensor(entry, MagicMock(), MagicMock())
        sensor.updateTapo({"connectionInformation": {}})
        assert sensor._attr_native_value == STATE_UNAVAILABLE

    def test_updateTapo_false_connection(self):
        entry = make_entry()
        sensor = TapoRSSISensor(entry, MagicMock(), MagicMock())
        sensor.updateTapo({"connectionInformation": False})
        assert sensor._attr_native_value == STATE_UNAVAILABLE


class TestTapoLinkTypeSensor:
    def test_updateTapo(self):
        entry = make_entry()
        sensor = TapoLinkTypeSensor(entry, MagicMock(), MagicMock())
        sensor.updateTapo({"connectionInformation": {"link_type": "wifi"}})
        assert sensor._attr_native_value == "wifi"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        sensor = TapoLinkTypeSensor(entry, MagicMock(), MagicMock())
        sensor.updateTapo(None)
        assert sensor._attr_native_value == STATE_UNAVAILABLE


class TestTapoSSIDSensor:
    def test_updateTapo(self):
        entry = make_entry()
        sensor = TapoSSIDSensor(entry, MagicMock(), MagicMock())
        sensor.updateTapo({"connectionInformation": {"ssid": "TestWiFi"}})
        assert sensor._attr_native_value == "TestWiFi"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        sensor = TapoSSIDSensor(entry, MagicMock(), MagicMock())
        sensor.updateTapo({})
        assert sensor._attr_native_value == STATE_UNAVAILABLE


class TestTapoBatterySensor:
    def test_updateTapo(self):
        entry = make_entry()
        sensor = TapoBatterySensor(entry, MagicMock(), MagicMock())
        sensor.updateTapo({"basic_info": {"battery_percent": 85}})
        assert sensor._attr_native_value == 85

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        sensor = TapoBatterySensor(entry, MagicMock(), MagicMock())
        sensor.updateTapo(None)
        assert sensor._attr_native_value == STATE_UNAVAILABLE


class TestTapoHDDSensor:
    def test_updateTapo_status(self):
        entry = make_entry()
        sensor = TapoHDDSensor(entry, MagicMock(), MagicMock(), "sda", "status")
        sensor.updateTapo({"sdCardData": [{"disk_name": "sda", "status": "healthy", "space": "100GB"}]})
        assert sensor._attr_native_value == "healthy"

    def test_updateTapo_space_extracts_unit(self):
        entry = make_entry()
        sensor = TapoHDDSensor(entry, MagicMock(), MagicMock(), "sda", "space")
        sensor.updateTapo({"sdCardData": [{"disk_name": "sda", "status": "healthy", "space": "50.5GB"}]})
        assert sensor._attr_native_value == "50.5"

    def test_updateTapo_no_sd_card(self):
        entry = make_entry()
        sensor = TapoHDDSensor(entry, MagicMock(), MagicMock(), "sda", "status")
        sensor.updateTapo({})
        assert sensor._attr_native_value == STATE_UNAVAILABLE

    def test_updateTapo_empty_sd_card(self):
        entry = make_entry()
        sensor = TapoHDDSensor(entry, MagicMock(), MagicMock(), "sda", "status")
        sensor.updateTapo({"sdCardData": []})
        assert sensor._attr_native_value == STATE_UNAVAILABLE


class TestTapoChimeSignalLevel:
    def test_updateTapo(self):
        entry = make_entry()
        sensor = TapoChimeSignalLevel(entry, MagicMock(), MagicMock())
        sensor.updateTapo({"basic_info": {"signal_level": "good"}})
        assert sensor._attr_native_value == "good"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        sensor = TapoChimeSignalLevel(entry, MagicMock(), MagicMock())
        sensor.updateTapo({})
        assert sensor._attr_native_value == STATE_UNAVAILABLE


class TestTapoSyncSensor:
    def test_updateTapo_starting(self):
        hass = MagicMock()
        config_entry = MagicMock()
        config_entry.entry_id = "test_entry"
        hass.data = {
            DOMAIN: {
                "test_entry": {
                    ENABLE_MEDIA_SYNC: True,
                    "runningMediaSync": False,
                    "initialMediaScanDone": False,
                    "mediaSyncAvailable": True,
                    "downloadProgress": None,
                    "mediaSyncScheduled": False,
                    "mediaSyncRanOnce": False,
                }
            }
        }
        entry = make_entry()
        sensor = TapoSyncSensor(entry, hass, config_entry)
        sensor.updateTapo({"updated": 1000})
        assert sensor._attr_native_value == "Starting"

    def test_updateTapo_idle_when_media_sync_disabled(self):
        hass = MagicMock()
        config_entry = MagicMock()
        config_entry.entry_id = "test_entry"
        hass.data = {
            DOMAIN: {
                "test_entry": {
                    ENABLE_MEDIA_SYNC: False,
                    "runningMediaSync": False,
                }
            }
        }
        entry = make_entry()
        sensor = TapoSyncSensor(entry, hass, config_entry)
        sensor.updateTapo({"updated": 1000})
        assert sensor._attr_native_value == "Idle"
