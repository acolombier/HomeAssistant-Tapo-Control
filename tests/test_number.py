import pytest
from unittest.mock import MagicMock, AsyncMock
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tapo_control.number import (
    TapoMotionDetectionDigitalSensitivity,
    TapoMicrophoneVolume,
    TapoSpeakerVolume,
    TapoSirenVolume,
    TapoSirenDuration,
    TapoFloodlightBrightness,
    TapoSpotlightIntensity,
    TapoChimeDuration,
    TapoChimeVolume,
    TapoMovementAngle,
    TapoChimeVolumePlay,
    TapoChimeDurationPlay,
)
from custom_components.tapo_control.tapo.entities import TapoNumberEntity


def _run_job(fn, *args, **kwargs):
    return fn(*args, **kwargs)


def _setup_entity(entity, hass=None):
    if hass is None:
        hass = MagicMock()
    entity.hass = hass
    entity.entity_id = "number.test"
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
        "motion_detection_digital_sensitivity": 50,
        "microphoneVolume": 50,
        "speakerVolume": 50,
        "alarm_config": {
            "siren_volume": 5,
            "siren_duration": 30,
            "alarm_volume": 5,
            "alarm_duration": 30,
            "typeOfAlarm": "getAlarm",
            "automatic": "off",
            "mode": "light",
        },
        "alarm_is_hubSiren": False,
        "flood_light_config": {"intensity_level": 128},
        "flood_light_capability": {"min_intensity": 1, "intensity_level_max": 255},
        "whitelampConfigIntensity": "3",
        "smartwtl_digital_level": None,
        "ldcStyle": "standard",
        "chimeAlarmConfigurations": {
            "mac1": {"on_off": 1, "type": "type1", "volume": 10, "duration": 5}
        },
        "chInfo": None,
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
        "entities": [],
        "movement_angle": 15,
        "chime_play_volume": 15,
        "chime_play_duration": 0,
    }
    entry.update(overrides)
    return entry


class TestTapoMotionDetectionDigitalSensitivity:
    def test_init_sets_min_max(self):
        entry = make_entry()
        entity = TapoMotionDetectionDigitalSensitivity(entry, MagicMock(), MagicMock())
        assert entity._attr_min_value == 1
        assert entity._attr_max_value == 100
        assert entity._attr_native_min_value == 1
        assert entity._attr_native_max_value == 100
        assert entity._attr_step == 1

    @pytest.mark.asyncio
    async def test_set_value_correct_args(self):
        controller = MagicMock()
        controller.setMotionDetection = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoMotionDetectionDigitalSensitivity(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(75)
        controller.setMotionDetection.assert_called_once_with(None, 75, None)

    @pytest.mark.asyncio
    async def test_set_value_with_chn_id(self):
        controller = MagicMock()
        controller.setMotionDetection = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoMotionDetectionDigitalSensitivity(entry, MagicMock(), MagicMock(), "Lens2", 2)
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(75)
        controller.setMotionDetection.assert_called_once_with(None, 75, [2])

    def test_updateTapo(self):
        entry = make_entry()
        entity = TapoMotionDetectionDigitalSensitivity(entry, MagicMock(), MagicMock())
        entity.updateTapo({"motion_detection_digital_sensitivity": 75})
        assert entity._attr_state == 75

    def test_updateTapo_dict_value(self):
        entry = make_entry()
        entity = TapoMotionDetectionDigitalSensitivity(entry, MagicMock(), MagicMock(), chn_id=1)
        entity.updateTapo({"motion_detection_digital_sensitivity": {"1": 75}})
        assert entity._attr_state == 75

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        entity = TapoMotionDetectionDigitalSensitivity(entry, MagicMock(), MagicMock())
        entity.updateTapo(None)
        assert entity._attr_state == STATE_UNAVAILABLE


class TestTapoMicrophoneVolume:
    @pytest.mark.asyncio
    async def test_set_value_correct_args(self):
        controller = MagicMock()
        controller.setMicrophone = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoMicrophoneVolume(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(75)
        controller.setMicrophone.assert_called_once_with(75)

    def test_updateTapo(self):
        entry = make_entry()
        entity = TapoMicrophoneVolume(entry, MagicMock(), MagicMock())
        entity.updateTapo({"microphoneVolume": 75})
        assert entity._attr_state == 75

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        entity = TapoMicrophoneVolume(entry, MagicMock(), MagicMock())
        entity.updateTapo(None)
        assert entity._attr_state == STATE_UNAVAILABLE


class TestTapoSpeakerVolume:
    @pytest.mark.asyncio
    async def test_set_value_correct_args(self):
        controller = MagicMock()
        controller.setSpeakerVolume = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoSpeakerVolume(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(75)
        controller.setSpeakerVolume.assert_called_once_with(75)

    def test_updateTapo(self):
        entry = make_entry()
        entity = TapoSpeakerVolume(entry, MagicMock(), MagicMock())
        entity.updateTapo({"speakerVolume": 75})
        assert entity._attr_state == 75


class TestTapoSirenVolume:
    @pytest.mark.asyncio
    async def test_set_value_hub(self):
        controller = MagicMock()
        controller.setHubSirenConfig = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entry["camData"]["alarm_is_hubSiren"] = True
        entity = TapoSirenVolume(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(5)
        controller.setHubSirenConfig.assert_called_once_with(None, None, "5")

    @pytest.mark.asyncio
    async def test_set_value_non_hub_low(self):
        controller = MagicMock()
        controller.setAlarm = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entry["camData"]["alarm_is_hubSiren"] = False
        entity = TapoSirenVolume(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity.alarm_enabled = True
        entity.alarm_mode = "light,sound"
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(1)
        controller.setAlarm.assert_called_once_with(True, "sound" in "light,sound", "siren" in "light,sound" or "light" in "light,sound", "low")

    @pytest.mark.asyncio
    async def test_set_value_non_hub_normal(self):
        controller = MagicMock()
        controller.setAlarm = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entry["camData"]["alarm_is_hubSiren"] = False
        entity = TapoSirenVolume(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        entity.alarm_enabled = True
        entity.alarm_mode = "light"
        await entity.async_set_native_value(5)
        args, _ = controller.setAlarm.call_args
        assert args[3] == "normal"

    @pytest.mark.asyncio
    async def test_set_value_non_hub_high(self):
        controller = MagicMock()
        controller.setAlarm = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entry["camData"]["alarm_is_hubSiren"] = False
        entity = TapoSirenVolume(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        entity.alarm_enabled = True
        entity.alarm_mode = "light"
        await entity.async_set_native_value(10)
        args, _ = controller.setAlarm.call_args
        assert args[3] == "high"

    @pytest.mark.asyncio
    async def test_set_value_getAlarmConfig(self):
        controller = MagicMock()
        controller.executeFunction = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entry["camData"]["alarm_is_hubSiren"] = False
        entry["camData"]["alarm_config"]["typeOfAlarm"] = "getAlarmConfig"
        entity = TapoSirenVolume(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(5)
        controller.executeFunction.assert_called_once_with(
            "setAlarmConfig",
            {"msg_alarm": {"siren_volume": "normal"}},
        )

    def _alarm_with_volume(self, vol):
        return {"alarm_config": {"siren_volume": vol, "automatic": "off", "mode": "light"}}

    def test_updateTapo_numeric(self):
        entry = make_entry()
        entity = TapoSirenVolume(entry, MagicMock(), MagicMock())
        entity.updateTapo(self._alarm_with_volume(7))
        assert entity._attr_state == 7

    def test_updateTapo_low_str(self):
        entry = make_entry()
        entity = TapoSirenVolume(entry, MagicMock(), MagicMock())
        entity.updateTapo(self._alarm_with_volume("low"))
        assert entity._attr_state == 1

    def test_updateTapo_normal_str(self):
        entry = make_entry()
        entity = TapoSirenVolume(entry, MagicMock(), MagicMock())
        entity.updateTapo(self._alarm_with_volume("normal"))
        assert entity._attr_state == 5

    def test_updateTapo_high_str(self):
        entry = make_entry()
        entity = TapoSirenVolume(entry, MagicMock(), MagicMock())
        entity.updateTapo(self._alarm_with_volume("high"))
        assert entity._attr_state == 10


class TestTapoSirenDuration:
    @pytest.mark.asyncio
    async def test_set_value_hub(self):
        controller = MagicMock()
        controller.setHubSirenConfig = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entry["camData"]["alarm_is_hubSiren"] = True
        entity = TapoSirenDuration(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(60)
        controller.setHubSirenConfig.assert_called_once_with(60)

    @pytest.mark.asyncio
    async def test_set_value_getAlarm(self):
        controller = MagicMock()
        controller.setAlarm = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entry["camData"]["alarm_is_hubSiren"] = False
        entity = TapoSirenDuration(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        entity.alarm_enabled = True
        entity.alarm_mode = "light"
        await entity.async_set_native_value(60)
        controller.setAlarm.assert_called_once()
        args = controller.setAlarm.call_args[0]
        assert args[4] == 60

    @pytest.mark.asyncio
    async def test_set_value_getAlarmConfig(self):
        controller = MagicMock()
        controller.executeFunction = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entry["camData"]["alarm_is_hubSiren"] = False
        entry["camData"]["alarm_config"]["typeOfAlarm"] = "getAlarmConfig"
        entity = TapoSirenDuration(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(60)
        controller.executeFunction.assert_called_once_with(
            "setAlarmConfig",
            {"msg_alarm": {"siren_duration": 60}},
        )

    def test_hub_max_duration(self):
        entry = make_entry()
        entry["camData"]["alarm_is_hubSiren"] = True
        entity = TapoSirenDuration(entry, MagicMock(), MagicMock())
        assert entity._attr_native_max_value == 599

    def test_non_hub_max_duration(self):
        entry = make_entry()
        entry["camData"]["alarm_is_hubSiren"] = False
        entity = TapoSirenDuration(entry, MagicMock(), MagicMock())
        assert entity._attr_native_max_value == 300


class TestTapoFloodlightBrightness:
    @pytest.mark.asyncio
    async def test_set_value_correct_args(self):
        controller = MagicMock()
        controller.setFloodlightConfig = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoFloodlightBrightness(entry, MagicMock(), MagicMock(), 1, 255)
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(128)
        controller.setFloodlightConfig.assert_called_once_with(None, None, None, None, 128)

    def test_updateTapo(self):
        entry = make_entry()
        entity = TapoFloodlightBrightness(entry, MagicMock(), MagicMock(), 1, 255)
        entity.updateTapo({"flood_light_config": {"intensity_level": 200}})
        assert entity._attr_state == 200


class TestTapoSpotlightIntensity:
    @pytest.mark.asyncio
    async def test_set_value_correct_args(self):
        controller = MagicMock()
        controller.setWhitelampConfig = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoSpotlightIntensity(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(3)
        controller.setWhitelampConfig.assert_called_once_with(False, 3, None)

    def test_updateTapo(self):
        entry = make_entry()
        entity = TapoSpotlightIntensity(entry, MagicMock(), MagicMock())
        entity.updateTapo({"whitelampConfigIntensity": "5"})
        assert entity._attr_state == "5"

    def test_updateTapo_dict(self):
        entry = make_entry()
        entity = TapoSpotlightIntensity(entry, MagicMock(), MagicMock(), chn_id=1)
        entity.updateTapo({"whitelampConfigIntensity": {"1": "4"}})
        assert entity._attr_state == "4"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        entity = TapoSpotlightIntensity(entry, MagicMock(), MagicMock())
        entity.updateTapo(None)
        assert entity._attr_state == STATE_UNAVAILABLE


class TestTapoChimeDuration:
    @pytest.mark.asyncio
    async def test_set_value_below_5_makes_zero(self):
        controller = MagicMock()
        controller.setChimeAlarmConfigure = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoChimeDuration(entry, MagicMock(), MagicMock(), "mac1")
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(3)
        controller.setChimeAlarmConfigure.assert_called_once_with("mac1", None, None, None, 0)

    @pytest.mark.asyncio
    async def test_set_value_above_5(self):
        controller = MagicMock()
        controller.setChimeAlarmConfigure = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoChimeDuration(entry, MagicMock(), MagicMock(), "mac1")
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(10)
        controller.setChimeAlarmConfigure.assert_called_once_with("mac1", None, None, None, 10)

    def test_updateTapo(self):
        entry = make_entry()
        entity = TapoChimeDuration(entry, MagicMock(), MagicMock(), "mac1")
        entity.updateTapo({
            "chimeAlarmConfigurations": {"mac1": {"duration": 10, "volume": 5, "type": "type1"}}
        })
        assert entity._attr_state == 10


class TestTapoChimeVolume:
    @pytest.mark.asyncio
    async def test_set_value_correct_args(self):
        controller = MagicMock()
        controller.setChimeAlarmConfigure = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoChimeVolume(entry, MagicMock(), MagicMock(), "mac1")
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_set_native_value(8)
        controller.setChimeAlarmConfigure.assert_called_once_with("mac1", None, None, 8)

    def test_updateTapo(self):
        entry = make_entry()
        entity = TapoChimeVolume(entry, MagicMock(), MagicMock(), "mac1")
        entity.updateTapo({
            "chimeAlarmConfigurations": {"mac1": {"volume": 8, "duration": 5, "type": "type1"}}
        })
        assert entity._attr_state == 8
