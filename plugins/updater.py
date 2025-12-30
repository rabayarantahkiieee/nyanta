# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import asyncio
import re
import sys
import os
import git
from git import Repo
from pyrogram import filters
from pyrogram.types import Message

from bot import Bot
from config import ADMINS, HEROKU_API_KEY, HEROKU_APP_NAME, LOGGER, UPSTREAM_BRANCH, UPSTREAM_REPO


@Bot.on_message(filters.command("update") & filters.user(ADMINS))
async def update_bot(client: Bot, message: Message):
    if HEROKU_API_KEY is None or HEROKU_APP_NAME is None:
        await message.reply_text("❌ <b>HEROKU Credentials Tidak Ditemukan!</b>")
        return
    
    msg = await message.reply_text("<b>🔄 Memeriksa Update...</b>")
    
    try:
        repo = Repo()
        active_branch = repo.active_branch.name
        
        if active_branch != UPSTREAM_BRANCH:
            await msg.edit_text(f"❌ <b>Branch Tidak Aktif:</b> `{active_branch}`\n<b>Harus Branch:</b> `{UPSTREAM_BRANCH}`")
            return
        
        # Check for upstream remote
        try:
            repo.remote(name='upstream')
        except:
            repo.create_remote('upstream', UPSTREAM_REPO)
        
        repo.remote(name='upstream').fetch()
        commits_behind = repo.iter_commits(f'HEAD..upstream/{UPSTREAM_BRANCH}')
        commits_list = list(commits_behind)
        
        if not commits_list:
            await msg.edit_text("✅ <b>Bot Sudah Versi Terbaru!</b>")
            return
        
        await msg.edit_text(f"📦 <b>Tersedia {len(commits_list)} Update</b>\n\n⬇️ <b>Mulai Download Update...</b>")
        
        repo.remote(name='upstream').pull(UPSTREAM_BRANCH)
        await msg.edit_text("🔄 <b>Memasang Update...</b>")
        
        # Restart bot
        os.execl(sys.executable, sys.executable, "-m", "main")
        
    except Exception as e:
        LOGGER(__name__).error(e)
        await msg.edit_text(f"❌ <b>Error Update:</b> `{e}`")


@Bot.on_message(filters.command("restart") & filters.user(ADMINS))
async def restart_bot(client: Bot, message: Message):
    try:
        await message.reply_text("🔄 <b>Merestart Bot...</b>")
        os.execl(sys.executable, sys.executable, "-m", "main")
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error Restart:</b> `{e}`")


@Bot.on_message(filters.command("pull") & filters.user(ADMINS))
async def pull_updates(client: Bot, message: Message):
    try:
        await message.reply_text("⬇️ <b>Mengecek Update...</b>")
        
        repo = Repo()
        repo.remote(name='upstream').fetch()
        
        current_branch = repo.active_branch.name
        upstream_branch = repo.remote(name='upstream').refs[UPSTREAM_BRANCH]
        
        if repo.head.commit == upstream_branch.commit:
            await message.edit_text("✅ <b>Bot Sudah Versi Terbaru!</b>")
        else:
            repo.remote(name='upstream').pull(UPSTREAM_BRANCH)
            await message.edit_text("✅ <b>Update Berhasil Download!</b>\n🔄 <b>Gunakan /restart untuk restart bot</b>")
            
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`")