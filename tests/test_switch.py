import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from copy import deepcopy
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tapo_control.switch import (
    TapoPrivacySwitch,
    TapoIndicatorLedSwitch,
    TapoAutoTrackSwitch,
    TapoNotificationsSwitch,
    TapoAutoUpgradeSwitch,
    TapoRecordingPlanSwitch,
    TapoMicrophoneMuteSwitch,
    TapoMicrophoneNoiseCancellationSwitch,
    TapoRecordAudioSwitch,
    TapoCoverSwitch,
    TapoDiagnoseModeSwitch,
    TapoSmartTrackSwitch,
    TapoFlipSwitch,
    TapoHDRSwitch,
    TapoAlarmEventTypeSwitch,
    TapoLensDistortionCorrectionSwitch,
    TapoRichNotificationsSwitch,
    TapoEnableMediaSyncSwitch,
    TapoDualLinkageTargetSwitch,
    TapoChimeRingtoneSwitch,
)
from custom_components.tapo_control.const import LOGGER


def make_entry(controller=None, coordinator=None, camData=None, **overrides):
    ctrl = controller or MagicMock()
    coord = coordinator or MagicMock()
    coord.async_request_refresh = AsyncMock()
    data = camData or {
        "basic_info": {
            "mac": "aa:bb:cc:dd:ee:ff",
            "device_alias": "TestCamera",
            "device_model": "C200",
        },
        "privacy_mode": "off",
        "led": "on",
        "auto_track": "on",
        "notifications": "on",
        "rich_notifications": "on",
        "autoUpgradeEnabled": "on",
        "record_audio": True,
        "recordPlan": {"enabled": "on"},
        "microphoneMute": "off",
        "microphoneNoiseCancelling": "off",
        "flip": "on",
        "lens_distrotion_correction": "on",
        "smart_track_config": {"track_human_enabled": "on"},
        "cover_config": {"enabled": "off"},
        "diagnose_mode": {"diagnose_mode": "off"},
        "videoQualities": {"video": {"main": {"hdr": "1"}}},
        "videoCapability": {
            "video_capability": {"main": {"hdrs": True}},
        },
        "dualLinkageCapability": {"lens_support": "1"},
        "dualLinkageTargetSetting": {"lens_enabled": "on"},
        "chimeAlarmConfigurations": {
            "mac1": {"on_off": 1, "type": "type1", "volume": 10, "duration": 5}
        },
        "alert_event_types": [
            {"name": "motion", "enabled": "on"},
            {"name": "person", "enabled": "off"},
        ],
        "chInfo": None,
        "updated": 1000,
        "enable_media_sync": False,
    }
    entry = {
        "controller": ctrl,
        "coordinator": coord,
        "camData": data,
        "name": "TestCamera",
        "isChild": False,
        "entities": [],
        ENABLE_MEDIA_SYNC: False,
    }
    entry.update(overrides)
    return entry


from custom_components.tapo_control.const import ENABLE_MEDIA_SYNC


def _run_job(fn, *args, **kwargs):
    return fn(*args, **kwargs)


class BaseSwitchTest:
    SWITCH_CLASS = None
    SWITCH_KWARGS = {}
    SWITCH_CTRL_METHOD_TURN_ON = None
    SWITCH_CTRL_METHOD_TURN_OFF = None
    SWITCH_TURN_ON_ARGS = ()
    SWITCH_TURN_OFF_ARGS = ()
    SWITCH_CAMDATA_KEY = None
    SWITCH_CAMDATA_ON_VALUE = "on"

    def create_switch(self, entry, hass=None, config_entry=None):
        if hass is None:
            hass = MagicMock()
            hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        if config_entry is None:
            config_entry = MagicMock()
            config_entry.data = {"media_sync_hours": 24}
        switch = self.SWITCH_CLASS(entry, hass, config_entry, **self.SWITCH_KWARGS)
        switch.hass = hass
        switch.entity_id = "switch.test"
        switch.async_write_ha_state = MagicMock()
        return switch

    @pytest.mark.asyncio
    async def test_turn_on_calls_controller_with_correct_args(self):
        controller = MagicMock()
        setattr(controller, self.SWITCH_CTRL_METHOD_TURN_ON, MagicMock(return_value={"error_code": 0}))
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        await switch.async_turn_on()
        method = getattr(controller, self.SWITCH_CTRL_METHOD_TURN_ON)
        method.assert_called_once_with(*self.SWITCH_TURN_ON_ARGS)

    @pytest.mark.asyncio
    async def test_turn_off_calls_controller_with_correct_args(self):
        controller = MagicMock()
        setattr(controller, self.SWITCH_CTRL_METHOD_TURN_OFF, MagicMock(return_value={"error_code": 0}))
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        await switch.async_turn_off()
        method = getattr(controller, self.SWITCH_CTRL_METHOD_TURN_OFF)
        method.assert_called_once_with(*self.SWITCH_TURN_OFF_ARGS)

    @pytest.mark.asyncio
    async def test_turn_on_success_updates_state(self):
        controller = MagicMock()
        setattr(controller, self.SWITCH_CTRL_METHOD_TURN_ON, MagicMock(return_value={"error_code": 0}))
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        switch._hass.async_add_executor_job = AsyncMock(return_value={"error_code": 0})
        await switch.async_turn_on()
        assert switch._attr_state == "on"

    @pytest.mark.asyncio
    async def test_turn_on_error_code_does_not_change_state(self):
        controller = MagicMock()
        setattr(controller, self.SWITCH_CTRL_METHOD_TURN_ON, MagicMock(return_value={"error_code": -1}))
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        switch._attr_state = "off"
        switch._hass.async_add_executor_job = AsyncMock(return_value={"error_code": -1})
        await switch.async_turn_on()
        assert switch._attr_state == "off"

    @pytest.mark.asyncio
    async def test_turn_on_no_error_code_in_result_updates_state(self):
        controller = MagicMock()
        setattr(controller, self.SWITCH_CTRL_METHOD_TURN_ON, MagicMock(return_value={}))
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        switch._hass.async_add_executor_job = AsyncMock(return_value={})
        await switch.async_turn_on()
        assert switch._attr_state == "on"

    @pytest.mark.asyncio
    async def test_turn_on_writes_state_and_requests_refresh(self):
        controller = MagicMock()
        setattr(controller, self.SWITCH_CTRL_METHOD_TURN_ON, MagicMock(return_value={"error_code": 0}))
        coordinator = MagicMock()
        coordinator.async_request_refresh = AsyncMock()
        entry = make_entry(controller=controller, coordinator=coordinator)
        switch = self.create_switch(entry)
        switch.async_write_ha_state = MagicMock()
        switch._hass.async_add_executor_job = AsyncMock(return_value={"error_code": 0})
        await switch.async_turn_on()
        switch.async_write_ha_state.assert_called_once()
        coordinator.async_request_refresh.assert_called_once()

    def test_updateTapo_with_none_camData_sets_unavailable(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo(None)
        assert switch._attr_state == STATE_UNAVAILABLE

    def test_updateTapo_with_empty_dict_sets_unavailable(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({})
        assert switch._attr_state == STATE_UNAVAILABLE


class TestTapoPrivacySwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoPrivacySwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setPrivacyMode"
    SWITCH_CTRL_METHOD_TURN_OFF = "setPrivacyMode"
    SWITCH_TURN_ON_ARGS = (True,)
    SWITCH_TURN_OFF_ARGS = (False,)

    def test_updateTapo_parses_privacy_mode_on(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"privacy_mode": "on"})
        assert switch._attr_state == "on"
        assert switch._attr_is_on is True

    def test_updateTapo_parses_privacy_mode_off(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"privacy_mode": "off"})
        assert switch._attr_state == "off"
        assert switch._attr_is_on is False

    def test_icon_on_state(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch._attr_is_on = True
        assert switch.icon == "mdi:eye-off-outline"

    def test_icon_off_state(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch._attr_is_on = False
        assert switch.icon == "mdi:eye-outline"

    def test_entity_category_none(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        assert switch.entity_category is None


class TestTapoIndicatorLedSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoIndicatorLedSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setLEDEnabled"
    SWITCH_CTRL_METHOD_TURN_OFF = "setLEDEnabled"
    SWITCH_TURN_ON_ARGS = (True,)
    SWITCH_TURN_OFF_ARGS = (False,)

    def test_updateTapo_parses_led_on(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"led": "on"})
        assert switch._attr_state == "on"

    def test_updateTapo_parses_led_off(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"led": "off"})
        assert switch._attr_state == "off"


class TestTapoAutoTrackSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoAutoTrackSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setAutoTrackTarget"
    SWITCH_CTRL_METHOD_TURN_OFF = "setAutoTrackTarget"
    SWITCH_TURN_ON_ARGS = (True,)
    SWITCH_TURN_OFF_ARGS = (False,)

    def test_updateTapo(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"auto_track": "on"})
        assert switch._attr_state == "on"


class TestTapoNotificationsSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoNotificationsSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setNotificationsEnabled"
    SWITCH_CTRL_METHOD_TURN_OFF = "setNotificationsEnabled"
    SWITCH_TURN_ON_ARGS = (True,)
    SWITCH_TURN_OFF_ARGS = (False,)

    def test_updateTapo(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"notifications": "on"})
        assert switch._attr_state == "on"


class TestTapoRichNotificationsSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoRichNotificationsSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setNotificationsEnabled"
    SWITCH_CTRL_METHOD_TURN_OFF = "setNotificationsEnabled"
    SWITCH_TURN_ON_ARGS = (None, True)
    SWITCH_TURN_OFF_ARGS = (None, False)

    def test_updateTapo(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"rich_notifications": "on"})
        assert switch._attr_state == "on"


class TestTapoAutoUpgradeSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoAutoUpgradeSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setFirmwareAutoUpgradeConfig"
    SWITCH_CTRL_METHOD_TURN_OFF = "setFirmwareAutoUpgradeConfig"
    SWITCH_TURN_ON_ARGS = (True,)
    SWITCH_TURN_OFF_ARGS = (False,)

    def test_updateTapo(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"autoUpgradeEnabled": "on"})
        assert switch._attr_state == "on"


class TestTapoRecordingPlanSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoRecordingPlanSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setRecordPlan"
    SWITCH_CTRL_METHOD_TURN_OFF = "setRecordPlan"
    SWITCH_TURN_ON_ARGS = (True,)
    SWITCH_TURN_OFF_ARGS = (False,)

    def test_updateTapo(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"recordPlan": {"enabled": "on"}})
        assert switch._attr_state == "on"

    def test_updateTapo_missing_recordPlan(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"recordPlan": {}})
        assert switch._attr_state == STATE_UNAVAILABLE


class TestTapoMicrophoneMuteSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoMicrophoneMuteSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setMicrophone"
    SWITCH_CTRL_METHOD_TURN_OFF = "setMicrophone"
    SWITCH_TURN_ON_ARGS = (None, True)
    SWITCH_TURN_OFF_ARGS = (None, False)

    def test_updateTapo(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"microphoneMute": "on"})
        assert switch._attr_state == "on"


class TestTapoMicrophoneNoiseCancellationSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoMicrophoneNoiseCancellationSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setMicrophone"
    SWITCH_CTRL_METHOD_TURN_OFF = "setMicrophone"
    SWITCH_TURN_ON_ARGS = (None, None, True)
    SWITCH_TURN_OFF_ARGS = (None, None, False)

    @pytest.mark.asyncio
    async def test_turn_on_correct_args(self):
        controller = MagicMock()
        controller.setMicrophone = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        await switch.async_turn_on()
        controller.setMicrophone.assert_called_once_with(None, None, True)

    @pytest.mark.asyncio
    async def test_turn_off_correct_args(self):
        controller = MagicMock()
        controller.setMicrophone = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        await switch.async_turn_off()
        controller.setMicrophone.assert_called_once_with(None, None, False)

    def test_updateTapo(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"microphoneNoiseCancelling": "on"})
        assert switch._attr_state == "on"


class TestTapoRecordAudioSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoRecordAudioSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setRecordAudio"
    SWITCH_CTRL_METHOD_TURN_OFF = "setRecordAudio"
    SWITCH_TURN_ON_ARGS = (True,)
    SWITCH_TURN_OFF_ARGS = (False,)

    def test_updateTapo_on(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"record_audio": True})
        assert switch._attr_state == "on"

    def test_updateTapo_off(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"record_audio": False})
        assert switch._attr_state == "off"


class TestTapoCoverSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoCoverSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setCoverConfig"
    SWITCH_CTRL_METHOD_TURN_OFF = "setCoverConfig"
    SWITCH_TURN_ON_ARGS = (True,)
    SWITCH_TURN_OFF_ARGS = (False,)

    def test_updateTapo(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"cover_config": {"enabled": "on"}})
        assert switch._attr_state == "on"


class TestTapoDiagnoseModeSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoDiagnoseModeSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setDiagnoseMode"
    SWITCH_CTRL_METHOD_TURN_OFF = "setDiagnoseMode"
    SWITCH_TURN_ON_ARGS = (True,)
    SWITCH_TURN_OFF_ARGS = (False,)

    def test_updateTapo(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"diagnose_mode": {"diagnose_mode": "on"}})
        assert switch._attr_state == "on"


class TestTapoHDRSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoHDRSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setHDR"
    SWITCH_CTRL_METHOD_TURN_OFF = "setHDR"
    SWITCH_TURN_ON_ARGS = (True,)
    SWITCH_TURN_OFF_ARGS = (False,)

    def test_updateTapo_hdr_on(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"videoQualities": {"video": {"main": {"hdr": "1"}}}})
        assert switch._attr_state == "on"

    def test_updateTapo_hdr_off(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"videoQualities": {"video": {"main": {"hdr": "0"}}}})
        assert switch._attr_state == "off"


class TestTapoFlipSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoFlipSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setImageFlipVertical"
    SWITCH_CTRL_METHOD_TURN_OFF = "setImageFlipVertical"
    SWITCH_TURN_ON_ARGS = (True, None)
    SWITCH_TURN_OFF_ARGS = (False, None)

    @pytest.mark.asyncio
    async def test_turn_on_correct_args(self):
        controller = MagicMock()
        controller.setImageFlipVertical = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        await switch.async_turn_on()
        controller.setImageFlipVertical.assert_called_once_with(True, None)

    @pytest.mark.asyncio
    async def test_turn_on_with_chn_id(self):
        controller = MagicMock()
        controller.setImageFlipVertical = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = TapoFlipSwitch(entry, MagicMock(), MagicMock(), "Lens2", 2)
        switch.hass = switch._hass
        switch.entity_id = "switch.test"
        switch.async_write_ha_state = MagicMock()
        switch._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await switch.async_turn_on()
        controller.setImageFlipVertical.assert_called_once_with(True, [2])

    def test_updateTapo_simple_value(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"flip": "on"})
        assert switch._attr_state == "on"

    def test_updateTapo_dict_value(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"flip": {"1": "on"}})
        assert switch._attr_state == "on"


class TestTapoLensDistortionCorrectionSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoLensDistortionCorrectionSwitch
    SWITCH_CTRL_METHOD_TURN_ON = "setLensDistortionCorrection"
    SWITCH_CTRL_METHOD_TURN_OFF = "setLensDistortionCorrection"
    SWITCH_TURN_ON_ARGS = (True, None)
    SWITCH_TURN_OFF_ARGS = (False, None)

    @pytest.mark.asyncio
    async def test_turn_on_correct_args(self):
        controller = MagicMock()
        controller.setLensDistortionCorrection = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        await switch.async_turn_on()
        controller.setLensDistortionCorrection.assert_called_once_with(True, None)

    @pytest.mark.asyncio
    async def test_turn_on_with_chn_id(self):
        controller = MagicMock()
        controller.setLensDistortionCorrection = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = TapoLensDistortionCorrectionSwitch(entry, MagicMock(), MagicMock(), "Lens2", 2)
        switch.hass = switch._hass
        switch.entity_id = "switch.test"
        switch.async_write_ha_state = MagicMock()
        switch._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await switch.async_turn_on()
        controller.setLensDistortionCorrection.assert_called_once_with(True, [2])

    def test_updateTapo_simple_value(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"lens_distrotion_correction": "on"})
        assert switch._attr_state == "on"

    def test_updateTapo_dict_value(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"lens_distrotion_correction": {"1": "off"}})
        assert switch._attr_state == "off"


class TestTapoSmartTrackSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoSmartTrackSwitch
    SWITCH_TURN_ON_ARGS = ("track_human_enabled", True)
    SWITCH_TURN_OFF_ARGS = ("track_human_enabled", False)
    SWITCH_KWARGS = {"typeOfSmartTrack": "track_human_enabled"}

    @property
    def SWITCH_CTRL_METHOD_TURN_ON(self):
        return "setSmartTrackConfig"

    @property
    def SWITCH_CTRL_METHOD_TURN_OFF(self):
        return "setSmartTrackConfig"

    @pytest.mark.asyncio
    async def test_turn_on_correct_args(self):
        controller = MagicMock()
        controller.setSmartTrackConfig = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        await switch.async_turn_on()
        controller.setSmartTrackConfig.assert_called_once_with("track_human_enabled", True)

    @pytest.mark.asyncio
    async def test_turn_off_correct_args(self):
        controller = MagicMock()
        controller.setSmartTrackConfig = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        await switch.async_turn_off()
        controller.setSmartTrackConfig.assert_called_once_with("track_human_enabled", False)

    def test_updateTapo(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"smart_track_config": {"track_human_enabled": "on"}})
        assert switch._attr_state == "on"


class TestTapoAlarmEventTypeSwitch:
    @pytest.mark.asyncio
    async def test_turn_on_controller_arguments(self):
        controller = MagicMock()
        controller.setAlertEventType = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = TapoAlarmEventTypeSwitch(entry, MagicMock(), MagicMock(), "motion")
        switch.hass = switch._hass
        switch.entity_id = "switch.test"
        switch.async_write_ha_state = MagicMock()
        switch._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await switch.async_turn_on()
        controller.setAlertEventType.assert_called_once_with("motion", True)

    @pytest.mark.asyncio
    async def test_turn_off_controller_arguments(self):
        controller = MagicMock()
        controller.setAlertEventType = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = TapoAlarmEventTypeSwitch(entry, MagicMock(), MagicMock(), "motion")
        switch.hass = switch._hass
        switch.entity_id = "switch.test"
        switch.async_write_ha_state = MagicMock()
        switch._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await switch.async_turn_off()
        controller.setAlertEventType.assert_called_once_with("motion", False)

    @pytest.mark.asyncio
    async def test_turn_off_sets_state_to_off(self):
        controller = MagicMock()
        controller.setAlertEventType = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = TapoAlarmEventTypeSwitch(entry, MagicMock(), MagicMock(), "motion")
        switch.hass = switch._hass
        switch.entity_id = "switch.test"
        switch.async_write_ha_state = MagicMock()
        switch._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await switch.async_turn_off()
        assert switch._attr_state == "off"

    def test_updateTapo_event_enabled(self):
        entry = make_entry()
        switch = TapoAlarmEventTypeSwitch(entry, MagicMock(), MagicMock(), "motion")
        switch.updateTapo({"alert_event_types": [{"name": "motion", "enabled": "on"}]})
        assert switch._attr_state == "on"

    def test_updateTapo_event_disabled(self):
        entry = make_entry()
        switch = TapoAlarmEventTypeSwitch(entry, MagicMock(), MagicMock(), "motion")
        switch.updateTapo({"alert_event_types": [{"name": "motion", "enabled": "off"}]})
        assert switch._attr_state == "off"


class TestTapoDualLinkageTargetSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoDualLinkageTargetSwitch
    SWITCH_KWARGS = {"target_type": "lens"}
    SWITCH_TURN_ON_ARGS = ("lens_enabled", True)
    SWITCH_TURN_OFF_ARGS = ("lens_enabled", False)

    @property
    def SWITCH_CTRL_METHOD_TURN_ON(self):
        return "setLinkageTargetSetting"

    @property
    def SWITCH_CTRL_METHOD_TURN_OFF(self):
        return "setLinkageTargetSetting"

    @pytest.mark.asyncio
    async def test_turn_on_correct_args(self):
        controller = MagicMock()
        controller.setLinkageTargetSetting = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        await switch.async_turn_on()
        controller.setLinkageTargetSetting.assert_called_once_with("lens_enabled", True)

    @pytest.mark.asyncio
    async def test_turn_off_correct_args(self):
        controller = MagicMock()
        controller.setLinkageTargetSetting = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        await switch.async_turn_off()
        controller.setLinkageTargetSetting.assert_called_once_with("lens_enabled", False)

    def test_updateTapo(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"dualLinkageTargetSetting": {"lens_enabled": "on"}})
        assert switch._attr_state == "on"


class TestTapoChimeRingtoneSwitch(BaseSwitchTest):
    SWITCH_CLASS = TapoChimeRingtoneSwitch
    SWITCH_KWARGS = {"macAddress": "mac1"}
    SWITCH_TURN_ON_ARGS = ("mac1", True)
    SWITCH_TURN_OFF_ARGS = ("mac1", False)

    @property
    def SWITCH_CTRL_METHOD_TURN_ON(self):
        return "setChimeAlarmConfigure"

    @property
    def SWITCH_CTRL_METHOD_TURN_OFF(self):
        return "setChimeAlarmConfigure"

    @pytest.mark.asyncio
    async def test_turn_on_correct_args(self):
        controller = MagicMock()
        controller.setChimeAlarmConfigure = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        await switch.async_turn_on()
        controller.setChimeAlarmConfigure.assert_called_once_with("mac1", True)

    @pytest.mark.asyncio
    async def test_turn_off_correct_args(self):
        controller = MagicMock()
        controller.setChimeAlarmConfigure = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        switch = self.create_switch(entry)
        await switch.async_turn_off()
        controller.setChimeAlarmConfigure.assert_called_once_with("mac1", False)

    def test_updateTapo(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"chimeAlarmConfigurations": {"mac1": {"on_off": 1}}})
        assert switch._attr_state == "on"

    def test_updateTapo_missing_mac(self):
        entry = make_entry()
        switch = self.create_switch(entry)
        switch.updateTapo({"chimeAlarmConfigurations": {}})
        assert switch._attr_state == STATE_UNAVAILABLE


class TestTapoEnableMediaSyncSwitch:
    def test_initial_state_from_stored_value_true(self):
        entry = make_entry()
        hass = MagicMock()
        config_entry = MagicMock()
        config_entry.data = {"media_sync_hours": 24}
        entry_storage = MagicMock()
        switch = TapoEnableMediaSyncSwitch(entry, hass, config_entry, entry_storage, True)
        assert switch._attr_state == "on"

    def test_initial_state_from_stored_value_false(self):
        entry = make_entry()
        hass = MagicMock()
        config_entry = MagicMock()
        config_entry.data = {"media_sync_hours": 24}
        entry_storage = MagicMock()
        switch = TapoEnableMediaSyncSwitch(entry, hass, config_entry, entry_storage, False)
        assert switch._attr_state == "off"
