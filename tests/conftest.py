import sys
from unittest.mock import Mock, AsyncMock, MagicMock
from copy import deepcopy

import pytest

# ---------------------------------------------------------------------------
# Pre-seed sys.modules with mocks for ALL problematic transitive dependencies
# so that importing custom_components.tapo_control does not fail.
# These are inserted BEFORE any test module is imported.
# ---------------------------------------------------------------------------

# 1. aiodns (pycares type incompatibility with aiodns 3.5)
_mock_aiodns = MagicMock()
_mock_aiodns_resolver = MagicMock()
_mock_aiodns_resolver.query = AsyncMock(return_value=[])
_mock_aiodns_resolver.gethostbyname = AsyncMock(return_value="127.0.0.1")
_mock_aiodns_resolver.getaddrinfo = AsyncMock(return_value=[])
_mock_aiodns_resolver.close = AsyncMock()
_mock_aiodns_resolver.cancel = MagicMock()
_mock_aiodns.DNSResolver = MagicMock(return_value=_mock_aiodns_resolver)
sys.modules["aiodns"] = _mock_aiodns

# 2. onvif — the onvif-zeep 0.2.12 distribution is too old for HA
_mock_onvif = MagicMock()
_mock_onvif.ONVIFCamera = MagicMock()
_mock_onvif_util = MagicMock()
_mock_onvif_util.is_auth_error = MagicMock(return_value=False)
_mock_onvif_util.stringify_onvif_error = MagicMock(return_value="")
_mock_onvif.util = _mock_onvif_util
_mock_onvif.client = MagicMock()
_mock_onvif.client.NotificationManager = MagicMock()
sys.modules["onvif"] = _mock_onvif
sys.modules["onvif.util"] = _mock_onvif_util
sys.modules["onvif.client"] = _mock_onvif.client
sys.modules["onvif.event"] = MagicMock()
sys.modules["onvif.definition"] = MagicMock()

# 3. homeassistant.components.onvif sub-modules (to short-circuit event manager import)
sys.modules["homeassistant.components.onvif.event_manager"] = MagicMock()
sys.modules["homeassistant.components.onvif.event"] = MagicMock()
sys.modules["homeassistant.components.onvif.device"] = MagicMock()

# 4. haffmpeg
_mock_haffmpeg_core = MagicMock()
_mock_haffmpeg_core.HAFFmpeg = MagicMock()
sys.modules["haffmpeg"] = MagicMock()
sys.modules["haffmpeg.core"] = _mock_haffmpeg_core
sys.modules["haffmpeg.tools"] = MagicMock()
sys.modules["haffmpeg.sensor"] = MagicMock()
sys.modules["haffmpeg.camera"] = MagicMock()

# 5. numpy (image processing in HA stream)
sys.modules["numpy"] = MagicMock()

# ---------------------------------------------------------------------------

SAMPLE_CAM_DATA = {
    "basic_info": {
        "mac": "B0-19-21-F5-3D-94",
        "device_alias": "Tapo_Camera",
        "device_model": "C410",
        "sw_version": "1.2.1 Build 250917 Rel.58378n",
        "hw_version": "1.0",
        "battery_percent": 9,
        "battery_charging": "NO",
        "power": "BATTERY",
        "power_save_mode": "off",
        "region": "EU",
        "manufacturer_name": "TP-Link",
    },
    "motion_detection_enabled": {"1": "off"},
    "motion_detection_sensitivity": {"1": "normal"},
    "motion_detection_digital_sensitivity": {"1": "70"},
    "person_detection_enabled": {"1": "off"},
    "person_detection_sensitivity": {"1": "high"},
    "vehicle_detection_enabled": {"1": "off"},
    "vehicle_detection_sensitivity": {"1": "normal"},
    "babyCry_detection_enabled": None,
    "babyCry_detection_sensitivity": None,
    "pet_detection_enabled": {"1": "off"},
    "pet_detection_sensitivity": {"1": "high"},
    "bark_detection_enabled": None,
    "bark_detection_sensitivity": None,
    "meow_detection_enabled": None,
    "meow_detection_sensitivity": None,
    "glass_detection_enabled": None,
    "glass_detection_sensitivity": None,
    "tamper_detection_enabled": None,
    "tamper_detection_sensitivity": None,
    "privacy_mode": "off",
    "led": "on",
    "auto_track": None,
    "notifications": "on",
    "rich_notifications": "on",
    "autoUpgradeEnabled": "on",
    "record_audio": True,
    "flip": "on",
    "lens_distrotion_correction": "on",
    "microphoneMute": "off",
    "microphoneNoiseCancelling": "on",
    "microphoneVolume": "52",
    "speakerVolume": "100",
    "alarm_config": {
        "typeOfAlarm": "getAlarm",
        "mode": ["sound", "light"],
        "automatic": "off",
        "light_type": "0",
        "siren_type": "0",
        "alarm_duration": "0",
        "alarm_volume": "high",
    },
    "alarm_status": False,
    "alarm_is_hubSiren": False,
    "alarm_user_sounds": [],
    "alarm_user_start_id": "8195",
    "alarm_siren_type_list": ["Siren", "Emergency", "Red Alert"],
    "recordPlan": {
        "enabled": "on",
        "monday": '["0000-2400:2"]',
        "tuesday": '["0000-2400:2"]',
        "wednesday": '["0000-2400:2"]',
        "thursday": '["0000-2400:2"]',
        "friday": '["0000-2400:2"]',
        "saturday": '["0000-2400:2"]',
        "sunday": '["0000-2400:2"]',
    },
    "whitelampStatus": 0,
    "whitelampConfigForceTime": "300",
    "whitelampConfigIntensity": "5",
    "smartwtl_digital_level": "100",
    "force_white_lamp_state": None,
    "flood_light_config": None,
    "flood_light_status": None,
    "flood_light_capability": None,
    "night_vision_mode": "inf_night_vision",
    "night_vision_mode_switching": "auto",
    "night_vision_capability": ["inf_night_vision", "wtl_night_vision"],
    "light_frequency_mode": "auto",
    "timezone_timezone": "UTC-00:00",
    "timezone_zone_id": "Europe/London",
    "timezone_timing_mode": "ntp",
    "diagnose_mode": {
        "dev_alias": "Tapo_Camera",
        "diagnose_mode": "off",
        "console_debug": "off",
        "submod_dbg_mode": 31,
    },
    "smart_track_config": None,
    "cover_config": {"enabled": "off"},
    "dualCamLinkageEnabled": None,
    "dualCamLinkageType": None,
    "dualCamLinkageCapability": None,
    "dualLinkageTargetSetting": None,
    "dualCamCapability": False,
    "allChnInfo": False,
    "presets": {},
    "videoCapability": {
        "video_capability": {
            "main": {
                "encode_types": ["H264"],
                "resolutions": ["2304*1296"],
                "qualitys": ["1", "3", "5"],
                "minor_stream_support": "1",
            },
            "minor": {
                "encode_types": ["H264"],
                "resolutions": ["640*360"],
                "qualitys": ["1", "3", "5"],
                "minor_stream_support": "1",
            },
        }
    },
    "videoQualities": {
        "video": {
            "main": {
                "quality": "5",
                "bitrate": "1400",
                "encode_type": "H264",
                "resolution": "2304*1296",
            }
        }
    },
    "supportAlarmTypeList": None,
    "chimeAlarmConfigurations": None,
    "alert_event_types": [
        {"name": "motion_detection", "enabled": "off"},
        {"name": "people_detection", "enabled": "off"},
        {"name": "pet_detection", "enabled": "off"},
        {"name": "vehicle_detection", "enabled": "off"},
    ],
    "siren_type_list": ["Siren", "Emergency", "Red Alert"],
    "alert_type_list": ["type1", "type2"],
    "sdCardData": [{"disk_name": "1", "space": "0B", "status": "offline"}],
    "battery_level": 9,
    "rssi": -47,
    "ssid": "WhoDat",
    "link_type": "wifi",
    "network_ip_info": {
        "network": {
            "wan": {
                "ipaddr": "192.168.32.21",
                "netmask": "255.255.255.0",
                "gateway": "192.168.32.1",
            }
        }
    },
    "firmwareUpdateStatus": {
        "upgrade_status": {
            "state": "normal",
            "lastUpgradingSuccess": True,
        },
    },
    "childDevices": False,
    "connectionInformation": {
        "ssid": "WhoDat",
        "link_type": "wifi",
        "rssiValue": -47,
        "rssi": "4",
    },
    "updated": 1778950341.236933,
    "enable_media_sync": False,
    "quick_response": None,
    "chime_support": False,
    "time_sync_dst": 1,
    "time_sync_ndst": 0,
    "clock_data": {
        "local_time": "2026-05-16 14:44:53",
        "seconds_from_1970": 1778939093,
    },
    "dst_data": {
        "enabled": "1",
        "synced": "1",
        "dst_rule": "DST-01:00,M3.5.0/01:00:00,M10.5.0/02:00:00",
    },
    "nightVisionCapability": {
        "supplement_lamp_type": ["infrared_lamp", "white_lamp"],
        "night_vision_mode_range": ["inf_night_vision", "wtl_night_vision"],
    },
    "ldcStyle": "original",
    "has_stream6": False,
    "has_stream7": False,
    "is_child": False,
    "is_parent": True,
    "movement_angle": 15,
    "chime_play_type": 1,
    "chime_play_volume": 15,
    "chime_play_duration": 0,
    "alarm_mode": "Alarm",
    "alarm_event_type": "motion",
}


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.data = {"tapo_control": {}}
    hass.config = MagicMock()
    hass.config.config_dir = "/config"
    return hass


@pytest.fixture
def mock_controller():
    controller = MagicMock()
    controller.isKLAP = False
    for method_name in [
        "setPrivacyMode", "setLEDEnabled", "setAutoTrackTarget",
        "setNotificationsEnabled", "setFirmwareAutoUpgradeConfig",
        "setRecordPlan", "setMicrophone", "setRecordAudio",
        "setDayNightMode", "setNightVisionModeConfig", "setLightFrequencyMode",
        "setTimezone", "setCruise", "setAlarm",
        "startManualAlarm", "stopManualAlarm", "setSirenStatus",
        "setHubSirenStatus", "setHubSirenConfig", "testUsrDefAudio",
        "reboot", "format", "calibrateMotor", "moveMotor",
        "setMotionDetection", "setPersonDetection", "setVehicleDetection",
        "setBabyCryDetection", "setPetDetection", "setBarkDetection",
        "setMeowDetection", "setGlassBreakDetection", "setTamperDetection",
        "setDualCamLinkage", "setLinkageTargetSetting", "setChimeAlarmConfigure",
        "setHDR", "setLensDistortionCorrection", "setCoverConfig",
        "setDiagnoseMode", "setSmartTrackConfig", "setImageFlipVertical",
        "setForceWhitelampState", "reverseWhitelampStatus", "manualFloodlightOp",
        "setFloodlightConfig", "setWhitelampConfig", "setSpeakerVolume",
        "setAlertEventType", "playQuickResponse", "playAlarm",
        "startFirmwareUpgrade", "executeFunction",
    ]:
        setattr(controller, method_name, MagicMock(return_value={"error_code": 0}))
    return controller


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    coordinator.data = {}
    return coordinator


@pytest.fixture
def mock_config_entry():
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
def base_entry_dict(mock_controller, mock_coordinator, mock_config_entry):
    return {
        "controller": mock_controller,
        "coordinator": mock_coordinator,
        "camData": deepcopy(SAMPLE_CAM_DATA),
        "name": "TestCamera",
        "isChild": False,
        "isParent": True,
        "chInfo": None,
        "entities": [],
        "childDevices": [],
        "allControllers": [mock_controller],
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


@pytest.fixture
def mock_entry_storage():
    storage = AsyncMock()
    storage.async_load = AsyncMock(return_value={"enable_media_sync": False})
    storage.async_save = AsyncMock()
    return storage
