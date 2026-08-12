# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import asyncio

from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot import Bot
from config import ADMINS, CHANNEL_ID, DISABLE_CHANNEL_BUTTON, LOGGER
from config import encode
from database.sql import add_file_to_index

# Import for payment proof handling
from .user_limits import set_user_custom_limit

# Import for custom messages
try:
    from .button_management import get_custom_message, send_custom_message
    CUSTOM_MESSAGES_AVAILABLE = True
except ImportError:
    CUSTOM_MESSAGES_AVAILABLE = False


def extract_file_metadata(message: Message):
    """
    Extract (file_name, file_type, file_size) from a media message for the
    search index. Returns (None, None, None) for non-media/text messages.
    """
    for file_type in ("document", "video", "audio", "animation", "voice", "video_note"):
        media = getattr(message, file_type, None)
        if media:
            file_name = getattr(media, "file_name", None) or (
                message.caption.split("\n")[0][:100] if message.caption else file_type
            )
            return file_name, file_type, getattr(media, "file_size", None)

    if message.photo:
        file_name = message.caption.split("\n")[0][:100] if message.caption else "photo"
        return file_name, "photo", message.photo.file_size

    return None, None, None


def index_message_file(message: Message, indexed_message_id):
    """Index a media message's metadata so it becomes searchable via /search."""
    file_name, file_type, file_size = extract_file_metadata(message)
    if not file_name:
        return
    try:
        add_file_to_index(
            message_id=indexed_message_id,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            caption=message.caption.html if message.caption else None,
        )
    except Exception as e:
        LOGGER(__name__).warning(f"Failed to index file {indexed_message_id}: {e}")


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.forwarded)
async def handle_forwarded_payment_proof(client: Bot, message: Message):
    """Handle forwarded payment proof from admin to upgrade user limit"""
    try:
        # Check if forwarded from a user (not bot or channel)
        if not message.forward_from or message.forward_from.is_bot:
            await message.reply_text("❌ <b>Forward harus dari user asli, bukan bot atau channel.</b>", quote=True)
            return

        original_user_id = message.forward_from.id
        original_user_name = message.forward_from.first_name or "Unknown"
        original_username = f"@{message.forward_from.username}" if message.forward_from.username else "None"

        # Set premium limit (999 for unlimited, adjust as needed)
        premium_limit = 999
        set_user_custom_limit(original_user_id, premium_limit)

        # Confirm to admin
        await message.reply_text(
            f"✅ <b>Limit user berhasil diupgrade ke premium!</b>\n\n"
            f"<b>User:</b> {original_user_name} ({original_username})\n"
            f"<b>User ID:</b> <code>{original_user_id}</code>\n"
            f"<b>Limit Baru:</b> {premium_limit} downloads/hari\n"
            f"<b>Status:</b> Premium Activated",
            quote=True
        )

        # Optional: Send notification to user
        try:
            await client.send_message(
                chat_id=original_user_id,
                text=f"🎉 <b>Selamat! Limit download Anda telah diupgrade ke premium.</b>\n\n"
                     f"<b>Limit Baru:</b> {premium_limit} downloads/hari\n"
                     f"<b>Terima kasih atas pembayaran Anda!</b>\n\n"
                     f"💡 Gunakan /profile untuk melihat statistik Anda."
            )
        except Exception as e:
            LOGGER(__name__).warning(f"Failed to notify user {original_user_id}: {e}")
            await message.reply_text(f"⚠️ <b>Gagal kirim notifikasi ke user:</b> {e}", quote=True)

    except Exception as e:
        LOGGER(__name__).error(f"Error in handle_forwarded_payment_proof: {e}")
        await message.reply_text(f"❌ <b>Error:</b> {e}", quote=True)


@Bot.on_message(
    filters.private
    & filters.user(ADMINS)
    & ~filters.forwarded
    & ~filters.command(
        [
            "start",
            "users",
            "broadcast",
            "ping",
            "uptime",
            "batch",
            "logs",
            "genlink",
            "delvar",
            "getvar",
            "setvar",
            "speedtest",
            "usage",
            "stats",
            "vars",
            "id",
            "info",
            "addadmin",
            "deladmin",
            "getadmin",
            "addkonten",
            "delkonten",
            "getkonten",
            "limitkonten",
            "addbutton",
            "delbutton",
            "getbutton",
            "limitbutton",
            "setmsg",
            "getdb",
            "setdb",
            "backupdb",
            "restoredb",
            "cleardb",
            "setlimit",
            "getlimit",
            "userstats",
            "resetlimits",
            "checkuser",
            "profile",
            "feedback",
            "report",
            "tutorial",
            "viewfeedback",
            "viewreports",
            "setuserlimit",
            "deluserlimit",
            "getuserlimits",
            "search",
            "language",
            "setverify",
            "setverifydelay",
            "analytics",
        ]
    )
)
async def channel_post(client: Client, message: Message):
    reply_text = await message.reply_text("<code>Tunggu Sebentar...</code>", quote=True)
    try:
        post_message = await message.copy(
            chat_id=client.db_channel.id, disable_notification=True
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
        post_message = await message.copy(
            chat_id=client.db_channel.id, disable_notification=True
        )
    except Exception as e:
        LOGGER(__name__).warning(e)
        # Send custom error message with media support
        sent = await send_custom_message(client, message.chat.id, "error", quote=True)
        if not sent:
            # Fallback to default message
            await reply_text.edit_text("<b>Telah Terjadi Error...</b>")
        return
    index_message_file(message, post_message.id)

    converted_id = post_message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔁 Share Link", url=f"https://telegram.me/share/url?url={link}"
                )
            ]
        ]
    )

    await reply_text.edit(
        f"<b>Link Sharing File Berhasil Di Buat :</b>\n\n{link}",
        reply_markup=reply_markup,
    )

    if not DISABLE_CHANNEL_BUTTON:
        try:
            await post_message.edit_reply_markup(reply_markup)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await post_message.edit_reply_markup(reply_markup)
        except Exception:
            pass


@Bot.on_message(filters.channel & filters.incoming & filters.chat(CHANNEL_ID))
async def new_post(client: Client, message: Message):

    index_message_file(message, message.id)

    if DISABLE_CHANNEL_BUTTON:
        return

    converted_id = message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔁 Share Link", url=f"https://telegram.me/share/url?url={link}"
                )
            ]
        ]
    )
    try:
        await message.edit_reply_markup(reply_markup)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.edit_reply_markup(reply_markup)
    except Exception:
        pass
