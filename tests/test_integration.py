import json
import pytest
from unittest.mock import MagicMock, AsyncMock
from copy import deepcopy

from homeassistant.const import STATE_UNAVAILABLE

from custom_components.tapo_control.switch import (
    TapoPrivacySwitch,
    TapoIndicatorLedSwitch,
    TapoAutoTrackSwitch,
    TapoNotificationsSwitch,
    TapoRichNotificationsSwitch,
    TapoAutoUpgradeSwitch,
    TapoRecordingPlanSwitch,
    TapoFlipSwitch,
    TapoLensDistortionCorrectionSwitch,
    TapoMicrophoneMuteSwitch,
    TapoMicrophoneNoiseCancellationSwitch,
)
from custom_components.tapo_control.select import (
    TapoMotionDetectionSelect,
    TapoPersonDetectionSelect,
    TapoLightFrequencySelect,
)
from custom_components.tapo_control.sensor import (
    TapoBatterySensor,
    TapoRSSISensor,
    TapoSSIDSensor,
    TapoLinkTypeSensor,
    TapoHDDSensor,
)
from custom_components.tapo_control.number import (
    TapoMicrophoneVolume,
    TapoSpeakerVolume,
)
from custom_components.tapo_control.button import (
    TapoRebootButton,
)
from custom_components.tapo_control.update import TapoCamUpdate

REAL_CAM_DATA_PATH = "/workspaces/tapo/processed_camData.json"


def load_real_data():
    with open(REAL_CAM_DATA_PATH) as f:
        return json.load(f)


def make_entry(camData):
    coord = MagicMock()
    coord.async_request_refresh = AsyncMock()
    return {
        "controller": MagicMock(),
        "coordinator": coord,
        "camData": camData,
        "name": camData["basic_info"]["device_alias"],
        "isChild": False,
        "isParent": True,
        "entities": [],
        "childDevices": [],
        "allControllers": [MagicMock()],
        "uuid": "test-uuid",
        "timezoneOffset": 0,
        "refreshEnabled": True,
        "onvifManagement": None,
        "enable_media_sync": False,
        "movement_angle": 15,
        "chime_play_type": 0,
        "chime_play_volume": 0,
        "chime_play_duration": 0,
    }


class TestEndToEndC410:
    """End-to-end tests using real processed data from a Tapo C410 battery camera."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.camData = load_real_data()

    def _create_entry(self):
        return make_entry(deepcopy(self.camData))

    # --- Switch entities ---

    def test_privacy_off_state_matches_real(self):
        camData = deepcopy(self.camData)
        camData["privacy_mode"] = "off"
        entry = make_entry(camData)
        sw = TapoPrivacySwitch(entry, MagicMock(), MagicMock())
        assert sw._attr_state == "off"

    def test_privacy_on(self):
        camData = deepcopy(self.camData)
        camData["privacy_mode"] = "on"
        entry = make_entry(camData)
        sw = TapoPrivacySwitch(entry, MagicMock(), MagicMock())
        assert sw._attr_state == "on"

    def test_led_on_matches_real(self):
        camData = deepcopy(self.camData)
        camData["led"] = "on"
        entry = make_entry(camData)
        sw = TapoIndicatorLedSwitch(entry, MagicMock(), MagicMock())
        assert sw._attr_state == "on"

    def test_auto_track_defaults_to_off_when_not_supported(self):
        camData = deepcopy(self.camData)
        camData["auto_track"] = None
        entry = make_entry(camData)
        sw = TapoAutoTrackSwitch(entry, MagicMock(), MagicMock())
        assert sw._attr_state == "off"

    def test_notification_on_matches_real(self):
        camData = deepcopy(self.camData)
        camData["notifications"] = "on"
        entry = make_entry(camData)
        sw = TapoNotificationsSwitch(entry, MagicMock(), MagicMock())
        assert sw._attr_state == "on"

    def test_rich_notification_on_matches_real(self):
        camData = deepcopy(self.camData)
        camData["rich_notifications"] = "on"
        entry = make_entry(camData)
        sw = TapoRichNotificationsSwitch(entry, MagicMock(), MagicMock())
        assert sw._attr_state == "on"

    def test_auto_upgrade_matches_real(self):
        camData = deepcopy(self.camData)
        camData["autoUpgradeEnabled"] = "on"
        entry = make_entry(camData)
        sw = TapoAutoUpgradeSwitch(entry, MagicMock(), MagicMock())
        assert sw._attr_state == "on"

    def test_record_plan_enabled_matches_real(self):
        camData = deepcopy(self.camData)
        camData["recordPlan"] = {"enabled": "on"}
        entry = make_entry(camData)
        sw = TapoRecordingPlanSwitch(entry, MagicMock(), MagicMock())
        assert sw._attr_state == "on"

    def test_flip_matches_real(self):
        camData = deepcopy(self.camData)
        camData["flip"] = "on"
        entry = make_entry(camData)
        sw = TapoFlipSwitch(entry, MagicMock(), MagicMock())
        assert sw._attr_state == "on"

    def test_lens_distortion_matches_real(self):
        camData = deepcopy(self.camData)
        camData["lens_distrotion_correction"] = "on"
        entry = make_entry(camData)
        sw = TapoLensDistortionCorrectionSwitch(entry, MagicMock(), MagicMock())
        assert sw._attr_state == "on"

    def test_mic_mute_off_matches_real(self):
        camData = deepcopy(self.camData)
        camData["microphoneMute"] = "off"
        entry = make_entry(camData)
        sw = TapoMicrophoneMuteSwitch(entry, MagicMock(), MagicMock())
        assert sw._attr_state == "off"

    def test_mic_noise_cancelling_on_matches_real(self):
        camData = deepcopy(self.camData)
        camData["microphoneNoiseCancelling"] = "on"
        entry = make_entry(camData)
        sw = TapoMicrophoneNoiseCancellationSwitch(entry, MagicMock(), MagicMock())
        assert sw._attr_state == "on"

    # --- Select entities ---

    def test_motion_detection_off_matches_real(self):
        camData = deepcopy(self.camData)
        camData["motion_detection_enabled"] = {"1": "off"}
        camData["motion_detection_sensitivity"] = {"1": "normal"}
        entry = make_entry(camData)
        sel = TapoMotionDetectionSelect(entry, MagicMock(), MagicMock())
        assert sel._attr_state == "off"

    def test_person_detection_off_matches_real(self):
        camData = deepcopy(self.camData)
        camData["person_detection_enabled"] = {"1": "off"}
        camData["person_detection_sensitivity"] = {"1": "high"}
        entry = make_entry(camData)
        sel = TapoPersonDetectionSelect(entry, MagicMock(), MagicMock())
        assert sel._attr_state == "off"

    def test_light_frequency_matches_real(self):
        camData = deepcopy(self.camData)
        camData["light_frequency_mode"] = "auto"
        entry = make_entry(camData)
        sel = TapoLightFrequencySelect(entry, MagicMock(), MagicMock())
        assert sel._attr_current_option == "auto"

    # --- Sensor entities ---

    def test_battery_low_matches_real(self):
        camData = deepcopy(self.camData)
        camData["battery_level"] = 9
        entry = make_entry(camData)
        sensor = TapoBatterySensor(entry, MagicMock(), MagicMock())
        assert sensor._attr_native_value == 9

    def test_rssi_matches_real(self):
        camData = deepcopy(self.camData)
        camData["rssi"] = -47
        entry = make_entry(camData)
        sensor = TapoRSSISensor(entry, MagicMock(), MagicMock())
        assert sensor._attr_native_value == -47

    def test_ssid_matches_real(self):
        camData = deepcopy(self.camData)
        camData["ssid"] = "WhoDat"
        entry = make_entry(camData)
        sensor = TapoSSIDSensor(entry, MagicMock(), MagicMock())
        assert sensor._attr_native_value == "WhoDat"

    def test_link_type_wifi_matches_real(self):
        camData = deepcopy(self.camData)
        camData["link_type"] = "wifi"
        entry = make_entry(camData)
        sensor = TapoLinkTypeSensor(entry, MagicMock(), MagicMock())
        assert sensor._attr_native_value == "wifi"

    def test_sdcard_offline_matches_real(self):
        camData = deepcopy(self.camData)
        camData["sdCardData"] = [
            {"disk_name": "1", "space": "0B", "status": "offline"}
        ]
        entry = make_entry(camData)
        sensor = TapoHDDSensor(entry, MagicMock(), MagicMock(), "1", "status")
        assert sensor._attr_native_value == "offline"

    # --- Number entities ---

    def test_microphone_volume_matches_real(self):
        camData = deepcopy(self.camData)
        camData["microphoneVolume"] = "52"
        entry = make_entry(camData)
        vol = TapoMicrophoneVolume(entry, MagicMock(), MagicMock())
        assert vol._attr_state == "52"

    def test_speaker_volume_matches_real(self):
        camData = deepcopy(self.camData)
        camData["speakerVolume"] = "100"
        entry = make_entry(camData)
        vol = TapoSpeakerVolume(entry, MagicMock(), MagicMock())
        assert vol._attr_state == "100"

    # --- Button entities ---

    def test_reboot_button_created(self):
        entry = self._create_entry()
        btn = TapoRebootButton(entry, MagicMock(), MagicMock())
        assert btn.name == "Reboot"

    def test_firmware_update_normal_matches_real(self):
        camData = deepcopy(self.camData)
        camData["firmwareUpdateStatus"] = {
            "upgrade_status": {"state": "normal", "lastUpgradingSuccess": True}
        }
        entry = make_entry(camData)
        entry["latestFirmwareVersion"] = None
        update = TapoCamUpdate(entry, MagicMock(), MagicMock())
        assert update.installed_version == "1.2.1 Build 250917 Rel.58378n"
        assert update.latest_version == "1.2.1 Build 250917 Rel.58378n"

    # --- Unavailable state propagation ---

    def test_switch_goes_unavailable_on_null_camData(self):
        entry = self._create_entry()
        sw = TapoPrivacySwitch(entry, MagicMock(), MagicMock())
        sw.updateTapo(None)
        assert sw._attr_state == STATE_UNAVAILABLE

    # --- Async turn_on / turn_off with real data ---

    @pytest.mark.asyncio
    async def test_privacy_turn_on_with_real_data(self):
        camData = deepcopy(self.camData)
        camData["privacy_mode"] = "off"
        ctrl = MagicMock()
        ctrl.setPrivacyMode = MagicMock(return_value={"error_code": 0})
        entry = make_entry(camData)
        entry["controller"] = ctrl
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(
            side_effect=lambda fn, *a, **kw: fn(*a, **kw)
        )
        sw = TapoPrivacySwitch(entry, hass, MagicMock())
        sw.hass = hass
        sw.entity_id = "switch.test_privacy"
        sw.async_write_ha_state = MagicMock()
        await sw.async_turn_on()
        ctrl.setPrivacyMode.assert_called_with(True)
        assert sw._attr_state == "on"

    @pytest.mark.asyncio
    async def test_privacy_turn_off_with_real_data(self):
        camData = deepcopy(self.camData)
        camData["privacy_mode"] = "on"
        ctrl = MagicMock()
        ctrl.setPrivacyMode = MagicMock(return_value={"error_code": 0})
        entry = make_entry(camData)
        entry["controller"] = ctrl
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(
            side_effect=lambda fn, *a, **kw: fn(*a, **kw)
        )
        sw = TapoPrivacySwitch(entry, hass, MagicMock())
        sw.hass = hass
        sw.entity_id = "switch.test_privacy"
        sw.async_write_ha_state = MagicMock()
        await sw.async_turn_off()
        ctrl.setPrivacyMode.assert_called_with(False)
        assert sw._attr_state == "off"
