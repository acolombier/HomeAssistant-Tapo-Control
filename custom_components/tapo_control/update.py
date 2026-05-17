from typing import Callable

from homeassistant.core import HomeAssistant

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import device_registry as dr
import datetime

from .const import DOMAIN, LOGGER
from .utils import build_device_info
from .tapo.entities import TapoUpdateEntity


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
):
    entry = hass.data[DOMAIN][config_entry.entry_id]

    async def setupEntities(entry):
        updates = []
        if not entry["controller"].isKLAP:
            entry["updateEntity"] = TapoCamUpdate(entry, hass, entry)
            updates.append(entry["updateEntity"])

        return updates

    updates = await setupEntities(entry)
    for childDevice in entry["childDevices"]:
        updates.extend(await setupEntities(childDevice))

    async_add_entities(updates)


class TapoCamUpdate(UpdateEntity):
    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._in_progress = False
        self._hass = hass
        self._lastDataUpdate = 0
        # This is needed because some cameras still report normal firmware update process
        # just after hitting update, even if they are in progress, we need to give them time.
        self._installRequestedTime = 0
        TapoUpdateEntity.__init__(self, "Update", entry, hass, config_entry)

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

    def updateTapo(self, camData):
        # prevent instantinous internal refresh with old data triggering update
        # on this entity and cancelling in progress update
        LOGGER.debug("Updating firmware entity data")
        if camData and camData["updated"] > self._lastDataUpdate:
            LOGGER.debug("Processing new data from %s", camData["updated"])
            self._lastDataUpdate = camData["updated"]
            self._attributes = camData["basic_info"]
            if self._in_progress:
                LOGGER.debug("Firmware update status:")
                LOGGER.debug("Firmware status: %s", camData["firmwareUpdateStatus"])
                ts = datetime.datetime.utcnow().timestamp()
                if (
                    ts > self._installRequestedTime + 60
                    and "firmwareUpdateStatus" in camData
                    and "upgrade_status" in camData["firmwareUpdateStatus"]
                    and "state" in camData["firmwareUpdateStatus"]["upgrade_status"]
                    and camData["firmwareUpdateStatus"]["upgrade_status"]["state"]
                    == "normal"
                ):
                    LOGGER.debug(
                        "Update has been finished, updating information in integration..."
                    )
                    # Update Device Registry with new information
                    deviceRegistry = dr.async_get(self._hass)
                    newDeviceInfo = build_device_info(camData["basic_info"])
                    device = deviceRegistry.async_get_device(
                        newDeviceInfo["identifiers"]
                    )
                    deviceRegistry.async_update_device(
                        device.id, sw_version=newDeviceInfo["sw_version"]
                    )
                    # Reset check for firmware check
                    self._entry["lastFirmwareCheck"] = 0
                    self._in_progress = False
                    LOGGER.debug("Update has been fully completed.")

    async def async_added_to_hass(self) -> None:
        self._enabled = True

    async def async_will_remove_from_hass(self) -> None:
        self._enabled = False

    @property
    def supported_features(self):
        return (
            UpdateEntityFeature.INSTALL
            | UpdateEntityFeature.PROGRESS
            | UpdateEntityFeature.RELEASE_NOTES
        )

    async def async_release_notes(self) -> str:
        """Return the release notes."""
        if (
            self._entry["latestFirmwareVersion"]
            and "release_log" in self._entry["latestFirmwareVersion"]
        ):
            return self._entry["latestFirmwareVersion"]["release_log"].replace(
                "\\n", "\n"
            )
        else:
            return "No update available."

    @property
    def in_progress(self) -> bool:
        return self._in_progress

    @property
    def installed_version(self) -> str:
        return self._attributes["sw_version"]

    @property
    def latest_version(self) -> str:
        if (
            self._entry["latestFirmwareVersion"]
            and "version" in self._entry["latestFirmwareVersion"]
        ):
            LOGGER.debug("Latest version from cloud")
            LOGGER.debug("Latest firmware: %s", self._entry["latestFirmwareVersion"])
            return self._entry["latestFirmwareVersion"]["version"]
        else:
            LOGGER.debug("No cloud update available")
            LOGGER.debug("Current version: %s", self._attributes["sw_version"])
            return self._attributes["sw_version"]

    @property
    def release_summary(self) -> str:
        if (
            self._entry["latestFirmwareVersion"]
            and "release_log" in self._entry["latestFirmwareVersion"]
        ):
            LOGGER.debug("Release summary from cloud")
            maxLength = 255
            releaseLog = self._entry["latestFirmwareVersion"]["release_log"].replace(
                "\\n", "\n"
            )
            return (
                (releaseLog[: maxLength - 3] + "...")
                if len(releaseLog) > maxLength
                else releaseLog
            )
        else:
            LOGGER.debug("No release summary available")
            return None

    async def async_install(
        self,
        version,
        backup,
    ):
        LOGGER.debug("Firmware install triggered")
        LOGGER.debug("Version: %s", version)
        LOGGER.debug("Backup: %s", backup)
        try:
            await self.hass.async_add_executor_job(
                self._controller.startFirmwareUpgrade
            )
            self._installRequestedTime = datetime.datetime.utcnow().timestamp()
            self._in_progress = True
            LOGGER.debug("Firmware install in progress...")
        except Exception as e:
            LOGGER.exception("Firmware install failed: %s", e)
