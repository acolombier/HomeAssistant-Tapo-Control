import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.tapo_control.siren import TapoSiren, TapoSirenEntity
from custom_components.tapo_control.utils import result_has_error


def _run_job(fn, *args, **kwargs):
    return fn(*args, **kwargs)


def make_entry(controller=None, camData=None, **overrides):
    ctrl = controller or MagicMock()
    data = camData or {
        "basic_info": {
            "mac": "aa:bb:cc:dd:ee:ff",
            "device_alias": "TestCamera",
            "device_model": "C200",
        },
        "alarm_config": {"siren_type": "test_type"},
        "alarm_status": "off",
        "alarm_is_hubSiren": False,
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


class TestTapoSiren:
    @pytest.mark.asyncio
    async def test_turn_on_hub(self):
        controller = MagicMock()
        controller.setHubSirenStatus = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entry["camData"]["alarm_is_hubSiren"] = True
        siren = TapoSiren(entry, MagicMock(), MagicMock())
        siren.hass = MagicMock()
        siren.entity_id = "siren.test"
        siren.async_write_ha_state = MagicMock()
        siren.hass.async_create_task = MagicMock()
        siren._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await siren.async_turn_on()
        controller.setHubSirenStatus.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_turn_on_hub_with_duration(self):
        controller = MagicMock()
        controller.setHubSirenStatus = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entry["camData"]["alarm_is_hubSiren"] = True
        siren = TapoSiren(entry, MagicMock(), MagicMock())
        siren.hass = MagicMock()
        siren.entity_id = "siren.test"
        siren.async_write_ha_state = MagicMock()
        siren.hass.async_create_task = MagicMock()
        siren._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await siren.async_turn_on(duration=10)
        controller.setHubSirenStatus.assert_called_once_with(True)
        siren.hass.async_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_on_non_hub_calls_both(self):
        controller = MagicMock()
        controller.startManualAlarm = MagicMock(return_value={"error_code": 0})
        controller.setSirenStatus = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        siren = TapoSiren(entry, MagicMock(), MagicMock())
        siren.hass = MagicMock()
        siren.entity_id = "siren.test"
        siren.async_write_ha_state = MagicMock()
        siren.hass.async_create_task = MagicMock()
        siren._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await siren.async_turn_on()
        controller.startManualAlarm.assert_called_once()
        controller.setSirenStatus.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_turn_on_non_hub_both_fail_raises(self):
        controller = MagicMock()
        controller.startManualAlarm = MagicMock(side_effect=Exception("fail"))
        controller.setSirenStatus = MagicMock(side_effect=Exception("fail"))
        entry = make_entry(controller=controller)
        siren = TapoSiren(entry, MagicMock(), MagicMock())
        siren.entity_id = "siren.test"
        siren.async_write_ha_state = MagicMock()
        siren._hass.async_add_executor_job = AsyncMock(side_effect=[
            Exception("fail"),
            Exception("fail"),
        ])
        with pytest.raises(Exception, match="Camera does not support triggering the siren"):
            await siren.async_turn_on()

    @pytest.mark.asyncio
    async def test_turn_on_sets_is_on(self):
        controller = MagicMock()
        controller.startManualAlarm = MagicMock(return_value={"error_code": 0})
        controller.setSirenStatus = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        siren = TapoSiren(entry, MagicMock(), MagicMock())
        siren.hass = MagicMock()
        siren.entity_id = "siren.test"
        siren.async_write_ha_state = MagicMock()
        siren.hass.async_create_task = MagicMock()
        siren._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await siren.async_turn_on()
        assert siren._attr_is_on is True

    @pytest.mark.asyncio
    async def test_turn_off_hub(self):
        controller = MagicMock()
        controller.setHubSirenStatus = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        entry["camData"]["alarm_is_hubSiren"] = True
        siren = TapoSiren(entry, MagicMock(), MagicMock())
        siren.hass = MagicMock()
        siren.entity_id = "siren.test"
        siren.async_write_ha_state = MagicMock()
        siren._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await siren.async_turn_off()
        controller.setHubSirenStatus.assert_called_once_with(False)

    @pytest.mark.asyncio
    async def test_turn_off_non_hub(self):
        controller = MagicMock()
        controller.stopManualAlarm = MagicMock(return_value={"error_code": 0})
        controller.setSirenStatus = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        siren = TapoSiren(entry, MagicMock(), MagicMock())
        siren.hass = MagicMock()
        siren.entity_id = "siren.test"
        siren.async_write_ha_state = MagicMock()
        siren._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await siren.async_turn_off()
        controller.stopManualAlarm.assert_called_once()
        controller.setSirenStatus.assert_called_once_with(False)

    @pytest.mark.asyncio
    async def test_turn_off_non_hub_both_fail_raises(self):
        controller = MagicMock()
        controller.stopManualAlarm = MagicMock(side_effect=Exception("fail"))
        controller.setSirenStatus = MagicMock(side_effect=Exception("fail"))
        entry = make_entry(controller=controller)
        siren = TapoSiren(entry, MagicMock(), MagicMock())
        siren.entity_id = "siren.test"
        siren.async_write_ha_state = MagicMock()
        siren._hass.async_add_executor_job = AsyncMock(side_effect=[
            Exception("fail"),
            Exception("fail"),
        ])
        with pytest.raises(Exception, match="Camera does not support triggering the siren"):
            await siren.async_turn_off()

    @pytest.mark.asyncio
    async def test_turn_off_sets_is_on_false(self):
        controller = MagicMock()
        controller.stopManualAlarm = MagicMock(return_value={"error_code": 0})
        controller.setSirenStatus = MagicMock(return_value={"error_code": 0})
        entry = make_entry(controller=controller)
        siren = TapoSiren(entry, MagicMock(), MagicMock())
        siren.hass = MagicMock()
        siren.entity_id = "siren.test"
        siren.async_write_ha_state = MagicMock()
        siren._hass.async_add_executor_job = AsyncMock(side_effect=_run_job)
        await siren.async_turn_off()
        assert siren._attr_is_on is False

    def test_updateTapo_on(self):
        entry = make_entry()
        siren = TapoSiren(entry, MagicMock(), MagicMock())
        siren.updateTapo({"alarm_status": "on"})
        assert siren._is_on is True

    def test_updateTapo_off(self):
        entry = make_entry()
        siren = TapoSiren(entry, MagicMock(), MagicMock())
        siren.updateTapo({"alarm_status": "off"})
        assert siren._is_on is False

    def test_updateTapo_unavailable(self):
        entry = make_entry()
        siren = TapoSiren(entry, MagicMock(), MagicMock())
        siren.updateTapo(None)
        assert siren._is_on is False
