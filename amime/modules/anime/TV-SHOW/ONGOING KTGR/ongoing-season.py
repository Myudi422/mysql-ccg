import httpx
from anilist.types import Anime
from pyrogram import filters
from pyrogram.types import CallbackQuery
from pyromod.helpers import ikb
from pyromod.nav import Pagination

from amime.amime import Amime


@Amime.on_callback_query(filters.regex(r"^tv_ongoing_anime anime (?P<page>\d+)"))
async def anime_suggestions(bot: Amime, callback: CallbackQuery):
    page = int(callback.matches[0]["page"])

    message = callback.message
    lang = callback._lang

    keyboard = []
    async with httpx.AsyncClient(http2=True) as client:
        response = await client.post(
            url="https://graphql.anilist.co",
            json=dict(
                query="""
                query($page: Int, $perPage: Int) {
                    Page(page: $page, perPage: $perPage) {
                        media(type: ANIME, sort: TRENDING_DESC, status: RELEASING) {
                            id
                            title {
                                romaji
                                english
                                native
                            }
                            siteUrl
                        }
                    }
                }
                """,
                variables=dict(
                    perPage=100,
                ),
            ),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        data = response.json()
        await client.aclose()

        if data["data"]:
            items = data["data"]["Page"]["media"]
            suggestions = [
                Anime(id=item["id"], title=item["title"], url=item["siteUrl"])
                for item in items
            ]

            layout = Pagination(
                suggestions,
                item_data=lambda i, pg: f"menu {i.id}",
                item_title=lambda i, pg: f"{i.title.romaji}",
                page_data=lambda pg: f"tv_ongoing_anime anime {pg}",
            )

            lines = layout.create(page, lines=8)

            if len(lines) > 0:
                keyboard += lines
    keyboard.append([(lang.Hapus_text, "close_data"), (lang.back_button, "jadwal")])

    await message.edit_text(
        lang.jad_text,
        reply_markup=ikb(keyboard),
    )