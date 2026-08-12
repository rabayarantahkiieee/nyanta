# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import asyncio

from bot import Bot
from config import ADMINS, LOGGER
from pyrogram import filters
from pyrogram.types import Message

# Import user limits utilities
from .user_limits import (
    get_all_user_stats,
    set_daily_limit,
    reset_all_user_limits,
    get_daily_limit_config,
    set_user_custom_limit,
    delete_user_custom_limit,
    get_all_user_custom_limits,
    get_user_custom_limit
)
from .stats_utils import make_bar

@Bot.on_message(filters.command("setlimit") & filters.user(ADMINS))
async def set_daily_download_limit(client: Bot, message: Message):
    """Set daily download limit for all users"""
    if len(message.command) != 2:
        await message.reply_text(
            "❌ <b>Penggunaan:</b> /setlimit JUMLAH\n\n"
            "<b>Contoh:</b> /setlimit 5\n\n"
            f"<b>Limit saat ini:</b> {get_daily_limit_config()} kali per hari",
            quote=True
        )
        return
    
    try:
        new_limit = int(message.command[1])
        if new_limit < 1 or new_limit > 50:
            await message.reply_text("❌ <b>Limit harus antara 1-50!</b>", quote=True)
            return
        
        old_limit = get_daily_limit_config()
        set_daily_limit(new_limit)
        
        await message.reply_text(
            f"✅ <b>Daily limit berhasil diset!</b>\n\n"
            f"<b>Limit lama:</b> {old_limit} kali per hari\n"
            f"<b>Limit baru:</b> {new_limit} kali per hari\n"
            f"<b>Efektif:</b> Segera",
            quote=True
        )
        
    except ValueError:
        await message.reply_text("❌ <b>Limit harus berupa angka!</b>", quote=True)
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("getlimit") & filters.user(ADMINS))
async def get_daily_limit(client: Bot, message: Message):
    """Get current daily download limit"""
    try:
        current_limit = get_daily_limit_config()
        
        await message.reply_text(
            f"📊 <b>CURRENT DAILY LIMIT</b>\n\n"
            f"<b>Daily Download Limit:</b> {current_limit} kali per hari\n"
            f"<b>Reset Time:</b> 00:00 UTC\n"
            f"<b>Scope:</b> Semua user\n"
            f"<b>Status:</b> {'🟢 Active' if current_limit > 0 else '🔴 Disabled'}",
            quote=True
        )
        
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("setuserlimit") & filters.user(ADMINS))
async def set_user_custom_limit_cmd(client: Bot, message: Message):
    """Set custom daily limit for specific user"""
    if len(message.command) != 3:
        await message.reply_text(
            "❌ <b>Penggunaan:</b> /setuserlimit USER_ID LIMIT\n\n"
            "<b>Contoh:</b> /setuserlimit 123456789 10\n"
            "<b>Untuk unlimited:</b> /setuserlimit 123456789 999",
            quote=True
        )
        return

    try:
        user_id = int(message.command[1])
        new_limit = int(message.command[2])

        if new_limit < 1 or new_limit > 1000:
            await message.reply_text("❌ <b>Limit harus antara 1-1000!</b>", quote=True)
            return

        old_limit = get_user_custom_limit(user_id)
        set_user_custom_limit(user_id, new_limit)

        await message.reply_text(
            f"✅ <b>Custom limit berhasil diset!</b>\n\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n"
            f"<b>Limit lama:</b> {old_limit} downloads/hari\n"
            f"<b>Limit baru:</b> {new_limit} downloads/hari\n"
            f"<b>Efektif:</b> Segera",
            quote=True
        )

    except ValueError:
        await message.reply_text("❌ <b>User ID dan limit harus berupa angka!</b>", quote=True)
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("deluserlimit") & filters.user(ADMINS))
async def delete_user_custom_limit_cmd(client: Bot, message: Message):
    """Delete custom limit for specific user (fallback to global)"""
    if len(message.command) != 2:
        await message.reply_text(
            "❌ <b>Penggunaan:</b> /deluserlimit USER_ID\n\n"
            "<b>Contoh:</b> /deluserlimit 123456789",
            quote=True
        )
        return

    try:
        user_id = int(message.command[1])

        # Check if user has custom limit
        custom_limits = get_all_user_custom_limits()
        if str(user_id) not in custom_limits:
            await message.reply_text("❌ <b>User ini tidak punya custom limit!</b>", quote=True)
            return

        old_limit = custom_limits[str(user_id)]
        global_limit = get_daily_limit_config()

        delete_user_custom_limit(user_id)

        await message.reply_text(
            f"✅ <b>Custom limit berhasil dihapus!</b>\n\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n"
            f"<b>Custom limit:</b> {old_limit} downloads/hari\n"
            f"<b>Kembali ke global limit:</b> {global_limit} downloads/hari",
            quote=True
        )

    except ValueError:
        await message.reply_text("❌ <b>User ID harus berupa angka!</b>", quote=True)
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("getuserlimits") & filters.user(ADMINS))
async def get_user_custom_limits_cmd(client: Bot, message: Message):
    """Get all users with custom limits"""
    try:
        custom_limits = get_all_user_custom_limits()
        global_limit = get_daily_limit_config()

        if not custom_limits:
            await message.reply_text(
                f"❌ <b>Belum ada user dengan custom limit!</b>\n\n"
                f"<b>Global limit saat ini:</b> {global_limit} downloads/hari",
                quote=True
            )
            return

        limits_list = []
        for user_id_str, limit in custom_limits.items():
            limits_list.append(f"├ <b>{user_id_str}:</b> {limit} downloads/hari")

        limits_text = "\n".join(limits_list)

        await message.reply_text(
            f"👥 <b>CUSTOM USER LIMITS</b>\n\n"
            f"<b>Global limit:</b> {global_limit} downloads/hari\n\n"
            f"{limits_text}\n\n"
            f"<b>Total users dengan custom limit:</b> {len(custom_limits)}",
            quote=True
        )

    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("userstats") & filters.user(ADMINS))
async def get_user_statistics(client: Bot, message: Message):
    """Get user download statistics"""
    msg = await message.reply_text("<code>Mengambil statistik user...</code>", quote=True)
    try:
        # Get user statistics
        user_stats = get_all_user_stats()

        if not user_stats:
            await msg.edit_text("❌ <b>Belum ada data download user hari ini!</b>")
            return

        # Sort by download count (highest first)
        user_stats.sort(key=lambda x: x['today_downloads'], reverse=True)

        # Build statistics message
        stats_lines = []
        stats_lines.append("📊 <b>USER DOWNLOAD STATISTICS (Hari Ini)</b>")
        stats_lines.append(f"<b>Total Users Active:</b> {len(user_stats)}")
        stats_lines.append(f"<b>Daily Limit Global:</b> {user_stats[0]['daily_limit']} downloads")
        stats_lines.append("")

        # Show top 20 users
        for i, stat in enumerate(user_stats[:20], 1):
            user_id = stat['user_id']
            downloads = stat['today_downloads']
            limit = stat['daily_limit']
            remaining = stat['remaining']

            status = "🔴" if remaining <= 0 else "🟡" if remaining <= 1 else "🟢"
            usage_bar = make_bar(downloads / limit if limit else 0, length=8)

            stats_lines.append(
                f"{status} <b>{i}.</b> User <code>{user_id}</code>\n"
                f"   <code>{usage_bar}</code> {downloads}/{limit} (Sisa: {remaining})"
            )

        if len(user_stats) > 20:
            stats_lines.append(f"\n📝 ...dan {len(user_stats) - 20} user lainnya")

        stats_text = "\n".join(stats_lines)

        await msg.edit_text(stats_text)

    except Exception as e:
        LOGGER(__name__).error(e)
        await msg.edit_text(f"❌ <b>Error:</b> `{e}`")

@Bot.on_message(filters.command("resetlimits") & filters.user(ADMINS))
async def reset_user_limits(client: Bot, message: Message):
    """Reset all user daily limits"""
    try:
        await message.reply_text(
            "⚠️ <b>KONFIRMASI RESET</b>\n\n"
            "Apakah Anda yakin ingin mereset semua user limits?\n"
            "Semua user akan bisa download lagi hari ini.\n\n"
            "<b>Reply dengan 'YES' untuk konfirmasi</b>",
            quote=True
        )
        
        # Wait for confirmation
        try:
            confirm_msg = await client.ask(
                chat_id=message.from_user.id,
                text="Ketik 'YES' untuk konfirmasi reset:",
                timeout=30
            )
            
            if confirm_msg.text.upper() != 'YES':
                await message.reply_text("❌ <b>Reset dibatalkan!</b>", quote=True)
                return
                
        except asyncio.TimeoutError:
            await message.reply_text("⏰ <b>Timeout! Reset dibatalkan!</b>", quote=True)
            return
        
        # Reset all limits
        reset_all_user_limits()
        
        await message.reply_text(
            "✅ <b>RESET BERHASIL!</b>\n\n"
            "Semua user limits telah direset.\n"
            "User sekarang bisa download lagi hari ini.",
            quote=True
        )
        
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("checkuser") & filters.user(ADMINS))
async def check_user_limit(client: Bot, message: Message):
    """Check specific user limit status"""
    if len(message.command) != 2:
        await message.reply_text(
            "❌ <b>Penggunaan:</b> /checkuser USER_ID\n\n"
            "<b>Contoh:</b> /checkuser 123456789",
            quote=True
        )
        return
    
    try:
        user_id = int(message.command[1])
        
        # We need to get this from user_limits.py
        from .user_limits import get_user_stats
        
        stats = get_user_stats(user_id)
        
        await message.reply_text(
            f"👤 <b>USER LIMIT STATUS</b>\n\n"
            f"<b>User ID:</b> {user_id}\n"
            f"<b>Downloads hari ini:</b> {stats['today_downloads']}\n"
            f"<b>Daily limit:</b> {stats['daily_limit']}\n"
            f"<b>Sisa limit:</b> {stats['remaining']}\n"
            f"<b>Status:</b> {'🔴 Habis' if stats['remaining'] <= 0 else '🟢 Available'}",
            quote=True
        )
        
    except ValueError:
        await message.reply_text("❌ <b>User ID harus berupa angka!</b>", quote=True)
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)
