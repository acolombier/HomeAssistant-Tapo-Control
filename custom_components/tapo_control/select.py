from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, LOGGER
from .tapo.entities import TapoDetectionSelect, TapoSelectEntity
from .utils import (
    check_and_create,
    check_functionality,
    getNightModeName,
    getNightModeValue,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    LOGGER.debug("Setting up selects")
    entry = hass.data[DOMAIN][config_entry.entry_id]

    async def setupEntities(entry):
        selects = []

        tapoTimezoneSelect = await check_and_create(
            entry, hass, TapoTimezoneSelect, "getTimezone", config_entry
        )
        if tapoTimezoneSelect:
            LOGGER.debug("Adding tapoTimezoneSelect...")
            selects.append(tapoTimezoneSelect)

        if (
            "night_vision_mode_switching" in entry["camData"]
            and entry["camData"]["night_vision_mode_switching"] is not None
        ):
            if entry["chInfo"]:
                for lens in entry["chInfo"]:
                    chn_alias = lens.get("chn_alias", "")
                    chn_id = lens.get("chn_id")
                    tapoNightVisionSelect = TapoNightVisionSelect(
                        entry,
                        hass,
                        config_entry,
                        "Night Vision Switching",
                        ["auto", "on", "off"],
                        "night_vision_mode_switching",
                        entry["controller"].setDayNightMode,
                        chn_alias,
                        chn_id,
                    )
                    LOGGER.debug(
                        f"Adding tapoNightVisionSelect (Night Vision Switching) for {chn_alias}, id: {chn_id}..."
                    )
                    selects.append(tapoNightVisionSelect)
            else:
                tapoNightVisionSelect = TapoNightVisionSelect(
                    entry,
                    hass,
                    config_entry,
                    "Night Vision Switching",
                    ["auto", "on", "off"],
                    "night_vision_mode_switching",
                    entry["controller"].setDayNightMode,
                )
                LOGGER.debug("Adding tapoNightVisionSelect (Night Vision Switching)...")
                selects.append(tapoNightVisionSelect)

        if (
            "night_vision_mode" in entry["camData"]
            and entry["camData"]["night_vision_mode"] is not None
            and entry["camData"]["night_vision_capability"] is not None
        ):
            if entry["chInfo"]:
                for lens in entry["chInfo"]:
                    chn_alias = lens.get("chn_alias", "")
                    chn_id = lens.get("chn_id")
                    tapoNightVisionSelect = TapoNightVisionSelect(
                        entry,
                        hass,
                        config_entry,
                        "Night Vision",
                        entry["camData"]["night_vision_capability"],
                        "night_vision_mode",
                        entry["controller"].setNightVisionModeConfig,
                        chn_alias,
                        chn_id,
                    )
                    LOGGER.debug(
                        f"Adding tapoNightVisionSelect (Night Vision) for {chn_alias}, id: {chn_id}..."
                    )
                    selects.append(tapoNightVisionSelect)
            else:
                tapoNightVisionSelect = TapoNightVisionSelect(
                    entry,
                    hass,
                    config_entry,
                    "Night Vision",
                    entry["camData"]["night_vision_capability"],
                    "night_vision_mode",
                    entry["controller"].setNightVisionModeConfig,
                )
                LOGGER.debug("Adding tapoNightVisionSelect (Night Vision)...")
                selects.append(tapoNightVisionSelect)

        tapoLightFrequencySelect = await check_and_create(
            entry, hass, TapoLightFrequencySelect, "getLightFrequencyMode", config_entry
        )
        if tapoLightFrequencySelect:
            LOGGER.debug("Adding tapoLightFrequencySelect...")
            selects.append(tapoLightFrequencySelect)

        tapoAutomaticAlarmModeSelect = await check_and_create(
            entry, hass, TapoAutomaticAlarmModeSelect, "getAlarm", config_entry
        )

        if not tapoAutomaticAlarmModeSelect:
            tapoAutomaticAlarmModeSelect = await check_and_create(
                entry,
                hass,
                TapoAutomaticAlarmModeSelect,
                "getAlarmConfig",
                config_entry,
            )

        if tapoAutomaticAlarmModeSelect:
            LOGGER.debug("Adding tapoAutomaticAlarmModeSelect...")
            selects.append(tapoAutomaticAlarmModeSelect)

        tapoSirenTypeSelect = await check_and_create(
            entry, hass, TapoSirenTypeSelect, "getSirenTypeList", config_entry
        )
        if tapoSirenTypeSelect:
            LOGGER.debug("Adding tapoSirenTypeSelect...")
            selects.append(tapoSirenTypeSelect)

        tapoAlertTypeSelect = await check_and_create(
            entry, hass, TapoAlertTypeSelect, "getAlertTypeList", config_entry
        )
        if entry["controller"].isKLAP is False:
            if tapoAlertTypeSelect:
                LOGGER.debug("Adding tapoAlertTypeSelect...")
                selects.append(tapoAlertTypeSelect)
            elif not tapoSirenTypeSelect:
                LOGGER.debug("Adding tapoAlertTypeSelect with start ID 0...")
                selects.append(TapoAlertTypeSelect(entry, hass, config_entry, 0))

        tapoMotionDetectionSelectAvailable = await check_functionality(
            entry, hass, TapoMotionDetectionSelect, "getMotionDetection"
        )
        if tapoMotionDetectionSelectAvailable:
            if entry["chInfo"]:
                for lens in entry["chInfo"]:
                    chn_alias = lens.get("chn_alias", "")
                    chn_id = lens.get("chn_id")
                    LOGGER.debug(
                        f"Adding TapoMotionDetectionSelect for {chn_alias}, id: {chn_id}..."
                    )
                    selects.append(
                        TapoMotionDetectionSelect(
                            entry, hass, config_entry, chn_alias, chn_id
                        )
                    )
            else:
                LOGGER.debug("Adding TapoMotionDetectionSelect...")
                selects.append(TapoMotionDetectionSelect(entry, hass, config_entry))

        tapoDualCamLinkageSelectAvailable = await check_functionality(
            entry, hass, TapoDualCamLinkage, "getDualCamLinkage"
        )
        if tapoDualCamLinkageSelectAvailable:
            LOGGER.debug("Adding TapoDualCamLinkage...")
            selects.append(TapoDualCamLinkage(entry, hass, config_entry))

        tapoPersonDetectionSelectAvailable = await check_functionality(
            entry, hass, TapoPersonDetectionSelect, "getPersonDetection"
        )
        if tapoPersonDetectionSelectAvailable:
            if entry["chInfo"]:
                for lens in entry["chInfo"]:
                    chn_alias = lens.get("chn_alias", "")
                    chn_id = lens.get("chn_id")
                    LOGGER.debug(
                        f"Adding tapoPersonDetectionSelect for {chn_alias}, id: {chn_id}..."
                    )
                    selects.append(
                        TapoPersonDetectionSelect(
                            entry, hass, config_entry, chn_alias, chn_id
                        )
                    )
            else:
                LOGGER.debug("Adding tapoPersonDetectionSelect...")
                selects.append(TapoPersonDetectionSelect(entry, hass, config_entry))

        tapoVehicleDetectionSelectAvailable = await check_functionality(
            entry, hass, TapoVehicleDetectionSelect, "getVehicleDetection"
        )
        if tapoVehicleDetectionSelectAvailable:
            if entry["chInfo"]:
                for lens in entry["chInfo"]:
                    chn_alias = lens.get("chn_alias", "")
                    chn_id = lens.get("chn_id")
                    LOGGER.debug(
                        f"Adding tapoVehicleDetectionSelect for {chn_alias}, id: {chn_id}..."
                    )
                    selects.append(
                        TapoVehicleDetectionSelect(
                            entry, hass, config_entry, chn_alias, chn_id
                        )
                    )
            else:
                LOGGER.debug("Adding tapoVehicleDetectionSelect...")
                selects.append(TapoVehicleDetectionSelect(entry, hass, config_entry))

        tapoBabyCryDetectionSelect = await check_and_create(
            entry, hass, TapoBabyCryDetectionSelect, "getBabyCryDetection", config_entry
        )
        if tapoBabyCryDetectionSelect:
            LOGGER.debug("Adding tapoBabyCryDetectionSelect...")
            selects.append(tapoBabyCryDetectionSelect)

        tapoPetDetectionSelectAvailable = await check_functionality(
            entry, hass, TapoPetDetectionSelect, "getPetDetection"
        )
        if tapoPetDetectionSelectAvailable:
            if entry["chInfo"]:
                for lens in entry["chInfo"]:
                    chn_alias = lens.get("chn_alias", "")
                    chn_id = lens.get("chn_id")
                    LOGGER.debug(
                        f"Adding tapoPetDetectionSelect for {chn_alias}, id: {chn_id}..."
                    )
                    selects.append(
                        TapoPetDetectionSelect(
                            entry, hass, config_entry, chn_alias, chn_id
                        )
                    )
            else:
                LOGGER.debug("Adding tapoPetDetectionSelect...")
                selects.append(TapoPetDetectionSelect(entry, hass, config_entry))

        tapoBarkDetectionSelect = await check_and_create(
            entry, hass, TapoBarkDetectionSelect, "getBarkDetection", config_entry
        )
        if tapoBarkDetectionSelect:
            LOGGER.debug("Adding tapoBarkDetectionSelect...")
            selects.append(tapoBarkDetectionSelect)

        tapoMeowDetectionSelect = await check_and_create(
            entry, hass, TapoMeowDetectionSelect, "getMeowDetection", config_entry
        )
        if tapoMeowDetectionSelect:
            LOGGER.debug("Adding tapoMeowDetectionSelect...")
            selects.append(tapoMeowDetectionSelect)

        tapoGlassBreakDetectionSelect = await check_and_create(
            entry,
            hass,
            TapoGlassBreakDetectionSelect,
            "getGlassBreakDetection",
            config_entry,
        )
        if tapoGlassBreakDetectionSelect:
            LOGGER.debug("Adding tapoGlassBreakDetectionSelect...")
            selects.append(tapoGlassBreakDetectionSelect)

        tapoTamperDetectionSelectAvailable = await check_functionality(
            entry, hass, TapoTamperDetectionSelect, "getTamperDetection"
        )
        if tapoTamperDetectionSelectAvailable:
            if entry["chInfo"]:
                for lens in entry["chInfo"]:
                    chn_alias = lens.get("chn_alias", "")
                    chn_id = lens.get("chn_id")
                    LOGGER.debug(
                        f"Adding tapoTamperDetectionSelect for {chn_alias}, id: {chn_id}..."
                    )
                    selects.append(
                        TapoTamperDetectionSelect(
                            entry, hass, config_entry, chn_alias, chn_id
                        )
                    )
            else:
                LOGGER.debug("Adding tapoTamperDetectionSelect...")
                selects.append(TapoTamperDetectionSelect(entry, hass, config_entry))

        tapoMoveToPresetSelect = await check_and_create(
            entry, hass, TapoMoveToPresetSelect, "getPresets", config_entry
        )
        if tapoMoveToPresetSelect:
            LOGGER.debug("Adding TapoMoveToPresetSelect...")
            selects.append(tapoMoveToPresetSelect)

        tapoPatrolModeSelect = await check_and_create(
            entry, hass, TapoPatrolModeSelect, "getPresets", config_entry
        )
        if tapoPatrolModeSelect:
            LOGGER.debug("Adding TapoPatrolModeSelect...")
            selects.append(tapoPatrolModeSelect)

        if entry["camData"]["whitelampConfigForceTime"] is not None:
            tapoWhitelampForceTimeSelectAvailable = await check_functionality(
                entry, hass, TapoWhitelampForceTimeSelect, "getWhitelampConfig"
            )
            if tapoWhitelampForceTimeSelectAvailable:
                if entry["chInfo"]:
                    for lens in entry["chInfo"]:
                        chn_alias = lens.get("chn_alias", "")
                        chn_id = lens.get("chn_id")
                        force_time = entry["camData"].get("whitelampConfigForceTime")
                        if isinstance(force_time, dict) and (
                            str(chn_id) not in force_time
                            or force_time.get(str(chn_id)) is None
                        ):
                            continue
                        LOGGER.debug(
                            f"Adding TapoWhitelampForceTimeSelect for {chn_alias}, id: {chn_id}..."
                        )
                        selects.append(
                            TapoWhitelampForceTimeSelect(
                                entry, hass, config_entry, chn_alias, chn_id
                            )
                        )
                else:
                    LOGGER.debug("Adding TapoWhitelampForceTimeSelect...")
                    selects.append(
                        TapoWhitelampForceTimeSelect(entry, hass, config_entry)
                    )

        if (
            entry["camData"]["whitelampConfigIntensity"] is not None
            and entry["camData"]["smartwtl_digital_level"] is None
        ):
            tapoWhitelampIntensityLevelSelectAvailable = await check_functionality(
                entry, hass, TapoWhitelampIntensityLevelSelect, "getWhitelampConfig"
            )
            if tapoWhitelampIntensityLevelSelectAvailable:
                if entry["chInfo"]:
                    for lens in entry["chInfo"]:
                        chn_alias = lens.get("chn_alias", "")
                        chn_id = lens.get("chn_id")
                        LOGGER.debug(
                            f"Adding TapoWhitelampIntensityLevelSelect for {chn_alias}, id: {chn_id}..."
                        )
                        selects.append(
                            TapoWhitelampIntensityLevelSelect(
                                entry, hass, config_entry, chn_alias, chn_id
                            )
                        )
                else:
                    LOGGER.debug("Adding TapoWhitelampIntensityLevelSelect...")
                    selects.append(
                        TapoWhitelampIntensityLevelSelect(entry, hass, config_entry)
                    )

        if (
            "quick_response" in entry["camData"]
            and entry["camData"]["quick_response"] is not None
            and len(entry["camData"]["quick_response"]) > 0
        ):
            tapoQuickResponseSelect = TapoQuickResponseSelect(entry, hass, config_entry)
            if tapoQuickResponseSelect:
                LOGGER.debug("Adding tapoQuickResponseSelect...")
                selects.append(tapoQuickResponseSelect)

        if (
            "chimeAlarmConfigurations" in entry["camData"]
            and entry["camData"]["chimeAlarmConfigurations"] is not None
            and len(entry["camData"]["chimeAlarmConfigurations"]) > 0
            and "supportAlarmTypeList" in entry["camData"]
            and entry["camData"]["supportAlarmTypeList"] is not None
        ):
            for macAddress in entry["camData"]["chimeAlarmConfigurations"]:
                tapoChimeRingtone = TapoChimeSound(
                    entry, hass, config_entry, macAddress
                )
                selects.append(tapoChimeRingtone)

        if (
            "supportAlarmTypeList" in entry["camData"]
            and entry["camData"]["supportAlarmTypeList"] is not None
        ):
            selects.append(TapoChimeSoundPlay(entry, hass, config_entry))
        return selects

    selects = await setupEntities(entry)
    for childDevice in entry["childDevices"]:
        selects.extend(await setupEntities(childDevice))

    async_add_entities(selects)


class TapoChimeSoundPlay(RestoreEntity, TapoSelectEntity):
    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._attr_options = entry["camData"]["supportAlarmTypeList"]["alarm_type_list"]
        self._attr_current_option = entry["chime_play_type"] = 1
        TapoSelectEntity.__init__(
            self,
            "Chime Play - Type",
            entry,
            hass,
            config_entry,
            "mdi:music",
        )
        RestoreEntity.__init__(self)

    def updateTapo(self, camData):
        if (
            "supportAlarmTypeList" not in camData
            or camData["supportAlarmTypeList"] is None
        ):
            self._attr_state = STATE_UNAVAILABLE

    async def async_select_option(self, option: str) -> None:
        self._attr_state = option
        self._attr_current_option = self._entry["chime_play_type"] = option
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        await super().async_added_to_hass()

        data = await self.async_get_last_state()

        if data is not None and data.state not in (
            None,
            STATE_UNKNOWN,
            STATE_UNAVAILABLE,
        ):
            self._attr_current_option = self._entry["chime_play_type"] = data.state
            self._attr_state = data.state
        else:
            self._attr_current_option = self._entry["chime_play_type"] = 1
            self._attr_state = 1


class TapoChimeSound(TapoSelectEntity):
    def __init__(self, entry: dict, hass: HomeAssistant, config_entry, macAddress: str):
        self.macAddress = macAddress
        self._attr_options = entry["camData"]["supportAlarmTypeList"]["alarm_type_list"]
        chimeData = entry["camData"]["chimeAlarmConfigurations"][self.macAddress]
        self._attr_current_option = chimeData["type"]
        TapoSelectEntity.__init__(
            self,
            f"{macAddress} - Chime Sound",
            entry,
            hass,
            config_entry,
            "mdi:music",
        )

    def updateTapo(self, camData):
        if (
            not camData
            or "chimeAlarmConfigurations" not in camData
            or len(camData["chimeAlarmConfigurations"]) == 0
            or self.macAddress not in camData["chimeAlarmConfigurations"]
            or "supportAlarmTypeList" not in camData
            or camData["supportAlarmTypeList"] is None
        ):
            self._attr_state = STATE_UNAVAILABLE
        else:
            chimeData = camData["chimeAlarmConfigurations"][self.macAddress]
            self._attr_current_option = chimeData["type"]
            self._attr_state = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        result = await self._hass.async_add_executor_job(
            self._controller.setChimeAlarmConfigure,
            self.macAddress,
            None,
            option,
        )
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = option
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()


class TapoWhitelampForceTimeSelect(TapoSelectEntity):
    def __init__(
        self,
        entry: dict,
        hass: HomeAssistant,
        config_entry,
        specific_name=None,
        chn_id=None,
    ):
        self._attr_options = ["5 min", "10 min", "15 min", "30 min"]
        self._attr_current_option = None
        self.chn_id = chn_id
        self.read_chn_id = str(chn_id) if chn_id else "1"
        TapoSelectEntity.__init__(
            self,
            f"Spotlight on/off for{" - " + specific_name if specific_name else ""}",
            entry,
            hass,
            config_entry,
            "mdi:clock-outline",
        )

    def updateTapo(self, camData):
        if not camData:
            self._attr_state = "unavailable"
        else:
            force_time = camData["whitelampConfigForceTime"]
            if isinstance(force_time, dict):
                force_time = force_time.get(self.read_chn_id)
            if force_time == "300":
                self._attr_current_option = self._attr_options[0]
            elif force_time == "600":
                self._attr_current_option = self._attr_options[1]
            elif force_time == "900":
                self._attr_current_option = self._attr_options[2]
            elif force_time == "1800":
                self._attr_current_option = self._attr_options[3]
            self._attr_state = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        if option == "5 min":
            result = await self._hass.async_add_executor_job(
                self._controller.setWhitelampConfig,
                300,
                False,
                [self.chn_id] if self.chn_id else None,
            )
        elif option == "10 min":
            result = await self._hass.async_add_executor_job(
                self._controller.setWhitelampConfig,
                600,
                False,
                [self.chn_id] if self.chn_id else None,
            )
        elif option == "15 min":
            result = await self._hass.async_add_executor_job(
                self._controller.setWhitelampConfig,
                900,
                False,
                [self.chn_id] if self.chn_id else None,
            )
        elif option == "30 min":
            result = await self._hass.async_add_executor_job(
                self._controller.setWhitelampConfig,
                1800,
                False,
                [self.chn_id] if self.chn_id else None,
            )
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = option
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()


class TapoWhitelampIntensityLevelSelect(TapoSelectEntity):
    def __init__(
        self,
        entry: dict,
        hass: HomeAssistant,
        config_entry,
        specific_name=None,
        chn_id=None,
    ):
        self._attr_options = ["1", "2", "3", "4", "5"]
        self._attr_current_option = None
        self.chn_id = chn_id
        self.read_chn_id = str(chn_id) if chn_id else "1"
        TapoSelectEntity.__init__(
            self,
            f"Spotlight Intensity{" - " + specific_name if specific_name else ""}",
            entry,
            hass,
            config_entry,
            "mdi:lightbulb-on-50",
        )

    def updateTapo(self, camData):
        if not camData:
            self._attr_state = "unavailable"
        else:
            intensity = camData["whitelampConfigIntensity"]
            if isinstance(intensity, dict):
                intensity = intensity.get(self.read_chn_id)
            self._attr_current_option = intensity
            self._attr_state = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        result = await self._hass.async_add_executor_job(
            self._controller.setWhitelampConfig,
            False,
            option,
            [self.chn_id] if self.chn_id else None,
        )
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = option
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()


class TapoQuickResponseSelect(TapoSelectEntity):
    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self.populateSelectOptions(entry["camData"])

        self._attr_current_option = None
        TapoSelectEntity.__init__(
            self,
            "Quick Response",
            entry,
            hass,
            config_entry,
            "mdi:comment-alert",
        )

    def populateSelectOptions(self, camData):
        self._attr_options = []
        self._attr_options_id = []
        for quick_resp_audio in camData["quick_response"]:
            for key in quick_resp_audio:
                self._attr_options.append(quick_resp_audio[key]["name"])
                self._attr_options_id.append(quick_resp_audio[key]["id"])

    def updateTapo(self, camData):
        if not camData:
            self._attr_state = "unavailable"
        else:
            self.populateSelectOptions(camData)
            self._attr_current_option = None
            self._attr_state = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        result = await self._hass.async_add_executor_job(
            self._controller.playQuickResponse,
            self._attr_options_id[self._attr_options.index(option)],
        )
        self._attr_state = None
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()


class TapoPatrolModeSelect(TapoSelectEntity):
    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._attr_options = ["Horizontal", "Vertical", "off"]
        self._attr_current_option = None
        TapoSelectEntity.__init__(
            self,
            "Patrol Mode",
            entry,
            hass,
            config_entry,
            "mdi:swap-horizontal",
            "patrol_mode",
        )

    def updateTapo(self, camData):
        if not camData or camData["privacy_mode"] == "on":
            self._attr_state = STATE_UNAVAILABLE
        else:
            self._attr_current_option = None
            self._attr_state = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        if option == "off":
            result = await self._hass.async_add_executor_job(
                self._controller.setCruise, False
            )
        else:
            result = await self._hass.async_add_executor_job(
                self._controller.setCruise, True, "x" if option == "Horizontal" else "y"
            )
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = option
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()

    @property
    def entity_category(self):
        return None


class TapoTimezoneSelect(TapoSelectEntity):
    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._attr_options = [
            "UTC+12:00 (Pacific/Wake)",
            "UTC-11:00 (Pacific/Midway)",
            "UTC-10:00 (Pacific/Honolulu)",
            "UTC-09:00 (America/Archorage)",
            "UTC-08:00 (America/Los_Angeles)",
            "UTC-07:00 (America/Chihuahua)",
            "UTC-07:00 (America/Denver)",
            "UTC-06:00 (America/Tegucigalpa)",
            "UTC-06:00 (America/Chicago)",
            "UTC-06:00 (America/Mexico_City)",
            "UTC-06:00 (Canada/Saskatchewan)",
            "UTC-05:00 (America/Bogota)",
            "UTC-05:00 (America/New_York)",
            "UTC-05:00 (America/Indiana/Indianapolis)",
            "UTC-04:00 (America/Caracas)",
            "UTC-04:00 (America/Asuncion)",
            "UTC-04:00 (America/Halifax)",
            "UTC-04:00 (America/Cuiaba)",
            "UTC-04:00 (America/La_Paz)",
            "UTC-04:00 (America/Santiago)",
            "UTC-03:30 (Canada/Newfoundland)",
            "UTC-03:00 (America/Sao_Paulo)",
            "UTC-03:00 (America/Buenos_Aires)",
            "UTC-03:00 (America/Cayenne)",
            "UTC-03:00 (America/Godthab)",
            "UTC-03:00 (America/Montevideo)",
            "UTC-02:00 (Atlantic/South_Georgia)",
            "UTC-01:00 (Atlantic Azores)",
            "UTC-01:00 (Atlantic/Cape_Verde)",
            "UTC-00:00 (Africa/Casablanca)",
            "UTC-00:00 (UTC)",
            "UTC-00:00 (Europe/London)",
            "UTC-00:00 (Atlantic/Reykjavik)",
            "UTC+01:00 (Europe/Amsterdam)",
            "UTC+01:00 (Europe/Belgrade)",
            "UTC+01:00 (Europe/Brussels)",
            "UTC+01:00 (Europe/Sarajevo)",
            "UTC+01:00 (Africa/Algiers)",
            "UTC+02:00 (Europe/Athens)",
            "UTC+02:00 (Asia/Beirut)",
            "UTC+02:00 (Africa/Cairo)",
            "UTC+02:00 (Asia/Damascus)",
            "UTC+02:00 (Africa/Harare)",
            "UTC+02:00 (Europe/Vilnius)",
            "UTC+02:00 (Asia/Jerusalem)",
            "UTC+02:00 (Asia/Amman)",
            "UTC+03:00 (Asia/Baghdad)",
            "UTC+03:00 (Europe/Minsk)",
            "UTC+03:00 (Asia/Kuwait)",
            "UTC+03:00 (Africa/Nairobi)",
            "UTC+03:00 (Asia/Istanbul)",
            "UTC+03:00 (Europe/Moscow)",
            "UTC+03:30 (Asia/Tehran)",
            "UTC+04:00 (Asia/Muscat)",
            "UTC+04:00 (Asia/Baku)",
            "UTC+04:00 (Asia/Tbilisi)",
            "UTC+04:00 (Asia/Yerevan)",
            "UTC+04:30 (Asia/Kabul)",
            "UTC+05:00 (Asia/Karachi)",
            "UTC+05:00 (Asia/Yekaterinburg)",
            "UTC+05:00 (Asia/Tashkent)",
            "UTC+05:30 (Asia/Kolkata)",
            "UTC+05:30 (Asia/Colombo)",
            "UTC+05:45 (Asia/Katmandu)",
            "UTC+06:00 (Asia/Dhaka)",
            "UTC+06:30 (Asia/Rangoon)",
            "UTC+07:00 (Asia/Bangkok)",
            "UTC+07:00 (Asia/Novosibirsk)",
            "UTC+07:00 (Asia/Krasnoyarsk)",
            "UTC+08:00 (Asia/Hong_Kong)",
            "UTC+08:00 (Asia/Kuala_Lumpur)",
            "UTC+08:00 (Australia/Perth)",
            "UTC+08:00 (Asia/Taipei)",
            "UTC+08:00 (Asia/Ulaanbaatar)",
            "UTC+08:00 (Asia/Irkutsk)",
            "UTC+09:00 (Asia/Tokyo)",
            "UTC+09:00 (Asia/Seoul)",
            "UTC+09:00 (Asia/Yakutsk)",
            "UTC+09:30 (Australia/Adelaide)",
            "UTC+09:30 (Australia/Darwin)",
            "UTC+10:00 (Australia/Brisbane)",
            "UTC+10:00 (Australia/Canberra)",
            "UTC+10:00 (Pacific/Guam)",
            "UTC+10:00 (Australia/Hobart)",
            "UTC+10:00 (Asia/Vladivostok)",
            "UTC+11:00 (Pacific/Noumea)",
            "UTC+11:00 (Asia/Magadan)",
            "UTC+12:00 (Pacific/Auckland)",
            "UTC+12:00 (Pacific/Fiji)",
            "UTC+12:00 (Asia/Kamchatka)",
            "UTC+13:00 (Pacific/Tongatapu)",
        ]
        self._attr_current_option = None
        TapoSelectEntity.__init__(
            self,
            "Timezone",
            entry,
            hass,
            config_entry,
            "mdi:map-clock",
        )

    def updateTapo(self, camData):

        if (
            not camData
            or camData["timezone_timezone"] is None
            or camData["timezone_zone_id"] is None
        ):
            self._attr_state = STATE_UNAVAILABLE
        else:
            self._attr_current_option = (
                f"{camData['timezone_timezone']} ({camData['timezone_zone_id']})"
            )
            self._attr_state = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        timezone_timezone = option.split(" ")[0]
        timezone_zone_id = option.split("(")[-1].strip(")")
        result = await self._hass.async_add_executor_job(
            self._controller.setTimezone, timezone_timezone, timezone_zone_id
        )
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = option
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()


class TapoNightVisionSelect(TapoSelectEntity):
    def __init__(
        self,
        entry: dict,
        hass: HomeAssistant,
        config_entry,
        entityName: str,
        nightVisionOptions: list,
        currentValueKey: str,
        method,
        specific_name=None,
        chn_id=None,
    ):
        self._attr_options = []
        self.method = method
        self.currentValueKey = currentValueKey
        self.chn_id = chn_id
        self.read_chn_id = str(chn_id) if chn_id else "1"
        for nightVisionCapability in nightVisionOptions:
            self._attr_options.append(getNightModeName(nightVisionCapability))

        self._attr_current_option = None
        TapoSelectEntity.__init__(
            self,
            f"{entityName}{" - " + specific_name if specific_name else ""}",
            entry,
            hass,
            config_entry,
            "mdi:theme-light-dark",
            "night_vision",
        )

    def updateTapo(self, camData):
        if not camData:
            self._attr_state = "unavailable"
        else:
            value = camData[self.currentValueKey]

            if isinstance(value, dict):
                value = value.get(self.read_chn_id)
            if value is None:
                self._attr_current_option = None
                self._attr_state = "unavailable"
            else:
                self._attr_current_option = getNightModeName(value)
                self._attr_state = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        LOGGER.debug("Calling " + self.method.__name__ + " with " + option + "...")
        result = await self._hass.async_add_executor_job(
            self.method,
            getNightModeValue(option),
            [self.chn_id] if self.chn_id else None,
        )
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = option
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()


class TapoLightFrequencySelect(TapoSelectEntity):
    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._attr_options = ["auto", "50", "60"]
        self._attr_current_option = None
        TapoSelectEntity.__init__(
            self, "Light Frequency", entry, hass, config_entry, "mdi:sine-wave"
        )

    def updateTapo(self, camData):
        if not camData:
            self._attr_state = STATE_UNAVAILABLE
        else:
            light_frequency_mode = camData["light_frequency_mode"]
            if isinstance(light_frequency_mode, dict):
                if "1" in light_frequency_mode:
                    light_frequency_mode = light_frequency_mode.get("1")
                else:
                    light_frequency_mode = next(
                        iter(light_frequency_mode.values()), None
                    )
            self._attr_current_option = light_frequency_mode
            self._attr_state = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        result = await self._hass.async_add_executor_job(
            self._controller.setLightFrequencyMode, option
        )
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = option
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()


class TapoAutomaticAlarmModeSelect(TapoSelectEntity):
    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._attr_options = ["both", "light", "sound", "off"]
        self._attr_current_option = None
        TapoSelectEntity.__init__(
            self,
            "Automatic Alarm",
            entry,
            hass,
            config_entry,
            "mdi:alarm-light-outline",
            "alarm",
        )

    def updateTapo(self, camData):
        if not camData:
            self._attr_state = STATE_UNAVAILABLE
        else:
            if camData["alarm_config"]["automatic"] == "off":
                self._attr_current_option = "off"
            else:
                light = "light" in camData["alarm_config"]["mode"]
                sound = "sound" in camData["alarm_config"]["mode"]
                if light and sound:
                    self._attr_current_option = "both"
                elif light and not sound:
                    self._attr_current_option = "light"
                else:
                    self._attr_current_option = "sound"
            self._attr_state = self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        LOGGER.debug(
            "setAlarm("
            + str(option != "off")
            + ", "
            + str(option == "off" or option in ["both", "sound"])
            + ", "
            + str(option == "off" or option in ["both", "light"])
            + ")"
        )
        result = await self.hass.async_add_executor_job(
            self._controller.setAlarm,
            option != "off",
            option == "off" or option in ["both", "sound"],
            option == "off" or option in ["both", "light"],
        )
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = option
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()


class TapoDualCamLinkage(TapoSelectEntity):
    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._options_map = {"Continuous tracking": 0, "Fixed view tracking": 1}
        self._attr_options = ["Continuous tracking", "Fixed view tracking", "off"]
        self._attr_current_option = None
        TapoSelectEntity.__init__(
            self, "Smart Dual Track Method", entry, hass, config_entry
        )

    def updateTapo(self, camData):
        LOGGER.debug(f"TapoDualCamLinkage updateTapo 1")
        if not camData:
            LOGGER.debug("TapoDualCamLinkage updateTapo 2")
            self._attr_state = STATE_UNAVAILABLE
            return
        LOGGER.debug(f"Enabled: {camData["dualCamLinkageEnabled"]}")
        LOGGER.debug(f"Type: {camData["dualCamLinkageType"]}")
        LOGGER.debug("TapoDualCamLinkage updateTapo 3")
        if camData["dualCamLinkageEnabled"] == "off":
            LOGGER.debug("TapoDualCamLinkage updateTapo 4")
            self._attr_current_option = "off"
        else:
            LOGGER.debug("TapoDualCamLinkage updateTapo 5")
            linkage_type = str(camData.get("dualCamLinkageType"))
            self._attr_current_option = next(
                (
                    option
                    for option, value in self._options_map.items()
                    if str(value) == linkage_type
                ),
                "off",
            )
        LOGGER.debug("TapoDualCamLinkage updateTapo 6")
        self._attr_state = self._attr_current_option
        LOGGER.debug("Updating TapoDualCamLinkage to: " + str(self._attr_state))

    async def async_select_option(self, option: str) -> None:
        result = await self.hass.async_add_executor_job(
            self._controller.setDualCamLinkage,
            option != "off",
            self._options_map[option] if option != "off" else None,
        )
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = option
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()


class TapoMotionDetectionSelect(TapoDetectionSelect):
    def __init__(self, entry, hass, config_entry, specific_name=None, chn_id=None):
        super().__init__(
            "Motion Detection",
            entry,
            hass,
            config_entry,
            "mdi:motion-sensor",
            "motion_detection",
            "motion_detection_enabled",
            "motion_detection_sensitivity",
            "setMotionDetection",
            True,
            specific_name,
            chn_id,
        )


class TapoPersonDetectionSelect(TapoDetectionSelect):
    def __init__(self, entry, hass, config_entry, specific_name=None, chn_id=None):
        super().__init__(
            "Person Detection",
            entry,
            hass,
            config_entry,
            "mdi:account-alert",
            "person_detection",
            "person_detection_enabled",
            "person_detection_sensitivity",
            "setPersonDetection",
            True,
            specific_name,
            chn_id,
        )


class TapoVehicleDetectionSelect(TapoDetectionSelect):
    def __init__(self, entry, hass, config_entry, specific_name=None, chn_id=None):
        super().__init__(
            "Vehicle Detection",
            entry,
            hass,
            config_entry,
            "mdi:truck-alert-outline",
            "vehicle_detection",
            "vehicle_detection_enabled",
            "vehicle_detection_sensitivity",
            "setVehicleDetection",
            True,
            specific_name,
            chn_id,
        )


class TapoBabyCryDetectionSelect(TapoDetectionSelect):
    def __init__(self, entry, hass, config_entry):
        super().__init__(
            "Baby Cry Detection",
            entry,
            hass,
            config_entry,
            "mdi:emoticon-cry-outline",
            "baby_cry_detection",
            "babyCry_detection_enabled",
            "babyCry_detection_sensitivity",
            "setBabyCryDetection",
        )


class TapoPetDetectionSelect(TapoDetectionSelect):
    def __init__(self, entry, hass, config_entry, specific_name=None, chn_id=None):
        super().__init__(
            "Pet Detection",
            entry,
            hass,
            config_entry,
            "mdi:paw",
            "pet_detection",
            "pet_detection_enabled",
            "pet_detection_sensitivity",
            "setPetDetection",
            True,
            specific_name,
            chn_id,
        )


class TapoBarkDetectionSelect(TapoDetectionSelect):
    def __init__(self, entry, hass, config_entry):
        super().__init__(
            "Bark Detection",
            entry,
            hass,
            config_entry,
            "mdi:dog",
            "bark_detection",
            "bark_detection_enabled",
            "bark_detection_sensitivity",
            "setBarkDetection",
        )


class TapoMeowDetectionSelect(TapoDetectionSelect):
    def __init__(self, entry, hass, config_entry):
        super().__init__(
            "Meow Detection",
            entry,
            hass,
            config_entry,
            "mdi:cat",
            "meow_detection",
            "meow_detection_enabled",
            "meow_detection_sensitivity",
            "setMeowDetection",
        )


class TapoGlassBreakDetectionSelect(TapoDetectionSelect):
    def __init__(self, entry, hass, config_entry):
        super().__init__(
            "Glass Break Detection",
            entry,
            hass,
            config_entry,
            "mdi:image-broken-variant",
            "glass_break_detection",
            "glass_detection_enabled",
            "glass_detection_sensitivity",
            "setGlassBreakDetection",
        )


class TapoTamperDetectionSelect(TapoDetectionSelect):
    def __init__(self, entry, hass, config_entry, specific_name=None, chn_id=None):
        super().__init__(
            "Tamper Detection",
            entry,
            hass,
            config_entry,
            "mdi:camera-enhance",
            "tamper_detection",
            "tamper_detection_enabled",
            "tamper_detection_sensitivity",
            "setTamperDetection",
            True,
            specific_name,
            chn_id,
        )


class TapoMoveToPresetSelect(TapoSelectEntity):
    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._presets = {}
        self._attr_options = []
        self._attr_current_option = None
        TapoSelectEntity.__init__(
            self, "Move to Preset", entry, hass, config_entry, "mdi:arrow-decision"
        )

    def updateTapo(self, camData):
        if not camData or camData["privacy_mode"] == "on":
            self._attr_state = STATE_UNAVAILABLE
        else:
            self._presets = camData["presets"]
            presetsConvertedToList = list(camData["presets"].values())
            if presetsConvertedToList:
                self._attr_options = list(camData["presets"].values())
                self._attr_current_option = None
                self._attr_state = self._attr_current_option
            else:
                self._attr_state = STATE_UNAVAILABLE

    async def async_select_option(self, option: str) -> None:
        foundKey = False
        for key, value in self._presets.items():
            if value == option:
                foundKey = key
                break
        if foundKey:
            await self.hass.async_add_executor_job(self._controller.setPreset, foundKey)
            self._attr_current_option = None
        else:
            LOGGER.error(f"Preset {option} does not exist.")

    @property
    def entity_category(self):
        return None


class TapoSirenTypeSelect(TapoSelectEntity):
    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._attr_options = entry["camData"]["alarm_siren_type_list"]
        self._attr_current_option = entry["camData"]["alarm_config"]["siren_type"]
        self.hub = entry["camData"]["alarm_is_hubSiren"]
        TapoSelectEntity.__init__(
            self,
            "Siren Type",
            entry,
            hass,
            config_entry,
            "mdi:home-sound-in-outline",
        )

    def updateTapo(self, camData):
        if not camData:
            self._attr_state = STATE_UNAVAILABLE
        else:
            if "siren_type" in camData["alarm_config"]:
                self._attr_current_option = camData["alarm_config"]["siren_type"]
            else:
                self._attr_state = STATE_UNAVAILABLE

            self._attr_state = self._attr_current_option
        LOGGER.debug("Updating TapoHubSirenTypeSelect to: " + str(self._attr_state))

    async def async_select_option(self, option: str) -> None:
        if self.hub:
            result = await self.hass.async_add_executor_job(
                self._controller.setHubSirenConfig, None, option
            )
        else:
            result = await self.hass.async_add_executor_job(
                self._controller.executeFunction,
                "setAlarmConfig",
                {
                    "msg_alarm": {
                        "siren_type": option,
                    }
                },
            )
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = option
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()


class TapoAlertTypeSelect(TapoSelectEntity):
    def __init__(self, entry: dict, hass: HomeAssistant, config_entry, startID=10):
        self.hub = entry["camData"]["alarm_is_hubSiren"]
        self.startID = startID
        self.alarm_siren_type_list = entry["camData"]["alarm_siren_type_list"]
        self.typeOfAlarm = entry["camData"]["alarm_config"]["typeOfAlarm"]

        if entry["camData"]["alarm_user_start_id"] is not None:
            self.startID = int(entry["camData"]["alarm_user_start_id"])

        TapoSelectEntity.__init__(
            self,
            "Siren Type",
            entry,
            hass,
            config_entry,
            "mdi:home-sound-in-outline",
        )

    def updateTapo(self, camData):
        if not camData:
            self._attr_state = STATE_UNAVAILABLE
        else:
            self._attr_options = camData["alarm_siren_type_list"]
            self.user_sounds = {}
            if camData["alarm_user_sounds"] is not None:
                for user_sound in camData["alarm_user_sounds"]:
                    if "name" in user_sound:
                        self._attr_options.append(user_sound["name"])
                        if "id" in user_sound:
                            self.user_sounds[user_sound["id"]] = user_sound["name"]

            self.alarm_enabled = camData["alarm_config"]["automatic"] == "on"
            self.alarm_mode = camData["alarm_config"]["mode"]
            currentSirenType = int(camData["alarm_config"]["siren_type"])
            if currentSirenType == 0:
                self._attr_current_option = camData["alarm_siren_type_list"][0]
            elif currentSirenType == 1:
                self._attr_current_option = camData["alarm_siren_type_list"][1]
            elif currentSirenType < self.startID:
                # on these cameras, the 0 is the first entry, but then it starts from 3
                # and it has 3 and 4 values, assuming -2 for the rest
                self._attr_current_option = camData["alarm_siren_type_list"][
                    currentSirenType - 2
                ]
            else:
                self._attr_current_option = self.user_sounds[currentSirenType]

            self._attr_state = self._attr_current_option
        LOGGER.debug("Updating TapoHubSirenTypeSelect to: " + str(self._attr_state))

    async def async_select_option(self, option: str) -> None:
        optionIndex = None
        for index in self.user_sounds:
            indexValue = self.user_sounds[index]
            if indexValue == option:
                optionIndex = index
        if optionIndex is None:
            optionIndex = self.alarm_siren_type_list.index(option)
            if optionIndex > 0 and optionIndex < self.startID:
                optionIndex += 2

        if self.typeOfAlarm == "getAlarm":
            result = await self._hass.async_add_executor_job(
                self._controller.setAlarm,
                self.alarm_enabled,
                "sound" in self.alarm_mode,
                "siren" in self.alarm_mode or "light" in self.alarm_mode,
                None,
                None,
                optionIndex,
            )
        else:
            # No idea if this works, cannot test on camera
            result = await self.hass.async_add_executor_job(
                self._controller.executeFunction,
                "setAlarmConfig",
                {
                    "msg_alarm": {
                        "siren_type": optionIndex,
                    }
                },
            )
        if "error_code" not in result or result["error_code"] == 0:
            self._attr_state = option
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()
