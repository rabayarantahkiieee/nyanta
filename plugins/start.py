# ============================================================================
# BROADCAST SYSTEM - Refactored & Enhanced
# ============================================================================

import asyncio
import json
import os
import re
from datetime import datetime
from time import time
import logging
import sys

from bot import Bot
from config import (
    ADMINS,
    CUSTOM_CAPTION,
    DISABLE_CHANNEL_BUTTON,
    FORCE_MSG,
    PROTECT_CONTENT,
    START_MSG,
)
from database.sql import add_user, delete_user, full_userbase, query_msg, update_user_subscription_status, sync_user_activity, mark_user_blocked, get_user_stats as get_db_user_stats
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from config import decode, get_messages, subsall, subsch, subsgc

from .button import fsub_button, start_button
from .content_utils import check_content_protection
from .user_limits import check_user_daily_limit, get_user_stats

# Setup logging for broadcast system
logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS FOR BROADCAST
# ============================================================================

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


def process_html_formatting(text):
    """Process HTML formatting in text content"""
    if not text:
        return text

    # Only process \n to newlines, leave HTML tags as is for Pyrogram HTML parsing
    text = text.replace('\\n', '\n')

    return text


async def send_broadcast_message(client, chat_id, broadcast_data, caption=None, content=None, protect_content=PROTECT_CONTENT):
    """
    Helper function to send broadcast message based on type.
    Supports: text, photo, video, document, audio, voice, animation, sticker, video_note
    """
    msg_type = broadcast_data["type"]
    media_id = broadcast_data.get("media_id")
    reply_markup = broadcast_data.get("reply_markup")
    
    try:
        if msg_type == "photo":
            return await client.send_photo(
                chat_id=chat_id,
                photo=media_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                protect_content=protect_content,
                reply_markup=reply_markup
            )
        
        elif msg_type == "video":
           return await client.send_video(
               chat_id=chat_id,
               video=media_id,
               caption=caption,
               parse_mode=ParseMode.HTML,
               protect_content=protect_content,
               reply_markup=reply_markup
           )

        elif msg_type == "document":
           return await client.send_document(
               chat_id=chat_id,
               document=media_id,
               caption=caption,
               parse_mode=ParseMode.HTML,
               protect_content=protect_content,
               reply_markup=reply_markup
           )

        elif msg_type == "audio":
           return await client.send_audio(
               chat_id=chat_id,
               audio=media_id,
               caption=caption,
               parse_mode=ParseMode.HTML,
               protect_content=protect_content,
               reply_markup=reply_markup
           )

        elif msg_type == "voice":
           return await client.send_voice(
               chat_id=chat_id,
               voice=media_id,
               caption=caption,
               parse_mode=ParseMode.HTML,
               protect_content=protect_content,
               reply_markup=reply_markup
           )

        elif msg_type == "animation":
           return await client.send_animation(
               chat_id=chat_id,
               animation=media_id,
               caption=caption,
               parse_mode=ParseMode.HTML,
               protect_content=protect_content,
               reply_markup=reply_markup
           )

        elif msg_type == "sticker":
           return await client.send_sticker(
               chat_id=chat_id,
               sticker=media_id,
               protect_content=protect_content
           )

        elif msg_type == "video_note":
           return await client.send_video_note(
               chat_id=chat_id,
               video_note=media_id,
               protect_content=protect_content
           )

        elif msg_type == "text":
           return await client.send_message(
               chat_id=chat_id,
               text=content,
               parse_mode=ParseMode.HTML,
               protect_content=protect_content,
               reply_markup=reply_markup
           )
        
        else:
            logger.warning(f"Unknown message type: {msg_type}")
            return None
    
    except Exception as e:
        logger.error(f"Error sending {msg_type} to {chat_id}: {e}")
        raise


async def get_broadcast_message_type(broadcast_msg):
    """
    Determine broadcast message type and prepare data.
    Returns dict with type, media_id, caption, reply_markup
    """
    broadcast_data = {
        "type": "text",
        "content": None,
        "caption": "",
        "media_id": None,
        "reply_markup": None
    }
    
    # Extract inline keyboard if available
    if broadcast_msg.reply_markup and isinstance(broadcast_msg.reply_markup, InlineKeyboardMarkup):
        broadcast_data["reply_markup"] = broadcast_msg.reply_markup

    # Parse button markup from content/caption if no reply_markup exists
    if not broadcast_data["reply_markup"]:
        text_to_parse = broadcast_data.get("content", "") or broadcast_data.get("caption", "")
        if text_to_parse:
            button_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
            buttons = re.findall(button_pattern, text_to_parse)
            if buttons:
                keyboard_buttons = []
                current_row = []
                for button_text, button_url in buttons:
                    if button_text and button_url:
                        current_row.append(
                            InlineKeyboardButton(
                                text=button_text,
                                url=button_url
                            )
                        )
                        if len(current_row) == 2:
                            keyboard_buttons.append(current_row)
                            current_row = []
                if current_row:
                    keyboard_buttons.append(current_row)
                if keyboard_buttons:
                    broadcast_data["reply_markup"] = InlineKeyboardMarkup(keyboard_buttons)
                    # Remove button markup from text
                    if broadcast_data.get("content"):
                        broadcast_data["content"] = re.sub(button_pattern, '', broadcast_data["content"]).strip().replace("&&", "").strip()
                    if broadcast_data.get("caption"):
                        broadcast_data["caption"] = re.sub(button_pattern, '', broadcast_data["caption"]).strip().replace("&&", "").strip()
    
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

    elif broadcast_msg.voice:
        broadcast_data["type"] = "voice"
        broadcast_data["media_id"] = broadcast_msg.voice.file_id
        broadcast_data["caption"] = broadcast_msg.caption or ""

    elif broadcast_msg.animation:
        broadcast_data["type"] = "animation"
        broadcast_data["media_id"] = broadcast_msg.animation.file_id
        broadcast_data["caption"] = broadcast_msg.caption or ""

    elif broadcast_msg.sticker:
        broadcast_data["type"] = "sticker"
        broadcast_data["media_id"] = broadcast_msg.sticker.file_id

    elif broadcast_msg.video_note:
        broadcast_data["type"] = "video_note"
        broadcast_data["media_id"] = broadcast_msg.video_note.file_id

    elif broadcast_msg.text is not None:
        broadcast_data["type"] = "text"
        broadcast_data["content"] = broadcast_msg.text

    else:
        return None  # Unsupported type

    # Add custom buttons if no reply_markup is present
    if not broadcast_data["reply_markup"]:
        custom_buttons = get_custom_buttons()
        if custom_buttons:
            broadcast_data["reply_markup"] = InlineKeyboardMarkup(custom_buttons)

    return broadcast_data


def check_placeholders(text):
    """Check if text contains placeholders"""
    placeholders = ['{ID}', '{NAME}', '{SURNAME}', '{NAMESURNAME}', '{LANG}', 
                   '{DATE}', '{TIME}', '{WEEKDAY}', '{MENTION}', '{USERNAME}']
    return any(placeholder in (text or "") for placeholder in placeholders)


async def update_progress_message(pls_wait, total, successful, failed, blocked, deleted, flood_waits):
    """Update progress message with current stats"""
    status = f"<b>📢 Broadcasting in progress...</b>\n\n" \
             f"<b>📊 Progress:</b> {total} users processed\n" \
             f"├ <b>✅ Success:</b> {successful}\n" \
             f"├ <b>❌ Failed:</b> {failed}\n" \
             f"├ <b>🚫 Blocked:</b> {blocked}\n" \
             f"├ <b>🗑️ Deleted:</b> {deleted}\n" \
             f"└ <b>⏳ Flood Waits:</b> {flood_waits}"
    
    try:
        await pls_wait.edit(status)
    except Exception:
        pass  # Ignore update errors


async def send_final_report(pls_wait, message, total, successful, failed, blocked, deleted, flood_waits, msg_type):
    """Send final broadcast report with success rate"""
    success_rate = ((successful/total)*100) if total > 0 else 0
    
    status = f"""<b><u>📢 BROADCAST COMPLETED</u></b>

<b>📊 Statistics:</b>
├ <b>Total Users:</b> <code>{total}</code>
├ <b>Successful:</b> <code>{successful}</code>
├ <b>Failed:</b> <code>{failed}</code>
├ <b>Blocked:</b> <code>{blocked}</code>
├ <b>Deleted:</b> <code>{deleted}</code>
├ <b>Flood Waits:</b> <code>{flood_waits}</code>
└ <b>Success Rate:</b> <code>{success_rate:.1f}%</code>

<b>📝 Message Type:</b> {msg_type.title()}"""
    
    try:
        await pls_wait.edit(status)
    except Exception:
        try:
            await message.reply(status)
        except Exception:
            pass  # Ignore sending errors


def log_broadcast_activity(admin_id, msg_type, total_users, successful, failed, blocked=0, deleted=0, flood_waits=0):
    """Log broadcast activity for audit trail with detailed information"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success_rate = ((successful/total_users)*100) if total_users > 0 else 0
    
    log_entry = f"[{timestamp}] BROADCAST | Admin: {admin_id} | Type: {msg_type} | " \
                f"Total: {total_users} | Success: {successful} | Failed: {failed} | " \
                f"Blocked: {blocked} | Deleted: {deleted} | FloodWaits: {flood_waits} | " \
                f"Success Rate: {success_rate:.1f}%"
    
    logger.info(log_entry)
    
    # Also print to console for visibility
    print(f"[BROADCAST] {log_entry}")
    
    # Log to file for persistent storage
    try:
        with open('broadcast_logs.txt', 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except Exception as e:
        logger.error(f"Failed to write to broadcast log file: {e}")


def log_broadcast_error(chat_id, error_type, error_message, retry_count=0):
    """Log detailed broadcast errors for debugging"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_entry = f"[{timestamp}] BROADCAST_ERROR | ChatID: {chat_id} | " \
                 f"Type: {error_type} | Message: {error_message} | " \
                 f"Retries: {retry_count}"
    
    logger.error(error_entry)
    
    try:
        with open('broadcast_errors.txt', 'a', encoding='utf-8') as f:
            f.write(error_entry + '\n')
    except Exception as e:
        logger.error(f"Failed to write to broadcast error log: {e}")


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

    # Sync user activity - this will add or update user in database
    # Also reactivates user if they were previously blocked/deleted
    sync_user_activity(id, user_name)
    
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

        # Initialize limit message sent flag for this download attempt
        limit_message_sent = False
        
        for msg in messages:
            # Check user daily limit first
            is_allowed = check_user_daily_limit(message.from_user.id)

            if not is_allowed:
                # Send custom limit message with media support only once per download attempt
                if not limit_message_sent:
                    sent = await send_custom_message(client, message.from_user.id, "limit", quote=True)
                    if not sent:
                        # Fallback to default message
                        await message.reply_text("X LIMIT HARIAN HABIS!\n\nAnda sudah mencapai batas download harian.\nCoba lagi besok!", quote=True)
                    limit_message_sent = True
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
    id = message.from_user.id
    user_name = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else None
    )
    
    # Sync user activity even if not subscribed (to track potential users)
    sync_user_activity(id, user_name)
    
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
    users = await full_userbase(include_inactive=False)  # Only active users
    stats = get_db_user_stats()

    stats_text = f"""
<b>📊 BOT STATISTICS</b>

<b>👥 Total Users:</b> {stats['total_users']:,}
<b>🔥 Active Users:</b> {stats['active_users']:,}
<b>🚫 Blocked:</b> {stats['blocked_users']:,}
<b>🗑️ Deleted:</b> {stats['deleted_users']:,}
<b>🔥 Active Today:</b> {stats['active_today']}

<b>💾 Database:</b> {'PostgreSQL' if 'postgresql' in DB_URI else 'SQLite'}
<b>🔄 Status:</b> Active & Persistent
"""

    await msg.edit(stats_text)


@Bot.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    """
    Enhanced broadcast function with batch processing, concurrency control, and comprehensive error handling.
    
    Features:
    - Batch processing for better performance
    - Configurable concurrency control
    - Advanced error handling and retry mechanism
    - Detailed logging and monitoring
    - Support for all media types
    - HTML formatting and placeholder variables
    - Real-time progress tracking
    """
    
    if not message.reply_to_message:
        try:
            msg = await message.reply(
                "<code>❌ Gunakan perintah ini dengan reply ke pesan yang ingin di-broadcast!</code>\n\n"
                "<b>📱 Supported Media:</b> Text, Photo, Video, Document, Audio, Voice, Animation, Sticker, Video Note\n"
                "<b>🎨 HTML Support:</b> <code><b></code>, <code><i></code>, <code><blockquote></code>, <code>\\n</code>\n"
                "<b>🔘 Button Markup:</b> <code>[Button Text](Button URL)</code>\n"
                "<code>[Btn1](URL1) && [Btn2](URL2)</code> untuk 2 buttons per row\n"
                "<b>📊 Placeholder Variables:</b>\n"
                "<code>{ID}</code> - User ID\n"
                "<code>{NAME}</code> - First name\n"
                "<code>{SURNAME}</code> - Last name\n"
                "<code>{NAMESURNAME}</code> - Full name\n"
                "<code>{USERNAME}</code> - Username\n"
                "<code>{MENTION}</code> - User mention\n"
                "<code>{DATE}</code> - Current date\n"
                "<code>{TIME}</code> - Current time\n"
                "<code>{WEEKDAY}</code> - Day name\n"
                "<code>{LANG}</code> - Language code",
                parse_mode=ParseMode.HTML
            )
            await asyncio.sleep(15)
            await msg.delete()
        except Exception as e:
            logger.error(f"Failed to send help message: {e}")
        return
    
    # Get users from database with error handling
    try:
        query = await query_msg(active_only=False)
        if not query:
            await message.reply("❌ <b>Tidak ada pengguna yang ditemukan untuk broadcast!</b>")
            return

        # Convert to list of user IDs
        user_ids = [int(row[0]) for row in query]

        # Filter valid user IDs (exclude admins and invalid IDs)
        user_ids = [id for id in user_ids if isinstance(id, int) and 0 < id <= 2000000000 and id not in ADMINS]

    except Exception as e:
        logger.error(f"Failed to query users: {e}", exc_info=True)
        await message.reply(f"❌ <b>Gagal mengambil data pengguna: {str(e)}</b>")
        return
    
    broadcast_msg = message.reply_to_message
    
    # Initialize counters
    total = 0
    successful = 0
    blocked = 0
    deleted = 0
    unsuccessful = 0
    flood_waits = 0
    retries = 0
    max_retries = 3  # Maximum retry attempts
    start_time = time()  # Track broadcast duration
    
    # Show initial progress message
    pls_wait = await message.reply(
        "<code>📢 Preparing broadcast...</code>"
    )
    
    # Get broadcast message type and data
    broadcast_data = await get_broadcast_message_type(broadcast_msg)
    
    if broadcast_data is None:
        await pls_wait.edit(
            "❌ <b>Tipe pesan tidak didukung untuk broadcast!</b>\n\n"
            "<b>Supported:</b> Text, Photo, Video, Document, Audio, Voice, Animation, Sticker, Video Note"
        )
        return
    
    # Process HTML formatting
    broadcast_data["caption"] = process_html_formatting(broadcast_data.get("caption", ""))
    broadcast_data["content"] = process_html_formatting(broadcast_data.get("content"))
    
    # Check if message contains placeholders
    has_placeholders = check_placeholders(broadcast_data.get("caption", "")) or check_placeholders(broadcast_data.get("content"))
    
    # Get configuration values
    delay = 0.15 if has_placeholders else 0.05
    batch_size = 10  # Process in batches
    max_concurrent = 5  # Maximum concurrent tasks
    
    # Update initial status
    await update_progress_message(pls_wait, 0, 0, 0, 0, 0, 0)
    
    logger.info(f"Starting enhanced broadcast to {len(user_ids)} users | Type: {broadcast_data['type']} | Has placeholders: {has_placeholders}")
    
    # Process users in batches
    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i:i + batch_size]
        
        # Create tasks for this batch
        tasks = []
        for chat_id in batch:
            # Skip admins
            if chat_id in ADMINS:
                continue
            
            tasks.append(send_broadcast_to_user(
                client=client,
                chat_id=chat_id,
                broadcast_data=broadcast_data,
                has_placeholders=has_placeholders,
                max_retries=max_retries
            ))
        
        # Process batch with concurrency control
        if tasks:
            # Process tasks in chunks to respect max_concurrent
            for j in range(0, len(tasks), max_concurrent):
                chunk = tasks[j:j + max_concurrent]
                
                # Execute chunk concurrently
                results = await asyncio.gather(*chunk, return_exceptions=True)
                
                # Process results
                for result in results:
                    if isinstance(result, Exception):
                        # Handle exceptions
                        if isinstance(result, UserIsBlocked):
                            blocked += 1
                        elif isinstance(result, InputUserDeactivated):
                            deleted += 1
                        elif isinstance(result, FloodWait):
                            flood_waits += 1
                        else:
                            unsuccessful += 1
                        
                        logger.error(f"Broadcast error: {str(result)}")
                    else:
                        # Successful result
                        successful += 1
                    
                    total += 1
                    
                    # Update progress every 10 users
                    if total % 10 == 0:
                        await update_progress_message(pls_wait, total, successful, unsuccessful, blocked, deleted, flood_waits)
                
                # Rate limiting
                await asyncio.sleep(delay)
    
    # Send final report
    await send_final_report(pls_wait, message, total, successful, unsuccessful, blocked, deleted, flood_waits, broadcast_data["type"])
    
    # Log broadcast activity for audit with detailed information
    log_broadcast_activity(
        admin_id=message.from_user.id,
        msg_type=broadcast_data["type"],
        total_users=total,
        successful=successful,
        failed=unsuccessful,
        blocked=blocked,
        deleted=deleted,
        flood_waits=flood_waits
    )
    
    # Calculate success rate and duration
    duration = time() - start_time
    success_rate = ((successful/total)*100) if total > 0 else 0
    
    logger.info(f"Broadcast completed | Total: {total} | Success: {successful} | Failed: {unsuccessful} | "
                f"Blocked: {blocked} | Deleted: {deleted} | FloodWaits: {flood_waits} | "
                f"Success Rate: {success_rate:.1f}% | Duration: {duration:.2f}s")


async def send_broadcast_to_user(client, chat_id, broadcast_data, has_placeholders, max_retries):
    """
    Send broadcast message to a single user with retry mechanism and detailed logging.

    Args:
        client: Bot client
        chat_id: User chat ID
        broadcast_data: Broadcast message data
        has_placeholders: Whether message contains placeholders
        max_retries: Maximum retry attempts

    Returns:
        True if successful, Exception if failed
    """
    # Validate chat_id
    if not isinstance(chat_id, int) or chat_id <= 0 or chat_id > 2000000000:
        logger.warning(f"Skipping invalid chat_id: {chat_id}")
        return Exception("Invalid chat_id")

    retry_count = 0
    last_error = None
    start_time = time()
    
    while retry_count <= max_retries:
        try:
            # Prepare personalized content
            caption = broadcast_data["caption"]
            content = broadcast_data["content"]
            
            # Replace placeholders if present
            if has_placeholders:
                try:
                    user = await client.get_users(chat_id)
                    caption = replace_placeholders(caption, user)
                    content = replace_placeholders(content, user)
                    logger.debug(f"Successfully applied placeholders for user {chat_id}")
                except Exception as e:
                    error_msg = f"Failed to get user info for {chat_id}: {e}"
                    logger.warning(error_msg)
                    log_broadcast_error(chat_id, "PLACEHOLDER_ERROR", error_msg, retry_count)
                    # Continue without placeholders
            
            # Send message using helper function
            result = await send_broadcast_message(
                client=client,
                chat_id=chat_id,
                broadcast_data=broadcast_data,
                caption=caption,
                content=content,
                protect_content=PROTECT_CONTENT
            )
            
            if result:
                elapsed = time() - start_time
                logger.info(f"Successfully sent broadcast to {chat_id} in {elapsed:.2f}s (attempts: {retry_count + 1})")
                return True
            else:
                raise Exception("Failed to send message - no result returned")
                
        except FloodWait as e:
            # Handle flood wait with exponential backoff
            # Note: FloodWait has 'value' attribute, not 'x'
            wait_time = min(e.value * (retry_count + 1), 60)  # Max 60 seconds
            error_msg = f"FloodWait for {chat_id} - {e.value}s wait"
            logger.warning(f"{error_msg} - retry {retry_count + 1}/{max_retries} - waiting {wait_time}s")
            log_broadcast_error(chat_id, "FLOOD_WAIT", error_msg, retry_count)
            await asyncio.sleep(wait_time)
            last_error = e
            retry_count += 1
            
        except UserIsBlocked:
            # Mark user as blocked
            error_msg = f"User {chat_id} has blocked the bot"
            logger.warning(error_msg)
            log_broadcast_error(chat_id, "USER_BLOCKED", error_msg)
            mark_user_blocked(chat_id)
            return UserIsBlocked()
            
        except InputUserDeactivated:
            # Mark user as deleted
            error_msg = f"User {chat_id} account is deactivated"
            logger.warning(error_msg)
            log_broadcast_error(chat_id, "USER_DEACTIVATED", error_msg)
            mark_user_blocked(chat_id)  # Reuse for deactivated accounts
            return InputUserDeactivated()
            
        except Exception as e:
            error_msg = f"Broadcast error for {chat_id}: {str(e)}"
            logger.error(f"{error_msg} (attempt {retry_count + 1}/{max_retries})")
            log_broadcast_error(chat_id, type(e).__name__, error_msg, retry_count)
            last_error = e
            retry_count += 1
            
            # Exponential backoff
            if retry_count < max_retries:
                backoff_time = 0.5 * (2 ** retry_count)
                logger.debug(f"Retrying {chat_id} in {backoff_time}s (attempt {retry_count + 1})")
                await asyncio.sleep(backoff_time)
    
    # If we get here, all retries failed
    error_msg = f"Failed to send broadcast to {chat_id} after {max_retries} attempts"
    logger.error(error_msg)
    log_broadcast_error(chat_id, "MAX_RETRIES_EXCEEDED", error_msg, max_retries)
    return last_error if last_error else Exception("Unknown error")


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
