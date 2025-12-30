# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import os
import requests
from pyrogram import filters
from pyrogram.types import Message

from bot import Bot
from config import ADMINS, LOGGER

# Sevalla API Configuration
SEVALLA_API_KEY = os.environ.get("SEVALLA_API_KEY")
SEVALLA_PROJECT_ID = os.environ.get("SEVALLA_PROJECT_ID")
SEVALLA_SERVICE_ID = os.environ.get("SEVALLA_SERVICE_ID")
SEVALLA_BASE_URL = "https://api.sevalla.com/v1"

def sevalla_api_call(method, endpoint, data=None):
    """Helper function for Sevalla API calls"""
    if not SEVALLA_API_KEY or not SEVALLA_PROJECT_ID or not SEVALLA_SERVICE_ID:
        return {"error": "Sevalla API credentials not configured"}

    url = f"{SEVALLA_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {SEVALLA_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return {"error": "Invalid method"}

        if response.status_code in [200, 201]:
            return response.json() if response.content else {"success": True}
        else:
            return {"error": f"API Error: {response.status_code} - {response.text}"}
    except Exception as e:
        LOGGER(__name__).error(f"Sevalla API call failed: {e}")
        return {"error": str(e)}


@Bot.on_message(filters.command("setvar") & filters.user(ADMINS))
async def setvar(client: Bot, message: Message):
    if len(message.command) < 3:
        await message.reply_text("❌ <b>Penggunaan:</b> /setvar KEY VALUE", quote=True)
        return

    key = message.command[1]
    value = " ".join(message.command[2:])

    result = sevalla_api_call("POST", f"/projects/{SEVALLA_PROJECT_ID}/services/{SEVALLA_SERVICE_ID}/env", {"key": key, "value": value})

    if "error" in result:
        await message.reply_text(f"❌ <b>Gagal set env var:</b> {result['error']}", quote=True)
    else:
        await message.reply_text(
            f"✅ <b>Env var berhasil diset!</b>\n\n"
            f"<b>Key:</b> <code>{key}</code>\n"
            f"<b>Value:</b> <code>{value}</code>\n\n"
            "🔄 <b>Restart bot untuk apply perubahan.</b>",
            quote=True
        )


@Bot.on_message(filters.command("delvar") & filters.user(ADMINS))
async def delvar(client: Bot, message: Message):
    if len(message.command) != 2:
        await message.reply_text("❌ <b>Penggunaan:</b> /delvar KEY", quote=True)
        return

    key = message.command[1]

    result = sevalla_api_call("DELETE", f"/projects/{SEVALLA_PROJECT_ID}/services/{SEVALLA_SERVICE_ID}/env/{key}")

    if "error" in result:
        await message.reply_text(f"❌ <b>Gagal hapus env var:</b> {result['error']}", quote=True)
    else:
        await message.reply_text(
            f"✅ <b>Env var berhasil dihapus!</b>\n\n"
            f"<b>Key:</b> <code>{key}</code>\n\n"
            "🔄 <b>Restart bot untuk apply perubahan.</b>",
            quote=True
        )


@Bot.on_message(filters.command("getvar") & filters.user(ADMINS))
async def getvar(client: Bot, message: Message):
    if len(message.command) > 1:
        key = message.command[1]
        # Get specific env var
        result = sevalla_api_call("GET", f"/projects/{SEVALLA_PROJECT_ID}/services/{SEVALLA_SERVICE_ID}/env/{key}")
        if "error" in result:
            await message.reply_text(f"❌ <b>Gagal ambil env var:</b> {result['error']}", quote=True)
        else:
            value = result.get("value", "Not found")
            await message.reply_text(
                f"🔍 <b>Env Var Info</b>\n\n"
                f"<b>Key:</b> <code>{key}</code>\n"
                f"<b>Value:</b> <code>{value}</code>",
                quote=True
            )
    else:
        # Get all env vars
        result = sevalla_api_call("GET", f"/projects/{SEVALLA_PROJECT_ID}/services/{SEVALLA_SERVICE_ID}/env")
        if "error" in result:
            await message.reply_text(f"❌ <b>Gagal ambil env vars:</b> {result['error']}", quote=True)
        else:
            env_vars = result.get("variables", [])
            if not env_vars:
                await message.reply_text("❌ <b>Tidak ada env vars ditemukan!</b>", quote=True)
                return

            env_list = "\n".join([f"├ <code>{var['key']}</code> = <code>{var['value'][:50]}{'...' if len(var['value']) > 50 else ''}</code>" for var in env_vars])
            await message.reply_text(
                f"📋 <b>DAFTAR ENV VARS</b>\n\n{env_list}\n\n"
                f"<b>Total:</b> {len(env_vars)}\n\n"
                "💡 <b>Gunakan /getvar KEY untuk detail spesifik.</b>",
                quote=True
            )


@Bot.on_message(filters.command("usage") & filters.user(ADMINS))
async def usage(client: Bot, message: Message):
    await message.reply_text(
        "📊 <b>SEVALLA APP MONITORING</b>\n\n"
        "💡 <b>Untuk monitoring aplikasi:</b>\n"
        "1. Buka Sevalla Dashboard\n"
        "2. Pilih aplikasi Anda\n"
        "3. Lihat logs di tab 'Logs'\n"
        "4. Monitor performance di tab 'Metrics'\n\n"
        "🔗 <b>Dashboard:</b> https://app.sevalla.com/\n\n"
        "⚙️ <b>Env Management via Bot:</b>\n"
        "├ /setvar KEY VALUE - Set env var\n"
        "├ /delvar KEY - Hapus env var\n"
        "├ /getvar [KEY] - Lihat env vars\n"
        "└ /restart - Restart bot"
    )