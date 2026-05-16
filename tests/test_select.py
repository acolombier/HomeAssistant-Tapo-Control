import pytest
from unittest.mock import MagicMock, AsyncMock
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tapo_control.select import (
    TapoNightVisionSelect,
    TapoLightFrequencySelect,
    TapoAutomaticAlarmModeSelect,
    TapoDualCamLinkage,
    TapoMotionDetectionSelect,
    TapoPersonDetectionSelect,
    TapoBabyCryDetectionSelect,
    TapoPatrolModeSelect,
    TapoTimezoneSelect,
    TapoChimeSound,
    TapoWhitelampForceTimeSelect,
    TapoWhitelampIntensityLevelSelect,
)
from custom_components.tapo_control.const import LOGGER


def make_entry(controller=None, camData=None, **overrides):
    ctrl = controller or MagicMock()
    data = camData or {
        "basic_info": {
            "mac": "aa:bb:cc:dd:ee:ff",
            "device_alias": "TestCamera",
            "device_model": "C200",
        },
        "night_vision_mode": "auto",
        "night_vision_mode_switching": "auto",
        "night_vision_capability": ["auto", "on", "off"],
        "light_frequency_mode": "50",
        "alarm_config": {"automatic": "off", "mode": "light", "siren_type": "test"},
        "alarm_is_hubSiren": False,
        "timezone_timezone": "UTC+01:00",
        "timezone_zone_id": "Europe/Amsterdam",
        "motion_detection_enabled": {"1": "on"},
        "motion_detection_sensitivity": {"1": "normal"},
        "person_detection_enabled": "on",
        "person_detection_sensitivity": "normal",
        "vehicle_detection_enabled": "off",
        "vehicle_detection_sensitivity": "off",
        "babyCry_detection_enabled": "off",
        "babyCry_detection_sensitivity": "off",
        "privacy_mode": "off",
        "dualCamLinkageEnabled": "off",
        "dualCamLinkageType": None,
        "supportAlarmTypeList": {"alarm_type_list": ["type1", "type2"]},
        "chimeAlarmConfigurations": {
            "mac1": {"on_off": 1, "type": "type1", "volume": 10, "duration": 5}
        },
        "whitelampConfigForceTime": "300",
        "whitelampConfigIntensity": "3",
        "quick_response": [{"1": {"name": "Hello", "id": "1"}}],
        "chInfo": None,
        "updated": 1000,
        "enable_media_sync": False,
    }
    coord = MagicMock()
    coord.async_request_refresh = AsyncMock()
    entry = {
        "controller": ctrl,
        "coordinator": coord,
        "camData": data,
        "name": "TestCamera",
        "isChild": False,
        "entities": [],
    }
    entry.update(overrides)
    return entry


class TestTapoNightVisionSelect:
    def test_updateTapo(self):
        entry = make_entry()
        switch = TapoNightVisionSelect(
            entry, MagicMock(), MagicMock(),
            "Night Vision", ["auto", "on", "off"],
            "night_vision_mode", entry["controller"].setDayNightMode,
        )
        switch.updateTapo({"night_vision_mode": "auto"})
        assert switch._attr_state == "auto"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        switch = TapoNightVisionSelect(
            entry, MagicMock(), MagicMock(),
            "Night Vision", ["auto", "on", "off"],
            "night_vision_mode", entry["controller"].setDayNightMode,
        )
        switch.updateTapo({})
        assert switch._attr_state == "unavailable"

    def test_updateTapo_dict_value(self):
        entry = make_entry()
        switch = TapoNightVisionSelect(
            entry, MagicMock(), MagicMock(),
            "Night Vision", ["auto", "on", "off"],
            "night_vision_mode_switching", entry["controller"].setDayNightMode,
            chn_id=1,
        )
        switch.updateTapo({"night_vision_mode_switching": {"1": "on"}})
        assert switch._attr_state == "on"


class TestTapoLightFrequencySelect:
    def test_updateTapo(self):
        entry = make_entry()
        switch = TapoLightFrequencySelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"light_frequency_mode": "50"})
        assert switch._attr_state == "50"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        switch = TapoLightFrequencySelect(entry, MagicMock(), MagicMock())
        switch.updateTapo(None)
        assert switch._attr_state == STATE_UNAVAILABLE

    def test_updateTapo_dict_value(self):
        entry = make_entry()
        switch = TapoLightFrequencySelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"light_frequency_mode": {"1": "60"}})
        assert switch._attr_state == "60"


class TestTapoAutomaticAlarmModeSelect:
    def test_updateTapo_off(self):
        entry = make_entry()
        switch = TapoAutomaticAlarmModeSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"alarm_config": {"automatic": "off", "mode": "light"}})
        assert switch._attr_state == "off"

    def test_updateTapo_both(self):
        entry = make_entry()
        switch = TapoAutomaticAlarmModeSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"alarm_config": {"automatic": "on", "mode": "light,sound"}})
        assert switch._attr_state == "both"

    def test_updateTapo_light_only(self):
        entry = make_entry()
        switch = TapoAutomaticAlarmModeSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"alarm_config": {"automatic": "on", "mode": "light"}})
        assert switch._attr_state == "light"

    def test_updateTapo_sound_only(self):
        entry = make_entry()
        switch = TapoAutomaticAlarmModeSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"alarm_config": {"automatic": "on", "mode": "sound"}})
        assert switch._attr_state == "sound"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        switch = TapoAutomaticAlarmModeSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo(None)
        assert switch._attr_state == STATE_UNAVAILABLE


class TestTapoDualCamLinkage:
    def test_updateTapo_off(self):
        entry = make_entry()
        switch = TapoDualCamLinkage(entry, MagicMock(), MagicMock())
        switch.updateTapo({"dualCamLinkageEnabled": "off", "dualCamLinkageType": None})
        assert switch._attr_state == "off"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        switch = TapoDualCamLinkage(entry, MagicMock(), MagicMock())
        switch.updateTapo(None)
        assert switch._attr_state == STATE_UNAVAILABLE


class TestTapoMotionDetectionSelect:
    def test_updateTapo_off(self):
        entry = make_entry()
        switch = TapoMotionDetectionSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"motion_detection_enabled": {"1": "off"}, "motion_detection_sensitivity": {"1": "normal"}})
        assert switch._attr_state == "off"

    def test_updateTapo_sensitivity(self):
        entry = make_entry()
        switch = TapoMotionDetectionSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"motion_detection_enabled": {"1": "on"}, "motion_detection_sensitivity": {"1": "high"}})
        assert switch._attr_state == "high"

    def test_updateTapo_dict_keys(self):
        entry = make_entry()
        switch = TapoMotionDetectionSelect(entry, MagicMock(), MagicMock(), chn_id=1)
        switch.updateTapo({
            "motion_detection_enabled": {"1": "on"},
            "motion_detection_sensitivity": {"1": "low"},
        })
        assert switch._attr_state == "low"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        switch = TapoMotionDetectionSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo(None)
        assert switch._attr_state == STATE_UNAVAILABLE


class TestTapoPersonDetectionSelect:
    def test_updateTapo_off(self):
        entry = make_entry()
        switch = TapoPersonDetectionSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"person_detection_enabled": "off", "person_detection_sensitivity": "normal"})
        assert switch._attr_state == "off"

    def test_updateTapo_sensitivity(self):
        entry = make_entry()
        switch = TapoPersonDetectionSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"person_detection_enabled": "on", "person_detection_sensitivity": "high"})
        assert switch._attr_state == "high"

    def test_updateTapo_dict_keys(self):
        entry = make_entry()
        switch = TapoPersonDetectionSelect(entry, MagicMock(), MagicMock(), chn_id=1)
        switch.updateTapo({
            "person_detection_enabled": {"1": "on"},
            "person_detection_sensitivity": {"1": "low"},
        })
        assert switch._attr_state == "low"


class TestTapoBabyCryDetectionSelect:
    def test_updateTapo_off(self):
        entry = make_entry()
        switch = TapoBabyCryDetectionSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"babyCry_detection_enabled": "off", "babyCry_detection_sensitivity": "normal"})
        assert switch._attr_state == "off"

    def test_updateTapo_sensitivity(self):
        entry = make_entry()
        switch = TapoBabyCryDetectionSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"babyCry_detection_enabled": "on", "babyCry_detection_sensitivity": "high"})
        assert switch._attr_state == "high"


class TestTapoPatrolModeSelect:
    def test_updateTapo_unavailable_when_privacy_on(self):
        entry = make_entry()
        switch = TapoPatrolModeSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"privacy_mode": "on"})
        assert switch._attr_state == STATE_UNAVAILABLE

    def test_updateTapo_no_privacy(self):
        entry = make_entry()
        switch = TapoPatrolModeSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"privacy_mode": "off"})
        assert switch._attr_state is None


class TestTapoTimezoneSelect:
    def test_updateTapo(self):
        entry = make_entry()
        switch = TapoTimezoneSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"timezone_timezone": "UTC+01:00", "timezone_zone_id": "Europe/Amsterdam"})
        assert switch._attr_state == "UTC+01:00 (Europe/Amsterdam)"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        switch = TapoTimezoneSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"timezone_timezone": None, "timezone_zone_id": None})
        assert switch._attr_state == STATE_UNAVAILABLE


class TestTapoChimeSound:
    def test_updateTapo(self):
        entry = make_entry()
        switch = TapoChimeSound(entry, MagicMock(), MagicMock(), "mac1")
        switch.updateTapo({
            "chimeAlarmConfigurations": {"mac1": {"type": "type2", "volume": 10, "duration": 5}},
            "supportAlarmTypeList": {"alarm_type_list": ["type1", "type2"]},
        })
        assert switch._attr_state == "type2"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        switch = TapoChimeSound(entry, MagicMock(), MagicMock(), "mac1")
        switch.updateTapo({})
        assert switch._attr_state == STATE_UNAVAILABLE


class TestTapoWhitelampForceTimeSelect:
    def test_updateTapo_5min(self):
        entry = make_entry()
        switch = TapoWhitelampForceTimeSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"whitelampConfigForceTime": "300"})
        assert switch._attr_state == "5 min"

    def test_updateTapo_10min(self):
        entry = make_entry()
        switch = TapoWhitelampForceTimeSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"whitelampConfigForceTime": "600"})
        assert switch._attr_state == "10 min"

    def test_updateTapo_15min(self):
        entry = make_entry()
        switch = TapoWhitelampForceTimeSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"whitelampConfigForceTime": "900"})
        assert switch._attr_state == "15 min"

    def test_updateTapo_30min(self):
        entry = make_entry()
        switch = TapoWhitelampForceTimeSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"whitelampConfigForceTime": "1800"})
        assert switch._attr_state == "30 min"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        switch = TapoWhitelampForceTimeSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo(None)
        assert switch._attr_state == "unavailable"


class TestTapoWhitelampIntensityLevelSelect:
    def test_updateTapo(self):
        entry = make_entry()
        switch = TapoWhitelampIntensityLevelSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo({"whitelampConfigIntensity": "3"})
        assert switch._attr_state == "3"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        switch = TapoWhitelampIntensityLevelSelect(entry, MagicMock(), MagicMock())
        switch.updateTapo(None)
        assert switch._attr_state == "unavailable"
