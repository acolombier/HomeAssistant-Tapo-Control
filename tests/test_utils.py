import datetime
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import base64
from custom_components.tapo_control.utils import (
    result_has_error,
    tryParseInt,
    getNightModeMap,
    getNightModeName,
    getNightModeValue,
    convertBasicInfo,
    getFileName,
    _getOldFileName,
    getIP,
    motionSensitivityFromData,
    detectionSensitivityFromPercentage,
    extractFieldByChannel,
    getCamData,
)


class TestResultHasError:
    def test_false_result(self):
        assert result_has_error(False) is True

    def test_no_error_code(self):
        assert result_has_error({"some_key": "value"}) is False

    def test_error_code_zero(self):
        assert result_has_error({"error_code": 0}) is False

    def test_error_code_nonzero(self):
        assert result_has_error({"error_code": -1}) is True

    def test_error_code_nonzero_positive(self):
        assert result_has_error({"error_code": 1}) is True

    def test_result_has_error_in_responses_all_ok(self):
        result = {
            "result": {
                "responses": [
                    {"error_code": 0},
                    {"error_code": 0},
                ]
            }
        }
        assert result_has_error(result) is False

    def test_result_has_error_in_responses_one_good_ignores_bad(self):
        result = {
            "result": {
                "responses": [
                    {"error_code": 0},
                    {"error_code": -1},
                ]
            }
        }
        assert result_has_error(result) is False

    def test_result_without_responses_key_is_not_error(self):
        result = {"result": {"some_key": "value"}}
        assert result_has_error(result) is False


class TestTryParseInt:
    def test_parses_valid_int(self):
        assert tryParseInt("42") == 42

    def test_parses_zero(self):
        assert tryParseInt("0") == 0

    def test_parses_negative(self):
        assert tryParseInt("-10") == -10

    def test_returns_none_for_non_int(self):
        assert tryParseInt("abc") is None

    def test_returns_none_for_none(self):
        assert tryParseInt(None) is None

    def test_returns_none_for_empty_string(self):
        assert tryParseInt("") is None

    def test_returns_none_for_float_string(self):
        assert tryParseInt("3.14") is None


class TestGetNightModeMap:
    def test_returns_dict_with_all_modes(self):
        night_map = getNightModeMap()
        assert "inf_night_vision" in night_map
        assert "wtl_night_vision" in night_map
        assert "md_night_vision" in night_map
        assert "dbl_night_vision" in night_map
        assert "shed_night_vision" in night_map

    def test_values_are_display_names(self):
        night_map = getNightModeMap()
        assert night_map["inf_night_vision"] == "Infrared Mode"
        assert night_map["wtl_night_vision"] == "Full Color Mode"


class TestGetNightModeName:
    def test_known_value(self):
        assert getNightModeName("inf_night_vision") == "Infrared Mode"

    def test_unknown_value_passed_through(self):
        assert getNightModeName("custom_mode") == "custom_mode"

    def test_empty_string(self):
        assert getNightModeName("") == ""


class TestGetNightModeValue:
    def test_known_display_name(self):
        assert getNightModeValue("Infrared Mode") == "inf_night_vision"

    def test_unknown_value_passed_through(self):
        assert getNightModeValue("Custom Label") == "Custom Label"

    def test_empty_string(self):
        assert getNightModeValue("") == ""


class TestConvertBasicInfo:
    def test_converts_basic_info(self):
        basic_info = {
            "nickname": base64.b64encode(b"TestCamera").decode("utf-8"),
            "model": "C200",
            "fw_ver": "1.0.0",
            "hw_ver": "1.0",
        }
        result = convertBasicInfo(basic_info)
        assert result["device_alias"] == "TestCamera"
        assert result["device_model"] == "C200"
        assert result["sw_version"] == "1.0.0"
        assert result["hw_version"] == "1.0"


class TestGetIP:
    def test_from_basic_info(self):
        data = {"basic_info": {"ip": "192.168.1.100"}}
        assert getIP(data) == "192.168.1.100"

    def test_from_network_ip_info(self):
        data = {"network_ip_info": {"network": {"wan": {"ipaddr": "10.0.0.1"}}}}
        assert getIP(data) == "10.0.0.1"

    def test_returns_false_when_not_found(self):
        assert getIP({}) is False

    def test_prefers_basic_info(self):
        data = {
            "basic_info": {"ip": "192.168.1.100"},
            "network_ip_info": {"network": {"wan": {"ipaddr": "10.0.0.1"}}},
        }
        assert getIP(data) == "192.168.1.100"


class TestMotionSensitivityFromData:
    def test_returns_low(self):
        assert motionSensitivityFromData({"sensitivity": "low"}) == "low"

    def test_returns_normal(self):
        assert motionSensitivityFromData({"sensitivity": "medium"}) == "normal"

    def test_returns_high(self):
        assert motionSensitivityFromData({"sensitivity": "high"}) == "high"

    def test_returns_digital_sensitivity(self):
        assert motionSensitivityFromData({"digital_sensitivity": "20"}) == "low"

    def test_returns_none_when_no_data(self):
        assert motionSensitivityFromData({}) is None


class TestDetectionSensitivityFromPercentage:
    def test_low_range(self):
        assert detectionSensitivityFromPercentage("20") == "low"

    def test_normal_range(self):
        assert detectionSensitivityFromPercentage("50") == "normal"

    def test_high_range(self):
        assert detectionSensitivityFromPercentage("80") == "high"

    def test_boundary_low(self):
        assert detectionSensitivityFromPercentage("33") == "low"

    def test_boundary_normal(self):
        assert detectionSensitivityFromPercentage("34") == "normal"
        assert detectionSensitivityFromPercentage("66") == "normal"

    def test_boundary_high(self):
        assert detectionSensitivityFromPercentage("67") == "high"

    def test_invalid_input(self):
        assert detectionSensitivityFromPercentage("abc") is None


class TestExtractFieldByChannel:
    def test_simple_field(self):
        result = extractFieldByChannel({"enabled": "on"}, "enabled")
        assert result == "on"

    def test_not_a_dict(self):
        assert extractFieldByChannel("not a dict", "field") is None

    def test_field_not_found_in_empty_dict(self):
        assert extractFieldByChannel({}, "field") is None

    def test_per_channel_extraction(self):
        container = {
            "1": {"enabled": "on", "sensitivity": "high"},
            "2": {"enabled": "off", "sensitivity": "low"},
        }
        result = extractFieldByChannel(container, "enabled")
        assert result == {"1": "on", "2": "off"}


class TestGetFileName:
    def test_valid_int_returns_iso_format(self):
        result = getFileName(1715000000, 1715000100)
        assert result == "2024-05-06_12-53-20"

    def test_valid_string_returns_iso_format(self):
        result = getFileName("1715000000", "1715000100")
        assert result == "2024-05-06_12-53-20"

    def test_non_positive_start_returns_old_format(self):
        result = getFileName(0, 500)
        assert result == "0-500"

    def test_non_positive_string_start_returns_old_format(self):
        result = getFileName("-1", "500")
        assert result == "-1-500"

    def test_encrypted_returns_md5(self):
        result = getFileName(100, 200, encrypted=True)
        assert isinstance(result, str) and len(result) == 32

    def test_child_id_prefixed(self):
        result = getFileName(1715000000, 1715000100, childID="abc123")
        assert result == "abc123-2024-05-06_12-53-20"

    def test_child_id_with_non_positive_start(self):
        result = getFileName(0, 500, childID="abc123")
        assert result == "abc123-0-500"

    def test_string_start_causes_no_type_error(self):
        result = getFileName("1715000000", 1715000100)
        assert result == "2024-05-06_12-53-20"

    def test_string_end_causes_no_type_error(self):
        result = getFileName(1715000000, "1715000100")
        assert result == "2024-05-06_12-53-20"

    def test_both_strings_causes_no_type_error(self):
        result = getFileName("1715000000", "1715000100")
        assert result == "2024-05-06_12-53-20"


class TestGetOldFileName:
    def test_returns_old_format(self):
        assert _getOldFileName(100, 200) == "100-200"

    def test_child_id_prefixed(self):
        assert _getOldFileName(100, 200, childID="abc") == "abc-100-200"

    def test_string_timestamps(self):
        assert _getOldFileName("100", "200", childID="abc") == "abc-100-200"


def _build_raw_data(**overrides):
    data = {
        "get_device_info": [{"device_alias": "TestCam", "device_model": "C200", "model": "C200", "mac": "aa:bb:cc:dd:ee:ff", "led_off": 0, "nickname": "VGVzdENhbQ==", "fw_ver": "1.2.1 Build 250917 Rel.58378n", "hw_ver": "1.0", "device_type": "C200", "region": "EU", "manufacturer_name": "TP-Link"}],
        "getDeviceInfo": [{"device_info": {"basic_info": {"device_alias": "TestCam", "device_model": "C200", "mac": "aa:bb:cc:dd:ee:ff"}}}],
        "getDetectionConfig": [{"motion_detection": {"motion_det": {"enabled": "on", "digital_sensitivity": "70", "sensitivity": "medium"}}}],
        "getDstRule": [{"system": {"dst": {"enabled": "1", "synced": "1", "dst_rule": "DST-01:00,M3.5.0/01:00:00,M10.5.0/02:00:00"}}}],
        "getClockStatus": [{"system": {"clock_status": {"local_time": "2026-05-16 14:44:53", "seconds_from_1970": 1778939093}}}],
        "getTimezone": [{"system": {"basic": {"timezone": "UTC-00:00", "zone_id": "Europe/London", "timing_mode": "ntp"}}}],
        "getAlertEventType": [{"msg_alarm": {"msg_alarm_type": [{"name": "motion_detection", "enabled": "off"}]}}],
        "getPersonDetectionConfig": [{"people_detection": {"detection": {"enabled": "on", "sensitivity": "80"}}}],
        "getVehicleDetectionConfig": [{"vehicle_detection": {"detection": {"enabled": "off", "sensitivity": "50"}}}],
        "getPetDetectionConfig": [{"pet_detection": {"detection": {"enabled": "on", "sensitivity": "90"}}}],
        "getTamperDetectionConfig": [{"tamper_detection": {"tamper_det": {"enabled": "off", "sensitivity": "medium"}}}],
        "getBarkDetectionConfig": [{"bark_detection": {"detection": {"enabled": "off", "sensitivity": "50"}}}],
        "getMeowDetectionConfig": [{"meow_detection": {"detection": {"enabled": "off", "sensitivity": "50"}}}],
        "getGlassDetectionConfig": [{"glass_detection": {"detection": {"enabled": "off", "sensitivity": "50"}}}],
        "getTamperDetectionConfig": [{"tamper_detection": {"tamper_det": {"enabled": "off", "sensitivity": "medium"}}}],
        "getPresetConfig": [{"preset": {"preset": {"id": ["1", "2"], "name": ["Home", "Garden"]}}}],
        "getLensMaskConfig": [{"lens_mask": {"lens_mask_info": {"enabled": "off"}}}],
        "getMsgPushConfig": [{"msg_push": {"chn1_msg_push_info": {"notification_enabled": "on", "rich_notification_enabled": "on"}}}],
        "getLdc": [{"image": {"switch": {"ldc": "on", "force_wtl_state": "off"}, "common": {"style": "original", "light_freq_mode": "auto", "inf_type": "auto", "smartwtl_digital_level": "100"}}}],
        "getNightVisionModeConfig": [{"image": {"switch": {"night_vision_mode": "inf_night_vision"}}}],
        "getDiagnoseMode": [{"system": {"sys": {"diagnose_mode": "off"}}}],
        "getCoverConfig": [{"cover": {"cover": {"enabled": "off"}}}],
        "getSmartTrackConfig": [{"smart_track": {"smart_track_info": {"enabled": "off"}}}],
        "getDeviceIpAddress": [{"network": {"wan": {"ipaddr": "192.168.1.100"}}}],
        "getNightVisionCapability": [{"image_capability": {"supplement_lamp": {"night_vision_mode_range": ["inf_night_vision", "wtl_night_vision"]}}}],
        "getFloodlightConfig": [{"floodlight": {"config": {"brightness": "100"}}}],
        "getFloodlightStatus": [{"status": {"state": "off"}}],
        "getFloodlightCapability": [{"floodlight": {"capability": {"supported": True}}}],
        "getRotationStatus": [{"image": {"switch_chn": {"flip_type": "center"}}}],
        "getSirenConfig": [{"siren_type": "0", "volume": "high", "duration": "5"}],
        "getAlarmConfig": [{"alarm_mode": ["sound", "light"], "enabled": "off", "light_type": "0", "siren_type": "0", "siren_duration": "5", "alarm_duration": "10", "siren_volume": "high", "alarm_volume": "high"}],
        "getLastAlarmInfo": [{"msg_alarm": {"chn1_msg_alarm_info": {"alarm_mode": ["sound"], "enabled": "off"}}}],
        "getSirenStatus": [{"status": False}],
        "getSirenTypeList": [{"siren_type_list": ["Siren", "Tone"]}],
        "getAlertTypeList": [{"msg_alarm": {"alert_type": {"alert_type_list": ["type1", "type2"]}}}],
        "getAlertConfig": [{"msg_alarm": {"usr_def_audio": [{"1": "sound1"}], "capability": {"usr_def_start_file_id": "8195"}}}],
        "getLedStatus": [{"led": {"config": {"enabled": "on"}}}],
        "getTargetTrackConfig": [{"target_track": {"target_track_info": {"enabled": "off"}}}],
        "getFirmwareUpdateStatus": [{"cloud_config": {"upgrade_status": {"state": "normal", "lastUpgradingSuccess": True}}}],
        "getChildDeviceList": [{"child_device_list": [{"device_id": "child1"}]}],
        "getWhitelampConfig": [{"image": {"switch": {"wtl_force_time": "300", "wtl_intensity_level": "5", "force_wtl_state": "off", "flip_type": "center", "smartwtl_digital_level": "100"}}}],
        "getWhitelampStatus": [{"status": 0}],
        "getSdCardStatus": [{"harddisk_manage": {"hd_info": [{"hd_info_1": {"disk_name": "1", "space": "0B", "status": "offline"}}]}}],
        "getLightFrequencyInfo": [{"image": {"common": {"light_freq_mode": "auto", "inf_type": "auto"}}}],
    }
    data.update(overrides)
    return data


def _run_job_sync(fn, *args, **kwargs):
    return fn(*args, **kwargs)


class TestGetCamData:
    @pytest.mark.asyncio
    async def test_non_klap_full_data(self):
        controller = MagicMock()
        controller.isKLAP = False
        controller.getMost = MagicMock(return_value=_build_raw_data())
        controller.user = "admin"
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=_run_job_sync)

        camData = await getCamData(hass, controller)

        assert camData["basic_info"]["device_alias"] == "TestCam"
        assert camData["motion_detection_enabled"] == {"1": "on"}
        assert camData["motion_detection_sensitivity"] == {"1": "normal"}
        assert camData["motion_detection_digital_sensitivity"] == {"1": "70"}
        assert camData["person_detection_enabled"] == {"1": "on"}
        assert camData["vehicle_detection_enabled"] == {"1": "off"}
        assert camData["babyCry_detection_enabled"] is None
        assert camData["pet_detection_enabled"] == {"1": "on"}
        assert camData["bark_detection_enabled"] == "off"
        assert camData["meow_detection_enabled"] == "off"
        assert camData["glass_detection_enabled"] == "off"
        assert camData["tamper_detection_enabled"] == {"1": "off"}
        assert camData["tamper_detection_sensitivity"] == {"1": "normal"}
        assert camData["presets"] == {"1": "Home", "2": "Garden"}
        assert camData["privacy_mode"] == "off"
        assert camData["notifications"] == "on"
        assert camData["rich_notifications"] == "on"
        assert camData["lens_distrotion_correction"] == "on"
        assert camData["ldcStyle"] == "original"
        assert camData["light_frequency_mode"] == "auto"
        assert camData["night_vision_mode"] == "inf_night_vision"
        assert camData["diagnose_mode"]["diagnose_mode"] == "off"
        assert camData["cover_config"]["enabled"] == "off"
        assert camData["smart_track_config"]["enabled"] == "off"
        assert camData["network_ip_info"]["network"]["wan"]["ipaddr"] == "192.168.1.100"
        assert camData["night_vision_capability"] == ["inf_night_vision", "wtl_night_vision"]
        assert camData["night_vision_mode_switching"] == "auto"
        assert camData["flip"] == "on"
        assert camData["alarm_config"]["typeOfAlarm"] == "getSirenConfig"
        assert camData["alarm_config"]["siren_type"] == "0"
        assert camData["alarm_is_hubSiren"] is True
        assert camData["alarm_status"] is False
        assert camData["alarm_user_sounds"] == ["sound1"]
        assert camData["alarm_user_start_id"] == "8195"
        assert camData["led"] == "on"
        assert camData["auto_track"] == "off"
        assert camData["firmwareUpdateStatus"]["upgrade_status"]["state"] == "normal"
        assert camData["childDevices"]["child_device_list"][0]["device_id"] == "child1"
        assert camData["whitelampConfigForceTime"] == "300"
        assert camData["whitelampConfigIntensity"] == "5"
        assert camData["whitelampStatus"] == 0
        assert camData["force_white_lamp_state"] == "off"
        assert camData["smartwtl_digital_level"] == "100"
        assert camData["flood_light_config"]["brightness"] == "100"
        assert camData["flood_light_status"]["state"] == "off"
        assert camData["flood_light_capability"]["supported"] is True
        assert camData["sdCardData"][0]["disk_name"] == "1"
        assert camData["timezone_timezone"] == "UTC-00:00"
        assert camData["timezone_zone_id"] == "Europe/London"
        assert camData["timezone_timing_mode"] == "ntp"
        assert camData["clock_data"]["local_time"] == "2026-05-16 14:44:53"
        assert camData["dst_data"]["enabled"] == "1"
        assert camData["alert_event_types"][0]["name"] == "motion_detection"
        assert camData["user"] == "admin"

    @pytest.mark.asyncio
    async def test_klap_basic_info(self):
        controller = MagicMock()
        controller.isKLAP = True
        controller.getMost = MagicMock(return_value=_build_raw_data())
        controller.user = "admin"
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=_run_job_sync)

        camData = await getCamData(hass, controller)

        assert camData["basic_info"]["device_alias"] == "TestCam"
        assert camData["basic_info"]["device_model"] == "C200"
        assert camData["basic_info"]["mac"] == "aa:bb:cc:dd:ee:ff"

    @pytest.mark.asyncio
    async def test_empty_data_returns_none_defaults(self):
        controller = MagicMock()
        controller.isKLAP = False
        controller.getMost = MagicMock(return_value={
            "getDeviceInfo": [{"device_info": {"basic_info": {}}}],
            "get_device_info": [{"led_off": 0}],
        })
        controller.user = "admin"
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=_run_job_sync)

        camData = await getCamData(hass, controller)

        assert camData["motion_detection_enabled"] is None
        assert camData["motion_detection_sensitivity"] is None
        assert camData["person_detection_enabled"] is None
        assert camData["vehicle_detection_enabled"] is None
        assert camData["babyCry_detection_enabled"] is None
        assert camData["pet_detection_enabled"] is None
        assert camData["bark_detection_enabled"] is None
        assert camData["meow_detection_enabled"] is None
        assert camData["glass_detection_enabled"] is None
        assert camData["tamper_detection_enabled"] is None
        assert camData["privacy_mode"] is None
        assert camData["notifications"] is None
        assert camData["rich_notifications"] is None
        assert camData["lens_distrotion_correction"] is None
        assert camData["ldcStyle"] is None
        assert camData["night_vision_mode"] is None
        assert camData["diagnose_mode"] is None
        assert camData["cover_config"] is None
        assert camData["smart_track_config"] is None
        assert camData["network_ip_info"] is None
        assert camData["night_vision_capability"] is None
        assert camData["flip"] is None
        assert camData["alarm_config"] is None
        assert camData["led"] == "on"  # from get_device_info led_off=0
        assert camData["auto_track"] is None
        assert camData["firmwareUpdateStatus"] is None
        assert camData["childDevices"] is None
        assert camData["whitelampConfigForceTime"] is None
        assert camData["whitelampConfigIntensity"] is None
        assert camData["whitelampStatus"] is None
        assert camData["sdCardData"] == []
        assert camData["timezone_timezone"] is None
        assert camData["timezone_zone_id"] is None
        assert camData["timezone_timing_mode"] is None
        assert camData["clock_data"] is None
        assert camData["dst_data"] is None
        assert camData["alert_event_types"] is None
        assert camData["presets"] == {}
        assert camData["alarm_siren_type_list"] == ["Siren", "Tone"]

    @pytest.mark.asyncio
    async def test_multi_lens_chInfo(self):
        controller = MagicMock()
        controller.isKLAP = False
        controller.getMost = MagicMock(return_value=_build_raw_data(
            getDetectionConfig=[{"motion_detection": {"motion_det": {
                "1": {"enabled": "on", "digital_sensitivity": "70", "sensitivity": "medium"},
                "2": {"enabled": "off", "digital_sensitivity": "50", "sensitivity": "low"},
            }}}],
            getPersonDetectionConfig=[{"people_detection": {"detection": {
                "1": {"enabled": "on", "sensitivity": "80"},
                "2": {"enabled": "off", "sensitivity": "20"},
            }}}],
            getVehicleDetectionConfig=[{"vehicle_detection": {"detection": {
                "1": {"enabled": "off", "sensitivity": "50"},
                "2": {"enabled": "on", "sensitivity": "90"},
            }}}],
            getTamperDetectionConfig=[{"tamper_detection": {"tamper_det": {
                "1": {"enabled": "off", "sensitivity": "medium"},
                "2": {"enabled": "on", "sensitivity": "low"},
            }}}],
        ))
        controller.user = "admin"
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=_run_job_sync)
        chInfo = [{"chn_id": 1}, {"chn_id": 2}]

        camData = await getCamData(hass, controller, chInfo)

        assert camData["motion_detection_enabled"] == {"1": "on", "2": "off"}
        assert camData["motion_detection_sensitivity"] == {"1": "normal", "2": "low"}
        assert camData["motion_detection_digital_sensitivity"] == {"1": "70", "2": "50"}
        assert camData["person_detection_enabled"] == {"1": "on", "2": "off"}
        assert camData["tamper_detection_enabled"] == {"1": "off", "2": "on"}
        assert camData["tamper_detection_sensitivity"] == {"1": "normal", "2": "low"}

    @pytest.mark.asyncio
    async def test_baby_cry_sensitivity_mapping(self):
        controller = MagicMock()
        controller.isKLAP = False
        controller.getMost = MagicMock(return_value=_build_raw_data(
            getBCDConfig=[{"sound_detection": {"bcd": {"enabled": "on", "sensitivity": "low"}}}],
        ))
        controller.user = "admin"
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=_run_job_sync)

        camData = await getCamData(hass, controller)
        assert camData["babyCry_detection_enabled"] == "on"
        assert camData["babyCry_detection_sensitivity"] == "low"

        controller.getMost = MagicMock(return_value=_build_raw_data(
            getBCDConfig=[{"sound_detection": {"bcd": {"enabled": "on", "sensitivity": "medium"}}}],
        ))
        camData = await getCamData(hass, controller)
        assert camData["babyCry_detection_sensitivity"] == "normal"

        controller.getMost = MagicMock(return_value=_build_raw_data(
            getBCDConfig=[{"sound_detection": {"bcd": {"enabled": "on", "sensitivity": "high"}}}],
        ))
        camData = await getCamData(hass, controller)
        assert camData["babyCry_detection_sensitivity"] == "high"

    @pytest.mark.asyncio
    async def test_led_fallback_to_device_info(self):
        controller = MagicMock()
        controller.isKLAP = False
        controller.getMost = MagicMock(return_value={
            "get_device_info": [{"led_off": 0}],
            "getDeviceInfo": [{"device_info": {"basic_info": {}}}],
        })
        controller.user = "admin"
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=_run_job_sync)

        camData = await getCamData(hass, controller)
        assert camData["led"] == "on"

        controller.getMost = MagicMock(return_value={
            "get_device_info": [{"led_off": 1}],
            "getDeviceInfo": [{"device_info": {"basic_info": {}}}],
        })
        camData = await getCamData(hass, controller)
        assert camData["led"] == "off"

    @pytest.mark.asyncio
    async def test_presets_fallback_on_exception(self):
        controller = MagicMock()
        controller.isKLAP = False
        controller.getMost = MagicMock(return_value=_build_raw_data(
            getPresetConfig=[{"preset": {"preset": {"id": [], "name": []}}}],
        ))
        controller.user = "admin"
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=_run_job_sync)

        camData = await getCamData(hass, controller)
        assert camData["presets"] == {}

    @pytest.mark.asyncio
    async def test_alarm_config_progression(self):
        controller = MagicMock()
        controller.isKLAP = False
        controller.getMost = MagicMock(return_value=_build_raw_data(
            getSirenConfig=[False],
            getAlarmConfig=[{"alarm_mode": ["sound"], "enabled": "on"}],
        ))
        controller.user = "admin"
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=_run_job_sync)

        camData = await getCamData(hass, controller)
        assert camData["alarm_config"]["typeOfAlarm"] == "getAlarmConfig"
        assert camData["alarm_config"]["mode"] == ["sound"]
        assert camData["alarm_is_hubSiren"] is False

    @pytest.mark.asyncio
    async def test_siren_type_list_fallback(self):
        controller = MagicMock()
        controller.isKLAP = False
        controller.getMost = MagicMock(return_value=_build_raw_data(
            getSirenTypeList=[False],
            getAlertTypeList=[False],
        ))
        controller.user = "admin"
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=_run_job_sync)

        camData = await getCamData(hass, controller)
        assert camData["alarm_siren_type_list"] == ["Siren", "Tone"]

    @pytest.mark.asyncio
    async def test_non_dict_detection_entries_skipped(self):
        controller = MagicMock()
        controller.isKLAP = False
        controller.getMost = MagicMock(return_value=_build_raw_data(
            getPersonDetectionConfig=[{"people_detection": {"detection": {
                "1": {"enabled": "on", "sensitivity": "80"},
                "2": "not_a_dict",
            }}}],
        ))
        controller.user = "admin"
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=_run_job_sync)
        chInfo = [{"chn_id": 1}, {"chn_id": 2}]

        camData = await getCamData(hass, controller, chInfo)
        assert camData["person_detection_enabled"]["1"] == "on"
        assert "2" not in camData["person_detection_enabled"]

    @pytest.mark.asyncio
    async def test_whitelamp_night_vision_fallback_path(self):
        controller = MagicMock()
        controller.isKLAP = False
        controller.getMost = MagicMock(return_value=_build_raw_data(
            getLdc=[{"image": {"switch": {}, "common": {}}}],
            getLightFrequencyInfo=[{"image": {"common": {"light_freq_mode": "60hz", "inf_type": "auto"}}}],
            getNightVisionModeConfig=[{"image": {"switch": {"night_vision_mode": "wtl_night_vision"}}}],
        ))
        controller.user = "admin"
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=_run_job_sync)

        camData = await getCamData(hass, controller)
        assert camData["light_frequency_mode"] == "60hz"
        assert camData["night_vision_mode_switching"] == "auto"
        assert camData["night_vision_mode"] == "wtl_night_vision"

    @pytest.mark.asyncio
    async def test_flip_fallback_to_rotation_status(self):
        controller = MagicMock()
        controller.isKLAP = False
        controller.getMost = MagicMock(return_value=_build_raw_data(
            getLdc=[{"image": {"switch": {}, "common": {}}}],
            getRotationStatus=[{"image": {"switch": {"flip_type": "center"}}}],
        ))
        controller.user = "admin"
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=_run_job_sync)

        camData = await getCamData(hass, controller)
        assert camData["flip"] == "on"
