# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

from pyrogram import filters, StopPropagation
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot import Bot
from database.sql import set_user_language
from .i18n import t

LANGUAGE_BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="setlang:id"),
            InlineKeyboardButton("🇬🇧 English", callback_data="setlang:en"),
        ]
    ]
)


@Bot.on_message(filters.private & filters.command("language"))
async def language_command(client: Bot, message: Message):
    await message.reply_text(
        f"{t(message.from_user.id, 'language_prompt')}\n\n🌐 Pilih / Choose:",
        reply_markup=LANGUAGE_BUTTONS,
        quote=True,
    )


@Bot.on_callback_query(filters.regex(r"^setlang:"), group=-1)
async def set_language_callback(client: Bot, callback_query: CallbackQuery):
    lang = callback_query.data.split(":", 1)[1]
    set_user_language(callback_query.from_user.id, lang)
    await callback_query.answer()
    await callback_query.message.edit_text(
        t(callback_query.from_user.id, "language_set"),
        reply_markup=LANGUAGE_BUTTONS,
    )
    raise StopPropagation
