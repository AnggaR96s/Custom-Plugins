import asyncio
from pyrogram.types import Message
import os
from subprocess import PIPE, Popen
import aria2p
from requests import get
from userge import userge, Message, config
logger = userge.getLogger(__name__)

EDIT_SLEEP_TIME_OUT = 10


def subprocess_run(cmd):
    subproc = Popen(
        cmd,
        stdout=PIPE,
        stderr=PIPE,
        shell=True,
        universal_newlines=True)
    talk = subproc.communicate()
    exitCode = subproc.returncode
    if exitCode != 0:
        return
    return talk


trackers_list = get(
    "https://raw.githubusercontent.com/XIU2/TrackersListCollection/master/all.txt"
).text.replace("\n\n", ",")
trackers = f"[{trackers_list}]"

cmd = f"aria2c \
--enable-rpc \
--rpc-listen-all=false \
--rpc-listen-port 6800 \
--max-connection-per-server=10 \
--rpc-max-request-size=1024M \
--seed-time=0.01 \
--max-upload-limit=5K \
--max-concurrent-downloads=5 \
--min-split-size=10M \
--follow-torrent=mem \
--split=10 \
--bt-tracker={trackers} \
--daemon=true \
--allow-overwrite=true"

subprocess_run(cmd)
if not os.path.isdir(config.Dynamic.DOWN_PATH):
    os.makedirs(config.Dynamic.DOWN_PATH)
download_path = os.getcwd() + config.Dynamic.DOWN_PATH.strip(".")

aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret=""))

aria2.set_global_options({"dir": download_path})


@userge.on_cmd("addmag",
               about={'header': "Download from torrent to server",
                      'usage': "{tr}addmag [magnet link]"},
               check_downpath=True)
async def magnet_download(message: Message):
    magnet_uri = message.input_str
    logger.info(magnet_uri)
    try:  # Add Magnet URI Into Queue
        download = aria2.add_magnet(magnet_uri)
    except Exception as e:
        logger.info(str(e))
        await message.edit_text("Error :\n{}".format(str(e)))
        return
    gid = download.gid
    await progress_status(gid=gid, message=message, previous=None)
    await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
    new_gid = await check_metadata(gid)
    await progress_status(gid=new_gid, message=message, previous=None)


@userge.on_cmd("addtor",
               about={'header': "Download from torrent to server",
                      'usage': "{tr}addtor location .torrent file",
                      'examples': "{tr}addtor file.torrent"},
               check_downpath=True)
async def torrent_download(message: Message):
    var = message.text[8:]
    torrent_file_path = var
    torrent_file_path = torrent_file_path.replace("`", "")
    logger.info(torrent_file_path)

    try:  # Add Torrent Into Queue
        download = aria2.add_torrent(
            torrent_file_path, uris=None, options=None, position=None
        )
    except Exception as e:
        await message.edit_text("Error :\n`{}`".format(str(e)))
        return
    gid = download.gid
    await progress_status(gid=gid, message=message, previous=None)


@userge.on_cmd("ariarm",
               about={'header': "Remove all aria download queue",
                      'usage': "{tr}ariarm",
                      'examples': "{tr}ariarm"},
               check_downpath=True)
async def remove_all(message: Message):
    try:
        removed = aria2.remove_all(force=True)
        aria2.purge_all()
    except BaseException:
        pass
    if removed == False:  # If API returns False Try to Remove Through System Call.
        os.system("aria2p remove-all")
    await message.edit_text("`Removed All Downloads.`")


@userge.on_cmd("ariap",
               about={'header': "Pause all torrent download",
                      'usage': "{tr}ariap",
                      'examples': "{tr}ariap"},
               check_downpath=True)
async def pause_all(message: Message):
    # Pause ALL Currently Running Downloads.
    paused = aria2.pause_all(force=True)
    await message.edit_text("Output: " + str(paused))


@userge.on_cmd("ariare",
               about={'header': "Resume all torrent download",
                      'usage': "{tr}ariare",
                      'examples': "{tr}ariare"},
               check_downpath=True)
async def resume_all(message: Message):
    resumed = aria2.resume_all()
    await message.edit_text("Output: " + str(resumed))


@userge.on_cmd("ariastatus",
               about={'header': "Get details download status",
                      'usage': "{tr}ariastatus",
                      'examples': "{tr}ariastatus"},
               check_downpath=True)
async def show_all(message: Message):
    output = "output.txt"
    downloads = aria2.get_downloads()
    msg = ""
    for download in downloads:
        msg = (
            msg
            + "File: `"
            + str(download.name)
            + "`\nSpeed: "
            + str(download.download_speed_string())
            + "\nProgress: "
            + str(download.progress_string())
            + "\nTotal Size: "
            + str(download.total_length_string())
            + "\nStatus: "
            + str(download.status)
            + "\nETA:  "
            + str(download.eta_string())
            + "\n\n"
        )
    if len(msg) <= 4096:
        await message.edit_text("`Current Downloads: `\n" + msg)
    else:
        await message.edit_text("`Output is huge.Sending as file.. `")
        with open(output, "w") as f:
            f.write(msg)
        await asyncio.sleep(2)
        await message.delete()
        await client.send_document(
            chat_id=message.chat_id,
            document=output,
            caption="`Output is huge. Sending as a file...`",
        )


async def check_metadata(gid):
    file = aria2.get_download(gid)
    new_gid = file.followed_by_ids[0]
    logger.info("Changing GID " + gid + " to " + new_gid)
    return new_gid


async def progress_status(gid, message, previous):
    try:
        file = aria2.get_download(gid)
        if not file.is_complete:
            if not file.error_message:
                msg = (
                    "Downloading File: `"
                    + str(file.name)
                    + "`\nSpeed: "
                    + str(file.download_speed_string())
                    + "\nProgress: "
                    + str(file.progress_string())
                    + "\nTotal Size: "
                    + str(file.total_length_string())
                    + "\nStatus: "
                    + str(file.status)
                    + "\nETA:  "
                    + str(file.eta_string())
                    + "\n\n"
                )
                if previous != msg:
                    await message.edit_text(msg)
                    previous = msg
            else:
                logger.info(str(file.error_message))
                await message.edit_text("Error : `{}`".format(str(file.error_message)))
                retur
            await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
            await progress_status(gid, message, previous)
        else:
            await message.edit_text(
                f"`File Downloaded Successfully:` `{config.Dynamic.DOWN_PATH + file.name}`"
            )
            return
    except Exception as e:
        if " not found" in str(e) or "'file'" in str(e):
            await message.edit_text("Download Canceled :\n`{}`".format(file.name))
            return
        elif " depth exceeded" in str(e):
            file.remove(force=True)
            await message.edit_text(
                "Download Auto Canceled :\n`{}`\nYour Torrent/Link is Dead.".format(
                    file.name
                )
            )
        else:
            logger.info(str(e))
            await message.edit_text("Error :\n`{}`".format(str(e)))
            return
