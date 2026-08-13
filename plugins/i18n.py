# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

"""
Lightweight i18n for the bot's core user-facing messages (file delivery
flow, /about, /language). Admin commands and env-configurable messages
(START_MSG, /help, /setmsg custom messages) stay Indonesian-only.
"""

from database.sql import get_effective_language, DEFAULT_LANGUAGE

STRINGS = {
    "id": {
        "please_wait": "Tunggu Sebentar...",
        "error_generic": "<b>Telah Terjadi Error </b>🥺",
        "limit_exceeded": (
            "❌ <b>LIMIT HARIAN HABIS!</b>\n\n"
            "Anda sudah mencapai batas download harian.\n"
            "Coba lagi besok!"
        ),
        "protected_limit_exceeded": (
            "❌ <b>LIMIT DOWNLOAD HABIS!</b>\n\n"
            "Konten ini sudah mencapai batas download maksimal."
        ),
        "daily_info": "Limit harian: {used}/{limit} (Sisa: {remaining})",
        "language_prompt": "🌐 <b>Pilih bahasa kamu:</b>",
        "language_set": "✅ Bahasa berhasil diatur ke <b>Bahasa Indonesia</b> 🇮🇩",
        "about_title": "🤖 File Sharing Bot - Bot Berbagi File Telegram Canggih",
        "about_body": (
            "<b>📋 Tentang Bot ini:</b>\n\n"
            "<b>@{username} adalah Bot Telegram canggih untuk:</b>\n"
            " ├ ✅ Menyimpan file pribadi di channel database\n"
            " ├ ✅ Generate link sharing dengan proteksi\n"
            " ├ ✅ Force subscription untuk channel/group\n"
            " ├ ✅ Pencarian file (/search) & inline sharing\n"
            " ├ ✅ Verifikasi anti-leech dalam bot\n"
            " ├ ✅ Admin management lengkap\n"
            " ├ ✅ Content protection & limits\n"
            " └ ✅ Broadcast system untuk user\n\n"
            "<b>👨‍💻 Developed by </b><a href='https://t.me/{owner}'>@{owner}</a>"
        ),
    },
    "en": {
        "please_wait": "Please wait a moment...",
        "error_generic": "<b>An error occurred </b>🥺",
        "limit_exceeded": (
            "❌ <b>DAILY LIMIT REACHED!</b>\n\n"
            "You've reached your daily download limit.\n"
            "Try again tomorrow!"
        ),
        "protected_limit_exceeded": (
            "❌ <b>DOWNLOAD LIMIT REACHED!</b>\n\n"
            "This content has reached its maximum download limit."
        ),
        "daily_info": "Daily limit: {used}/{limit} (Remaining: {remaining})",
        "language_prompt": "🌐 <b>Choose your language:</b>",
        "language_set": "✅ Language set to <b>English</b> 🇬🇧",
        "about_title": "🤖 File Sharing Bot - Advanced Telegram File Manager",
        "about_body": (
            "<b>📋 About this bot:</b>\n\n"
            "<b>@{username} is an advanced Telegram bot for:</b>\n"
            " ├ ✅ Storing personal files in a database channel\n"
            " ├ ✅ Generating protected sharing links\n"
            " ├ ✅ Force subscription for channels/groups\n"
            " ├ ✅ File search (/search) & inline sharing\n"
            " ├ ✅ In-bot anti-leech verification\n"
            " ├ ✅ Full admin management\n"
            " ├ ✅ Content protection & limits\n"
            " └ ✅ Broadcast system for users\n\n"
            "<b>👨‍💻 Developed by </b><a href='https://t.me/{owner}'>@{owner}</a>"
        ),
    },
}


def t(user_id, key, **kwargs):
    """
    Translate `key` for the given user, formatting with kwargs if provided.
    Uses their explicit /language choice if they made one, otherwise falls
    back to their Telegram client's language automatically.
    """
    lang = get_effective_language(user_id)
    template = STRINGS.get(lang, {}).get(key) or STRINGS[DEFAULT_LANGUAGE].get(key, key)
    return template.format(**kwargs) if kwargs else template
