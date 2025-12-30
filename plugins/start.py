# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import asyncio
import json
import os
from datetime import datetime
from time import time

from bot import Bot
from config import (
    ADMINS,
    CUSTOM_CAPTION,
    DISABLE_CHANNEL_BUTTON,
    FORCE_MSG,
    PROTECT_CONTENT,
    START_MSG,
)
from database.sql import add_user, delete_user, full_userbase, query_msg, get_user_stats, update_user_subscription_status
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from config import decode, get_messages, subsall, subsch, subsgc

from .button import fsub_button, start_button
from .content_utils import check_content_protection
from .user_limits import check_user_daily_limit, get_user_stats

def replace_placeholders(text, user):
    """Replace placeholders in text with user data"""
    if not text:
        return text

    from datetime import datetime
    import locale

    try:
        # Set locale for Indonesian day names
        locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
    except:
        pass  # Fallback to default locale

    now = datetime.now()

    replacements = {
        '{ID}': str(user.id),
        '{NAME}': user.first_name or '',
        '{SURNAME}': user.last_name or '',
        '{NAMESURNAME}': f"{user.first_name or ''} {user.last_name or ''}".strip(),
        '{LANG}': 'id',  # Default to Indonesian
        '{DATE}': now.strftime('%d/%m/%Y'),
        '{TIME}': now.strftime('%H:%M:%S'),
        '{WEEKDAY}': now.strftime('%A'),  # Full weekday name
        '{MENTION}': user.mention,
        '{USERNAME}': f"@{user.username}" if user.username else 'None'
    }

    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)

    return text

# Import button management and user features
try:
    from .button_management import load_button_settings, get_custom_message, send_custom_message
    BUTTONS_AVAILABLE = True
except ImportError:
    BUTTONS_AVAILABLE = False

try:
    from .user_features import update_user_activity, save_user_data, load_user_data
    USER_TRACKING_AVAILABLE = True
except ImportError:
    USER_TRACKING_AVAILABLE = False

def get_custom_buttons():
    """Get custom buttons for download"""
    if not BUTTONS_AVAILABLE:
        return []

    try:
        settings = load_button_settings()
        if not settings["custom_buttons"]:
            return []

        buttons = []
        current_row = []
        for btn_id, btn_data in settings["custom_buttons"].items():
            current_row.append(
                InlineKeyboardButton(
                    text=btn_data["text"],
                    url=btn_data["url"]
                )
            )

            # Group buttons in rows of 2
            if len(current_row) == 2:
                buttons.append(current_row)
                current_row = []

        # Add any remaining buttons in the current row
        if current_row:
            buttons.append(current_row)

        return buttons
    except Exception:
        return []

def update_user_tracking(user_id):
    """Update user activity and stats"""
    if not USER_TRACKING_AVAILABLE:
        return
    
    try:
        user_data = load_user_data()
        update_user_activity(user_id, user_data)
        
        # Update activity score and downloads
        user_stats = user_data.get(str(user_id), {})
        user_stats['total_downloads'] = user_stats.get('total_downloads', 0) + 1
        user_stats['downloads_today'] = user_stats.get('downloads_today', 0) + 1
        user_stats['activity_score'] = user_stats.get('activity_score', 0) + 10
        
        user_data[str(user_id)] = user_stats
        save_user_data(user_data)
    except Exception as e:
        print(f"Error updating user tracking: {e}")

START_TIME = datetime.utcnow()
START_TIME_ISO = START_TIME.replace(microsecond=0).isoformat()
TIME_DURATION_UNITS = (
    ("week", 60 * 60 * 24 * 7),
    ("day", 60**2 * 24),
    ("hour", 60**2),
    ("min", 60),
    ("sec", 1),
)


async def _human_time_duration(seconds):
    if seconds == 0:
        return "inf"
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append(f'{amount} {unit}{"" if amount == 1 else "s"}')
    return ", ".join(parts)


@Bot.on_message(filters.command("start") & filters.private & subsall & subsch & subsgc)
async def start_command(client: Bot, message: Message):
    id = message.from_user.id
    user_name = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else None
    )

    add_user(id, user_name)
    # Update subscription status for real-time tracking
    update_user_subscription_status(id, user_name, is_subscribed=True)
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except BaseException:
            return
        string = await decode(base64_string)
        argument = string.split("-")
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except BaseException:
                return
            if start <= end:
                ids = range(start, end + 1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except BaseException:
                return
        temp_msg = await message.reply("<code>Tunggu Sebentar...</code>")
        try:
            messages = await get_messages(client, ids)
        except BaseException:
            # Send custom error message with media support
            sent = await send_custom_message(client, message.from_user.id, "error", quote=True)
            if not sent:
                # Fallback to default message
                await message.reply_text("<b>Telah Terjadi Error </b>🥺")
            return
        await temp_msg.delete()

        for msg in messages:
            # Check user daily limit first
            is_allowed = check_user_daily_limit(message.from_user.id)

            if not is_allowed:
                # Send custom limit message with media support
                sent = await send_custom_message(client, message.from_user.id, "limit", quote=True)
                if not sent:
                    # Fallback to default message
                    await message.reply_text("X LIMIT HARIAN HABIS!\n\nAnda sudah mencapai batas download harian.\nCoba lagi besok!", quote=True)
                continue
            
            # Check content protection before sending
            is_allowed, content_msg = check_content_protection(msg.id, message.from_user.id)

            if not is_allowed:
                # Send custom protected message with media support
                if content_msg == "protected_limit_exceeded":
                    sent = await send_custom_message(client, message.from_user.id, "protected", quote=True)
                    if not sent:
                        # Fallback to default message
                        await message.reply_text("X LIMIT DOWNLOAD HABIS!\n\nKonten ini sudah mencapai batas download maksimal.", quote=True)
                else:
                    # For other content messages (like remaining limit info)
                    await message.reply_text(content_msg, quote=True)
                continue
            
            # Update user tracking (successful download)
            update_user_tracking(message.from_user.id)

            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(
                    previouscaption=msg.caption.html if msg.caption else "",
                    filename=msg.document.file_name,
                )
            else:
                caption = msg.caption.html if msg.caption else ""

            # Build custom buttons if available
            custom_buttons = get_custom_buttons()
            
            if custom_buttons:
                reply_markup = InlineKeyboardMarkup(custom_buttons)
            elif not DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            
            # Add daily limit info to caption
            user_stats = get_user_stats(message.from_user.id)
            daily_info = f"Limit harian: {user_stats['today_downloads']}/{user_stats['daily_limit']} (Sisa: {user_stats['remaining']})"
            caption = f"{caption}\n\n{daily_info}" if caption else daily_info
            
            # Add content limit info to caption if content is limited
            if content_msg and "Sisa limit" in content_msg:
                caption = f"{caption}\n{content_msg}" if caption else content_msg

            try:
                await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    protect_content=PROTECT_CONTENT,
                    reply_markup=reply_markup,
                )
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    protect_content=PROTECT_CONTENT,
                    reply_markup=reply_markup,
                )
            except BaseException:
                pass
    else:
        out = start_button(client)
        await message.reply_text(
            text=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=f"@{message.from_user.username}"
                if message.from_user.username
                else None,
                mention=message.from_user.mention,
                id=message.from_user.id,
            ),
            reply_markup=InlineKeyboardMarkup(out),
            quote=True,
        )


    return


@Bot.on_message(filters.command("start") & filters.private)
async def not_joined(client: Bot, message: Message):
    buttons = fsub_button(client, message)
    await message.reply(
        text=FORCE_MSG.format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=f"@{message.from_user.username}"
            if message.from_user.username
            else None,
            mention=message.from_user.mention,
            id=message.from_user.id,
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True,
    )


@Bot.on_message(filters.command(["users", "stats"]) & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(
        chat_id=message.chat.id, text="<code>Processing ...</code>"
    )
    users = await full_userbase()
    stats = get_user_stats()

    stats_text = f"""
<b>📊 BOT STATISTICS</b>

<b>👥 Total Users:</b> {len(users):,}
<b>🔥 Active Today:</b> {stats['active_today']}
<b>📈 Total Registered:</b> {stats['total_users']:,}

<b>💾 Database:</b> {'PostgreSQL' if 'postgresql' in DB_URI else 'SQLite'}
<b>🔄 Status:</b> Active & Persistent
"""

    await msg.edit(stats_text)


@Bot.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        try:
            query = query_msg()
            if not query:
                await message.reply("❌ <b>Tidak ada pengguna yang ditemukan untuk broadcast!</b>")
                return
        except Exception as e:
            await message.reply(f"❌ <b>Gagal mengambil data pengguna: {e}</b>")
            return

        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        flood_waits = 0

        pls_wait = await message.reply(
            "<code>Broadcasting Message Tunggu Sebentar...</code>"
        )

        # Determine broadcast type and prepare content
        broadcast_data = {
            "type": "text",
            "content": None,
            "caption": "",
            "media_id": None
        }

        # Check message type
        if broadcast_msg.photo:
            broadcast_data["type"] = "photo"
            broadcast_data["media_id"] = broadcast_msg.photo.file_id
            broadcast_data["caption"] = broadcast_msg.caption or ""
        elif broadcast_msg.video:
            broadcast_data["type"] = "video"
            broadcast_data["media_id"] = broadcast_msg.video.file_id
            broadcast_data["caption"] = broadcast_msg.caption or ""
        elif broadcast_msg.document:
            broadcast_data["type"] = "document"
            broadcast_data["media_id"] = broadcast_msg.document.file_id
            broadcast_data["caption"] = broadcast_msg.caption or ""
        elif broadcast_msg.audio:
            broadcast_data["type"] = "audio"
            broadcast_data["media_id"] = broadcast_msg.audio.file_id
            broadcast_data["caption"] = broadcast_msg.caption or ""
        elif broadcast_msg.text:
            broadcast_data["type"] = "text"
            broadcast_data["content"] = broadcast_msg.text
        else:
            await pls_wait.edit("❌ <b>Tipe pesan tidak didukung untuk broadcast!</b>\n\n<b>Supported:</b> Text, Photo, Video, Document, Audio")
            return

        # Process HTML formatting in caption/text
        if broadcast_data["caption"]:
            # Basic HTML support
            broadcast_data["caption"] = broadcast_data["caption"].replace('<b>', '<b>').replace('</b>', '</b>')
            broadcast_data["caption"] = broadcast_data["caption"].replace('<i>', '<i>').replace('</i>', '</i>')
            broadcast_data["caption"] = broadcast_data["caption"].replace('<blockquote>', '┌\n│ ').replace('</blockquote>', '\n└')
            broadcast_data["caption"] = broadcast_data["caption"].replace('\\n', '\n')

        if broadcast_data["content"]:
            broadcast_data["content"] = broadcast_data["content"].replace('<b>', '<b>').replace('</b>', '</b>')
            broadcast_data["content"] = broadcast_data["content"].replace('<i>', '<i>').replace('</i>', '</i>')
            broadcast_data["content"] = broadcast_data["content"].replace('<blockquote>', '┌\n│ ').replace('</blockquote>', '\n└')
            broadcast_data["content"] = broadcast_data["content"].replace('\\n', '\n')

        # Check if message contains placeholders
        has_placeholders = any(placeholder in (broadcast_data["caption"] or "") or placeholder in (broadcast_data["content"] or "")
                             for placeholder in ['{ID}', '{NAME}', '{SURNAME}', '{NAMESURNAME}', '{LANG}', '{DATE}', '{TIME}', '{WEEKDAY}', '{MENTION}', '{USERNAME}'])

        # Broadcast to all users
        for row in query:
            chat_id = int(row[0])
            if chat_id not in ADMINS:
                try:
                    # Prepare personalized content
                    caption = broadcast_data["caption"]
                    content = broadcast_data["content"]

                    if has_placeholders:
                        # Get user info for personalization
                        try:
                            user = await client.get_users(chat_id)
                            caption = replace_placeholders(caption, user)
                            content = replace_placeholders(content, user)
                        except Exception as e:
                            print(f"Failed to get user info for {chat_id}: {e}")
                            # Continue with original content if user info unavailable
                            await asyncio.sleep(0.1)

                    # Send based on type
                    if broadcast_data["type"] == "photo":
                        await client.send_photo(
                            chat_id=chat_id,
                            photo=broadcast_data["media_id"],
                            caption=caption,
                            parse_mode="HTML",
                            protect_content=PROTECT_CONTENT
                        )
                    elif broadcast_data["type"] == "video":
                        await client.send_video(
                            chat_id=chat_id,
                            video=broadcast_data["media_id"],
                            caption=caption,
                            parse_mode="HTML",
                            protect_content=PROTECT_CONTENT
                        )
                    elif broadcast_data["type"] == "document":
                        await client.send_document(
                            chat_id=chat_id,
                            document=broadcast_data["media_id"],
                            caption=caption,
                            parse_mode="HTML",
                            protect_content=PROTECT_CONTENT
                        )
                    elif broadcast_data["type"] == "audio":
                        await client.send_audio(
                            chat_id=chat_id,
                            audio=broadcast_data["media_id"],
                            caption=caption,
                            parse_mode="HTML",
                            protect_content=PROTECT_CONTENT
                        )
                    else:  # text
                        await client.send_message(
                            chat_id=chat_id,
                            text=content,
                            parse_mode="HTML",
                            protect_content=PROTECT_CONTENT
                        )

                    successful += 1

                except FloodWait as e:
                    flood_waits += 1
                    await asyncio.sleep(e.x)
                    # Retry after flood wait
                    try:
                        if broadcast_data["type"] == "photo":
                            await client.send_photo(chat_id=chat_id, photo=broadcast_data["media_id"], caption=caption, parse_mode="HTML", protect_content=PROTECT_CONTENT)
                        elif broadcast_data["type"] == "video":
                            await client.send_video(chat_id=chat_id, video=broadcast_data["media_id"], caption=caption, parse_mode="HTML", protect_content=PROTECT_CONTENT)
                        elif broadcast_data["type"] == "document":
                            await client.send_document(chat_id=chat_id, document=broadcast_data["media_id"], caption=caption, parse_mode="HTML", protect_content=PROTECT_CONTENT)
                        elif broadcast_data["type"] == "audio":
                            await client.send_audio(chat_id=chat_id, audio=broadcast_data["media_id"], caption=caption, parse_mode="HTML", protect_content=PROTECT_CONTENT)
                        else:
                            await client.send_message(chat_id=chat_id, text=content, parse_mode="HTML", protect_content=PROTECT_CONTENT)
                        successful += 1
                    except Exception:
                        unsuccessful += 1

                except UserIsBlocked:
                    await delete_user(chat_id)
                    blocked += 1
                except InputUserDeactivated:
                    await delete_user(chat_id)
                    deleted += 1
                except BaseException as e:
                    print(f"Broadcast error for {chat_id}: {e}")
                    unsuccessful += 1
                    # Update status message periodically
                    if total % 20 == 0:
                        status = f"<b>📢 Broadcasting in progress...</b>\n\n<b>📊 Progress:</b> {total} users processed"
                        try:
                            await pls_wait.edit(status)
                        except Exception as e:
                            print(f"Failed to update progress message: {e}")
                total += 1

                # Update status message periodically
                if total % 20 == 0:
                    status = f"<b>📢 Broadcasting in progress...</b>\n\n<b>📊 Progress:</b> {total} users processed"
                    try:
                        await pls_wait.edit(status)
                    except Exception as e:
                        print(f"Failed to update progress message: {e}")
                        # Fallback to sending a new message if editing fails
                        await message.reply(status)

                # Rate limiting to avoid flood (slower when using placeholders)
                delay = 0.1 if has_placeholders else 0.05
                await asyncio.sleep(delay)

        status = f"""<b><u>📢 BROADCAST COMPLETED</u></b>

<b>📊 Statistics:</b>
├ <b>Total Users:</b> <code>{total}</code>
├ <b>Successful:</b> <code>{successful}</code>
├ <b>Failed:</b> <code>{unsuccessful}</code>
├ <b>Blocked:</b> <code>{blocked}</code>
├ <b>Deleted:</b> <code>{deleted}</code>
└ <b>Flood Waits:</b> <code>{flood_waits}</code>

<b>📝 Message Type:</b> {broadcast_data["type"].title()}"""

        try:
            await pls_wait.edit(status)
        except Exception as e:
            print(f"Failed to update status message: {e}")
            # Fallback to sending a new message if editing fails
            try:
                await message.reply(status)
            except Exception as e:
                print(f"Failed to send fallback status message: {e}")

        return
    else:
        try:
            msg = await message.reply(
                "<code>❌ Gunakan perintah ini dengan reply ke pesan yang ingin di-broadcast!</code>\n\n"
                "<b>Supported media:</b> Text, Photo, Video, Document, Audio\n"
                "<b>HTML Support:</b> <code><b></code>, <code><i></code>, <code><blockquote></code>, <code>\\n</code>\n"
                "<b>Placeholder Variables:</b>\n"
                "<code>{ID}</code> - User ID\n"
                "<code>{NAME}</code> - First name\n"
                "<code>{SURNAME}</code> - Last name\n"
                "<code>{NAMESURNAME}</code> - Full name\n"
                "<code>{USERNAME}</code> - Username\n"
                "<code>{MENTION}</code> - User mention\n"
                "<code>{DATE}</code> - Current date\n"
                "<code>{TIME}</code> - Current time\n"
                "<code>{WEEKDAY}</code> - Day name\n"
                "<code>{LANG}</code> - Language code"
            )
            await asyncio.sleep(15)
            await msg.delete()
        except Exception as e:
            print(f"Failed to send help message: {e}")


@Bot.on_message(filters.command("ping"))
async def ping_pong(client, m: Message):
    start = time()
    current_time = datetime.utcnow()
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime = await _human_time_duration(int(uptime_sec))
    m_reply = await m.reply_text("Pinging...")
    delta_ping = time() - start
    await m_reply.edit_text(
        "<b>PONG!!</b>🏓 \n"
        f"<b>• Pinger -</b> <code>{delta_ping * 1000:.3f}ms</code>\n"
        f"<b>• Uptime -</b> <code>{uptime}</code>\n"
    )


@Bot.on_message(filters.command("uptime"))
async def get_uptime(client, m: Message):
    current_time = datetime.utcnow()
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime = await _human_time_duration(int(uptime_sec))
    await m.reply_text(
        "🤖 <b>Bot Status:</b>\n"
        f"• <b>Uptime:</b> <code>{uptime}</code>\n"
        f"• <b>Start Time:</b> <code>{START_TIME_ISO}</code>"
    )
