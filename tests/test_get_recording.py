import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from homeassistant.components.media_source.error import Unresolvable


@pytest.fixture(autouse=True)
def auto_patches():
    with (
        patch("custom_components.tapo_control.utils.getColdDirPathForEntry", return_value="/mock/cold/dir"),
        patch("custom_components.tapo_control.utils.getColdFile", return_value="/mock/cold/dir/videos/123-456.mp4"),
        patch("custom_components.tapo_control.utils.getFileName", return_value="123-456"),
        patch("custom_components.tapo_control.utils.processDownload", new=AsyncMock()),
        patch("custom_components.tapo_control.utils.Downloader") as mock_downloader_cls,
    ):
        mock_downloader = MagicMock()
        mock_downloader.downloadFile = AsyncMock(return_value={"currentAction": "Completed", "progress": 100, "total": 100})
        mock_downloader_cls.return_value = mock_downloader
        yield {"downloader": mock_downloader, "downloader_cls": mock_downloader_cls}


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.data = {"tapo_control": {}}
    hass.bus = MagicMock()
    hass.bus.fire = MagicMock()
    hass.async_add_executor_job = AsyncMock(side_effect=lambda fn, *a, **kw: fn(*a, **kw))
    return hass


@pytest.fixture
def mock_tapo():
    tapo = MagicMock()
    tapo.getTimeCorrection = MagicMock(return_value=0)
    tapo.getRecordings = MagicMock(return_value=["rec1", "rec2"])
    return tapo


@pytest.fixture
def entry_data():
    return {
        "isChild": False,
        "camData": {
            "basic_info": {
                "mac": "aa:bb:cc:dd:ee:ff",
                "dev_id": "test-dev-id",
            },
        },
        "isDownloadingStream": False,
        "downloadedStreams": {},
        "mediaScanResult": {},
        "downloadProgress": None,
    }


from custom_components.tapo_control.utils import getRecording


@pytest.mark.asyncio
class TestGetRecording:
    async def test_cold_file_exists_returns_path(
        self, mock_hass, mock_tapo, entry_data, auto_patches, monkeypatch
    ):
        monkeypatch.setattr("custom_components.tapo_control.utils.os.path.exists", lambda p: True)

        result = await getRecording(
            mock_hass, mock_tapo, "entry1", entry_data,
            "2026-05-16", 123, 456, False, False,
        )
        assert result == "/mock/cold/dir/videos/123-456.mp4"
        mock_tapo.getRecordings.assert_not_called()

        from custom_components.tapo_control.utils import processDownload
        processDownload.assert_awaited_once_with(
            mock_hass, "entry1", entry_data, 123, 456
        )
        mock_hass.bus.fire.assert_not_called()

    async def test_cold_file_missing_downloads_file(
        self, mock_hass, mock_tapo, entry_data, auto_patches, monkeypatch
    ):
        monkeypatch.setattr("custom_components.tapo_control.utils.os.path.exists", lambda p: False)

        result = await getRecording(
            mock_hass, mock_tapo, "entry1", entry_data,
            "2026-05-16", 123, 456, False, False,
        )
        assert result == "/mock/cold/dir/videos/123-456.mp4"
        mock_tapo.getRecordings.assert_called_once_with("2026-05-16")
        assert entry_data["isDownloadingStream"] is False
        mock_hass.bus.fire.assert_called_once_with(
            "tapo_control_media_downloaded",
            {
                "entry_id": "entry1",
                "startDate": 123,
                "endDate": 456,
                "filePath": "/mock/cold/dir/videos/123-456.mp4",
            },
        )

        from custom_components.tapo_control.utils import processDownload
        processDownload.assert_awaited_once_with(
            mock_hass, "entry1", entry_data, 123, 456
        )

    async def test_download_in_progress_raises_unresolvable(
        self, mock_hass, mock_tapo, entry_data, auto_patches, monkeypatch
    ):
        monkeypatch.setattr("custom_components.tapo_control.utils.os.path.exists", lambda p: False)

        auto_patches["downloader"].downloadFile = AsyncMock(
            return_value={"currentAction": "Recording in progress", "progress": 0, "total": 0}
        )

        with pytest.raises(Unresolvable, match="Recording is currently in progress."):
            await getRecording(
                mock_hass, mock_tapo, "entry1", entry_data,
                "2026-05-16", 123, 456, False, False,
            )

    async def test_download_isDownloadingStream_reset_on_exception(
        self, mock_hass, mock_tapo, entry_data, auto_patches, monkeypatch
    ):
        monkeypatch.setattr("custom_components.tapo_control.utils.os.path.exists", lambda p: False)

        auto_patches["downloader"].downloadFile = AsyncMock(side_effect=Exception("Download failed"))

        with pytest.raises(Exception, match="Download failed"):
            await getRecording(
                mock_hass, mock_tapo, "entry1", entry_data,
                "2026-05-16", 123, 456, False, False,
            )

    async def test_child_device_sets_child_id(
        self, mock_hass, mock_tapo, auto_patches, monkeypatch
    ):
        monkeypatch.setattr("custom_components.tapo_control.utils.os.path.exists", lambda p: False)

        entry_data = {
            "isChild": True,
            "camData": {
                "basic_info": {
                    "mac": "aa:bb:cc:dd:ee:ff",
                    "dev_id": "child-dev-id-123",
                },
            },
            "isDownloadingStream": False,
            "downloadedStreams": {},
            "mediaScanResult": {},
            "downloadProgress": None,
        }

        result = await getRecording(
            mock_hass, mock_tapo, "entry1", entry_data,
            "2026-05-16", 123, 456, False, False,
        )
        assert result is not None
        mock_tapo.getRecordings.assert_called_once()

    async def test_time_correction_called(
        self, mock_hass, mock_tapo, entry_data, auto_patches, monkeypatch
    ):
        monkeypatch.setattr("custom_components.tapo_control.utils.os.path.exists", lambda p: True)

        await getRecording(
            mock_hass, mock_tapo, "entry1", entry_data,
            "2026-05-16", 123, 456, False, False,
        )
        mock_tapo.getTimeCorrection.assert_called_once()

    async def test_start_end_date_are_ints(
        self, mock_hass, mock_tapo, entry_data, auto_patches, monkeypatch
    ):
        monkeypatch.setattr("custom_components.tapo_control.utils.os.path.exists", lambda p: True)

        result = await getRecording(
            mock_hass, mock_tapo, "entry1", entry_data,
            "2026-05-16", "123", "456", False, False,
        )
        assert result == "/mock/cold/dir/videos/123-456.mp4"
