# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from bot import Bot
from config import encode
from database.sql import search_file_index

MAX_RESULTS = 15


def human_readable_size(size):
    if not size:
        return ""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


async def build_share_link(client, message_id):
    converted_id = message_id * abs(client.db_channel.id)
    base64_string = await encode(f"get-{converted_id}")
    return f"https://t.me/{client.username}?start={base64_string}"


@Bot.on_message(filters.private & filters.command("search"))
async def search_files_command(client: Bot, message: Message):
    if len(message.command) < 2:
        await message.reply_text(
            "❌ <b>Penggunaan:</b> <code>/search kata_kunci</code>\n\n"
            "<b>Contoh:</b> <code>/search naruto s1</code>\n\n"
            "💡 Kamu juga bisa cari & share file langsung di chat lain dengan mengetik:\n"
            f"<code>@{client.username} kata_kunci</code>",
            quote=True,
        )
        return

    keyword = message.text.split(" ", 1)[1].strip()
    if len(keyword) < 2:
        await message.reply_text("❌ <b>Kata kunci minimal 2 karakter!</b>", quote=True)
        return

    results = search_file_index(keyword, limit=MAX_RESULTS)
    if not results:
        await message.reply_text(
            f"❌ <b>Tidak ada file ditemukan untuk:</b> <code>{keyword}</code>",
            quote=True,
        )
        return

    buttons = []
    for item in results:
        link = await build_share_link(client, item["message_id"])
        size_label = human_readable_size(item.get("file_size"))
        label = item["file_name"]
        if size_label:
            label = f"{label} ({size_label})"
        buttons.append([InlineKeyboardButton(f"📄 {label[:60]}", url=link)])

    await message.reply_text(
        f"🔎 <b>Hasil pencarian untuk:</b> <code>{keyword}</code>\n"
        f"<b>Ditemukan:</b> {len(results)} file",
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True,
    )


@Bot.on_inline_query()
async def search_files_inline(client: Bot, inline_query: InlineQuery):
    keyword = inline_query.query.strip()
    if len(keyword) < 2:
        await inline_query.answer(
            results=[],
            cache_time=5,
            switch_pm_text="Ketik minimal 2 karakter untuk mencari file...",
            switch_pm_parameter="search",
        )
        return

    results = search_file_index(keyword, limit=MAX_RESULTS)

    answers = []
    for item in results:
        link = await build_share_link(client, item["message_id"])
        size_label = human_readable_size(item.get("file_size"))
        description = f"{size_label} • Tap untuk share link" if size_label else "Tap untuk share link"
        answers.append(
            InlineQueryResultArticle(
                title=item["file_name"][:60],
                description=description,
                input_message_content=InputTextMessageContent(
                    f"📄 <b>{item['file_name']}</b>\n\n{link}"
                ),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("📥 Buka File", url=link)]]
                ),
            )
        )

    await inline_query.answer(
        results=answers,
        cache_time=30,
        switch_pm_text="Tidak nemu? Buka bot" if not answers else "Cari lebih lanjut di bot",
        switch_pm_parameter="search",
    )
