import pytest
from unittest.mock import Mock, MagicMock, patch
from copy import deepcopy

from custom_components.tapo_control.tapo.entities import (
    TapoEntity,
    TapoSwitchEntity,
    TapoSensorEntity,
    TapoButtonEntity,
    TapoSelectEntity,
    TapoNumberEntity,
    TapoLightEntity,
    TapoBinarySensorEntity,
)
from custom_components.tapo_control.const import BRAND


def _make_entry(**overrides):
    entry = {
        "controller": MagicMock(),
        "coordinator": MagicMock(),
        "camData": {
            "basic_info": {
                "mac": "aa:bb:cc:dd:ee:ff",
                "device_alias": "TestCamera",
                "device_model": "C200",
                "sw_version": "1.0",
                "hw_version": "1.0",
            },
        },
        "name": "TestCamera",
        "isChild": False,
        "entities": [],
    }
    entry.update(overrides)
    return entry


class TestTapoEntity:
    def test_name_returns_suffix_only(self):
        entry = _make_entry()
        entity = TapoEntity(entry, "Switch")
        assert entity.name == "Switch"

    def test_unique_id(self):
        entry = _make_entry()
        entity = TapoEntity(entry, "Switch")
        assert entity.unique_id == "aa:bb:cc:dd:ee:ff-testcamera-switch"

    def test_model_from_attributes(self):
        entry = _make_entry()
        entity = TapoEntity(entry, "Switch")
        assert entity.model == "C200"

    def test_brand_constant(self):
        entry = _make_entry()
        entity = TapoEntity(entry, "Switch")
        assert entity.brand == BRAND

    def test_name_with_child_device(self):
        entry = _make_entry(
            isChild=True,
            camData={
                "basic_info": {
                    "mac": "aa:bb:cc:dd:ee:ff",
                    "device_alias": "ChildCamera",
                    "device_model": "C200",
                },
            },
        )
        entity = TapoEntity(entry, "Sensor")
        assert entity.name == "Sensor"

    def test_unique_id_lowercased(self):
        entry = _make_entry(
            camData={
                "basic_info": {
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "device_alias": "TestCamera",
                    "device_model": "C200",
                },
            },
        )
        entity = TapoEntity(entry, "Switch")
        assert entity.unique_id == entity.unique_id.lower()

    def test_enabled_default_false(self):
        entry = _make_entry()
        entity = TapoEntity(entry, "Switch")
        assert not entity._enabled

    @pytest.mark.asyncio
    async def test_async_added_to_hass_enables(self):
        entry = _make_entry()
        entity = TapoEntity(entry, "Switch")
        await entity.async_added_to_hass()
        assert entity._enabled

    @pytest.mark.asyncio
    async def test_async_will_remove_from_hass_disables(self):
        entry = _make_entry()
        entity = TapoEntity(entry, "Switch")
        await entity.async_added_to_hass()
        await entity.async_will_remove_from_hass()
        assert not entity._enabled

    def test_updateTapo_default_noop(self):
        entry = _make_entry()
        entity = TapoEntity(entry, "Switch")
        result = entity.updateTapo({"some": "data"})
        assert result is None

    def test_device_info_built(self):
        entry = _make_entry()
        entity = TapoEntity(entry, "Switch")
        info = entity.device_info
        assert info is not None

    def test_entity_registered_in_entry(self):
        entry = _make_entry()
        entity = TapoEntity(entry, "Switch")
        assert entity._entry is entry
        assert entity._controller is entry["controller"]
        assert entity._coordinator is entry["coordinator"]


class TestTapoSwitchEntity:
    def test_init_adds_to_entry_entities(self):
        entry = _make_entry()
        hass = MagicMock()
        config_entry = MagicMock()
        entity = TapoSwitchEntity("Switch", entry, hass, config_entry)
        assert len(entry["entities"]) == 1
        assert entry["entities"][0]["entity"] is entity

    def test_entity_category_config(self):
        entry = _make_entry()
        hass = MagicMock()
        config_entry = MagicMock()
        entity = TapoSwitchEntity("Switch", entry, hass, config_entry)
        assert entity.entity_category is not None


class TestTapoSensorEntity:
    def test_available_when_native_value_set(self):
        entry = _make_entry()
        hass = MagicMock()
        config_entry = MagicMock()
        entity = TapoSensorEntity("Sensor", entry, hass, config_entry)
        entity._attr_native_value = 85
        assert entity.available

    def test_unavailable_when_native_value_unavailable(self):
        entry = _make_entry()
        hass = MagicMock()
        config_entry = MagicMock()
        entity = TapoSensorEntity("Sensor", entry, hass, config_entry)
        from homeassistant.const import STATE_UNAVAILABLE

        entity._attr_native_value = STATE_UNAVAILABLE
        assert not entity.available


class TestTapoButtonEntity:
    def test_init(self):
        entry = _make_entry()
        hass = MagicMock()
        entity = TapoButtonEntity("Button", entry, hass)
        assert len(entry["entities"]) == 1

    def test_state_default(self):
        entry = _make_entry()
        hass = MagicMock()
        entity = TapoButtonEntity("Button", entry, hass)
        assert entity.state is None


class TestTapoSelectEntity:
    def test_init_adds_to_entry_entities(self):
        entry = _make_entry()
        hass = MagicMock()
        config_entry = MagicMock()
        entity = TapoSelectEntity("Select", entry, hass, config_entry)
        assert len(entry["entities"]) == 1

    def test_entity_category_config(self):
        entry = _make_entry()
        hass = MagicMock()
        config_entry = MagicMock()
        entity = TapoSelectEntity("Select", entry, hass, config_entry)
        assert entity.entity_category is not None


class TestTapoNumberEntity:
    def test_init_adds_to_entry_entities(self):
        entry = _make_entry()
        hass = MagicMock()
        config_entry = MagicMock()
        entity = TapoNumberEntity("Number", entry, hass, config_entry)
        assert len(entry["entities"]) == 1

    def test_entity_category_config(self):
        entry = _make_entry()
        hass = MagicMock()
        config_entry = MagicMock()
        entity = TapoNumberEntity("Number", entry, hass, config_entry)
        assert entity.entity_category is not None


class TestTapoLightEntity:
    def test_init_adds_to_entry_entities(self):
        entry = _make_entry()
        hass = MagicMock()
        config_entry = MagicMock()
        entity = TapoLightEntity("Light", entry, hass, config_entry)
        assert len(entry["entities"]) == 1


class TestTapoBinarySensorEntity:
    def test_init_adds_to_entry_entities(self):
        entry = _make_entry()
        hass = MagicMock()
        config_entry = MagicMock()
        entity = TapoBinarySensorEntity("Binary", entry, hass, config_entry)
        assert len(entry["entities"]) == 1
