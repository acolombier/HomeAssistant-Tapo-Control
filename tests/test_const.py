import importlib
import sys


def _get_const():
    """Lazy-import const module to avoid triggering full import chain at collection time."""
    # Ensure we can find custom_components
    sys.path.insert(0, "/workspaces/tapo/HomeAssistant-Tapo-Control/custom_components")
    from tapo_control import const
    return const


def test_domain():
    const = _get_const()
    assert const.DOMAIN == "tapo_control"


def test_brand():
    const = _get_const()
    assert const.BRAND == "TP-Link"


def test_pytapo_required_version():
    const = _get_const()
    assert const.PYTAPO_REQUIRED_VERSION == "3.4.11"


def test_doorbell_udp_port():
    const = _get_const()
    assert const.DOORBELL_UDP_PORT == 20005


def test_default_scan_interval():
    const = _get_const()
    assert const.DEFAULT_SCAN_INTERVAL == 10


def test_update_intervals():
    const = _get_const()
    assert const.UPDATE_INTERVAL_MAIN_DEFAULT == 30
    assert const.UPDATE_INTERVAL_BATTERY_DEFAULT == 600


def test_time_sync_defaults():
    const = _get_const()
    assert const.TIME_SYNC_DST_DEFAULT == 1
    assert const.TIME_SYNC_NDST_DEFAULT == 0


def test_time_sync_period():
    const = _get_const()
    assert const.TIME_SYNC_PERIOD == 3600


def test_media_constants():
    const = _get_const()
    assert const.MEDIA_CLEANUP_PERIOD == 600
    assert const.UPDATE_CHECK_PERIOD == 86400
    assert const.COLD_DIR_DELETE_TIME == 86400
    assert const.HOT_DIR_DELETE_TIME == 3600


def test_toggle_states():
    const = _get_const()
    assert const.TOGGLE_STATES == ["on", "off"]


def test_rtsp_transport_protocols():
    const = _get_const()
    assert const.RTSP_TRANS_PROTOCOLS == ["tcp", "udp", "udp_multicast", "http"]


def test_tapo_prefixes():
    const = _get_const()
    expected = (
        r"^c[0-9]{3}[a-zA-Z]*_.*",
        r"^d[0-9]{3}[a-zA-Z]*_.*",
        r"^tc[0-9]{2,3}[a-zA-Z]*_.*",
        r"^d[0-9]{3}[a-zA-Z]*c_.*",
        r"^h[0-9]{3}[a-zA-Z]*_.*",
    )
    assert const.TAPO_PREFIXES == expected


def test_misc_constants():
    const = _get_const()
    assert const.ENABLE_MOTION_SENSOR == "enable_motion_sensor"
    assert const.ENABLE_MEDIA_SYNC == "enable_media_sync"
    assert const.ENABLE_STREAM == "enable_stream"
    assert const.ENABLE_WEBHOOKS == "enable_webhooks"
    assert const.ENABLE_SOUND_DETECTION == "enable_sound_detection"
    assert const.ENABLE_TIME_SYNC == "enable_time_sync"
    assert const.IS_KLAP_DEVICE == "is_klap_device"
    assert const.REPORTED_IP_ADDRESS == "reported_ip_address"
    assert const.CONTROL_PORT == "control_port"
    assert const.CLOUD_USERNAME == "cloud_username"
    assert const.CLOUD_PASSWORD == "cloud_password"
    assert const.HAS_STREAM_6 == "has_stream6"
    assert const.HAS_STREAM_7 == "has_stream7"
    assert const.ALARM_MODE == "alarm_mode"
    assert const.PRESET == "preset"
    assert const.LIGHT == "light"
    assert const.SOUND == "sound"
    assert const.PRIVACY_MODE == "privacy_mode"
    assert const.ALARM == "alarm"
    assert const.LED_MODE == "led_mode"
    assert const.NAME == "name"
    assert const.MOTION_DETECTION_MODE == "motion_detection_mode"
    assert const.AUTO_TRACK_MODE == "auto_track_mode"


def test_logger_created():
    const = _get_const()
    assert const.LOGGER.name == "custom_components.tapo_control"


def test_recording_unavailable_message():
    const = _get_const()
    assert "Recordings are unavailable" in const.RECORDINGS_UNAVAILABLE_MESSAGE
