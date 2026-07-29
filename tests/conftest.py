import datetime
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

# 6. homeassistant — entire package tree (HA is not installed in CI-like envs)
import types as _types

def _make_ha_module(name, attrs=None):
    mod = _types.ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    sys.modules[name] = mod
    return mod

# Root homeassistant as a package
_ha = _make_ha_module("homeassistant")
_ha.__path__ = []

# UnitOfInformation — fake enum supporting `in` and `()` like real HA enum
class _UOIMeta(type):
    _members = {"MB", "GB", "KB", "TB", "B", "kB", "MiB", "KiB"}
    def __contains__(cls, item):
        return item in cls._members
    def __call__(cls, value):
        return value

class _UnitOfInformation(metaclass=_UOIMeta):
    MEGABYTES = "MB"
    GIGABYTES = "GB"
    KILOBYTES = "kB"
    BYTES = "B"

# homeassistant.const
_ha_const = _make_ha_module("homeassistant.const", {
    "STATE_UNAVAILABLE": "unavailable",
    "STATE_ON": "on",
    "STATE_OFF": "off",
    "STATE_HOME": "home",
    "STATE_NOT_HOME": "not_home",
    "CONF_IP_ADDRESS": "ip_address",
    "CONF_USERNAME": "username",
    "CONF_PASSWORD": "password",
    "PERCENTAGE": "%",
    "SIGNAL_STRENGTH_DECIBELS": "dB",
    "SIGNAL_STRENGTH_DECIBELS_MILLIWATT": "dBm",
    "CONF_NAME": "name",
    "CONF_HOST": "host",
    "CONF_PORT": "port",
    "CONF_DEVICE_ID": "device_id",
    "CONF_MAC": "mac",
    "CONF_MODEL": "model",
    "CONF_SW_VERSION": "sw_version",
    "CONF_MANUFACTURER": "manufacturer",
    "EVENT_HOMEASSISTANT_STOP": "homeassistant_stop",
    "EVENT_HOMEASSISTANT_START": "homeassistant_start",
    "STATE_UNKNOWN": "unknown",
    "UnitOfInformation": _UnitOfInformation,
    "__version__": "2025.10.0",
})

# homeassistant.core
_ha_core = _make_ha_module("homeassistant.core", {
    "HomeAssistant": MagicMock,
    "callback": lambda fn: fn,
    "Event": MagicMock,
    "State": MagicMock,
    "ServiceCall": MagicMock,
    "ConfigEntry": MagicMock,
})

# homeassistant.config_entries
_ha_config_entries = _make_ha_module("homeassistant.config_entries", {
    "ConfigEntry": MagicMock,
    "ConfigEntryNotReady": type("ConfigEntryNotReady", (Exception,), {}),
    "ConfigEntryAuthFailed": type("ConfigEntryAuthFailed", (Exception,), {}),
})

# homeassistant.exceptions
_ha_exceptions = _make_ha_module("homeassistant.exceptions", {
    "HomeAssistantError": type("HomeAssistantError", (Exception,), {}),
    "ConfigEntryNotReady": _ha_config_entries.ConfigEntryNotReady,
    "ConfigEntryAuthFailed": _ha_config_entries.ConfigEntryAuthFailed,
    "Unauthorized": type("Unauthorized", (Exception,), {}),
    "DependencyError": type("DependencyError", (Exception,), {}),
})

# homeassistant.helpers
_ha_helpers = _make_ha_module("homeassistant.helpers")
_ha_helpers.__path__ = []

# Fake Entity base class — avoids MagicMock attribute interception issues
class _FakeEntity:
    hass = None
    entity_id = None
    _attr_native_value = None
    _attr_native_unit_of_measurement = None
    _attr_device_class = None
    _attr_state_class = None
    _attr_icon = None
    _attr_entity_category = None
    _attr_entity_registry_enabled_default = True
    _enabled = False
    _is_cam_entity = False
    _is_noise_sensor = False
    _attr_state = None
    _attr_is_on = None

    @property
    def is_on(self):
        return self._attr_is_on

# homeassistant.helpers.entity
_ha_helpers_entity = _make_ha_module("homeassistant.helpers.entity", {
    "Entity": _FakeEntity,
    "EntityCategory": type("EntityCategory", (), {
        "CONFIG": 1,
        "DIAGNOSTIC": 2,
        "SYSTEM": 3,
    }),
    "DeviceInfo": MagicMock,
    "async_track_entity_registry_updated_event": lambda *a, **kw: lambda: None,
})

# homeassistant.helpers.entity_platform
_ha_helpers_entity_platform = _make_ha_module("homeassistant.helpers.entity_platform", {
    "AddEntitiesCallback": MagicMock,
})

# homeassistant.helpers.update_coordinator
_ha_helpers_update_coordinator = _make_ha_module("homeassistant.helpers.update_coordinator", {
    "DataUpdateCoordinator": MagicMock,
    "UpdateFailed": type("UpdateFailed", (Exception,), {}),
})

# homeassistant.helpers.event
_ha_helpers_event = _make_ha_module("homeassistant.helpers.event", {
    "async_track_time_interval": MagicMock,
    "async_track_point_in_utc_time": MagicMock,
    "async_track_state_change": MagicMock,
})

# homeassistant.helpers.network
_ha_helpers_network = _make_ha_module("homeassistant.helpers.network", {
    "NoURLAvailableError": type("NoURLAvailableError", (Exception,), {}),
    "get_url": MagicMock(return_value="http://localhost:8123"),
})

# homeassistant.helpers.dispatcher
_ha_helpers_dispatcher = _make_ha_module("homeassistant.helpers.dispatcher", {
    "async_dispatcher_connect": MagicMock,
    "async_dispatcher_send": MagicMock,
})

# homeassistant.helpers.device_registry
_ha_helpers_device_registry = _make_ha_module("homeassistant.helpers.device_registry", {
    "async_get": MagicMock,
    "async_entries_for_config_entry": MagicMock(return_value=[]),
    "DeviceRegistry": MagicMock,
})

# homeassistant.helpers.config_validation
_ha_helpers_config_validation = _make_ha_module("homeassistant.helpers.config_validation", {
    "string": lambda v: v,
    "boolean": lambda v: bool(v),
    "number": lambda v: float(v),
    "positive_int": lambda v: int(v),
    "ensure_list": lambda v: v if isinstance(v, list) else [v],
})
sys.modules["homeassistant.helpers"].config_validation = _ha_helpers_config_validation

# homeassistant.helpers.storage
_ha_helpers_storage = _make_ha_module("homeassistant.helpers.storage", {
    "Store": MagicMock,
})

# homeassistant.components
_ha_components = _make_ha_module("homeassistant.components")
_ha_components.__path__ = []

# homeassistant.components.sensor
_ha_components_sensor = _make_ha_module("homeassistant.components.sensor", {
    "SensorDeviceClass": type("SensorDeviceClass", (), {
        "BATTERY": "battery",
        "SIGNAL_STRENGTH": "signal_strength",
        "TIMESTAMP": "timestamp",
        "DATA_SIZE": "data_size",
        "DATA_RATE": "data_rate",
    }),
    "SensorStateClass": type("SensorStateClass", (), {
        "MEASUREMENT": "measurement",
        "TOTAL_INCREASING": "total_increasing",
    }),
    "SensorEntity": type("SensorEntity", (_FakeEntity,), {}),
})

# homeassistant.components.binary_sensor
_ha_components_binary_sensor = _make_ha_module("homeassistant.components.binary_sensor", {
    "BinarySensorDeviceClass": type("BinarySensorDeviceClass", (), {
        "MOTION": "motion",
        "DOOR": "door",
        "WINDOW": "window",
        "SOUND": "sound",
    }),
    "BinarySensorEntity": type("BinarySensorEntity", (_FakeEntity,), {}),
})

# homeassistant.components.switch
_ha_components_switch = _make_ha_module("homeassistant.components.switch", {
    "SwitchEntity": type("SwitchEntity", (_FakeEntity,), {}),
})

# homeassistant.components.select
_ha_components_select = _make_ha_module("homeassistant.components.select", {
    "SelectEntity": type("SelectEntity", (_FakeEntity,), {}),
})

# homeassistant.components.button
_ha_components_button = _make_ha_module("homeassistant.components.button", {
    "ButtonEntity": type("ButtonEntity", (_FakeEntity,), {}),
})

# homeassistant.components.number
_ha_components_number = _make_ha_module("homeassistant.components.number", {
    "NumberEntity": type("NumberEntity", (_FakeEntity,), {}),
})

# homeassistant.components.light
_ha_components_light = _make_ha_module("homeassistant.components.light", {
    "LightEntity": type("LightEntity", (_FakeEntity,), {}),
    "ColorMode": type("ColorMode", (), {
        "ONOFF": "onoff",
        "BRIGHTNESS": "brightness",
    }),
})

# homeassistant.components.update
_ha_components_update = _make_ha_module("homeassistant.components.update", {
    "UpdateEntity": type("UpdateEntity", (_FakeEntity,), {}),
    "UpdateEntityFeature": type("UpdateEntityFeature", (), {
        "INSTALL": 1,
        "PROGRESS": 2,
        "RELEASE_NOTES": 4,
    }),
})

# homeassistant.components.camera
_ha_components_camera = _make_ha_module("homeassistant.components.camera", {
    "Camera": type("Camera", (_FakeEntity,), {}),
    "CameraEntityFeature": type("CameraEntityFeature", (), {
        "STREAM": 1,
    }),
})

# homeassistant.components.ffmpeg
_ha_components_ffmpeg = _make_ha_module("homeassistant.components.ffmpeg", {
    "DATA_FFMPEG": "ffmpeg",
    "FFmpegManager": MagicMock,
    "CONF_EXTRA_ARGUMENTS": "extra_arguments",
})

# homeassistant.components.stream
_ha_components_stream = _make_ha_module("homeassistant.components.stream", {
    "Stream": MagicMock,
})

# homeassistant.components.media_source
_ha_components_media_source = _make_ha_module("homeassistant.components.media_source")
_ha_components_media_source.__path__ = []
_ha_components_media_source_error = _make_ha_module("homeassistant.components.media_source.error", {
    "Unresolvable": type("Unresolvable", (Exception,), {}),
})

# homeassistant.helpers.entity_registry
_ha_helpers_entity_registry = _make_ha_module("homeassistant.helpers.entity_registry", {
    "async_entries_for_config_entry": MagicMock(return_value=[]),
    "async_get": MagicMock,
})

# homeassistant.util
_ha_util = _make_ha_module("homeassistant.util")
_ha_util.__path__ = []

# homeassistant.util.enum
_ha_util_enum = _make_ha_module("homeassistant.util.enum", {
    "try_parse_enum": lambda enum, value, default=None: default,
})

# homeassistant.util.dt
_ha_util_dt = _make_ha_module("homeassistant.util.dt", {
    "as_timestamp": MagicMock(side_effect=lambda x: 1000),
    "utcnow": MagicMock(return_value=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)),
    "now": MagicMock(return_value=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)),
    "parse_datetime": MagicMock(return_value=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)),
})

# homeassistant.util.slugify
_ha_util_slugify = _make_ha_module("homeassistant.util", {
    "slugify": lambda s: s.lower().replace(" ", "_").replace("-", "_"),
})

# homeassistant.backports
_ha_backports = _make_ha_module("homeassistant.backports")
_ha_backports.__path__ = []  # Not present in older versions

# homeassistant.loader
_ha_loader = _make_ha_module("homeassistant.loader", {
    "async_get_integration": MagicMock,
    "Integration": MagicMock,
})

# 7. pytapo (not installed, used by utils.py)
_pytapo = _make_ha_module("pytapo")
_pytapo.__path__ = []
_pytapo_media_stream = _make_ha_module("pytapo.media_stream")
_pytapo_media_stream.__path__ = []
_pytapo_media_stream_downloader = _make_ha_module("pytapo.media_stream.downloader", {
    "Downloader": MagicMock,
})
_pytapo.Tapo = MagicMock

# 8. Add CONST_HOST to const mock
sys.modules["homeassistant.const"].CONF_HOST = "host"

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
