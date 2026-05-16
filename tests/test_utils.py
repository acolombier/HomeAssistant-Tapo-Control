import datetime
import pytest
from unittest.mock import MagicMock, patch
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
