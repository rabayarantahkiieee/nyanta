# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import asyncio
from datetime import datetime
from pyrogram import filters, enums
from pyrogram.types import Message
from pyrogram.errors import UserNotParticipant

from bot import Bot
from config import ADMINS, FORCE_SUB_CHANNELS, FORCE_SUB_GROUPS


@Bot.on_message(filters.command("id") & filters.private)
async def showid(client, message):
    """Enhanced ID command with comprehensive user information"""
    try:
        user = message.from_user
        chat = message.chat

        # Basic user info
        user_info = f"""
<b>👤 USER INFORMATION</b>

<b>📋 Basic Info:</b>
├ <b>User ID:</b> <code>{user.id}</code>
├ <b>Username:</b> @{user.username if user.username else "None"}
├ <b>First Name:</b> {user.first_name}
├ <b>Last Name:</b> {user.last_name if user.last_name else "None"}
└ <b>Language:</b> {user.language_code if user.language_code else "Unknown"}

<b>📅 Account Info:</b>
├ <b>Account Created:</b> {datetime.fromtimestamp(user.date).strftime('%Y-%m-%d %H:%M:%S UTC') if hasattr(user, 'date') and user.date else "Unknown"}
├ <b>Is Bot:</b> {"✅ Yes" if user.is_bot else "❌ No"}
├ <b>Is Premium:</b> {"✅ Yes" if getattr(user, 'is_premium', False) else "❌ No"}
├ <b>Is Verified:</b> {"✅ Yes" if getattr(user, 'is_verified', False) else "❌ No"}
└ <b>Is Restricted:</b> {"✅ Yes" if getattr(user, 'is_restricted', False) else "❌ No"}

<b>💬 Chat Info:</b>
├ <b>Chat ID:</b> <code>{chat.id}</code>
├ <b>Chat Type:</b> {chat.type.value.title()}
└ <b>Chat Title:</b> {getattr(chat, 'title', 'Private Chat')}
"""

        # Check subscription status
        sub_status = "\n<b>🔗 Subscription Status:</b>\n"

        channel_count = len(FORCE_SUB_CHANNELS)
        group_count = len(FORCE_SUB_GROUPS)

        for i, channel_id in enumerate(FORCE_SUB_CHANNELS):
            try:
                member = await client.get_chat_member(channel_id, user.id)
                channel_info = await client.get_chat(channel_id)
                prefix = "├" if i < channel_count - 1 or group_count > 0 else "└"
                sub_status += f"{prefix} <b>Channel ({channel_info.title}):</b> ✅ {member.status.value.title()}\n"
            except UserNotParticipant:
                channel_info = await client.get_chat(channel_id)
                prefix = "├" if i < channel_count - 1 or group_count > 0 else "└"
                sub_status += f"{prefix} <b>Channel ({channel_info.title}):</b> ❌ Not Joined\n"
            except Exception:
                prefix = "├" if i < channel_count - 1 or group_count > 0 else "└"
                sub_status += f"{prefix} <b>Channel {i+1}:</b> ⚠️ Error checking\n"

        for i, group_id in enumerate(FORCE_SUB_GROUPS):
            try:
                member = await client.get_chat_member(group_id, user.id)
                group_info = await client.get_chat(group_id)
                prefix = "└" if i == group_count - 1 else "├"
                sub_status += f"{prefix} <b>Group ({group_info.title}):</b> ✅ {member.status.value.title()}\n"
            except UserNotParticipant:
                group_info = await client.get_chat(group_id)
                prefix = "└" if i == group_count - 1 else "├"
                sub_status += f"{prefix} <b>Group ({group_info.title}):</b> ❌ Not Joined\n"
            except Exception:
                prefix = "└" if i == group_count - 1 else "├"
                sub_status += f"{prefix} <b>Group {i+1}:</b> ⚠️ Error checking\n"

        if not FORCE_SUB_CHANNELS and not FORCE_SUB_GROUPS:
            sub_status += "├ <b>Status:</b> No force subscription required\n"

        # Admin status
        admin_status = f"\n<b>👑 Admin Status:</b> {'✅ Yes' if user.id in ADMINS else '❌ No'}"

        # Bot info
        bot_info = f"""

<b>🤖 Bot Information:</b>
├ <b>Bot Username:</b> @{client.username}
├ <b>Bot Name:</b> {client.namebot}
├ <b>Bot ID:</b> <code>{client.bot_token.split(':')[0]}</code>
└ <b>Pyrogram Version:</b> {getattr(client, 'pyrogram_version', 'Unknown')}
"""

        full_message = user_info + sub_status + admin_status + bot_info

        await message.reply_text(full_message, quote=True)

    except Exception as e:
        await message.reply_text(
            f"❌ <b>Error getting user info:</b> {str(e)}",
            quote=True
        )


@Bot.on_message(filters.command("id") & filters.group)
async def showid_group(client, message):
    """Enhanced ID command for groups"""
    try:
        user = message.from_user
        chat = message.chat

        # Get replied user if any
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            target_text = " (Replied User)"
        else:
            target_user = user
            target_text = " (Yourself)"

        user_info = f"""
<b>👥 GROUP USER INFORMATION{target_text}</b>

<b>📋 User Info:</b>
├ <b>User ID:</b> <code>{target_user.id}</code>
├ <b>Username:</b> @{target_user.username if target_user.username else "None"}
├ <b>Name:</b> {target_user.first_name} {target_user.last_name if target_user.last_name else ""}
└ <b>Mention:</b> {target_user.mention}

<b>💬 Chat Info:</b>
├ <b>Chat ID:</b> <code>{chat.id}</code>
├ <b>Chat Title:</b> {chat.title}
├ <b>Chat Type:</b> {chat.type.value.title()}
└ <b>Member Count:</b> {getattr(chat, 'members_count', 'Unknown')}
"""

        # Check if user is admin in group
        try:
            member = await client.get_chat_member(chat.id, target_user.id)
            user_info += f"\n<b>👑 Group Status:</b> {member.status.value.title()}"
            if member.status.value in ['administrator', 'creator']:
                user_info += f"\n<b>⚡ Admin Rights:</b> {', '.join([right for right in dir(member) if right.endswith('_rights') and getattr(member, right, None)])}"
        except Exception:
            user_info += f"\n<b>👑 Group Status:</b> Unknown"

        await message.reply_text(user_info, quote=True)

    except Exception as e:
        await message.reply_text(
            f"❌ <b>Error getting group user info:</b> {str(e)}",
            quote=True
        )


@Bot.on_message(filters.command("stats"))
async def user_stats(client, message):
    """Show user statistics"""
    try:
        user = message.from_user

        # Get user count from database
        from database.sql import full_userbase
        users = await full_userbase()
        total_users = len(users)

        # Get bot uptime
        from plugins.start import START_TIME
        from datetime import datetime
        current_time = datetime.utcnow()
        uptime = current_time - START_TIME

        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        stats = f"""
<b>📊 BOT STATISTICS</b>

<b>👥 User Stats:</b>
├ <b>Total Users:</b> {total_users:,}
├ <b>Your ID:</b> <code>{user.id}</code>
├ <b>Username:</b> @{user.username if user.username else "None"}
└ <b>Language:</b> {user.language_code if user.language_code else "Unknown"}

<b>⏰ Bot Uptime:</b>
├ <b>Days:</b> {days}
├ <b>Hours:</b> {hours}
├ <b>Minutes:</b> {minutes}
└ <b>Seconds:</b> {seconds}

<b>🤖 Bot Info:</b>
├ <b>Username:</b> @{client.username}
├ <b>Name:</b> {client.namebot}
└ <b>Version:</b> 4.0.0 Enhanced
"""

        await message.reply_text(stats, quote=True)

    except Exception as e:
        await message.reply_text(
            f"❌ <b>Error getting stats:</b> {str(e)}",
            quote=True
        )


@Bot.on_message(filters.command("ping"))
async def enhanced_ping(client, message):
    """Enhanced ping with more details"""
    import time
    start_time = time.time()

    # Send initial message
    ping_msg = await message.reply_text("🏓 <b>Pinging...</b>", quote=True)

    # Calculate ping
    ping_time = time.time() - start_time
    ping_ms = round(ping_time * 1000, 2)

    # Get system info
    import psutil
    import platform

    # CPU and Memory
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent

    # System info
    system_info = platform.system()
    python_version = platform.python_version()

    enhanced_ping_text = f"""
<b>🏓 PONG! Enhanced Ping Test</b>

<b>⚡ Response Time:</b>
└ <b>Ping:</b> <code>{ping_ms}ms</code>

<b>💻 System Status:</b>
├ <b>CPU Usage:</b> <code>{cpu_percent}%</code>
├ <b>Memory Usage:</b> <code>{memory_percent}%</code>
├ <b>System:</b> <code>{system_info}</code>
└ <b>Python:</b> <code>{python_version}</code>

<b>🤖 Bot Status:</b>
├ <b>Username:</b> @{client.username}
├ <b>Status:</b> ✅ Online
└ <b>Response:</b> ⚡ Fast
"""

    await ping_msg.edit_text(enhanced_ping_text)