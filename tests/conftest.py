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
        "mac": "aa:bb:cc:dd:ee:ff",
        "device_alias": "TestCamera",
        "device_model": "C200",
    },
    "motion_detection_enabled": {"1": "on"},
    "motion_detection_sensitivity": {"1": "normal"},
    "motion_detection_digital_sensitivity": 50,
    "person_detection_enabled": "on",
    "person_detection_sensitivity": "normal",
    "vehicle_detection_enabled": "on",
    "vehicle_detection_sensitivity": "normal",
    "babyCry_detection_enabled": "off",
    "babyCry_detection_sensitivity": "off",
    "pet_detection_enabled": "on",
    "pet_detection_sensitivity": "normal",
    "bark_detection_enabled": "off",
    "bark_detection_sensitivity": "off",
    "meow_detection_enabled": "off",
    "meow_detection_sensitivity": "off",
    "glass_detection_enabled": "off",
    "glass_detection_sensitivity": "off",
    "tamper_detection_enabled": "off",
    "tamper_detection_sensitivity": "off",
    "privacy_mode": "off",
    "led": "on",
    "auto_track": "on",
    "notifications": "on",
    "rich_notifications": "on",
    "autoUpgradeEnabled": "on",
    "record_audio": True,
    "flip": "on",
    "lens_distrotion_correction": "on",
    "microphoneMute": "off",
    "microphoneNoiseCancelling": "off",
    "microphoneVolume": 50,
    "speakerVolume": 50,
    "alarm_config": {
        "automatic": "off",
        "mode": "light",
        "siren_volume": 5,
        "siren_duration": 30,
        "alarm_volume": 5,
        "alarm_duration": 30,
        "typeOfAlarm": "getAlarm",
        "siren_type": "test_type",
    },
    "alarm_status": "off",
    "alarm_is_hubSiren": False,
    "alarm_user_sounds": None,
    "alarm_user_start_id": None,
    "recordPlan": {"enabled": "on"},
    "whitelampStatus": "1",
    "whitelampConfigForceTime": "300",
    "whitelampConfigIntensity": "3",
    "smartwtl_digital_level": None,
    "force_white_lamp_state": "on",
    "flood_light_config": {
        "intensity_level": 128,
        "min_intensity": 1,
        "intensity_level_max": 255,
    },
    "flood_light_status": "1",
    "flood_light_capability": {
        "min_intensity": 1,
        "intensity_level_max": 255,
    },
    "night_vision_mode": "auto",
    "night_vision_mode_switching": "auto",
    "night_vision_capability": ["auto", "on", "off"],
    "light_frequency_mode": "50",
    "timezone_timezone": "UTC+01:00",
    "timezone_zone_id": "Europe/Amsterdam",
    "diagnose_mode": {"diagnose_mode": "off"},
    "smart_track_config": {"track_human_enabled": "on"},
    "cover_config": {"enabled": "off"},
    "dualCamLinkageEnabled": "off",
    "dualCamLinkageType": None,
    "dualCamLinkageCapability": {"lens_support": "1"},
    "dualLinkageTargetSetting": {"lens_enabled": "on"},
    "dualCamCapability": {},
    "presets": {},
    "videoCapability": {
        "video_capability": {
            "main": {
                "hdrs": True,
            }
        }
    },
    "videoQualities": {
        "video": {
            "main": {
                "hdr": "1",
            }
        }
    },
    "supportAlarmTypeList": {
        "alarm_type_list": ["type1", "type2"],
    },
    "chimeAlarmConfigurations": {
        "mac1": {"on_off": 1, "type": "type1", "volume": 10, "duration": 5}
    },
    "alert_event_types": [
        {"name": "motion", "enabled": "on"},
        {"name": "person", "enabled": "off"},
    ],
    "siren_type_list": ["type1", "type2"],
    "alert_type_list": ["type1", "type2"],
    "sdCardData": [{"disk_name": "sda", "space": "100GB", "status": "healthy"}],
    "battery_level": 85,
    "rssi": -45,
    "ssid": "TestWiFi",
    "link_type": "wifi",
    "firmwareUpdateStatus": {
        "upgrade_status": {"state": "normal"},
    },
    "childDevices": [],
    "connectionInformation": {
        "ssid": "TestWiFi",
        "link_type": "wifi",
        "rssiValue": -45,
    },
    "updated": 1000,
    "enable_media_sync": False,
    "quick_response": [{"1": {"name": "Hello", "id": "1"}}],
    "chime_support": True,
    "time_sync_dst": 1,
    "time_sync_ndst": 0,
    "clock_data": {"local_time": "12:00", "seconds_from_1970": "1000000"},
    "dst_data": {"start": "2024-01-01"},
    "nightVisionCapability": None,
    "ldcStyle": "standard",
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
