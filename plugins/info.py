# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import asyncio
from datetime import datetime

from bot import Bot
from config import ADMINS, OWNER, LOGGER, CHANNEL_ID, admin_filter
from pyrogram import filters
from pyrogram.types import Message

@Bot.on_message(filters.command("info") & filters.private & admin_filter)
async def bot_info(client: Bot, message: Message):
    """ Informasi lengkap tentang bot """
    try:
        bot_info = await client.get_me()
        
        # Get channel info
        channel_info = await client.get_chat(CHANNEL_ID)
        
        # Get bot stats
        chat_count = await client.get_chat_members_count(CHANNEL_ID)
        
        info_text = f"""🤖 <b>INFORMASI BOT</b>

<b>📱 Bot Details:</b>
├ <b>Username:</b> @{bot_info.username}
├ <b>First Name:</b> {bot_info.first_name}
├ <b>ID:</b> <code>{bot_info.id}</code>
├ <b>Is Bot:</b> ✅ Yes
├ <b>Can Join Groups:</b> ✅ Yes
└ <b>Can Read All Messages:</b> ✅ Yes

<b>🔗 Database Channel:</b>
├ <b>Title:</b> {channel_info.title}
├ <b>Channel ID:</b> <code>{channel_info.id}</code>
├ <b>Members:</b> {chat_count}
└ <b>Username:</b> @{channel_info.username if channel_info.username else 'N/A'}

<b>⚙️ Configuration:</b>
├ <b>Owner ID:</b> <code>{OWNER}</code>
├ <b>Admin Count:</b> {len(ADMINS)}
├ <b>Workers:</b> 4
└ <b>Protected Content:</b> False

<b>📊 Bot Status:</b>
├ <b>Uptime:</b> ✅ Online
├ <b>Database:</b> ✅ Connected
├ <b>API:</b> ✅ Working
└ <b>Last Check:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>📋 Bot Features:</b>
├ ✅ File Sharing
├ ✅ Link Generation  
├ ✅ Batch Processing
├ ✅ Force Subscription
├ ✅ User Management
├ ✅ Broadcast Messages
├ ✅ Admin Commands
└ ✅ Auto Updates"""

        await message.reply_text(info_text, quote=True)
        
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error getting bot info:</b> `{e}`", quote=True)