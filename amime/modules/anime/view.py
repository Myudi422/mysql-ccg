# MIT License
#
# Copyright (c) 2021 Andriel Rodrigues for Amano Team
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import asyncio
import math
from typing import Union

import anilist
from datetime import datetime
from time import time
from anilist.types import next_airing
from pyrogram import filters
from pyrogram.types import CallbackQuery, InputMediaPhoto, Message
from pyromod.helpers import array_chunk, ikb

from amime.amime import Amime
from amime.database import Episodes, Users
from amime.modules.favorites import get_favorite_button
from amime.modules.mylists import get_mylist_button
from amime.modules.notify import get_notify_button
from amime.modules.a_lists import get_a_list_button




def make_it_rw(time_stamp):
    """Converting Time Stamp to Readable Format"""
    seconds, milliseconds = divmod(int(time_stamp), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + " Hari, ") if days else "")
        + ((str(hours) + " Jam, ") if hours else "")
        + ((str(minutes) + " Menit, ") if minutes else "")
        + ((str(seconds) + " Detik, ") if seconds else "")
        + ((str(milliseconds) + " ms, ") if milliseconds else "")
    )
    return tmp[:-2]


@Amime.on_message(filters.cmd(r"menu (.+)"))
@Amime.on_callback_query(filters.regex(r"^menu (\d+)\s?(\d+)?\s?(\d+)?"))
async def anime_view(bot: Amime, union: Union[CallbackQuery, Message]):
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    chat = message.chat
    user = union.from_user
    lang = union._lang

    is_private = await filters.private(bot, message)
    is_collaborator = await filters.sudo(bot, union)
    is_auth = await filters.collaborator(bot, union)

    query = union.matches[0].group(1)

    if is_callback:
        user_id = union.matches[0].group(2)
        if user_id is not None:
            user_id = int(user_id)

            if user_id != user.id:
                return

        to_delete = union.matches[0].group(3)
        if bool(to_delete) and not is_private:
            await message.delete()
    
    if not bool(query):
        return

        
    async with anilist.AsyncClient() as client:
        if not query.isdecimal():
            results = await client.search(query, "anime", 15)
            if results is None:
                await asyncio.sleep(0.5)
                results = await client.search(query, "anime", 10)
                

            if results is None:
                return    

            if len(results) == 1:
                anime_id = results[0].id
                
                
            else:
                keyboard = []
                for result in results:

                    keyboard.append(
                        [(result.title.romaji, f"menu {result.id} {user.id} 1"), (lang.search1_button, f"!a {result.title.romaji}", "switch_inline_query_current_chat")]
                    )
                keyboard.append([(lang.Hapus_text, "close_data"), (lang.home_button, "menu")])

                await message.reply_text(
                    lang.search_results_text(
                        query=query,
                    ),
                    reply_markup=ikb(keyboard),
                )
                return
        else:
            anime_id = int(query)

        anime = await client.get(anime_id, "anime")

        if anime is None:
            return

        user_db = await Users.get(id=user.id)
        language = user_db.language_anime

        episodes = await Episodes.filter(anime=anime.id)
        episodes1 = await Episodes.filter(anime=anime_id, language=language)
        episodes = sorted(episodes, key=lambda episode: episode.number)
        episodes = [*filter(lambda episode: len(episode.file_id) > 0, episodes)]

        
        if is_private:
            if len(episodes) > 0 and anime.status.lower() == "releasing":
                air_on = make_it_rw(anime.next_airing.time_until*1000)
                text = f"<b>{anime.title.romaji}</b> ({anime.title.native}) |" 
                if len(episodes1) > 0:
                    text += f" ✅ ({len(episodes1)}) List Episode Tersedia untuk ditonton."
                if len(episodes1) < 1:
                    text += f" ✅ List Episode Tersedia untuk ditonton."
                if anime.status.lower() == "releasing":
                    if hasattr(anime.next_airing, "time_until") and air_on:
                        text += f"\n\nℹ️ Episode ({anime.next_airing.episode}) akan rilis dalam {air_on}"

            if len(episodes) > 0 and not anime.status.lower() == "releasing":
                text = f"<b>{anime.title.romaji}</b> ({anime.title.native}) |" 
                if len(episodes1) > 0:
                    text += f" ✅ ({len(episodes1)}) List Episode Tersedia untuk ditonton."
                if len(episodes1) < 1:
                    text += f" ✅ List Episode Tersedia untuk ditonton."

            if len(episodes) < 1 and anime.status.lower() == "releasing":
                air_on = make_it_rw(anime.next_airing.time_until*1000)
                text = f"\n\n❌ Belum Tersedia. - <code>{anime.title.romaji}</code>"
                if hasattr(anime.title, "native"):
                    text += f" (<b>{anime.title.native}</b>)"
                if hasattr(anime.next_airing, "time_until") and air_on:
                    text += f"\n\nℹ️ Episode ({anime.next_airing.episode}) akan rilis dalam {air_on}"
                text += f"\nCek progres: <a href='https://t.me/otakuindonew/49696'>Disini</a>"
                
            if len(episodes) < 1 and not anime.status.lower() == "releasing":
                text = f"\n\n❌ Belum Tersedia. - <code>{anime.title.romaji}</code>"
                if hasattr(anime.title, "native"):
                    text += f" (<b>{anime.title.native}</b>)"
                text += f"\nCek progres: <a href='https://t.me/otakuindonew/49696'>Disini</a></b>"
            
        buttons = [
            (
                        lang.view_more_button,
                        f"anime more {anime.id} {user.id}"
                    )       
        ]
         

        if len(episodes) > 0:
            if is_private:
                buttons.append(
                    (
                        lang.watch_button,
                        f"episodes {anime.id} {episodes[0].season} 1",
                    )
                )


        if is_collaborator:
            buttons.append(
                (
                    lang.manage_button,
                    f"manage anime {anime.id} 0 1 {language} 1",
                )
            )
        
        if is_collaborator:
            buttons.append(
                (
                    lang.ngelist_more_button,
                    f"ngelist more {anime.id} {user.id}",
                )
            )

 
             

        if len(episodes) < 1 and is_private and not anime.status.lower() == "not_yet_released" and not anime.status.lower() == "releasing" and not hasattr(anime, "genres") == 'hentai':      
            buttons.append((lang.inline, f"{anime.title.romaji}", "switch_inline_query_current_chat"))

        
        
        if is_private:
            buttons.append(
                await get_notify_button(
                    lang, user if is_private else chat, "anime", anime.id
                )
            )

        if is_private and not anime.status.lower() == "not_yet_released":
            button = (
                lang.request_content_button,
                f"request episodes {anime.id} {language}",
            )
            if anime.status.lower() == "releasing":
                if hasattr(anime, "next_airing"):
                    next_episode = anime.next_airing.episode
                    if len(episodes) < (next_episode - 1):
                        buttons.append(button)
                else:
                    buttons.append(button)
            elif hasattr(anime, "episodes"):
                if len(episodes) < anime.episodes:
                    buttons.append(button)


        if is_private:       
            buttons.append(
                    (
                        lang.Hapus_text, 
                        f"close_data"
                    ),
                )

        keyboard = array_chunk(buttons, 2)

        if is_collaborator:
            photo: str = ""
            if hasattr(anime, "banner"):
                photo = anime.banner
            elif hasattr(anime, "cover"):
                if hasattr(anime.cover, "extra_large"):
                    photo = anime.cover.extra_large
                elif hasattr(anime.cover, "large"):
                    photo = anime.cover.large
                elif hasattr(anime.cover, "medium"):
                    photo = anime.cover.medium
                    
        if not is_collaborator:
            photo = f"https://img.anili.st/media/{anime.id}"

        if bool(message.video) and is_callback:
            await union.edit_message_media(
                InputMediaPhoto(
                    photo,
                    caption=text,
                ),
                reply_markup=ikb(keyboard),
            )
        elif bool(message.photo) and not bool(message.via_bot):
            await message.edit_text(
                text,
                reply_markup=ikb(keyboard),
            )
        else:
            await message.reply_photo(
                photo,
                caption=text,
                reply_markup=ikb(keyboard),
            )


@Amime.on_callback_query(filters.regex(r"^anime more (\d+) (\d+)"))
async def anime_view_more(bot: Amime, callback: CallbackQuery):
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    user_id = int(callback.matches[0].group(2))


    if user_id != user.id:
        return

    async with anilist.AsyncClient() as client:
        anime = await client.get(anime_id, "anime")

        buttons = [
            (lang.Login, f"btn_{anime.id}_True_{user_id}"),
            (lang.Guest, f"btn_{anime.id}_ANI_False_{user_id}"),
            #(lang.characters_button, f"anime characters {anime_id} {user_id}"),
        ]

       # if hasattr(anime, "trailer"):
            #if hasattr(anime.trailer, "url"):
       #         buttons.append((lang.trailer_button, anime.trailer.url, "url"))

        keyboard = array_chunk(buttons, 2)

        keyboard.append([(lang.back_button, f"menu {anime_id} {user_id}")])

        await message.edit_text(
            lang.view_more_text,
            reply_markup=ikb(keyboard),
        )


@Amime.on_callback_query(filters.regex(r"^ngelist more (\d+) (\d+)"))
async def ngelist_view_more(bot: Amime, callback: CallbackQuery):
    message = callback.message
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    user_id = int(callback.matches[0].group(2))

    is_private = await filters.private(bot, message)
    is_collaborator = await filters.sudo(bot, message)


    if user_id != user.id:
        return

    async with anilist.AsyncClient() as client:
        anime = await client.get(anime_id, "anime")

        buttons = []

       # if hasattr(anime, "trailer"):
            #if hasattr(anime.trailer, "url"):
       #         buttons.append((lang.trailer_button, anime.trailer.url, "url"))
        buttons.append(await get_a_list_button(lang, user.id, "anime", anime.id)),
        buttons.append(await get_a_list_button(lang, user.id, "anime", anime.id)),
        buttons.append(await get_a_list_button(lang, user.id, "anime", anime.id)),

        keyboard = array_chunk(buttons, 3)

        keyboard.append([(lang.back_button, f"menu {anime_id} {user_id}")])

        await message.edit_text(
            lang.ngelist_more_text,
            reply_markup=ikb(keyboard),
        )


@Amime.on_callback_query(filters.regex(r"anime description (\d+) (\d+) (\d+)"))
async def anime_view_description(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    user_id = int(callback.matches[0].group(2))
    page = int(callback.matches[0].group(3))

    if user_id != user.id:
        return

    async with anilist.AsyncClient() as client:
        anime = await client.get(anime_id, "anime")

        description = anime.description
        amount = 1024
        page = 1 if page <= 0 else page
        offset = (page - 1) * amount
        stop = offset + amount
        pages = math.ceil(len(description) / amount)
        description = description[offset - (3 if page > 1 else 0) : stop]

        page_buttons = []
        if page > 1:
            page_buttons.append(
                ("⬅️", f"anime description {anime_id} {user_id} {page - 1}")
            )
        if not page == pages:
            description = description[: len(description) - 3] + "..."
            page_buttons.append(
                ("➡️", f"anime description {anime_id} {user_id} {page + 1}")
            )

        keyboard = []
        if len(page_buttons) > 0:
            keyboard.append(page_buttons)

        keyboard.append([(lang.back_button, f"anime more {anime_id} {user_id}")])

        await message.edit_text(
            description,
            reply_markup=ikb(keyboard),
        )


@Amime.on_callback_query(filters.regex(r"^anime characters (\d+) (\d+)"))
async def anime_view_characters(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    user_id = int(callback.matches[0].group(2))

    if user_id != user.id:
        return

    async with anilist.AsyncClient() as client:
        anime = await client.get(anime_id, "anime")

        keyboard = [
            [
                (lang.back_button, f"anime more {anime_id} {user_id}"),
            ],
        ]

        text = lang.characters_text

        characters = sorted(anime.characters, key=lambda character: character.id)
        for character in characters:
            text += f"\n• <code>{character.id}</code> - <a href='https://t.me/{bot.me.username}/?start=character_{character.id}'>{character.name.full}</a> (<i>{character.role}</i>)"

        await message.edit_text(
            text,
            reply_markup=ikb(keyboard),
        )


@Amime.on_callback_query(filters.regex(r"^anime studios (\d+) (\d+)"))
async def anime_view_studios(bot: Amime, callback: CallbackQuery):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    lang = callback._lang

    anime_id = int(callback.matches[0].group(1))
    user_id = int(callback.matches[0].group(2))

    if user_id != user.id:
        return

    await callback.answer(lang.unfinished_function_alert, show_alert=True)
