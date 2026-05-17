from homeassistant.core import HomeAssistant

from homeassistant.components.button import ButtonEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.update import UpdateEntity
from homeassistant.components.light import LightEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import (
    STATE_UNAVAILABLE,
)

from ..const import BRAND, LOGGER
from ..utils import build_device_info


class TapoEntity(Entity):
    def __init__(self, entry: dict, name_suffix: str):
        self._entry = entry
        self._enabled = False
        self._is_cam_entity = False
        self._is_noise_sensor = False
        if self._entry["isChild"]:
            self._name = entry["camData"]["basic_info"]["device_alias"]
        else:
            self._name = entry["name"]
        self._name_suffix = name_suffix
        self._controller = entry["controller"]
        self._coordinator = entry["coordinator"]
        self._attributes = entry["camData"]["basic_info"]

    @property
    def name(self) -> str:
        return "{} {}".format(self._name, self._name_suffix)

    @property
    def device_info(self) -> DeviceInfo:
        return build_device_info(self._attributes)

    @property
    def unique_id(self) -> str:
        id_suffix = "".join(self._name_suffix.split())
        return "{}-{}-{}".format(self._attributes["mac"], self._name, id_suffix).lower()

    @property
    def model(self):
        return self._attributes["device_model"]

    @property
    def brand(self):
        return BRAND

    async def async_added_to_hass(self) -> None:
        self._enabled = True

    async def async_will_remove_from_hass(self) -> None:
        self._enabled = False

    async def async_update(self) -> None:
        await self._coordinator.async_request_refresh()

    def updateTapo(self, camData):
        pass


class TapoUpdateEntity(UpdateEntity, TapoEntity):
    def __init__(
        self,
        name_suffix,
        entry: dict,
        hass: HomeAssistant,
        config_entry,
        icon=None,
        device_class=None,
    ):
        LOGGER.debug("Initializing entity: %s", name_suffix)
        self._attr_is_on = False
        self._hass = hass
        self._attr_icon = icon
        self._config_entry = config_entry
        self._attr_device_class = device_class
        entry["entities"].append({"entity": self, "entry": entry})

        TapoEntity.__init__(self, entry, name_suffix)
        UpdateEntity.__init__(self)

        self.updateTapo(entry["camData"])

        LOGGER.debug("Entity initialized: %s", name_suffix)

    @property
    def entity_category(self):
        return EntityCategory.CONFIG

    @property
    def state(self):
        return self._attr_state


class TapoSwitchEntity(SwitchEntity, TapoEntity):
    def __init__(
        self,
        name_suffix,
        entry: dict,
        hass: HomeAssistant,
        config_entry,
        icon=None,
        device_class=None,
        on_method_name=None,
    ):
        LOGGER.debug("Initializing entity: %s", name_suffix)
        self._attr_is_on = False
        self._hass = hass
        self._attr_icon = icon
        self._config_entry = config_entry
        self._attr_device_class = device_class
        self._on_method_name = on_method_name
        entry["entities"].append({"entity": self, "entry": entry})
        self.updateTapo(entry["camData"])

        TapoEntity.__init__(self, entry, name_suffix)
        SwitchEntity.__init__(self)
        LOGGER.debug("Entity initialized: %s", name_suffix)

    async def _async_set_switch(self, method, *args):
        value = next((a for a in reversed(args) if isinstance(a, bool)), True)
        result = await self._hass.async_add_executor_job(method, *args)
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = "on" if value else "off"
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs):
        if self._on_method_name:
            method = getattr(self._controller, self._on_method_name)
            await self._async_set_switch(method, True)

    async def async_turn_off(self, **kwargs):
        if self._on_method_name:
            method = getattr(self._controller, self._on_method_name)
            await self._async_set_switch(method, False)

    @property
    def entity_category(self):
        return EntityCategory.CONFIG

    @property
    def state(self):
        return self._attr_state


class TapoSensorEntity(SensorEntity, TapoEntity):
    def __init__(
        self,
        name_suffix,
        entry: dict,
        hass: HomeAssistant,
        config_entry,
        icon=None,
        device_class=None,
    ):
        LOGGER.debug("Initializing entity: %s", name_suffix)
        self._attr_is_on = False
        self._hass = hass
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._config_entry = config_entry
        entry["entities"].append({"entity": self, "entry": entry})

        TapoEntity.__init__(self, entry, name_suffix)
        SensorEntity.__init__(self)
        self.updateTapo(entry["camData"])
        LOGGER.debug("Entity initialized: %s", name_suffix)

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self._attr_native_value != STATE_UNAVAILABLE


class TapoButtonEntity(ButtonEntity, TapoEntity):
    def __init__(
        self,
        name_suffix,
        entry: dict,
        hass: HomeAssistant,
        icon=None,
        device_class=None,
    ):
        LOGGER.debug("Initializing entity: %s", name_suffix)
        self._hass = hass
        self._attr_icon = icon
        self._attr_device_class = device_class
        entry["entities"].append({"entity": self, "entry": entry})
        self.updateTapo(entry["camData"])

        TapoEntity.__init__(self, entry, name_suffix)
        ButtonEntity.__init__(self)
        LOGGER.debug("Entity initialized: %s", name_suffix)

    @property
    def state(self):
        return self._attr_state


class TapoBinarySensorEntity(BinarySensorEntity, TapoEntity):
    def __init__(
        self,
        name_suffix,
        entry: dict,
        hass: HomeAssistant,
        config_entry,
        icon=None,
        device_class=None,
    ):
        LOGGER.debug("Initializing entity: %s", name_suffix)
        self._attr_is_on = False
        self._hass = hass
        self._attr_icon = icon
        self._attr_device_class = device_class
        entry["entities"].append({"entity": self, "entry": entry})
        self.updateTapo(entry["camData"])

        TapoEntity.__init__(self, entry, name_suffix)
        BinarySensorEntity.__init__(self)
        LOGGER.debug("Entity initialized: %s", name_suffix)

    @property
    def state(self):
        return self._attr_state


class TapoLightEntity(LightEntity, TapoEntity):
    def __init__(
        self,
        name_suffix,
        entry: dict,
        hass: HomeAssistant,
        config_entry,
        icon=None,
        device_class=None,
    ):
        LOGGER.debug("Initializing entity: %s", name_suffix)
        self._hass = hass
        self._attr_icon = icon
        self._attr_device_class = device_class
        LOGGER.debug("Appending entity: %s", name_suffix)
        entry["entities"].append({"entity": self, "entry": entry})
        LOGGER.debug("Updating entity: %s", name_suffix)
        self.updateTapo(entry["camData"])

        LOGGER.debug("Initializing TapoEntity: %s", name_suffix)
        TapoEntity.__init__(self, entry, name_suffix)
        LOGGER.debug("Initializing SelectEntity: %s", name_suffix)
        LightEntity.__init__(self)
        LOGGER.debug("Entity initialized: %s", name_suffix)


class TapoSelectEntity(SelectEntity, TapoEntity):
    def __init__(
        self,
        name_suffix,
        entry: dict,
        hass: HomeAssistant,
        config_entry,
        icon=None,
        device_class=None,
    ):
        LOGGER.debug("Initializing entity: %s", name_suffix)
        self._hass = hass
        self._attr_icon = icon
        self._attr_device_class = device_class
        LOGGER.debug("Appending entity: %s", name_suffix)
        entry["entities"].append({"entity": self, "entry": entry})
        LOGGER.debug("Updating entity: %s", name_suffix)
        self.updateTapo(entry["camData"])

        LOGGER.debug("Initializing TapoEntity: %s", name_suffix)
        TapoEntity.__init__(self, entry, name_suffix)
        LOGGER.debug("Initializing SelectEntity: %s", name_suffix)
        SelectEntity.__init__(self)
        LOGGER.debug("Entity initialized: %s", name_suffix)

    @property
    def entity_category(self):
        return EntityCategory.CONFIG

    @property
    def state(self):
        return self._attr_state


class TapoDetectionSelect(TapoSelectEntity):
    def __init__(
        self,
        name_suffix,
        entry,
        hass,
        config_entry,
        icon,
        device_class,
        enabled_key,
        sensitivity_key,
        method_name,
        supports_channels=False,
        specific_name=None,
        chn_id=None,
    ):
        self._attr_options = ["high", "normal", "low", "off"]
        self._attr_current_option = None
        self.chn_id = chn_id
        self.read_chn_id = str(chn_id) if chn_id else "1"
        self._enabled_key = enabled_key
        self._sensitivity_key = sensitivity_key
        self._method_name = method_name
        self._supports_channels = supports_channels
        display_name = f"{name_suffix}{' - ' + specific_name if specific_name else ''}"
        TapoSelectEntity.__init__(
            self, display_name, entry, hass, config_entry, icon, device_class
        )

    def updateTapo(self, camData):
        if not camData:
            self._attr_state = STATE_UNAVAILABLE
            return

        enabled = camData[self._enabled_key]
        sensitivity = camData[self._sensitivity_key]
        if isinstance(enabled, dict):
            enabled = enabled.get(self.read_chn_id)
        if isinstance(sensitivity, dict):
            sensitivity = sensitivity.get(self.read_chn_id)
        if enabled == "off":
            self._attr_current_option = "off"
        else:
            self._attr_current_option = sensitivity
        self._attr_state = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        method = getattr(self._controller, self._method_name)
        args = [option != "off", option if option != "off" else False]
        if self._supports_channels:
            args.append([self.chn_id] if self.chn_id else None)
        result = await self.hass.async_add_executor_job(method, *args)
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = option
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()


class TapoNumberEntity(NumberEntity, TapoEntity):
    def __init__(
        self,
        name_suffix,
        entry: dict,
        hass: HomeAssistant,
        config_entry,
        icon=None,
        device_class=None,
        on_method_name=None,
    ):
        LOGGER.debug("Initializing entity: %s", name_suffix)
        self._hass = hass
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._on_method_name = on_method_name
        LOGGER.debug("Appending entity: %s", name_suffix)
        entry["entities"].append({"entity": self, "entry": entry})
        LOGGER.debug("Updating entity: %s", name_suffix)
        self.updateTapo(entry["camData"])

        LOGGER.debug("Initializing TapoEntity: %s", name_suffix)
        TapoEntity.__init__(self, entry, name_suffix)
        LOGGER.debug("Initializing NumberEntity: %s", name_suffix)
        NumberEntity.__init__(self)
        LOGGER.debug("Entity initialized: %s", name_suffix)

    @property
    def entity_category(self):
        return EntityCategory.CONFIG

    async def _async_set_number(self, method, *args):
        value = next((a for a in reversed(args) if isinstance(a, (int, float))), None)
        result = await self._hass.async_add_executor_job(method, *args)
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = value
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()

    async def async_set_native_value(self, value: float) -> None:
        if self._on_method_name:
            method = getattr(self._controller, self._on_method_name)
            await self._async_set_number(method, value)

    @property
    def entity_category(self):
        return EntityCategory.CONFIG

    @property
    def state(self):
        return self._attr_state
