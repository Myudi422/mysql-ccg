from typing import Union

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import ikb

import datetime
import re
import anilist
from pyromod.helpers import array_chunk, ikb

from amime.amime import Amime
from amime.config import CHATS
from amime.database import Requests
from amime.modules.anime.view import anime_view




@Amime.on_message(filters.cmd(r"kamis$") & filters.private)
@Amime.on_callback_query(filters.regex(r"^kamis$"))
async def anime_menu(bot: Amime, union: Union[CallbackQuery, Message]):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    lang = union._lang

    keyboard = [
        [
            (lang.anime_delapan, f"menu 111321"),
        ],
        [
            (lang.anime_empat, f"menu 130586"),
        ],
        [
            (lang.anime_sembilan, f"menu 142984"),
        ],
        


    ]

    if is_callback:
        keyboard.append([(lang.back_button, "jadwal")])

    await (message.edit_text if is_callback else message.reply_text)(
        lang.ongoing_text,
        reply_markup=ikb(keyboard),
    )