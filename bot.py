# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import pyromod.listen
import sys

from pyrogram import Client, enums
from pyrogram.types import BotCommand

from config import (
    ADMINS,
    API_HASH,
    APP_ID,
    CHANNEL_ID,
    FORCE_SUB_CHANNELS,
    FORCE_SUB_GROUPS,
    LOGGER,
    OWNER,
    TG_BOT_TOKEN,
    TG_BOT_WORKERS,
)


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN,
        )
        self.LOGGER = LOGGER

    async def start(self, use_qr=None, except_ids=None):
        try:
            await super().start()
            usr_bot_me = await self.get_me()
            self.username = usr_bot_me.username
            self.namebot = usr_bot_me.first_name
            self.LOGGER(__name__).info(
                f"TG_BOT_TOKEN detected!\n┌ First Name: {self.namebot}\n└ Username: @{self.username}\n——"
            )
        except Exception as a:
            self.LOGGER(__name__).warning(a)
            self.LOGGER(__name__).info(
                "Bot Berhenti. Hubungi Developer @yawrenmaru untuk Bantuan"
            )
            sys.exit()

        # Initialize invite links for channels and groups as lists
        self.invitelinks = []  # List of invite links for channels
        self.invitelinks2 = []  # List of invite links for groups

        # Process channels
        for i, channel_id in enumerate(FORCE_SUB_CHANNELS, 1):
            try:
                info = await self.get_chat(channel_id)
                link = info.invite_link
                if not link:
                    link = await self.export_chat_invite_link(channel_id)
                self.invitelinks.append(link)
                if i == 1:  # Backward compatibility: first channel still uses invitelink
                    self.invitelink = link
                self.LOGGER(__name__).info(
                    f"FORCE_SUB_CHANNEL_{i} detected!\n┌ Title: {info.title}\n└ Chat ID: {info.id}\n——"
                )
            except Exception as a:
                self.LOGGER(__name__).warning(a)
                self.LOGGER(__name__).warning(
                    f"Bot tidak dapat Mengambil link invite dari FORCE_SUB_CHANNEL_{i}!"
                )
                self.LOGGER(__name__).warning(
                    f"Pastikan @{self.username} adalah admin di Channel Tersebut, Chat ID F-Subs Channel_{i} Saat Ini: {channel_id}"
                )
                self.LOGGER(__name__).info(
                    "Bot Berhenti. Hubungi Developer @yawrenmaru untuk Bantuan"
                )
                sys.exit()

        # Process groups
        for i, group_id in enumerate(FORCE_SUB_GROUPS, 1):
            try:
                info = await self.get_chat(group_id)
                link = info.invite_link
                if not link:
                    link = await self.export_chat_invite_link(group_id)
                self.invitelinks2.append(link)
                if i == 1:  # Backward compatibility: first group still uses invitelink2
                    self.invitelink2 = link
                self.LOGGER(__name__).info(
                    f"FORCE_SUB_GROUP_{i} detected!\n┌ Title: {info.title}\n└ Chat ID: {info.id}\n——"
                )
            except Exception as a:
                self.LOGGER(__name__).warning(a)
                self.LOGGER(__name__).warning(
                    f"Bot tidak dapat Mengambil link invite dari FORCE_SUB_GROUP_{i}!"
                )
                self.LOGGER(__name__).warning(
                    f"Pastikan @{self.username} adalah admin di Group Tersebut, Chat ID F-Subs Group_{i} Saat Ini: {group_id}"
                )
                self.LOGGER(__name__).info(
                    "Bot Berhenti. Hubungi Developer @yawrenmaru untuk Bantuan"
                )
                sys.exit()

        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Test Message", disable_notification=True)
            await test.delete()
            self.LOGGER(__name__).info(
                f"CHANNEL_ID Database detected!\n┌ Title: {db_channel.title}\n└ Chat ID: {db_channel.id}\n——"
            )
        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(
                f"Pastikan @{self.username} adalah admin di Channel DataBase anda, CHANNEL_ID Saat Ini: {CHANNEL_ID}"
            )
            self.LOGGER(__name__).info(
                "Bot Berhenti. Hubungi Developer @yawrenmaru untuk Bantuan"
            )
            sys.exit()

        # Set up bot commands menu
        await self.setup_bot_commands()

        self.set_parse_mode(enums.ParseMode.HTML)
        self.LOGGER(__name__).info(
            f"[🔥 BERHASIL DIAKTIFKAN! 🔥]\n\nBOT Developed by Soxmed\nHubungi @yawrenmaru untuk Support"
        )

    async def setup_bot_commands(self):
        """Setup bot commands menu for better UX"""
        try:
            # User commands
            user_commands = [
                BotCommand("start", "Mulai bot & generate file links"),
                BotCommand("help", "Bantuan lengkap semua perintah"),
                BotCommand("about", "Informasi lengkap tentang bot"),
                BotCommand("profile", "Lihat profil & statistik pengguna"),
                BotCommand("id", "Lihat informasi profile lengkap"),
                BotCommand("ping", "Test respons bot"),
                BotCommand("uptime", "Lihat status uptime bot"),
                BotCommand("stats", "Lihat statistik bot"),
                BotCommand("feedback", "Kirim feedback ke developer"),
                BotCommand("report", "Laporkan masalah atau bug"),
                BotCommand("tutorial", "Panduan lengkap penggunaan bot"),
            ]

            # Admin commands (only visible to admins)
            admin_commands = user_commands + [
                BotCommand("users", "Statistik pengguna bot"),
                BotCommand("broadcast", "Kirim pesan broadcast ke semua user"),
                BotCommand("logs", "Download file logs bot"),
                BotCommand("vars", "Lihat semua config variables"),
                BotCommand("speedtest", "Test kecepatan server"),
                BotCommand("info", "Informasi lengkap bot & statistik"),
                BotCommand("getdb", "Informasi database"),
                BotCommand("setdb", "Set database URL"),
                BotCommand("backupdb", "Backup database"),
                BotCommand("restoredb", "Restore database dari backup"),
                BotCommand("cleardb", "Clear database (PERINGATAN!)"),
                BotCommand("addadmin", "Tambahkan admin baru"),
                BotCommand("deladmin", "Hapus admin dari daftar"),
                BotCommand("getadmin", "Lihat daftar admin"),
                BotCommand("addbutton", "Tambahkan custom button"),
                BotCommand("delbutton", "Hapus custom button"),
                BotCommand("getbutton", "Lihat daftar custom buttons"),
                BotCommand("limitbutton", "Enable/disable custom button"),
                BotCommand("setmsg", "Set custom message"),
                BotCommand("addkonten", "Tambahkan file ke protected list"),
                BotCommand("delkonten", "Hapus file dari protected list"),
                BotCommand("getkonten", "Lihat daftar protected content"),
                BotCommand("limitkonten", "Set limit untuk konten tertentu"),
                BotCommand("setvar", "Set environment variable"),
                BotCommand("delvar", "Hapus environment variable"),
                BotCommand("getvar", "Lihat environment variable"),
                BotCommand("usage", "Monitoring aplikasi Heroku"),
                BotCommand("update", "Update bot dari GitHub"),
                BotCommand("restart", "Restart bot"),
                BotCommand("pull", "Pull update tanpa restart"),
                BotCommand("viewfeedback", "Lihat feedback dari pengguna"),
                BotCommand("viewreports", "Lihat laporan masalah dari pengguna"),
                BotCommand("batch", "Generate link untuk multiple files"),
                BotCommand("genlink", "Generate link untuk single file"),
                BotCommand("setlimit", "Set daily download limit"),
                BotCommand("getlimit", "Lihat current daily limit"),
                BotCommand("userstats", "Statistik semua user"),
                BotCommand("resetlimits", "Reset semua user limits"),
                BotCommand("checkuser", "Check informasi user tertentu"),
                BotCommand("setuserlimit", "Set custom limit untuk user tertentu"),
                BotCommand("deluserlimit", "Hapus custom limit user"),
                BotCommand("getuserlimits", "Lihat semua custom user limits"),
            ]

            # Set commands for all users
            await self.set_bot_commands(user_commands, scope=None)

            # Set commands for admins (private chats only)
            from pyrogram.types import BotCommandScopeChat
            for admin_id in ADMINS:
                try:
                    scope = BotCommandScopeChat(chat_id=admin_id)
                    await self.set_bot_commands(admin_commands, scope=scope)
                except Exception as e:
                    self.LOGGER(__name__).warning(f"Failed to set admin commands for {admin_id}: {e}")

            self.LOGGER(__name__).info("✅ Bot commands menu berhasil diatur!")

        except Exception as e:
            self.LOGGER(__name__).error(f"Failed to setup bot commands: {e}")

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")
