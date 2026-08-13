# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import asyncio

from bot import Bot
from config import LOGGER, OWNER, admin_filter
from pyrogram import filters
from pyrogram.types import Message

# Import utility functions for content protection
from .content_utils import load_content_settings, save_content_settings, add_protected_file, remove_protected_file, set_file_limit

@Bot.on_message(filters.command("addkonten") & admin_filter)
async def add_content(client: Bot, message: Message):
    """Tambahkan file/konten ke protected list"""
    if len(message.command) != 2:
        await message.reply_text("❌ <b>Penggunaan:</b> /addkonten FILE_ID", quote=True)
        return
    
    try:
        file_id = message.command[1]
        settings = load_content_settings()
        
        if file_id in settings["protected_files"]:
            await message.reply_text("❌ <b>File sudah ada dalam protected list!</b>", quote=True)
            return
        
        add_protected_file(file_id)
        settings = load_content_settings()
        
        await message.reply_text(
            f"✅ <b>File berhasil ditambahkan ke protected list!</b>\n\n"
            f"<b>File ID:</b> <code>{file_id}</code>\n"
            f"<b>Total Protected Files:</b> {len(settings['protected_files'])}",
            quote=True
        )
        
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("delkonten") & admin_filter)
async def del_content(client: Bot, message: Message):
    """Hapus file dari protected list"""
    if len(message.command) != 2:
        await message.reply_text("❌ <b>Penggunaan:</b> /delkonten FILE_ID", quote=True)
        return
    
    try:
        file_id = message.command[1]
        settings = load_content_settings()
        
        if file_id not in settings["protected_files"]:
            await message.reply_text("❌ <b>File tidak ada dalam protected list!</b>", quote=True)
            return
        
        remove_protected_file(file_id)
        settings = load_content_settings()
        
        await message.reply_text(
            f"✅ <b>File berhasil dihapus dari protected list!</b>\n\n"
            f"<b>File ID:</b> <code>{file_id}</code>\n"
            f"<b>Total Protected Files:</b> {len(settings['protected_files'])}",
            quote=True
        )
        
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("getkonten") & admin_filter)
async def get_content(client: Bot, message: Message):
    """Lihat daftar protected content"""
    try:
        settings = load_content_settings()
        protected_files = settings["protected_files"]
        
        if not protected_files:
            await message.reply_text("❌ <b>Belum ada file yang diprotect!</b>", quote=True)
            return
        
        content_list = []
        for i, file_id in enumerate(protected_files[:20], 1):  # Limit to 20
            content_list.append(f"├ <b>{i}.</b> <code>{file_id}</code>")
        
        if len(protected_files) > 20:
            content_list.append(f"├ ... <b>dan {len(protected_files) - 20} lainnya</b>")
        
        content_text = "\n".join(content_list)
        
        await message.reply_text(
            f"🛡️ <b>PROTECTED CONTENT LIST</b>\n\n{content_text}\n\n"
            f"<b>Total Protected Files:</b> {len(protected_files)}",
            quote=True
        )
        
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("limitkonten") & admin_filter)
async def limit_content(client: Bot, message: Message):
    """Set limit untuk konten tertentu"""
    if len(message.command) != 3:
        await message.reply_text("❌ <b>Penggunaan:</b> /limitkonten FILE_ID LIMIT", quote=True)
        return
    
    try:
        file_id = message.command[1]
        limit = int(message.command[2])
        
        set_file_limit(file_id, limit)
        settings = load_content_settings()
        
        await message.reply_text(
            f"✅ <b>Limit konten berhasil diset!</b>\n\n"
            f"<b>File ID:</b> <code>{file_id}</code>\n"
            f"<b>Limit:</b> {limit} downloads\n"
            f"<b>Status:</b> {limit} kali tersisa",
            quote=True
        )
        
    except ValueError:
        await message.reply_text("❌ <b>Limit harus berupa angka!</b>", quote=True)
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)