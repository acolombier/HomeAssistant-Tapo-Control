import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tapo_control.button import (
    TapoRebootButton,
    TapoFormatButton,
    TapoSyncTimeButton,
    TapoCalibrateButton,
    TapoMoveUpButton,
    TapoMoveDownButton,
    TapoMoveRightButton,
    TapoMoveLeftButton,
    TapoStartManualAlarmButton,
    TapoStopManualAlarmButton,
    TapoChimeRing,
)
from custom_components.tapo_control.const import DOMAIN, LOGGER


def _run_job(fn, *args, **kwargs):
    return fn(*args, **kwargs)


def _setup_entity(entity, hass=None):
    if hass is None:
        hass = MagicMock()
    entity.hass = hass
    entity.entity_id = "button.test"
    entity.async_write_ha_state = MagicMock()
    return hass


def make_entry(controller=None, camData=None, **overrides):
    ctrl = controller or MagicMock()
    data = camData or {
        "basic_info": {
            "mac": "aa:bb:cc:dd:ee:ff",
            "device_alias": "TestCamera",
            "device_model": "C200",
        },
        "privacy_mode": "off",
        "alarm_config": {"siren_type": "test_type"},
        "clock_data": {"local_time": "12:00", "seconds_from_1970": "1000000"},
        "dst_data": {"start": "2024-01-01"},
        "updated": 1000,
    }
    coord = MagicMock()
    coord.async_request_refresh = AsyncMock()
    entry = {
        "controller": ctrl,
        "coordinator": coord,
        "camData": data,
        "name": "TestCamera",
        "isChild": False,
        "isParent": True,
        "entities": [],
        "movement_angle": 15,
        "chime_play_type": 1,
        "chime_play_volume": 15,
        "chime_play_duration": 0,
    }
    entry.update(overrides)
    return entry


class TestTapoRebootButton:
    @pytest.mark.asyncio
    async def test_press_calls_reboot(self):
        controller = MagicMock()
        controller.reboot = MagicMock()
        entry = make_entry(controller=controller)
        button = TapoRebootButton(entry, MagicMock(), MagicMock())
        _setup_entity(button)
        button._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await button.async_press()
        controller.reboot.assert_called_once()

    def test_device_class(self):
        entry = make_entry()
        button = TapoRebootButton(entry, MagicMock(), MagicMock())
        assert button.device_class == "restart"


class TestTapoFormatButton:
    @pytest.mark.asyncio
    async def test_press_calls_format(self):
        controller = MagicMock()
        controller.format = MagicMock()
        entry = make_entry(controller=controller)
        button = TapoFormatButton(entry, MagicMock(), MagicMock())
        _setup_entity(button)
        button._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await button.async_press()
        controller.format.assert_called_once()


class TestTapoCalibrateButton:
    @pytest.mark.asyncio
    async def test_press_calls_calibrate(self):
        controller = MagicMock()
        controller.calibrateMotor = MagicMock()
        entry = make_entry(controller=controller)
        button = TapoCalibrateButton(entry, MagicMock(), MagicMock())
        _setup_entity(button)
        button._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await button.async_press()
        controller.calibrateMotor.assert_called_once()

    def test_updateTapo_unavailable_when_privacy_on(self):
        entry = make_entry()
        button = TapoCalibrateButton(entry, MagicMock(), MagicMock())
        button.updateTapo({"privacy_mode": "on"})
        assert button._attr_state == STATE_UNAVAILABLE

    def test_updateTapo_available(self):
        entry = make_entry()
        button = TapoCalibrateButton(entry, MagicMock(), MagicMock())
        button.updateTapo({"privacy_mode": "off"})
        assert button._attr_state is None


class TestTapoMoveButtons:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("button_class,expected_x,expected_y", [
        (TapoMoveUpButton, 0, 15),
        (TapoMoveDownButton, 0, -15),
        (TapoMoveRightButton, 15, 0),
        (TapoMoveLeftButton, -15, 0),
    ])
    async def test_move_correct_args(self, button_class, expected_x, expected_y):
        controller = MagicMock()
        controller.moveMotor = MagicMock()
        entry = make_entry(controller=controller)
        button = button_class(entry, MagicMock(), MagicMock())
        _setup_entity(button)
        button._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await button.async_press()
        controller.moveMotor.assert_called_once_with(expected_x, expected_y)

    @pytest.mark.asyncio
    async def test_movement_angle_from_entry(self):
        controller = MagicMock()
        controller.moveMotor = MagicMock()
        entry = make_entry(controller=controller, movement_angle=30)
        button = TapoMoveUpButton(entry, MagicMock(), MagicMock())
        _setup_entity(button)
        button._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await button.async_press()
        controller.moveMotor.assert_called_once_with(0, 30)


class TestTapoStartManualAlarmButton:
    @pytest.mark.asyncio
    async def test_press_calls_startManualAlarm(self):
        controller = MagicMock()
        controller.startManualAlarm = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        button = TapoStartManualAlarmButton(entry, MagicMock(), MagicMock())
        _setup_entity(button)
        button._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await button.async_press()
        controller.startManualAlarm.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_to_setSirenStatus(self):
        controller = MagicMock()
        controller.startManualAlarm = MagicMock(side_effect=Exception("fail"))
        controller.setSirenStatus = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        button = TapoStartManualAlarmButton(entry, MagicMock(), MagicMock())
        _setup_entity(button)
        button._hass.async_add_executor_job = AsyncMock(side_effect=[
            Exception("fail"),
            {"error_code": 0},
        ])
        await button.async_press()

    @pytest.mark.asyncio
    async def test_all_fail_raises_exception(self):
        controller = MagicMock()
        controller.startManualAlarm = MagicMock(side_effect=Exception("fail"))
        controller.setSirenStatus = MagicMock(side_effect=Exception("fail"))
        controller.testUsrDefAudio = MagicMock(return_value={"error_code": -1})
        entry = make_entry(controller=controller)
        button = TapoStartManualAlarmButton(entry, MagicMock(), MagicMock())
        button.sirenType = "test_type"
        _setup_entity(button)
        button._hass.async_add_executor_job = AsyncMock(side_effect=[
            Exception("fail"),
            Exception("fail"),
            {"error_code": -1},
        ])
        with pytest.raises(Exception, match="Camera does not support triggering the siren"):
            await button.async_press()

    @pytest.mark.asyncio
    async def test_all_fail_no_siren_type_raises(self):
        controller = MagicMock()
        controller.startManualAlarm = MagicMock(side_effect=Exception("fail"))
        controller.setSirenStatus = MagicMock(side_effect=Exception("fail"))
        entry = make_entry(controller=controller)
        entry["camData"]["alarm_config"] = {}
        button = TapoStartManualAlarmButton(entry, MagicMock(), MagicMock())
        button.sirenType = None
        _setup_entity(button)
        button._hass.async_add_executor_job = AsyncMock(side_effect=[
            Exception("fail"),
            Exception("fail"),
        ])
        with pytest.raises(Exception, match="Camera does not support triggering the siren"):
            await button.async_press()

    def test_updateTapo_privacy_mode(self):
        entry = make_entry()
        button = TapoStartManualAlarmButton(entry, MagicMock(), MagicMock())
        button.updateTapo({"privacy_mode": "on"})
        assert button.camData == STATE_UNAVAILABLE

    def test_updateTapo_sets_siren_type(self):
        entry = make_entry()
        button = TapoStartManualAlarmButton(entry, MagicMock(), MagicMock())
        button.updateTapo({"privacy_mode": "off", "alarm_config": {"siren_type": "test_type"}})
        assert button.sirenType == "test_type"


class TestTapoStopManualAlarmButton:
    @pytest.mark.asyncio
    async def test_press_calls_stopManualAlarm(self):
        controller = MagicMock()
        controller.stopManualAlarm = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        button = TapoStopManualAlarmButton(entry, MagicMock(), MagicMock())
        _setup_entity(button)
        button._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await button.async_press()
        controller.stopManualAlarm.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_fail_raises_exception(self):
        controller = MagicMock()
        controller.stopManualAlarm = MagicMock(side_effect=Exception("fail"))
        controller.setSirenStatus = MagicMock(side_effect=Exception("fail"))
        controller.testUsrDefAudio = MagicMock(return_value={"error_code": -1})
        entry = make_entry(controller=controller)
        button = TapoStopManualAlarmButton(entry, MagicMock(), MagicMock())
        button.sirenType = "test_type"
        _setup_entity(button)
        button._hass.async_add_executor_job = AsyncMock(side_effect=[
            Exception("fail"),
            Exception("fail"),
            {"error_code": -1},
        ])
        with pytest.raises(Exception, match="Camera does not support triggering the siren"):
            await button.async_press()


class TestTapoChimeRing:
    @pytest.mark.asyncio
    async def test_press_calls_playAlarm(self):
        controller = MagicMock()
        controller.playAlarm = MagicMock()
        entry = make_entry(controller=controller)
        button = TapoChimeRing(entry, MagicMock(), MagicMock())
        _setup_entity(button)
        button._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await button.async_press()
        controller.playAlarm.assert_called_once()
