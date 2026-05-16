import pytest
from unittest.mock import MagicMock, AsyncMock
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tapo_control.light import (
    TapoWhitelight,
    TapoFloodlightModern,
    TapoFloodlight,
)
from custom_components.tapo_control.const import LOGGER


def _run_job(fn, *args, **kwargs):
    return fn(*args, **kwargs)


def _setup_entity(entity, hass=None):
    if hass is None:
        hass = MagicMock()
    entity.hass = hass
    entity.entity_id = "light.test"
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
        "whitelampStatus": "1",
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
    }
    entry.update(overrides)
    return entry


class TestTapoWhitelight:
    @pytest.mark.asyncio
    async def test_turn_on_whitelamp_off_does_nothing(self):
        controller = MagicMock()
        controller.reverseWhitelampStatus = MagicMock(return_value={"error_code": 0})
        data = {"whitelampStatus": "0", "basic_info": {"mac": "aa:bb:cc:dd:ee:ff", "device_alias": "TestCamera", "device_model": "C200"}}
        entry = make_entry(controller=controller, camData=data)
        entity = TapoWhitelight(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_turn_on()
        controller.reverseWhitelampStatus.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_on_whitelamp_on_skips(self):
        controller = MagicMock()
        controller.reverseWhitelampStatus = MagicMock(return_value={"error_code": 0})
        data = {"whitelampStatus": "1", "basic_info": {"mac": "aa:bb:cc:dd:ee:ff", "device_alias": "TestCamera", "device_model": "C200"}}
        entry = make_entry(controller=controller, camData=data)
        entity = TapoWhitelight(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_turn_on()
        controller.reverseWhitelampStatus.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_off_whitelamp_on_calls_reverse(self):
        controller = MagicMock()
        controller.reverseWhitelampStatus = MagicMock(return_value={"error_code": 0})
        data = {"whitelampStatus": "1", "basic_info": {"mac": "aa:bb:cc:dd:ee:ff", "device_alias": "TestCamera", "device_model": "C200"}}
        entry = make_entry(controller=controller, camData=data)
        entity = TapoWhitelight(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_turn_off()
        controller.reverseWhitelampStatus.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off_whitelamp_off_skips(self):
        controller = MagicMock()
        controller.reverseWhitelampStatus = MagicMock(return_value={"error_code": 0})
        data = {"whitelampStatus": "0", "basic_info": {"mac": "aa:bb:cc:dd:ee:ff", "device_alias": "TestCamera", "device_model": "C200"}}
        entry = make_entry(controller=controller, camData=data)
        entity = TapoWhitelight(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_turn_off()
        controller.reverseWhitelampStatus.assert_not_called()

    def test_updateTapo_on(self):
        entry = make_entry()
        entity = TapoWhitelight(entry, MagicMock(), MagicMock())
        entity.updateTapo({"whitelampStatus": "1"})
        assert entity._attr_state == "on"

    def test_updateTapo_off(self):
        entry = make_entry()
        entity = TapoWhitelight(entry, MagicMock(), MagicMock())
        entity.updateTapo({"whitelampStatus": "0"})
        assert entity._attr_state == "off"

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        entity = TapoWhitelight(entry, MagicMock(), MagicMock())
        entity.updateTapo(None)
        assert entity._attr_state == STATE_UNAVAILABLE


class TestTapoFloodlightModern:
    @pytest.mark.asyncio
    async def test_turn_on_brightness_change(self):
        controller = MagicMock()
        controller.setFloodlightConfig = MagicMock(return_value={"error_code": 0})
        controller.manualFloodlightOp = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoFloodlightModern(entry, MagicMock(), MagicMock(), 1, 255)
        _setup_entity(entity)
        entity._attr_state = "off"
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        from homeassistant.components.light import ATTR_BRIGHTNESS
        await entity.async_turn_on(**{ATTR_BRIGHTNESS: 255})
        controller.setFloodlightConfig.assert_called_once_with(None, None, None, None, 255)

    @pytest.mark.asyncio
    async def test_turn_on_already_on_skips_second_call(self):
        controller = MagicMock()
        controller.setFloodlightConfig = MagicMock(return_value={"error_code": 0})
        controller.manualFloodlightOp = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoFloodlightModern(entry, MagicMock(), MagicMock(), 1, 255)
        _setup_entity(entity)
        entity._attr_state = "on"
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_turn_on()
        controller.manualFloodlightOp.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_off_skips_if_already_off(self):
        controller = MagicMock()
        controller.manualFloodlightOp = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoFloodlightModern(entry, MagicMock(), MagicMock(), 1, 255)
        _setup_entity(entity)
        entity._attr_state = "off"
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_turn_off()
        controller.manualFloodlightOp.assert_not_called()

    def test_scale_brightness_validates_range(self):
        entry = make_entry()
        entity = TapoFloodlightModern(entry, MagicMock(), MagicMock(), 1, 255)
        with pytest.raises(ValueError, match="Value must be between 1 and 255"):
            entity.scaleBrightnessValue(0)

    def test_scale_brightness_out_of_range_high(self):
        entry = make_entry()
        entity = TapoFloodlightModern(entry, MagicMock(), MagicMock(), 1, 255)
        with pytest.raises(ValueError, match="Value must be between 1 and 255"):
            entity.scaleBrightnessValue(256)

    def test_updateTapo_on(self):
        entry = make_entry()
        entity = TapoFloodlightModern(entry, MagicMock(), MagicMock(), 1, 255)
        entity.updateTapo({"flood_light_config": {"intensity_level": 128}, "flood_light_status": "1"})
        assert entity._attr_state == "on"

    def test_updateTapo_off(self):
        entry = make_entry()
        entity = TapoFloodlightModern(entry, MagicMock(), MagicMock(), 1, 255)
        entity.updateTapo({"flood_light_config": {"intensity_level": 128}, "flood_light_status": "0"})
        assert entity._attr_state == "off"


class TestTapoFloodlight:
    @pytest.mark.asyncio
    async def test_turn_on_correct_args(self):
        controller = MagicMock()
        controller.setForceWhitelampState = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoFloodlight(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_turn_on()
        controller.setForceWhitelampState.assert_called_once_with(True, None)

    @pytest.mark.asyncio
    async def test_turn_off_correct_args(self):
        controller = MagicMock()
        controller.setForceWhitelampState = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoFloodlight(entry, MagicMock(), MagicMock())
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_turn_off()
        controller.setForceWhitelampState.assert_called_once_with(False, None)

    @pytest.mark.asyncio
    async def test_turn_on_with_chn_id(self):
        controller = MagicMock()
        controller.setForceWhitelampState = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entity = TapoFloodlight(entry, MagicMock(), MagicMock(), "Lens2", 2)
        _setup_entity(entity)
        entity._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await entity.async_turn_on()
        controller.setForceWhitelampState.assert_called_once_with(True, [2])

    def test_updateTapo(self):
        entry = make_entry()
        entity = TapoFloodlight(entry, MagicMock(), MagicMock())
        entity.updateTapo({"force_white_lamp_state": "on"})
        assert entity._attr_state == "on"

    def test_updateTapo_off(self):
        entry = make_entry()
        entity = TapoFloodlight(entry, MagicMock(), MagicMock())
        entity.updateTapo({"force_white_lamp_state": "off"})
        assert entity._attr_state == "off"

    def test_updateTapo_dict(self):
        entry = make_entry()
        entity = TapoFloodlight(entry, MagicMock(), MagicMock(), chn_id=1)
        entity.updateTapo({"force_white_lamp_state": {"1": "on"}})
        assert entity._attr_state == "on"
