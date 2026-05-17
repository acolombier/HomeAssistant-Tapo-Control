import asyncio
import datetime
import hashlib
import pathlib
import onvif
import os
import shutil
import socket
import urllib.parse
import uuid
import requests
import base64

from functools import partial
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from pytapo.media_stream.downloader import Downloader
from homeassistant.components.media_source.error import Unresolvable

from haffmpeg.tools import IMAGE_JPEG, ImageFrame
from onvif import ONVIFCamera
from pytapo import Tapo
from yarl import URL
from homeassistant.helpers.network import NoURLAvailableError, get_url

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.ffmpeg import DATA_FFMPEG

try:
    # Home Assistant moved EventManager from `event` to `event_manager` in 2026.5.
    from homeassistant.components.onvif.event_manager import EventManager
except ModuleNotFoundError:
    from homeassistant.components.onvif.event import EventManager
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_HOST,
)
from homeassistant.util import slugify, dt as dt_util

from .const import (
    BRAND,
    CONF_TRANSPORT_METHOD,
    CONTROL_PORT,
    DOMAIN_CONFIG,
    ENABLE_MEDIA_SYNC,
    ENABLE_MOTION_SENSOR,
    DOMAIN,
    ENABLE_WEBHOOKS,
    HOT_DIR_DELETE_TIME,
    LOGGER,
    CLOUD_PASSWORD,
    ENABLE_TIME_SYNC,
    CONF_CUSTOM_STREAM_HD,
    CONF_CUSTOM_STREAM_SD,
    CONF_CUSTOM_STREAM_6,
    CONF_CUSTOM_STREAM_7,
    MEDIA_CLEANUP_FILES_REMOVED_FROM_CAMERA,
    MEDIA_SYNC_COLD_STORAGE_PATH,
    MEDIA_SYNC_HOURS,
    TIME_SYNC_DST,
    TIME_SYNC_NDST,
    TPLINK_DOMAIN,
)

UUID = uuid.uuid4().hex


def _is_used_by_tplink(hass: HomeAssistant, host: str) -> bool:
    for entry in hass.config_entries.async_entries(
        TPLINK_DOMAIN, include_ignore=False, include_disabled=False
    ):
        if entry.data.get(CONF_HOST) != host:
            continue
        return True
    return False


def isUsingHTTPS(hass):
    try:
        base_url = get_url(hass, prefer_external=False)
    except NoURLAvailableError:
        try:
            base_url = get_url(hass, prefer_external=True)
        except NoURLAvailableError:
            return True
    LOGGER.debug("Detected base_url schema: %s", URL(base_url).scheme)
    return URL(base_url).scheme == "https"


def getStreamSource(entry, stream):
    custom_stream_hd = entry.data.get(CONF_CUSTOM_STREAM_HD, "")
    custom_stream_sd = entry.data.get(CONF_CUSTOM_STREAM_SD, "")
    telephoto_custom_stream6 = entry.data.get(CONF_CUSTOM_STREAM_6, "")
    telephoto_custom_stream7 = entry.data.get(CONF_CUSTOM_STREAM_7, "")
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    host = entry.data.get(CONF_IP_ADDRESS)
    if stream == "stream6" and telephoto_custom_stream6:
        return telephoto_custom_stream6
    if stream == "stream7" and telephoto_custom_stream7:
        return telephoto_custom_stream7
    if stream == "stream1" and custom_stream_hd:
        return custom_stream_hd
    if stream == "stream2" and custom_stream_sd:
        return custom_stream_sd
    username = urllib.parse.quote_plus(username)
    password = urllib.parse.quote_plus(password)
    streamURL = f"rtsp://{username}:{password}@{host}:554/{stream}"
    return streamURL


def pytapoLog(msg):
    LOGGER.debug("pytapo: %s", msg)


def pytapoWarnLog(msg):
    LOGGER.warning("pytapo: %s", msg)


def isKLAP(host, port, timeout=2):
    try:
        url = f"http://{host}:{port}"
        response = requests.get(url, timeout=timeout)
        return "200 OK" in response.text
    except requests.RequestException:
        return False


def registerController(
    host,
    control_port,
    username,
    password,
    password_cloud="",
    super_secret_key="",
    device_id=None,
    is_klap=None,
    hass=None,
):
    selected_transport_method = (
        hass.data.get(DOMAIN_CONFIG, {}).get(CONF_TRANSPORT_METHOD)
        if hass is not None
        else None
    )
    LOGGER.debug(
        "Creating Tapo controller with transport method %s.",
        selected_transport_method,
    )

    return Tapo(
        host,
        username,
        password,
        password_cloud,
        super_secret_key,
        device_id,
        reuseSession=False,
        printDebugInformation=pytapoLog,
        printWarnInformation=pytapoWarnLog,
        retryStok=False,
        controlPort=control_port,
        isKLAP=is_klap,
        hass=hass,
        transportMethod=selected_transport_method,
    )


def isOpen(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except Exception:
        return False


def getDataPath():
    return os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    )


def getColdDirPathForEntry(hass: HomeAssistant, entry_id: str):
    # Fast retrieval of path without file IO
    if (
        entry_id in hass.data[DOMAIN]
        and hass.data[DOMAIN][entry_id]["mediaSyncColdDir"] is not False
    ):
        return hass.data[DOMAIN][entry_id]["mediaSyncColdDir"].rstrip("/")

    coldDirPath = os.path.join(getDataPath(), f".storage/{DOMAIN}/{entry_id}/")
    if entry_id in hass.data[DOMAIN]:
        entry: ConfigEntry = hass.data[DOMAIN][entry_id]["entry"]
    else:  # if device is disabled, get entry from HA storage
        entry: ConfigEntry = hass.config_entries.async_get_entry(entry_id)

    media_sync_cold_storage_path = entry.data.get(MEDIA_SYNC_COLD_STORAGE_PATH)

    if not media_sync_cold_storage_path == "":
        coldDirPath = f"{media_sync_cold_storage_path}/"

    if entry_id in hass.data[DOMAIN]:
        pathlib.Path(coldDirPath + "/videos").mkdir(parents=True, exist_ok=True)
        pathlib.Path(coldDirPath + "/thumbs").mkdir(parents=True, exist_ok=True)
        hass.data[DOMAIN][entry_id]["mediaSyncColdDir"] = coldDirPath

    return coldDirPath.rstrip("/")


def getHotDirPathForEntry(hass: HomeAssistant, entry_id: str):
    if hass.data[DOMAIN][entry_id]["mediaSyncHotDir"] is not False:
        return hass.data[DOMAIN][entry_id]["mediaSyncHotDir"].rstrip("/")

    hotDirPath = os.path.join(getDataPath(), f"www/{DOMAIN}/{entry_id}/")

    if entry_id in hass.data[DOMAIN]:
        if not hass.data[DOMAIN][entry_id]["mediaSyncHotDir"]:
            pathlib.Path(hotDirPath + "/videos").mkdir(parents=True, exist_ok=True)
            pathlib.Path(hotDirPath + "/thumbs").mkdir(parents=True, exist_ok=True)
            hass.data[DOMAIN][entry_id]["mediaSyncHotDir"] = hotDirPath

        hotDirPath = hass.data[DOMAIN][entry_id]["mediaSyncHotDir"]
    return hotDirPath.rstrip("/")


async def getRecordings(hass, entryData, tapoController, date):
    LOGGER.debug("Getting recordings for date %s...", date)
    childID = ""
    if entryData["isChild"]:
        childID = entryData["camData"]["basic_info"]["dev_id"]
    recordingsForDay = []
    try:
        recordingsForDay = await hass.async_add_executor_job(
            tapoController.getRecordings, date
        )
        if recordingsForDay is not None:
            for recording in recordingsForDay:
                for recordingKey in recording:
                    entryData["mediaScanResult"][
                        getFileName(
                            recording[recordingKey]["startTime"],
                            recording[recordingKey]["endTime"],
                            False,
                            childID=childID,
                        )
                    ] = True
    except Exception as err:
        if "-71105" in str(err):
            LOGGER.debug(
                "Received error -71105 when browsing for recordings for day %s: %s. Assuming no recordings.",
                date,
                err,
            )
        else:
            raise err
    return recordingsForDay


def getEntryStorageFile(config_entry, child_id):
    return f"tapo_control_{config_entry.entry_id}{child_id}"


# todo: findMedia needs to run periodically
async def findMedia(hass, entryData, entry):
    entry_id = entry.entry_id
    LOGGER.debug("Finding media for %s...", entryData["name"])
    entryData["initialMediaScanDone"] = False
    childID = ""
    if entryData["isChild"]:
        childID = entryData["camData"]["basic_info"]["dev_id"]
    tapoController: Tapo = entryData["controller"]

    recordingsList = await hass.async_add_executor_job(tapoController.getRecordingsList)
    mediaScanResult = {}
    for searchResult in recordingsList:
        for key in searchResult:
            LOGGER.debug("Getting media for day %s...", searchResult[key]["date"])
            recordingsForDay = await getRecordings(
                hass, entryData, tapoController, searchResult[key]["date"]
            )
            LOGGER.debug(
                "Looping through recordings for day %s...", searchResult[key]["date"]
            )
            for recording in recordingsForDay:
                for recordingKey in recording:
                    filePathVideo = getColdFile(
                        hass,
                        entry_id,
                        recording[recordingKey]["startTime"],
                        recording[recordingKey]["endTime"],
                        "videos",
                        childID=childID,
                    )
                    mediaScanResult[
                        getFileName(
                            recording[recordingKey]["startTime"],
                            recording[recordingKey]["endTime"],
                            False,
                            childID=childID,
                        )
                    ] = True
                    if os.path.exists(filePathVideo):
                        await processDownload(
                            hass,
                            entry_id,
                            entryData,
                            recording[recordingKey]["startTime"],
                            recording[recordingKey]["endTime"],
                        )
    LOGGER.debug("Found media for %s.", entryData["name"])
    entryData["mediaScanResult"] = mediaScanResult
    entryData["initialMediaScanDone"] = True

    await mediaCleanup(hass, entry, entryData)


async def processDownload(
    hass, entry_id: int, entryData: dict, startDate: int, endDate: int
):
    childID = ""
    if entryData["isChild"]:
        childID = entryData["camData"]["basic_info"]["dev_id"]
    filePath = getFileName(startDate, endDate, False, childID=childID)

    coldFilePath = getColdFile(
        hass, entry_id, startDate, endDate, "videos", childID=childID
    )

    if not os.path.exists(coldFilePath):
        raise Unresolvable("Failed to get file from cold storage: " + coldFilePath)

    if filePath not in entryData["downloadedStreams"]:
        entryData["downloadedStreams"][filePath] = {
            startDate: startDate,
            endDate: endDate,
        }
    mediaScanName = getFileName(startDate, endDate, False, childID=childID)
    if mediaScanName not in entryData["mediaScanResult"]:
        entryData["mediaScanResult"][mediaScanName] = True

    await generateThumb(hass, entry_id, startDate, endDate, childID=childID)


async def generateThumb(hass, entry_id, startDate: int, endDate: int, childID=""):
    filePathThumb = getColdFile(
        hass, entry_id, startDate, endDate, "thumbs", childID=childID
    )
    if not os.path.exists(filePathThumb):
        filePathVideo = getColdFile(
            hass, entry_id, startDate, endDate, "videos", childID=childID
        )
        _ffmpeg = hass.data[DATA_FFMPEG]
        ffmpeg = ImageFrame(_ffmpeg.binary)
        image = await asyncio.shield(
            ffmpeg.get_image(
                filePathVideo,
                output_format=IMAGE_JPEG,
            )
        )
        openHandler = await hass.async_add_executor_job(open, filePathThumb, "wb")
        with openHandler as binary_file:
            binary_file.write(image)
    return filePathThumb


# todo: findMedia needs to run periodically because of this function!!!
async def deleteFilesNoLongerPresentInCamera(
    hass, entry_id, entryData, extension, folder
):
    LOGGER.debug("Checking for files no longer present in camera")
    childID = ""
    if entryData["isChild"]:
        childID = entryData["camData"]["basic_info"]["dev_id"]
    if not entryData["initialMediaScanDone"]:
        LOGGER.debug("Initial media scan has not completed yet")
        return
    LOGGER.debug("Initial scanning done.")
    coldDirPath = getColdDirPathForEntry(hass, entry_id)
    path = coldDirPath + "/" + folder + "/"
    if not os.path.exists(path):
        LOGGER.debug("Path %s does not exist", path)
        return
    LOGGER.debug("Path exists")
    listDirFiles = await hass.async_add_executor_job(os.listdir, path)
    for f in listDirFiles:
        fileName = f.replace(extension, "")
        filePath = os.path.join(path, f)
        if (
            (not entryData["isChild"] and fileName.count("-") >= 1)
            or (
                (entryData["isChild"] and fileName.count("-") >= 2)
                and childID in fileName
            )
            and fileName not in entryData["mediaScanResult"]
        ):
            LOGGER.debug(
                "Removing %s (%s)...",
                filePath,
                fileName,
            )
            entryData["downloadedStreams"].pop(
                fileName,
                None,
            )
            LOGGER.debug("Removing %s", filePath)
            os.remove(filePath)


async def deleteColdFilesOlderThanMaxSyncTime(
    hass, entry, entryData, extension, folder
):
    childID = ""
    if entryData["isChild"]:
        childID = entryData["camData"]["basic_info"]["dev_id"]
    entry_id = entry.entry_id
    mediaSyncHours = entry.data.get(MEDIA_SYNC_HOURS)

    if mediaSyncHours != "":
        coldDirPath = getColdDirPathForEntry(hass, entry_id)
        tapoController: Tapo = entryData["controller"]
        timeCorrection = await hass.async_add_executor_job(
            tapoController.getTimeCorrection
        )
        mediaSyncTime = int(mediaSyncHours) * 60 * 60
        entry_id = entry.entry_id
        ts = datetime.datetime.utcnow().timestamp()
        if os.path.exists(coldDirPath + "/" + folder + "/"):
            listDirFiles = await hass.async_add_executor_job(
                os.listdir, coldDirPath + "/" + folder + "/"
            )
            for f in listDirFiles:
                fileName = f.replace(extension, "")
                filePath = os.path.join(coldDirPath + "/" + folder + "/", f)
                splitFileName = fileName.split("-")
                isOldFormat = (
                    not entryData["isChild"] and fileName.count("-") == 1
                ) or (
                    (entryData["isChild"] and fileName.count("-") == 2)
                    and childID in fileName
                )
                isNewFormat = (
                    not entryData["isChild"] and fileName.count("-") == 4
                ) or (
                    (entryData["isChild"] and fileName.count("-") == 5)
                    and childID in fileName
                )
                if isOldFormat:
                    endTS = int(splitFileName[-1])
                elif isNewFormat:
                    isoPart = (
                        fileName.replace(childID + "-", "") if childID else fileName
                    )
                    endTS = int(
                        datetime.datetime.strptime(
                            isoPart, "%Y-%m-%d_%H-%M-%S"
                        ).timestamp()
                    )
                else:
                    LOGGER.debug(
                        "Ignoring %s (%s) because of incorrect file name format...",
                        filePath,
                        fileName,
                    )
                    continue

                last_modified = os.stat(filePath).st_mtime
                if (endTS < (int(ts) - (int(mediaSyncTime) + timeCorrection))) and (
                    ts - last_modified > int(mediaSyncTime)
                ):
                    LOGGER.debug(
                        "Removing %s (%s) because it is older than %s seconds...",
                        filePath,
                        fileName,
                        mediaSyncTime,
                    )
                    entryData["downloadedStreams"].pop(
                        fileName,
                        None,
                    )
                    LOGGER.debug("Removing %s", filePath)
                    os.remove(filePath)


async def mediaCleanup(hass, entry, deviceData):
    entry_id = entry.entry_id

    childID = ""
    if deviceData["isChild"]:
        childID = deviceData["camData"]["basic_info"]["dev_id"]

    LOGGER.debug(
        "Initiating media cleanup for entity %s, child ID: %s...",
        entry_id,
        childID,
    )

    ts = datetime.datetime.utcnow().timestamp()
    deviceData["lastMediaCleanup"] = ts
    hotDirPath = getHotDirPathForEntry(hass, entry_id)

    # clean cache files from old HA instance
    LOGGER.debug(
        "Removing cache files from old HA instances for entity %s, child ID: %s...",
        entry_id,
        childID,
    )

    await deleteFilesNotIncluding(hass, hotDirPath + "/videos/", UUID)
    await deleteFilesNotIncluding(hass, hotDirPath + "/thumbs/", UUID)

    if entry.data.get(MEDIA_CLEANUP_FILES_REMOVED_FROM_CAMERA, True):
        LOGGER.debug("Removing files that are not on camera anymore")
        # await deleteFilesNoLongerPresentInCamera(
        #     hass, entry_id, deviceData, ".mp4", "videos"
        # )
        # await deleteFilesNoLongerPresentInCamera(
        #     hass, entry_id, deviceData, ".jpg", "thumbs"
        # )
    else:
        LOGGER.debug(
            "Not removing files that are not on camera anymore as requested by user"
        )

    await deleteColdFilesOlderThanMaxSyncTime(hass, entry, deviceData, ".mp4", "videos")
    await deleteColdFilesOlderThanMaxSyncTime(hass, entry, deviceData, ".jpg", "thumbs")

    # Delete everything other than HOT_DIR_DELETE_TIME seconds from hot storage
    LOGGER.debug(
        "Deleting hot storage files older than %s seconds for entity %s, child ID: %s...",
        HOT_DIR_DELETE_TIME,
        entry_id,
        childID,
    )
    await deleteFilesOlderThan(hass, hotDirPath + "/videos/", HOT_DIR_DELETE_TIME)
    await deleteFilesOlderThan(hass, hotDirPath + "/thumbs/", HOT_DIR_DELETE_TIME)


async def deleteDir(hass, dirPath):
    if (
        os.path.exists(dirPath)
        and os.path.isdir(dirPath)
        and dirPath != "/"
        and "tapo_control/" in dirPath
    ):
        LOGGER.debug("Deleting folder %s...", dirPath)
        await hass.async_add_executor_job(shutil.rmtree, dirPath)


async def deleteFilesOlderThan(hass: HomeAssistant, dirPath, deleteOlderThan):
    now = datetime.datetime.utcnow().timestamp()
    if os.path.exists(dirPath):

        listDirFiles = await hass.async_add_executor_job(os.listdir, dirPath)
        for f in listDirFiles:
            filePath = os.path.join(dirPath, f)
            last_modified = os.stat(filePath).st_mtime
            if now - last_modified > deleteOlderThan:
                LOGGER.debug("Removing %s", filePath)
                os.remove(filePath)


async def deleteFilesNotIncluding(hass: HomeAssistant, dirPath, includingString):
    if os.path.exists(dirPath):
        listDirFiles = await hass.async_add_executor_job(os.listdir, dirPath)
        for f in listDirFiles:
            filePath = os.path.join(dirPath, f)
            if includingString not in filePath:
                LOGGER.debug("Removing %s", filePath)
                os.remove(filePath)


def processDownloadStatus(
    entryData,
    date: str,
    allRecordingsCount: int,
    recordingCount: int = False,
):
    def processUpdate(status):
        LOGGER.debug("Download status: %s", status)
        if isinstance(status, str):
            entryData["downloadProgress"] = status
        else:
            entryData["downloadProgress"] = (
                status["currentAction"]
                + " "
                + date
                + (
                    f" ({recordingCount} / {allRecordingsCount})"
                    if recordingCount is not False
                    else ""
                )
                + (
                    ": " + str(round(status["progress"])) + " / " + str(status["total"])
                    if status["total"] > 0
                    else ""
                )
            )

    return processUpdate


def _getOldFileName(startDate: int, endDate: int, childID=""):
    return (
        ((str(childID) + "-") if childID != "" else "")
        + str(startDate)
        + "-"
        + str(endDate)
    )


def getFileName(startDate: int, endDate: int, encrypted=False, childID=""):
    startDate = int(startDate)
    endDate = int(endDate)
    if encrypted:
        return hashlib.md5(
            (str(childID) + str(startDate) + str(endDate)).encode()
        ).hexdigest()
    else:
        prefix = (str(childID) + "-") if childID != "" else ""
        if startDate > 0:
            return prefix + datetime.datetime.fromtimestamp(
                startDate, tz=datetime.timezone.utc
            ).strftime("%Y-%m-%d_%H-%M-%S")
        else:
            return prefix + str(startDate) + "-" + str(endDate)


def getColdFile(
    hass: HomeAssistant,
    entry_id: str,
    startDate: int,
    endDate: int,
    folder: str,
    childID="",
):
    coldDirPath = getColdDirPathForEntry(hass, entry_id)
    fileName = getFileName(startDate, endDate, False, childID=childID)
    oldFileName = _getOldFileName(startDate, endDate, childID=childID)

    if folder == "videos":
        extension = ".mp4"
    elif folder == "thumbs":
        extension = ".jpg"
    else:
        raise Unresolvable("Incorrect folder specified: " + folder)

    coldFilePath = coldDirPath + "/" + folder + "/" + fileName + extension
    oldColdFilePath = coldDirPath + "/" + folder + "/" + oldFileName + extension

    if os.path.exists(oldColdFilePath):
        return oldColdFilePath

    return coldFilePath


async def getHotFile(
    hass: HomeAssistant,
    entry_id: str,
    startDate: int,
    endDate: int,
    folder: str,
    childID="",
):
    coldFilePath = getColdFile(
        hass, entry_id, startDate, endDate, folder, childID=childID
    )
    hotDirPath = getHotDirPathForEntry(hass, entry_id)
    extension = pathlib.Path(coldFilePath).suffix
    fileNameEncrypted = getFileName(startDate, endDate, True, childID=childID)
    hotFilePath = f"{hotDirPath}/{folder}/{fileNameEncrypted}{UUID}{extension}"

    if not os.path.exists(hotFilePath):
        if not os.path.exists(coldFilePath):
            raise Unresolvable("Failed to get file from cold storage: " + coldFilePath)
        await hass.async_add_executor_job(shutil.copyfile, coldFilePath, hotFilePath)
    return hotFilePath


async def getWebFile(
    hass: HomeAssistant,
    entry_id: str,
    startDate: int,
    endDate: int,
    folder: str,
    childID="",
):
    hotFilePath = await getHotFile(
        hass, entry_id, startDate, endDate, folder, childID=childID
    )
    fileWebPath = hotFilePath[hotFilePath.index("/www/") + 5 :]  # remove ./www/

    return f"/local/{fileWebPath}"


async def getRecording(
    hass: HomeAssistant,
    tapo: Tapo,
    entry_id: str,
    entryData: dict,
    date: str,
    startDate: int,
    endDate: int,
    recordingCount: int = False,
    totalRecordingCount: int = False,
) -> str:
    timeCorrection = await hass.async_add_executor_job(tapo.getTimeCorrection)
    startDate = int(startDate)
    endDate = int(endDate)

    childID = ""
    if entryData["isChild"]:
        childID = entryData["camData"]["basic_info"]["dev_id"]

    coldDirPath = getColdDirPathForEntry(hass, entry_id)
    downloadUID = getFileName(startDate, endDate, False, childID=childID)

    coldFilePath = getColdFile(
        hass, entry_id, startDate, endDate, "videos", childID=childID
    )
    if not os.path.exists(coldFilePath):
        # this NEEDS to happen otherwise camera does not send data!
        allRecordings = await hass.async_add_executor_job(tapo.getRecordings, date)
        downloader = Downloader(
            tapo,
            startDate,
            endDate,
            timeCorrection,
            coldDirPath + "/videos/",
            0,
            None,
            None,
            downloadUID + ".mp4",
        )

        entryData["isDownloadingStream"] = True
        LOGGER.info("Downloading %s...", coldFilePath)
        downloadedFile = await downloader.downloadFile(
            processDownloadStatus(
                entryData,
                date,
                (
                    len(allRecordings)
                    if not totalRecordingCount
                    else totalRecordingCount
                ),
                recordingCount if recordingCount is not False else False,
            )
        )
        entryData["isDownloadingStream"] = False
        if downloadedFile["currentAction"] == "Recording in progress":
            raise Unresolvable("Recording is currently in progress.")
        LOGGER.info("Downloaded %s. Emitting event %s", coldFilePath, entry_id)

        hass.bus.fire(
            "tapo_control_media_downloaded",
            {
                "entry_id": entry_id,
                "startDate": startDate,
                "endDate": endDate,
                "filePath": coldFilePath,
            },
        )

    await processDownload(hass, entry_id, entryData, startDate, endDate)

    return coldFilePath


def areCameraPortsOpened(host, controlPort=443):
    return isOpen(host, int(controlPort)) and isOpen(host, 554) and isOpen(host, 2020)


async def isRtspStreamWorking(
    hass, host, username, password, stream: str | None = None
):
    LOGGER.debug("Testing RTSP stream for %s", host)
    _ffmpeg = hass.data[DATA_FFMPEG]
    LOGGER.debug("Creating image frame for %s", host)
    ffmpeg = ImageFrame(_ffmpeg.binary)
    LOGGER.debug("Encoding username and password for %s", host)
    username = urllib.parse.quote_plus(username)
    password = urllib.parse.quote_plus(password)

    stream_path = stream or "stream1"
    auth = f"{username}:{password}@" if username or password else ""
    streaming_url = f"rtsp://{auth}{host}:554/{stream_path}"

    safe_streaming_url = streaming_url
    if username:
        safe_streaming_url = safe_streaming_url.replace(username, "HIDDEN_USERNAME")
    if password:
        safe_streaming_url = safe_streaming_url.replace(password, "HIDDEN_PASSWORD")

    LOGGER.debug(
        "Getting image from %s for %s",
        safe_streaming_url,
        host,
    )
    image = await asyncio.shield(
        ffmpeg.get_image(
            streaming_url,
            output_format=IMAGE_JPEG,
        )
    )
    LOGGER.debug(
        "Image data received for %s",
        host,
    )
    return not image == b""


def result_has_error(result):
    if (
        result is not False
        and "result" in result
        and "responses" in result["result"]
        and any(
            map(
                lambda x: "error_code" not in x or x["error_code"] == 0,
                result["result"]["responses"],
            )
        )
    ):
        return False
    if result is not False and (
        "error_code" not in result or result["error_code"] == 0
    ):
        return False
    else:
        return True


async def initOnvifEvents(hass, host, username, password):
    device = ONVIFCamera(
        host,
        2020,
        username,
        password,
        f"{os.path.dirname(onvif.__file__)}/wsdl/",
        no_cache=True,
    )
    try:
        LOGGER.debug("Creating onvif connection...")
        await device.update_xaddrs()
        LOGGER.debug("Connection established.")
        device_mgmt = await device.create_devicemgmt_service()
        LOGGER.debug("Getting device information...")
        device_info = await device_mgmt.GetDeviceInformation()
        LOGGER.debug("Got device information.")
        if "Manufacturer" not in device_info:
            raise Exception("Onvif connection has failed.")

        return {"device": device, "device_mgmt": device_mgmt}
    except Exception as e:
        LOGGER.warning("ONVIF connection failed: %s", e, exc_info=True)

    return False


def tryParseInt(value):
    try:
        return int(value)
    except Exception as e:
        LOGGER.debug("Couldnt parse as integer: %s", str(e))
        return None


def getDataForController(hass, entry, controller):
    for controller in hass.data[DOMAIN][entry.entry_id]["allControllers"]:
        if controller == hass.data[DOMAIN][entry.entry_id]["controller"]:
            return hass.data[DOMAIN][entry.entry_id]
        elif (
            "childDevices" in hass.data[DOMAIN][entry.entry_id]
            and hass.data[DOMAIN][entry.entry_id]["childDevices"] is not False
        ):
            for childDevice in hass.data[DOMAIN][entry.entry_id]["childDevices"]:
                if controller == childDevice["controller"]:
                    return childDevice


def getNightModeMap():
    return {
        "inf_night_vision": "Infrared Mode",
        "wtl_night_vision": "Full Color Mode",
        "md_night_vision": "Smart Mode",
        "dbl_night_vision": "Doorbell Mode",
        "shed_night_vision": "Scheduled Mode",
    }


def getNightModeName(value: str):
    nightModeMap = getNightModeMap()
    if value in nightModeMap:
        return nightModeMap[value]
    return value


def getNightModeValue(value: str):
    night_mode_map = getNightModeMap()
    for key, val in night_mode_map.items():
        if val == value:
            return key
    return value


def convertBasicInfo(basicInfo):
    convertedBasicInfo = basicInfo
    convertedBasicInfo["device_alias"] = base64.b64decode(basicInfo["nickname"]).decode(
        "utf-8"
    )
    convertedBasicInfo["device_model"] = basicInfo["model"]
    convertedBasicInfo["sw_version"] = basicInfo["fw_ver"]
    convertedBasicInfo["hw_version"] = basicInfo["hw_ver"]
    return convertedBasicInfo


def getIP(data):
    # KLAP report IP in this function
    if (
        "basic_info" in data
        and data["basic_info"] is not None
        and "ip" in data["basic_info"]
    ):
        return data["basic_info"]["ip"]
    # cameras report IP in this function
    elif (
        "network_ip_info" in data
        and data["network_ip_info"] is not None
        and "network" in data["network_ip_info"]
        and "wan" in data["network_ip_info"]["network"]
        and "ipaddr" in data["network_ip_info"]["network"]["wan"]
    ):
        return data["network_ip_info"]["network"]["wan"]["ipaddr"]
    return False


def motionSensitivityFromData(motionDet):
    sensitivity_map = {"low": "low", "medium": "normal", "high": "high"}
    digital_map = {"20": "low", "50": "normal", "80": "high"}

    sensitivity = motionDet.get("sensitivity")
    if sensitivity in sensitivity_map:
        return sensitivity_map[sensitivity]

    return digital_map.get(motionDet.get("digital_sensitivity"))


def detectionSensitivityFromPercentage(value):
    sensitivity = tryParseInt(value)
    if sensitivity is None:
        return None
    if sensitivity <= 33:
        return "low"
    if sensitivity <= 66:
        return "normal"
    return "high"


def extractFieldByChannel(container, field):
    if not isinstance(container, dict):
        return None
    if field in container:
        return container[field]
    per_channel = {}
    for chn_key, chn_value in container.items():
        if isinstance(chn_value, dict) and field in chn_value:
            per_channel[str(chn_key)] = chn_value[field]
    if per_channel:
        return per_channel
    return None


def getLdcImageSection(ldc_data, section):
    if not ldc_data:
        return None
    entries = ldc_data if isinstance(ldc_data, list) else [ldc_data]
    result = None
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        image = entry.get("image")
        if not isinstance(image, dict):
            continue
        section_data = image.get(section)
        if section_data is None:
            continue
        if result is None:
            result = section_data
        elif isinstance(result, dict) and isinstance(section_data, dict):
            merged = dict(result)
            merged.update(section_data)
            result = merged
        else:
            result = section_data
    return result


def ldcHasField(rawData, section, field):
    ldc_data = rawData.get("getLdc", [])
    entries = ldc_data if isinstance(ldc_data, list) else [ldc_data]
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        image = entry.get("image")
        if not isinstance(image, dict):
            continue
        section_data = image.get(section)
        if not isinstance(section_data, dict):
            continue
        if field in section_data:
            return True
        for value in section_data.values():
            if isinstance(value, dict) and field in value:
                return True
    return False


async def getCamData(hass, controller, chInfo=None):
    LOGGER.debug("Fetching camera data")
    return camData


def convert_to_timestamp(date_string):
    date_format = "%Y%m%d"
    try:
        date = datetime.datetime.strptime(date_string, date_format)
        timestamp = datetime.datetime.timestamp(date)
        return int(timestamp)
    except ValueError:
        raise Exception(
            "Invalid date format. Please provide a date in the format 'YYYYMMDD'."
        )


async def update_listener(hass, entry):
    """Handle options update."""
    host = entry.data.get(CONF_IP_ADDRESS)
    controlPort = entry.data.get(CONTROL_PORT)
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    motionSensor = entry.data.get(ENABLE_MOTION_SENSOR)
    enableTimeSync = entry.data.get(ENABLE_TIME_SYNC)
    cloud_password = entry.data.get(CLOUD_PASSWORD)
    try:
        newUUID = hashlib.md5(
            (str(host) + str(username) + str(password) + str(cloud_password)).encode()
        ).hexdigest()
        # only update controller if auth data changed
        if newUUID != hass.data[DOMAIN][entry.entry_id]["uuid"]:
            hass.data[DOMAIN][entry.entry_id]["uuid"] = newUUID
            if (
                hass.data[DOMAIN][entry.entry_id]["controller"]
                in hass.data[DOMAIN][entry.entry_id]["allControllers"]
            ):
                hass.data[DOMAIN][entry.entry_id]["allControllers"].remove(
                    hass.data[DOMAIN][entry.entry_id]["controller"]
                )
            if cloud_password != "":
                tapoController = await hass.async_add_executor_job(
                    registerController,
                    host,
                    controlPort,
                    "admin",
                    cloud_password,
                    "",
                    "",
                    None,
                    None,
                    hass,
                )
            else:
                tapoController = await hass.async_add_executor_job(
                    registerController,
                    host,
                    controlPort,
                    username,
                    password,
                    "",
                    "",
                    None,
                    None,
                    hass,
                )
            hass.data[DOMAIN][entry.entry_id]["usingCloudPassword"] = (
                cloud_password != ""
            )
            hass.data[DOMAIN][entry.entry_id]["controller"] = tapoController
            hass.data[DOMAIN][entry.entry_id]["allControllers"].append(tapoController)
    except Exception:
        LOGGER.exception(
            "Authentication to Tapo camera failed. Please restart the camera and try again."
        )

    for entity in hass.data[DOMAIN][entry.entry_id]["entities"]:
        if "_host" in entity:
            entity._host = host
        if "_username" in entity:
            entity._username = username
        if "_password" in entity:
            entity._password = password
    if hass.data[DOMAIN][entry.entry_id]["events"]:
        await hass.data[DOMAIN][entry.entry_id]["events"].async_stop()
    if hass.data[DOMAIN][entry.entry_id]["motionSensorCreated"]:
        await hass.config_entries.async_forward_entry_unload(entry, "binary_sensor")
        hass.data[DOMAIN][entry.entry_id]["motionSensorCreated"] = False
    if motionSensor or enableTimeSync:
        onvifDevice = await initOnvifEvents(hass, host, username, password)
        hass.data[DOMAIN][entry.entry_id]["eventsDevice"] = onvifDevice["device"]
        hass.data[DOMAIN][entry.entry_id]["onvifManagement"] = onvifDevice[
            "device_mgmt"
        ]
        if motionSensor:
            await setupOnvif(hass, entry)


async def getLatestFirmwareVersion(hass, config_entry, entry, controller):
    entry["lastFirmwareCheck"] = datetime.datetime.utcnow().timestamp()
    try:
        updateInfo = await hass.async_add_executor_job(controller.isUpdateAvailable)
        if (
            "version"
            in updateInfo["result"]["responses"][1]["result"]["cloud_config"][
                "upgrade_info"
            ]
        ):
            updateInfo = updateInfo["result"]["responses"][1]["result"]["cloud_config"][
                "upgrade_info"
            ]
        else:
            updateInfo = False
    except Exception:
        updateInfo = False
    return updateInfo


async def syncTime(hass, entry_id):
    device_mgmt = hass.data[DOMAIN][entry_id]["onvifManagement"]
    if device_mgmt:
        LOGGER.debug(
            "Syncing time for %s, timezone offset is %s...",
            hass.data[DOMAIN][entry_id]["name"],
            hass.data[DOMAIN][entry_id]["timezoneOffset"],
        )
        isDST = dt_util.now().dst() != datetime.timedelta(0)

        timeSyncDST = int(hass.data[DOMAIN][entry_id][TIME_SYNC_DST])
        timeSyncNDST = int(hass.data[DOMAIN][entry_id][TIME_SYNC_NDST])

        LOGGER.debug("Is DST: %s", isDST)
        LOGGER.debug("DST offset: %s", timeSyncDST)
        LOGGER.debug("Non DST offset: %s", timeSyncNDST)
        now = dt_util.utcnow()

        LOGGER.debug("UTC Home Assistant time: %s", now)
        LOGGER.debug("Local Home Assistant time: %s", dt_util.as_local(now))

        adjustment_hours = timeSyncDST if isDST else timeSyncNDST
        adjusted_time = now + datetime.timedelta(hours=adjustment_hours)

        time_params = device_mgmt.create_type("SetSystemDateAndTime")
        time_params.DateTimeType = "Manual"
        time_params.DaylightSavings = isDST
        time_params.UTCDateTime = {
            "Date": {
                "Year": adjusted_time.year,
                "Month": adjusted_time.month,
                "Day": adjusted_time.day,
            },
            "Time": {
                "Hour": adjusted_time.hour,
                "Minute": adjusted_time.minute,
                "Second": adjusted_time.second,
            },
        }
        LOGGER.debug(
            "Sending time parameters to %s:", hass.data[DOMAIN][entry_id]["name"]
        )
        LOGGER.debug("Time parameters: %s", time_params)
        await device_mgmt.SetSystemDateAndTime(time_params)
        LOGGER.debug(
            "Finished synchronizing time successfully. Setting last time sync to: %s",
            now,
        )
        hass.data[DOMAIN][entry_id]["lastTimeSync"] = now.timestamp()
    else:
        LOGGER.warning(
            "Onvif has not been initialized yet, unable to synchronize time."
        )


async def setupOnvif(hass, entry):
    LOGGER.debug("Setting up ONVIF events")
    if hass.data[DOMAIN][entry.entry_id]["eventsDevice"]:
        LOGGER.debug("Setting up onvif...")
        hass.data[DOMAIN][entry.entry_id]["events"] = EventManager(
            hass,
            hass.data[DOMAIN][entry.entry_id]["eventsDevice"],
            entry,
            hass.data[DOMAIN][entry.entry_id]["name"],
        )

        hass.data[DOMAIN][entry.entry_id]["eventsSetup"] = await setupEvents(
            hass, entry
        )


async def setupEvents(hass, config_entry):
    LOGGER.debug("Setting up events")
    shouldUseWebhooks = not isUsingHTTPS(hass) and config_entry.data.get(
        ENABLE_WEBHOOKS
    )
    LOGGER.debug("Using HTTPS: %s", isUsingHTTPS(hass))
    LOGGER.debug("Webhook enabled: %s", config_entry.data.get(ENABLE_WEBHOOKS) is True)
    LOGGER.debug("Using Webhooks: %s", shouldUseWebhooks)
    if (
        hass.data[DOMAIN][config_entry.entry_id]["events"] is not False
        and not hass.data[DOMAIN][config_entry.entry_id]["events"].started
    ):
        LOGGER.debug("Setting up events...")
        events = hass.data[DOMAIN][config_entry.entry_id]["events"]
        onvif_capabilities = await hass.data[DOMAIN][config_entry.entry_id][
            "eventsDevice"
        ].get_capabilities()
        onvif_capabilities = onvif_capabilities or {}
        pull_point_support = onvif_capabilities.get("Events", {}).get(
            "WSPullPointSupport"
        )
        LOGGER.debug("WSPullPointSupport: %s", pull_point_support)
        if await events.async_start(pull_point_support is not False, shouldUseWebhooks):
            LOGGER.debug("Events started.")
            if not hass.data[DOMAIN][config_entry.entry_id]["motionSensorCreated"]:
                hass.data[DOMAIN][config_entry.entry_id]["motionSensorCreated"] = True
                if hass.data[DOMAIN][config_entry.entry_id]["eventsListener"]:
                    hass.data[DOMAIN][config_entry.entry_id][
                        "eventsListener"
                    ].createBinarySensor()
                else:
                    LOGGER.error(
                        "Trying to create motion sensor but motion listener not set up!"
                    )

                LOGGER.debug(
                    "Binary sensor creation for motion has been forwarded to component."
                )
            return True
        else:
            return False


def build_device_info(attributes: dict) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, slugify(f"{attributes['mac']}_tapo_control"))},
        connections={("mac", attributes["mac"])},
        name=attributes["device_alias"],
        manufacturer=BRAND,
        model=attributes["device_model"],
        sw_version=attributes["sw_version"],
        hw_version=attributes["hw_version"],
    )


PYTAPO_FUNCTION_MAP = {
    "getPrivacyMode": ["getLensMaskConfig"],
    "getNotificationsEnabled": ["getMsgPushConfig"],
    "getBasicInfo": ["getDeviceInfo"],
    "getMotionDetection": ["getDetectionConfig"],
    "getPersonDetection": ["getPersonDetectionConfig"],
    "getVehicleDetection": ["getVehicleDetectionConfig"],
    "getBabyCryDetection": ["getBCDConfig"],
    "getPetDetection": ["getPetDetectionConfig"],
    "getBarkDetection": ["getBarkDetectionConfig"],
    "getMeowDetection": ["getMeowDetectionConfig"],
    "getGlassBreakDetection": ["getGlassDetectionConfig"],
    "getTamperDetection": ["getTamperDetectionConfig"],
    "getLdc": ["getLensDistortionCorrection"],
    "getAlarm": ["getLastAlarmInfo", "getAlarmConfig"],
    "getLED": ["getLedStatus"],
    "getAutoTrackTarget": ["getTargetTrackConfig"],
    "getPresets": ["getPresetConfig"],
    "getLightFrequencyMode": ["getLightFrequencyInfo", "getLightFrequencyCapability"],
    "getChildDevices": ["getChildDeviceList"],
    "getForceWhitelampState": ["getLdc"],
    "getDayNightMode": ["getLightFrequencyInfo", "getNightVisionModeConfig"],
    "getImageFlipVertical": ["getRotationStatus", "getLdc"],
    "getLensDistortionCorrection": ["getLdc"],
}


def pytapoFunctionMap(pytapoFunctionName):
    return PYTAPO_FUNCTION_MAP.get(pytapoFunctionName, [pytapoFunctionName])


def isCacheSupported(check_function, rawData):
    rawFunctions = pytapoFunctionMap(check_function)
    for function in rawFunctions:
        if function in rawData:
            if rawData[function][0]:
                if check_function == "getForceWhitelampState":
                    return ldcHasField(rawData, "switch", "force_wtl_state")
                elif check_function == "getDayNightMode":
                    if (
                        "image" in rawData["getLightFrequencyInfo"][0]
                        and "common" in rawData["getLightFrequencyInfo"][0]["image"]
                    ):
                        common = rawData["getLightFrequencyInfo"][0]["image"]["common"]
                        if isinstance(common, dict) and "inf_type" in common:
                            return True
                        if isinstance(common, dict):
                            for entry in common.values():
                                if isinstance(entry, dict) and "inf_type" in entry:
                                    return True
                    return False
                elif check_function == "getImageFlipVertical":
                    if ldcHasField(rawData, "switch", "flip_type"):
                        return True
                    try:
                        rotation_image = rawData["getRotationStatus"][0].get(
                            "image", {}
                        )
                        rotation_switch = rotation_image.get(
                            "switch_chn"
                        ) or rotation_image.get("switch")
                        if isinstance(rotation_switch, dict):
                            if "flip_type" in rotation_switch:
                                return True
                            for entry in rotation_switch.values():
                                if isinstance(entry, dict) and "flip_type" in entry:
                                    return True
                    except Exception:
                        pass
                    return False
                elif check_function == "getLensDistortionCorrection":
                    return ldcHasField(rawData, "switch", "ldc")
                return True
            else:
                raise Exception(
                    f"Capability {check_function} (mapped to:{function}) cached but not supported."
                )
    return False


async def scheduleAll(hass, device, entry, mediaSync):
    LOGGER.debug("Scheduling for %s", device["name"])
    if device["mediaSyncAvailable"]:
        if device["initialMediaScanDone"] and not device["mediaSyncScheduled"]:
            device["mediaSyncScheduled"] = True
            LOGGER.debug("Scheduling media sync")
            callback = partial(mediaSync, entry=entry, device=device)

            entry.async_on_unload(
                async_track_time_interval(
                    hass,
                    callback,
                    datetime.timedelta(seconds=60),
                )
            )
        elif not device["initialMediaScanRunning"]:
            LOGGER.debug("Media scan running")
            device["initialMediaScanRunning"] = True
            try:
                await hass.async_add_executor_job(
                    device["controller"].getRecordingsList
                )
                hass.async_create_background_task(
                    findMedia(hass, device, entry),
                    "findMedia",
                )
            except Exception as err:
                device["initialMediaScanDone"] = True
                device["mediaSyncAvailable"] = False
                enableMediaSync = device[ENABLE_MEDIA_SYNC]
                errMsg = "Disabling media sync as there was error returned from getRecordingsList. Do you have SD card inserted?"
                if enableMediaSync:
                    LOGGER.warning("%s", errMsg)
                    LOGGER.warning("%s: %s", device["name"], err)
                else:
                    LOGGER.info("%s", errMsg)
                    LOGGER.info("%s: %s", device["name"], err)


async def check_functionality(entry, hass, cls, check_function):
    try:
        if isCacheSupported(check_function, entry["camData"]["raw"]):
            LOGGER.debug(
                "Found cached capability %s, creating %s", check_function, cls.__name__
            )
            return True
        else:
            if not entry[
                "controller"
            ].isKLAP:  # no uncached entries for klap devices, so no need to check them
                LOGGER.debug(
                    "Capability %s not found, querying again...", check_function
                )
                result = await hass.async_add_executor_job(
                    getattr(entry["controller"], check_function)
                )
                LOGGER.debug("Capability result: %s", result)
                LOGGER.debug("Creating %s", cls.__name__)
                return True
    except Exception as err:
        LOGGER.info("Camera does not support %s: %s", cls.__name__, err)
        return None
    return None


async def check_and_create(entry, hass, cls, check_function, config_entry):
    if await check_functionality(entry, hass, cls, check_function):
        try:
            return cls(entry, hass, config_entry)
        except Exception as err:
            LOGGER.info("Camera does not support %s: %s", cls.__name__, err)
            return None
    return None
