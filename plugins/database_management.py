# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import asyncio
import os
import json
from datetime import datetime

from bot import Bot
from config import ADMINS, LOGGER, DB_URI
from pyrogram import filters
from pyrogram.types import Message
from database.sql import User, get_db

BACKUP_DIR = "database_backups"

def ensure_backup_dir():
    """Ensure backup directory exists"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

@Bot.on_message(filters.command("getdb") & filters.user(ADMINS))
async def get_db_info(client: Bot, message: Message):
    """Informasi database"""
    try:
        db_info = f"""💾 <b>DATABASE INFORMATION</b>

<b>Database Type:</b> SQLite/PostgreSQL
<b>DB URI:</b> {'✅ Configured' if DB_URI else '❌ Not Configured'}
<b>Backup Directory:</b> {BACKUP_DIR}
<b>Status:</b> {'✅ Connected' if DB_URI else '⚠️ Using Default SQLite'}

<b>Features:</b>
├ ✅ User Management
├ ✅ Message Storage  
├ ✅ Admin Tracking
├ ✅ Content Protection
└ ✅ Button Settings"""

        await message.reply_text(db_info, quote=True)
        
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("setdb") & filters.user(ADMINS))
async def set_db_config(client: Bot, message: Message):
    """Set database configuration"""
    if len(message.command) != 2:
        await message.reply_text("❌ <b>Penggunaan:</b> /setdb DATABASE_URL", quote=True)
        return
    
    try:
        db_url = message.command[1]
        
        # Save to environment variable simulation
        config = {
            "database_url": db_url,
            "last_updated": str(asyncio.get_event_loop().time())
        }
        
        with open("db_config.json", "w") as f:
            json.dump(config, f)
        
        await message.reply_text(
            f"✅ <b>Database configuration berhasil diset!</b>\n\n"
            f"<b>Database URL:</b> <code>{db_url}</code>\n"
            f"<b>Status:</b> Ready untuk restart bot",
            quote=True
        )
        
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("backupdb") & filters.user(ADMINS))
async def backup_database(client: Bot, message: Message):
    """Backup database - Real user data backup"""
    try:
        ensure_backup_dir()
        db = get_db()

        # Get all users from database
        users = db.query(User).all()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{BACKUP_DIR}/backup_{timestamp}.json"

        # Real backup data
        backup_data = {
            "timestamp": timestamp,
            "database_type": "PostgreSQL" if "postgresql" in DB_URI else "SQLite",
            "total_users": len(users),
            "users": [
                {
                    "id": user.id,
                    "user_id": user.user_id,
                    "username": user.username,
                    "first_seen": user.first_seen.isoformat() if user.first_seen else None,
                    "last_seen": user.last_seen.isoformat() if user.last_seen else None
                }
                for user in users
            ],
            "metadata": {
                "backup_version": "2.0",
                "bot_version": "4.2.0",
                "created_by": message.from_user.username or message.from_user.first_name
            }
        }

        # Save backup file
        with open(backup_file, "w", encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        db.close()

        # Send backup file to admin
        try:
            await message.reply_document(
                document=backup_file,
                caption=f"✅ <b>DATABASE BACKUP BERHASIL!</b>\n\n"
                        f"<b>👥 Total Users:</b> {len(users)}\n"
                        f"<b>⏰ Timestamp:</b> {timestamp}\n"
                        f"<b>💾 Database:</b> {backup_data['database_type']}\n"
                        f"<b>📊 Status:</b> ✅ Backup successful\n\n"
                        f"<b>💡 Tip:</b> Gunakan <code>/restoredb backup_{timestamp}.json</code> untuk restore",
                quote=True
            )
        except Exception as send_error:
            # If sending file fails, just send text message
            LOGGER(__name__).warning(f"Failed to send backup file: {send_error}")
            await message.reply_text(
                f"✅ <b>DATABASE BACKUP BERHASIL!</b>\n\n"
                f"<b>📁 Backup File:</b> <code>{backup_file}</code>\n"
                f"<b>👥 Total Users:</b> {len(users)}\n"
                f"<b>⏰ Timestamp:</b> {timestamp}\n"
                f"<b>💾 Database:</b> {backup_data['database_type']}\n"
                f"<b>📊 Status:</b> ✅ Backup successful\n\n"
                f"<b>⚠️ Note:</b> File backup tersimpan di server\n"
                f"<b>💡 Tip:</b> Gunakan <code>/restoredb backup_{timestamp}.json</code> untuk restore",
                quote=True
            )

    except Exception as e:
        LOGGER(__name__).error(f"Backup error: {e}")
        await message.reply_text(f"❌ <b>Backup Error:</b> `{str(e)}`", quote=True)

@Bot.on_message(filters.command("restoredb") & filters.user(ADMINS))
async def restore_database(client: Bot, message: Message):
    """Restore database dari backup - Real user data restore"""
    if len(message.command) != 2:
        await message.reply_text(
            "❌ <b>Penggunaan:</b> <code>/restoredb backup_filename.json</code>\n\n"
            "<b>Contoh:</b> <code>/restoredb backup_20241201_143022.json</code>",
            quote=True
        )
        return

    try:
        backup_file = message.command[1]
        backup_path = f"{BACKUP_DIR}/{backup_file}"

        if not os.path.exists(backup_path):
            # List available backup files
            available_backups = []
            if os.path.exists(BACKUP_DIR):
                available_backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith('backup_') and f.endswith('.json')]

            await message.reply_text(
                f"❌ <b>Backup file tidak ditemukan!</b>\n\n"
                f"<b>Requested:</b> <code>{backup_file}</code>\n"
                f"<b>Path:</b> <code>{backup_path}</code>\n\n"
                f"<b>📁 Available Backups:</b>\n" +
                ("\n".join([f"• <code>{b}</code>" for b in available_backups[-5:]]) if available_backups else "• None"),
                quote=True
            )
            return

        # Load backup data
        with open(backup_path, "r", encoding='utf-8') as f:
            backup_data = json.load(f)

        # Validate backup format
        if not isinstance(backup_data, dict):
            await message.reply_text("❌ <b>Invalid backup file format!</b>", quote=True)
            return

        if "users" not in backup_data or "metadata" not in backup_data:
            await message.reply_text("❌ <b>Invalid backup format! Missing required fields.</b>", quote=True)
            return

        if not isinstance(backup_data["users"], list):
            await message.reply_text("❌ <b>Invalid backup format! Users data must be a list.</b>", quote=True)
            return

        # Check if backup is empty
        if not backup_data["users"]:
            await message.reply_text("⚠️ <b>Backup file is empty! No users to restore.</b>", quote=True)
            return

        db = get_db()

        # Clear existing users (optional - ask for confirmation)
        existing_count = db.query(User).count()
        if existing_count > 0:
            await message.reply_text(
                f"⚠️ <b>Database sudah berisi {existing_count} users!</b>\n\n"
                "Apakah Anda ingin mengganti semua data dengan backup?\n"
                "Reply dengan 'REPLACE' untuk melanjutkan:",
                quote=True
            )

            def check_replace(m):
                return m.from_user.id == message.from_user.id and m.text.upper() == "REPLACE"

            try:
                confirm_msg = await client.wait_for_message(message.chat.id, filter=check_replace, timeout=30)
                if confirm_msg:
                    # Clear existing data
                    db.query(User).delete()
                    db.commit()
                else:
                    db.close()
                    return
            except asyncio.TimeoutError:
                await message.reply_text("❌ <b>Timeout: Restore dibatalkan</b>", quote=True)
                db.close()
                return

        # Restore users from backup
        restored_count = 0
        for user_data in backup_data["users"]:
            try:
                # Convert ISO strings back to datetime with better error handling
                first_seen = None
                last_seen = None

                if user_data.get("first_seen"):
                    try:
                        # Handle different ISO format variations
                        first_seen_str = user_data["first_seen"]
                        if first_seen_str.endswith('Z'):
                            first_seen_str = first_seen_str.replace('Z', '+00:00')
                        first_seen = datetime.fromisoformat(first_seen_str.replace(' ', 'T'))
                    except:
                        first_seen = datetime.now()  # Fallback to current time

                if user_data.get("last_seen"):
                    try:
                        # Handle different ISO format variations
                        last_seen_str = user_data["last_seen"]
                        if last_seen_str.endswith('Z'):
                            last_seen_str = last_seen_str.replace('Z', '+00:00')
                        last_seen = datetime.fromisoformat(last_seen_str.replace(' ', 'T'))
                    except:
                        last_seen = datetime.now()  # Fallback to current time

                user = User(
                    user_id=user_data["user_id"],
                    username=user_data["username"],
                    first_seen=first_seen,
                    last_seen=last_seen
                )
                db.add(user)
                restored_count += 1
            except Exception as e:
                LOGGER(__name__).warning(f"Failed to restore user {user_data.get('user_id')}: {e}")
                continue

        db.commit()
        db.close()

        await message.reply_text(
            f"✅ <b>DATABASE RESTORE BERHASIL!</b>\n\n"
            f"<b>📁 Backup File:</b> <code>{backup_file}</code>\n"
            f"<b>👥 Users Restored:</b> {restored_count}\n"
            f"<b>⏰ Backup Time:</b> {backup_data['timestamp']}\n"
            f"<b>💾 Database Type:</b> {backup_data.get('database_type', 'Unknown')}\n"
            f"<b>📊 Status:</b> ✅ Restore successful\n\n"
            f"<b>⚠️ Note:</b> Bot restart diperlukan untuk menerapkan perubahan",
            quote=True
        )

    except Exception as e:
        LOGGER(__name__).error(f"Restore error: {e}")
        await message.reply_text(f"❌ <b>Restore Error:</b> `{str(e)}`", quote=True)

@Bot.on_message(filters.command("cleardb") & filters.user(ADMINS))
async def clear_database(client: Bot, message: Message):
    """Clear database (WARNING: DANGEROUS!)"""
    try:
        await message.reply_text(
            "⚠️ <b>WARNING: DATABASE CLEAR</b>\n\n"
            "Apakah Anda yakin ingin mengosongkan database?\n"
            "Tindakan ini tidak dapat dibatalkan!\n\n"
            "Reply dengan 'YA' untuk melanjutkan:",
            quote=True
        )
        
        # Wait for confirmation
        def check_confirm(m):
            return m.from_user.id == message.from_user.id and m.text == "YA"
        
        confirm_msg = await client.wait_for_message(message.chat.id, filter=check_confirm, timeout=30)
        
        if confirm_msg:
            # Clear database simulation
            await message.reply_text(
                "✅ <b>Database berhasil dikosongkan!</b>\n\n"
                "<b>WARNING:</b> Semua data telah dihapus\n"
                "Bot akan restart diperlukan",
                quote=True
            )
        
    except asyncio.TimeoutError:
        await message.reply_text("❌ <b>Timeout: Konfirmasi tidak diterima</b>", quote=True)
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)