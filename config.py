# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import asyncio
import base64
import json
import logging
import os
import re
from distutils.util import strtobool
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.types import InlineKeyboardButton

load_dotenv(".env")

# =============================================================================
# ADMIN MANAGEMENT FUNCTIONS
# =============================================================================

ADMIN_FILE = "admin_list.json"

def load_admins():
    """Load admin list from file"""
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, 'r') as f:
            return json.load(f)
    return []

def save_admins(admins):
    """Save admin list to file"""
    with open(ADMIN_FILE, 'w') as f:
        json.dump(admins, f)

# Bot token dari @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")

# API ID Anda dari my.telegram.org
APP_ID = int(os.environ.get("APP_ID", ""))

# API Hash Anda dari my.telegram.org
API_HASH = os.environ.get("API_HASH", "")

# ID Channel Database
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", ""))

# NAMA OWNER
OWNER = os.environ.get("OWNER", "")

# Protect Content
PROTECT_CONTENT = strtobool(os.environ.get("PROTECT_CONTENT", "False"))

# Heroku/Sevalla app identity (shown in /vars)
HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME", None)
HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY", None)

# Database
DB_URI = os.environ.get("DATABASE_URL", "sqlite:///bot_database.db")

# ID dari Channel Atau Group Untuk Wajib Subscribenya (Multiple Support)
FORCE_SUB_CHANNELS = [int(os.environ.get(f"FORCE_SUB_CHANNEL{i}", "0")) for i in range(1, 21) if os.environ.get(f"FORCE_SUB_CHANNEL{i}")]
FORCE_SUB_GROUPS = [int(os.environ.get(f"FORCE_SUB_GROUP{i}", "0")) for i in range(1, 21) if os.environ.get(f"FORCE_SUB_GROUP{i}")]

# Backward compatibility: Single env support (deprecated, use numbered envs)
FORCE_SUB_CHANNEL = int(os.environ.get("FORCE_SUB_CHANNEL", "0")) if not FORCE_SUB_CHANNELS else FORCE_SUB_CHANNELS[0]
FORCE_SUB_GROUP = int(os.environ.get("FORCE_SUB_GROUP", "0")) if not FORCE_SUB_GROUPS else FORCE_SUB_GROUPS[0]

TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

# Pesan Awalan /start
START_MSG = os.environ.get(
    "START_MESSAGE",
    "<b>Hello {first}</b>\n\n<b>Saya dapat menyimpan file pribadi di Channel Tertentu dan pengguna lain dapat mengaksesnya dari link khusus.</b>",
)
try:
    ADMINS = [int(x) for x in (os.environ.get("ADMINS", "").split())] + load_admins()
except ValueError:
    raise Exception("Daftar Admin Anda tidak berisi User ID Telegram yang valid.")

# Pesan Saat Memaksa Subscribe
FORCE_MSG = os.environ.get(
    "FORCE_SUB_MESSAGE",
    "<b>Hello {first}\n\nAnda harus bergabung di Channel/Grup saya Terlebih dahulu untuk Melihat File yang saya Bagikan\n\nSilakan Join Ke Channel & Group Terlebih Dahulu</b>",
)

# Atur Teks Kustom Anda di sini, Simpan (None) untuk Menonaktifkan Teks Kustom
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)

# Setel True jika Anda ingin Menonaktifkan tombol Bagikan Kiriman Saluran Anda
DISABLE_CHANNEL_BUTTON = strtobool(os.environ.get("DISABLE_CHANNEL_BUTTON", "False"))

# =============================================================================
# BROADCAST CONFIGURATION
# =============================================================================

# Delay antar pesan broadcast (dalam detik) - lebih lambat jika menggunakan placeholders
BROADCAST_DELAY = float(os.environ.get("BROADCAST_DELAY", "0.05"))

# Jumlah pesan per batch untuk broadcast
BROADCAST_BATCH_SIZE = int(os.environ.get("BROADCAST_BATCH_SIZE", "10"))

# Maksimal concurrent messages untuk broadcast
BROADCAST_MAX_CONCURRENT = int(os.environ.get("BROADCAST_MAX_CONCURRENT", "5"))

# Admin IDs are now managed through ADMINS environment variable + dynamic admin list
# No hardcoded admin IDs for security and flexibility

LOG_FILE_NAME = "logs.txt"
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler(LOG_FILE_NAME, maxBytes=50000000, backupCount=10),
        logging.StreamHandler(),
    ],
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)


# =============================================================================
# DATA CONSTANTS (FACTORIZED FROM Data.py)
# =============================================================================

class Data:
    HELP = """
<b> 🤖 File Sharing Bot - Complete Feature Set</b>

<b> ❏ Perintah untuk Pengguna BOT</b>
 ├ /start - Mulai Bot & Generate File Links
 ├ /about - Tentang Bot ini
 ├ /help - Bantuan Perintah Bot ini
 ├ /id - Lihat informasi profile lengkap
 ├ /profile - Lihat profil & statistik pengguna
 ├ /ping - Untuk mengecek bot hidup
 ├ /uptime - Untuk melihat status bot
 ├ /feedback - Kirim feedback ke developer
 ├ /report - Laporkan masalah atau bug
 ├ /tutorial - Panduan lengkap penggunaan bot
 ├ /stats - Lihat statistik bot (alias /users)

<b> ❏ Perintah Untuk Admin BOT</b>
 ├ <b>📁 File Management</b>
 ├ /genlink - Generate link untuk single file
 ├ /batch - Generate link untuk multiple files
 ├
 ├ <b>👥 Admin Management</b>
 ├ /addadmin - Tambahkan admin baru
 ├ /deladmin - Hapus admin
 ├ /getadmin - Lihat daftar admin
 ├
 ├ <b>💾 Database Management</b>
 ├ /getdb - Informasi database
 ├ /setdb - Set database configuration
 ├ /backupdb - Backup database
 ├ /restoredb - Restore database dari backup
 ├ /cleardb - Clear database (DANGER!)
 ├
 ├ <b>⚙️ System Management</b>
 ├ /logs - Untuk melihat logs bot
 ├ /vars - Lihat semua config variables
 ├ /info - Informasi lengkap bot & statistik
 ├ /speedtest - Test kecepatan server
 ├ /users - Statistik pengguna bot
 ├ /broadcast - Kirim pesan broadcast
 ├
 ├ <b>🔄 Bot Management</b>
 ├ /update - Update bot dari GitHub
 ├ /restart - Restart bot
 ├ /pull - Pull update tanpa restart
 ├
 ├ <b>🌐 Heroku Management</b>
 ├ /setvar - Set environment variables
 ├ /delvar - Hapus environment variables
 ├ /getvar - Lihat environment variables
 └ /usage - Monitoring aplikasi Heroku

<b> ❏ Content & Button Management (Admin)</b>
 ├ /addbutton - Tambahkan custom button
 ├ /delbutton - Hapus custom button
 ├ /getbutton - Lihat daftar custom buttons
 ├ /limitbutton - Enable/disable custom button feature
 ├ /setmsg - Set custom message untuk situasi tertentu
 ├ /addkonten - Tambahkan file ke protected list
 ├ /delkonten - Hapus file dari protected list
 ├ /getkonten - Lihat daftar protected content
 └ /limitkonten - Set limit untuk konten tertentu

<b> ❏ Admin Feedback Management</b>
 ├ /viewfeedback - Lihat feedback dari pengguna
 └ /viewreports - Lihat laporan masalah dari pengguna

<b> 📝 Cara Penggunaan:</b>
1. <b>Upload File</b> → Bot akan generate sharing link
2. <b>Forward File</b> dari channel database → Generate link
3. <b>Admin Commands</b> → Kelola bot via commands di atas
4. <b>User Features</b> → Gunakan commands untuk fitur tambahan

<b> 👨‍💻 Developed by </b><a href='https://t.me/yawrenmaru'>@yawrenmaru</a>
<b> 📚 Repository: </b><a href='https://github.com/rabayarantahkiieee/File-Sharing-Mann'>File-Sharing-Mann</a>
"""

    close = [
        [InlineKeyboardButton("ᴛᴜᴛᴜᴘ", callback_data="close")]
    ]

    mbuttons = [
        [
            InlineKeyboardButton("ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs", callback_data="help"),
            InlineKeyboardButton("ᴛᴜᴛᴜᴘ", callback_data="close")
        ],
    ]

    buttons = [
        [
            InlineKeyboardButton("ᴛᴇɴᴛᴀɴɢ sᴀʏᴀ", callback_data="about"),
            InlineKeyboardButton("ᴛᴜᴛᴜᴘ", callback_data="close")
        ],
    ]

    ABOUT = """
<b> 🤖 File Sharing Bot - Advanced Telegram File Manager</b>

<b> 📋 Tentang Bot ini:</b>

<b>@{} adalah Bot Telegram canggih untuk:</b>
 ├ ✅ <b>Menyimpan file pribadi</b> di channel database
 ├ ✅ <b>Generate link sharing</b> dengan proteksi
 ├ ✅ <b>Force subscription</b> untuk channel/group
 ├ ✅ <b>Admin management</b> lengkap
 ├ ✅ <b>Content protection</b> & limits
 ├ ✅ <b>Custom buttons</b> & messages
 ├ ✅ <b>Database management</b> tools
 ├ ✅ <b>Auto-updater</b> dari GitHub
 ├ ✅ <b>Speedtest</b> & monitoring
 └ ✅ <b>Broadcast system</b> untuk user

<b> 🔧 Technical Details:</b>
 ├ <b>Framework:</b> <a href='https://docs.pyrogram.org'>Pyrogram</a> (Latest)
 ├ <b>Database:</b> SQLite/PostgreSQL support
 ├ <b>Deployment:</b> Heroku, Sevalla, VPS
 ├ <b>Security:</b> File protection & access control
 ├ <b>Performance:</b> Optimized for high traffic
 └ <b>Updates:</b> Auto-update system

<b> 📊 Bot Statistics:</b>
  ├ <b>Version:</b> 4.3.0 (Multiple Force Subscriptions)
  ├ <b>Features:</b> 25+ commands
  ├ <b>Plugins:</b> 12 modules
  ├ <b>Compatibility:</b> All deployment platforms
  └ <b>Status:</b> Production Ready

<b> 🎯 Key Features:</b>
 ├ <b>File Management:</b> Upload, share, protect files
 ├ <b>Link Generation:</b> Single & batch link creation
 ├ <b>Admin Tools:</b> Complete bot management
 ├ <b>User Control:</b> Force sub, user stats, broadcast
 ├ <b>System Monitoring:</b> Logs, speedtest, uptime
 └ <b>Auto Maintenance:</b> Updates, backups, restarts

<b> 📚 Resources:</b>
 ├ <b>Source Code:</b> <a href='https://github.com/rabayarantahkiieee/File-Sharing-Mann'>File-Sharing-Mann</a>
 ├ <b>Documentation:</b> <a href='https://github.com/rabayarantahkiieee/File-Sharing-Mann#readme'>Complete Guide</a>
 ├ <b>Support:</b> <a href='https://t.me/yawrenmaru'>Developer</a>
 └ <b>Developer:</b> <a href='https://t.me/yawrenmaru'>@yawrenmaru</a>

<b> 🚀 Ready for Production Deployment!</b>
"""


# =============================================================================
# HELPER FUNCTIONS (FACTORIZED FROM helper_func.py)
# =============================================================================

async def subschannel(filter, client, update):
    if not FORCE_SUB_CHANNELS:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                return False
        except UserNotParticipant:
            return False
    return True


async def subsgroup(filter, client, update):
    if not FORCE_SUB_GROUPS:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
    for group_id in FORCE_SUB_GROUPS:
        try:
            member = await client.get_chat_member(chat_id=group_id, user_id=user_id)
            if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                return False
        except UserNotParticipant:
            return False
    return True


async def is_subscribed(filter, client, update):
    if not FORCE_SUB_CHANNELS and not FORCE_SUB_GROUPS:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
    # Check all channels
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                return False
        except UserNotParticipant:
            return False
    # Check all groups
    for group_id in FORCE_SUB_GROUPS:
        try:
            member = await client.get_chat_member(chat_id=group_id, user_id=user_id)
            if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                return False
        except UserNotParticipant:
            return False
    return True


async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string


async def decode(base64_string):
    base64_string = base64_string.strip("=") # links generated before this commit will be having = sign, hence striping them to handle padding errors.
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes) 
    string = string_bytes.decode("ascii")
    return string


async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages : total_messages + 200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id, message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.value)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id, message_ids=temb_ids
            )
        except BaseException:
            pass
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages


async def get_message_id(client, message):
    if (
        message.forward_from_chat
        and message.forward_from_chat.id == client.db_channel.id
    ):
        return message.forward_from_message_id
    elif message.forward_from_chat or message.forward_sender_name or not message.text:
        return 0
    else:
        pattern = "https://t.me/(?:c/)?(.*)/(\\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        elif channel_id == client.db_channel.username:
            return msg_id


# Filter exports
subsgc = filters.create(subsgroup)
subsch = filters.create(subschannel)
subsall = filters.create(is_subscribed)