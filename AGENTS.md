# AGENTS.md — HomeAssistant-Tapo-Control

## Project Overview

Home Assistant custom integration (`tapo_control`) for TP-Link Tapo cameras, doorbells, and chimes. Local control, no internet required. Version 7.1.13, min HA 2025.10.0.

- **Owner**: Juraj Nyiri (@JurajNyiri)
- **License**: Apache 2.0
- **Domain**: `tapo_control`
- **Repository**: https://github.com/JurajNyiri/HomeAssistant-Tapo-Control
- **HACS**: Default repository

## Architecture

```
Config Flow → __init__.py async_setup_entry → Tapo controller (pytapo) + DataUpdateCoordinator
  ├─ camera.py         — RTSP or proprietary Direct stream
  ├─ binary_sensor.py  — Motion (ONVIF), noise (ffmpeg), doorbell (UDP)
  ├─ switch.py / select.py / number.py / button.py / light.py / siren.py / sensor.py / update.py
  ├─ media_source.py   — Recording browser + media sync
  └─ tapo/entities.py  — Base entity classes
```

- Single `Tapo` (pytapo) controller per config entry. Supports child devices (hubs with multiple cameras).
- `DataUpdateCoordinator` polls `getCamData()` — configurable interval (30s mains, 10min battery).
- Entities created dynamically based on camera capabilities (checked via `camData["raw"]` cache + fallback API).
- Motion detection via ONVIF pullpoint or webhooks using HA's built-in `EventManager`.
- Media sync: background downloads recordings → cold storage (`.storage/tapo_control/`) + hot cache (`www/tapo_control/`).
- DHCP discovery matches hostname patterns: `C[0-9]*_*`, `D[0-9]*_*`, `TC[0-9]*_*`, `H[0-9]*_*`.

## Dependencies

- **Runtime**: `pytapo==3.4.11`, `python-kasa[speedups]==0.10.2`
- **HA integrations**: `ffmpeg`, `onvif`, `stream`, `network`
- **Transitive**: `aiohttp`, `voluptuous`, `haffmpeg`, `yarl`, `zeep`, `python-onvif-zeep`

## Build System

Not a pip package. Distributed via HACS. Metadata only in:
- `manifest.json` — HA component manifest
- `hacs.json` — HACS metadata
- `requirements.txt` — lists `pytapo`

## Testing

Unit tests live in `tests/`, configured by `tests/pyproject.toml`.

- **Framework**: pytest (requires `pytest-asyncio` for async tests).
- **Config**: `tests/pyproject.toml` — test paths, file patterns, `pythonpath` set to `custom_components` for direct import.
- **Global mocks**: `tests/conftest.py` pre-seeds `sys.modules` for heavy transitive dependencies (aiodns, onvif, haffmpeg, numpy) to avoid import failures in CI.
- **Run**: `python3 -m pytest tests/` from the repo root.
- **Coverage**: `pytest-cov` config present in `tests/pyproject.toml`; run with `--cov=custom_components.tapo_control`.
- **Test files**:
  - `test_get_recording.py` — Recording download flow (`getRecording`), uses `monkeypatch` + `unittest.mock`.
  - `test_utils.py`, `test_button.py`, `test_light.py`, `test_number.py`, `test_select.py`, `test_sensor.py`, `test_siren.py`, `test_switch.py`, `test_update.py`, `test_entities.py`, `test_integration.py` — Component-level and integration tests.
- **Pattern**: Fixtures in `conftest.py` provide a `mock_hass`, `mock_controller` (Tapo), `mock_coordinator`, `mock_config_entry`, and `base_entry_dict`. Individual test files use `patch`/`AsyncMock` to isolate the unit under test.

## Linting & Formatting

- **Flake8** — `max-line-length=88`, `extend-ignore=E203`
- **Black** — Default formatter (via `ms-python.black-formatter` in VS Code)
- **Pylint** — Disabled
- No pre-commit hooks, no mypy, no pyright

## Coding Conventions

| Convention | Rule |
|---|---|
| Indentation | 4 spaces |
| Strings | Double quotes preferred |
| Naming | Classes `PascalCase`, functions `snake_case`, constants `UPPER_SNAKE_CASE` |
| Logging | `LOGGER` from `custom_components.tapo_control` namespace; heavy debug logging |
| Async | All HA entry points `async`; blocking calls via `hass.async_add_executor_job()` |
| Entities | Each platform: `async_setup_entry()` → `async_add_entities()` |
| Config storage | Config entry data dict; media sync in separate HA `Store` (JSON) |
| Error handling | Broad `try/except` with `LOGGER.error()`; `ConfigEntryAuthFailed` / `ConfigEntryNotReady` |
| Capability detect | `check_functionality()` / `check_and_create()` / `isCacheSupported()` — checks `camData["raw"]` |
| Type hints | Inconsistent — some functions typed, many not |

## Platform Files (custom_components/tapo_control/)

| File | Entities | Notes |
|---|---|---|
| `camera.py` | Camera | RTSP stream OR proprietary Direct stream |
| `binary_sensor.py` | Motion, noise, doorbell | UDP broadcast listener on port 20005 |
| `button.py` | Reboot, format, sync time, calibrate, PTZ, chime ring, alarm | |
| `light.py` | Floodlight | On/off + brightness |
| `number.py` | Movement angle, sensitivity, volume, siren duration, brightness | |
| `select.py` | Night vision, timezone, alarm mode, sensitivity, presets | |
| `sensor.py` | Battery, RSSI, SSID, link type, SD card, sync status | |
| `switch.py` | Privacy, LED, recording, notifications, HDR, auto-track, media sync, etc. | |
| `siren.py` | Siren (on/off with duration) | |
| `update.py` | Firmware update | |

## Key Behaviors to Preserve

1. **KLAP protocol** — Newer Tapo devices use KLAP handshake. Auto-detected during DHCP discovery or IP setup. Uses email + cloud password instead of local camera account.
2. **Direct streaming** — Proprietary TP-Link protocol bypassing RTSP. Essential for battery/solar devices or when RTSP streams are exhausted.
3. **Config flow migrations** — Version 25+ with long history. `async_migrate_entry()` in `__init__.py` must handle old-to-new transitions.
4. **Two-tier media sync** — Cold (long-term `.storage/tapo_control/`) + hot (web-served `www/tapo_control/`). Files cleaned by age + camera availability.
5. **Dual-lens support** — Streams 6/7 for telephoto HD/SD on compatible cameras.
6. **Child device support** — Hubs with multiple doorbell cameras share one controller.
7. **Sound detection** — Uses `haffmpeg.sensor.SensorNoise` from SD stream audio.

## Config Flow

- Step: user (IP, auth), DHCP discovery, reauth on auth failure.
- Options: polling interval, streaming source, media sync directory, day/night threshold, etc.
- No YAML configuration. All via UI config entries.

## CI/CD

- **Only** `issues.yml` workflow: auto-closes non-template issues and known FAQ patterns. No test/build/lint CI.

## Reminders

- Tests live in `tests/` — write or update tests alongside code changes when the change touches logic with existing test coverage.
- No packaging setup (no `setup.py`, `setup.cfg`).
- README.md is the primary documentation.
