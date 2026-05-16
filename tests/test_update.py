import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import datetime

from custom_components.tapo_control.update import TapoCamUpdate


def make_entry(controller=None, camData=None, **overrides):
    ctrl = controller or MagicMock()
    data = camData or {
        "basic_info": {
            "mac": "aa:bb:cc:dd:ee:ff",
            "device_alias": "TestCamera",
            "device_model": "C200",
            "sw_version": "1.0.0",
            "hw_version": "1.0",
        },
        "firmwareUpdateStatus": {
            "upgrade_status": {"state": "normal"},
        },
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
        "latestFirmwareVersion": {
            "version": "2.0.0",
            "release_log": "New features",
        },
        "lastFirmwareCheck": 0,
    }
    entry.update(overrides)
    return entry


class TestTapoCamUpdate:
    def test_installed_version(self):
        entry = make_entry()
        update_entity = TapoCamUpdate(entry, MagicMock(), MagicMock())
        assert update_entity.installed_version == "1.0.0"

    def test_latest_version_from_cloud(self):
        entry = make_entry()
        update_entity = TapoCamUpdate(entry, MagicMock(), MagicMock())
        assert update_entity.latest_version == "2.0.0"

    def test_latest_version_fallback(self):
        entry = make_entry(latestFirmwareVersion=None)
        update_entity = TapoCamUpdate(entry, MagicMock(), MagicMock())
        assert update_entity.latest_version == "1.0.0"

    def test_release_summary_from_cloud(self):
        entry = make_entry()
        update_entity = TapoCamUpdate(entry, MagicMock(), MagicMock())
        assert update_entity.release_summary == "New features"

    def test_release_summary_truncated(self):
        entry = make_entry(
            latestFirmwareVersion={
                "version": "2.0.0",
                "release_log": "A" * 300,
            }
        )
        update_entity = TapoCamUpdate(entry, MagicMock(), MagicMock())
        assert len(update_entity.release_summary) <= 258  # 255 + "..."

    def test_release_summary_none(self):
        entry = make_entry(latestFirmwareVersion=None)
        update_entity = TapoCamUpdate(entry, MagicMock(), MagicMock())
        assert update_entity.release_summary is None

    @pytest.mark.asyncio
    async def test_release_notes(self):
        entry = make_entry()
        update_entity = TapoCamUpdate(entry, MagicMock(), MagicMock())
        assert await update_entity.async_release_notes() == "New features"

    @pytest.mark.asyncio
    async def test_release_notes_no_version(self):
        entry = make_entry(latestFirmwareVersion=None)
        update_entity = TapoCamUpdate(entry, MagicMock(), MagicMock())
        assert await update_entity.async_release_notes() == "No update available."

    def test_in_progress_default_false(self):
        entry = make_entry()
        update_entity = TapoCamUpdate(entry, MagicMock(), MagicMock())
        assert not update_entity.in_progress

    @pytest.mark.asyncio
    async def test_async_install_calls_firmware_upgrade(self):
        controller = MagicMock()
        controller.startFirmwareUpgrade = MagicMock()
        entry = make_entry(controller=controller)
        update_entity = TapoCamUpdate(entry, MagicMock(), MagicMock())
        update_entity.hass = MagicMock()
        update_entity.hass.async_add_executor_job = AsyncMock()
        await update_entity.async_install("2.0.0", False)
        update_entity.hass.async_add_executor_job.assert_called_once_with(
            controller.startFirmwareUpgrade
        )

    @pytest.mark.asyncio
    async def test_async_install_sets_in_progress(self):
        entry = make_entry()
        update_entity = TapoCamUpdate(entry, MagicMock(), MagicMock())
        update_entity.hass = MagicMock()
        update_entity.hass.async_add_executor_job = AsyncMock()
        await update_entity.async_install("2.0.0", False)
        assert update_entity._in_progress

    @pytest.mark.asyncio
    async def test_async_install_error_logged(self):
        controller = MagicMock()
        controller.startFirmwareUpgrade = MagicMock(side_effect=Exception("Upgrade failed"))
        entry = make_entry(controller=controller)
        update_entity = TapoCamUpdate(entry, MagicMock(), MagicMock())
        update_entity.hass = MagicMock()
        update_entity.hass.async_add_executor_job = AsyncMock(side_effect=Exception("Upgrade failed"))
        await update_entity.async_install("2.0.0", False)
        assert not update_entity._in_progress

    def test_updateTapo_firmware_complete_sets_in_progress_false(self):
        entry = make_entry()
        update_entity = TapoCamUpdate(entry, MagicMock(), MagicMock())
        update_entity._in_progress = True
        update_entity._installRequestedTime = 100
        update_entity._lastDataUpdate = 0
        device_registry = MagicMock()
        device_registry.async_get_device = MagicMock(return_value=MagicMock())
        device_registry.async_update_device = MagicMock()
        with patch("custom_components.tapo_control.update.dr.async_get", return_value=device_registry):
            update_entity.updateTapo({
                "basic_info": {
                    "mac": "aa:bb:cc:dd:ee:ff",
                    "device_alias": "TestCamera",
                    "device_model": "C200",
                    "sw_version": "2.0.0",
                    "hw_version": "1.0",
                },
                "firmwareUpdateStatus": {
                    "upgrade_status": {"state": "normal"},
                },
                "updated": 1001,
            })
        assert not update_entity._in_progress
