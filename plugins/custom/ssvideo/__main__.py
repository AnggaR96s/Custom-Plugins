""" generate screenshot """

# Copyright (C) 2020-2022 by UsergeTeam@Github, < https://github.com/UsergeTeam >.
#
# This file is part of < https://github.com/UsergeTeam/Userge > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/UsergeTeam/Userge/blob/master/LICENSE >
#
# All rights reserved.


import os
import asyncio


from userge import userge, Message, config
from userge.utils import progress


@userge.on_cmd("ssv", about={
    'header': "Screen Shot Generator",
    'description': "Generate Random Screen Shots from any video "
                   " **[NOTE: If no frame count is passed, default"
                   " value for number of ss is 10. ",
    'usage': "{tr}ssv [No of SS (optional)] [Path or reply to Video]"})
async def ss_gen(message: Message):
    replied = message.reply_to_message
    vid_loc = ''
    ss_c = 5
    should_clean = False
    await message.edit("Checking you Input?🧐🤔😳")
    if message.input_str:
        if ' ' in message.input_str:
            ss_c, vid_loc = message.input_str.split(" ", 1)
        else:
            try:
                ss_c = int(message.input_str)
            except ValueError:
                vid_loc = message.input_str

    if not vid_loc and replied:
        if not (
            replied.video
            or replied.animation
            or (replied.document and "video" in replied.document.mime_type)
        ):
            await message.edit("I doubt it is a video")
            return
        await message.edit("Downloading Video to my Local")
        vid = await message.client.download_media(
            message=replied,
            file_name=config.Dynamic.DOWN_PATH,
            progress=progress,
            progress_args=(message, "Downloading🧐? W8 plox")
        )
        vid_loc = os.path.join(config.Dynamic.DOWN_PATH, os.path.basename(vid))
        should_clean = True
    await message.edit("Compiling Resources")
    try:
        command = f"vcsi -g {ss_c}x{ss_c} {vid} -o ss.png"
        os.system(command)
    except Exception:
        command = f"vcsi -g {ss_c}x{ss_c} {vid_loc} -o ss.png"
        os.system(command)
    doc = "ss.png"
    await message.client.send_document(
        chat_id=message.chat.id,
        document=doc)
    if should_clean:
        os.remove(vid_loc)
        os.remove(doc)
    await asyncio.sleep(0.5)
    await message.edit("Done.")
