# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import secrets
import time

from pyrogram import filters, StopPropagation
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot import Bot
from config import ADMINS, admin_filter
from database.sql import (
    is_verification_enabled,
    set_verification_enabled,
    get_verification_delay_seconds,
    set_verification_delay_seconds,
    get_verification_valid_hours,
    is_user_verified,
    set_user_verified,
)

# Short-lived, in-process store for pending verification attempts.
# {token: {"user_id": int, "payload": str, "started_at": float | None}}
_PENDING_VERIFICATIONS = {}
_PENDING_TTL_SECONDS = 3600


def _prune_pending():
    now = time.time()
    stale = [
        token for token, data in _PENDING_VERIFICATIONS.items()
        if now - data.get("created_at", now) > _PENDING_TTL_SECONDS
    ]
    for token in stale:
        _PENDING_VERIFICATIONS.pop(token, None)


def _create_pending(user_id, payload):
    _prune_pending()
    token = secrets.token_urlsafe(6)
    _PENDING_VERIFICATIONS[token] = {
        "user_id": user_id,
        "payload": payload,
        "started_at": None,
        "created_at": time.time(),
    }
    return token


async def require_verification_or_prompt(client: Bot, message: Message, base64_string: str) -> bool:
    """
    Returns True if the caller may proceed with delivering the requested file(s).
    If verification is required and the user hasn't passed it yet, sends the
    verification prompt instead and returns False.
    """
    if not is_verification_enabled():
        return True

    user_id = message.from_user.id
    if user_id in ADMINS or is_user_verified(user_id):
        return True

    token = _create_pending(user_id, base64_string)
    await message.reply_text(
        "🔒 <b>Verifikasi Diperlukan</b>\n\n"
        "Untuk mencegah penyalahgunaan link, silakan verifikasi diri kamu dulu "
        "sebelum mengambil file ini. Cukup 2 langkah, tanpa perlu website luar.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("✅ Mulai Verifikasi", callback_data=f"vfy_go:{token}")]]
        ),
        quote=True,
    )
    return False


@Bot.on_callback_query(filters.regex(r"^vfy_go:"), group=-1)
async def verification_start(client: Bot, callback_query: CallbackQuery):
    token = callback_query.data.split(":", 1)[1]
    pending = _PENDING_VERIFICATIONS.get(token)

    if not pending or pending["user_id"] != callback_query.from_user.id:
        await callback_query.answer("❌ Sesi verifikasi tidak valid atau kedaluwarsa. Klik ulang link filenya.", show_alert=True)
        raise StopPropagation

    delay = get_verification_delay_seconds()
    pending["started_at"] = time.time()

    await callback_query.answer()
    await callback_query.message.edit_text(
        f"⏳ <b>Verifikasi Sedang Diproses...</b>\n\n"
        f"Tunggu <b>{delay} detik</b>, lalu tekan tombol di bawah untuk menyelesaikan verifikasi.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔓 Selesai, Ambil File", callback_data=f"vfy_done:{token}")]]
        ),
    )
    raise StopPropagation


@Bot.on_callback_query(filters.regex(r"^vfy_done:"), group=-1)
async def verification_finish(client: Bot, callback_query: CallbackQuery):
    token = callback_query.data.split(":", 1)[1]
    pending = _PENDING_VERIFICATIONS.get(token)

    if not pending or pending["user_id"] != callback_query.from_user.id:
        await callback_query.answer("❌ Sesi verifikasi tidak valid atau kedaluwarsa. Klik ulang link filenya.", show_alert=True)
        raise StopPropagation

    started_at = pending.get("started_at")
    delay = get_verification_delay_seconds()
    if not started_at or (time.time() - started_at) < delay:
        remaining = delay - (time.time() - started_at) if started_at else delay
        await callback_query.answer(f"⏳ Tunggu {max(1, int(remaining))} detik lagi...", show_alert=True)
        raise StopPropagation

    set_user_verified(callback_query.from_user.id)
    _PENDING_VERIFICATIONS.pop(token, None)

    link = f"https://t.me/{client.username}?start={pending['payload']}"
    valid_hours = get_verification_valid_hours()

    await callback_query.answer("✅ Verifikasi berhasil!", show_alert=False)
    await callback_query.message.edit_text(
        f"✅ <b>Verifikasi Berhasil!</b>\n\n"
        f"Status verifikasi kamu berlaku selama {valid_hours} jam. "
        f"Tekan tombol di bawah untuk mengambil file kamu.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("📥 Ambil File Sekarang", url=link)]]
        ),
    )
    raise StopPropagation


@Bot.on_message(filters.private & admin_filter & filters.command("setverify"))
async def set_verify_command(client: Bot, message: Message):
    if len(message.command) != 2 or message.command[1].lower() not in ("on", "off"):
        await message.reply_text(
            "❌ <b>Penggunaan:</b> <code>/setverify on</code> atau <code>/setverify off</code>\n\n"
            f"<b>Status saat ini:</b> {'🟢 Aktif' if is_verification_enabled() else '🔴 Nonaktif'}",
            quote=True,
        )
        return

    enabled = message.command[1].lower() == "on"
    set_verification_enabled(enabled)
    await message.reply_text(
        f"✅ <b>Verifikasi anti-leech {'diaktifkan' if enabled else 'dinonaktifkan'}!</b>",
        quote=True,
    )


@Bot.on_message(filters.private & admin_filter & filters.command("setverifydelay"))
async def set_verify_delay_command(client: Bot, message: Message):
    if len(message.command) != 2 or not message.command[1].isdigit():
        await message.reply_text(
            "❌ <b>Penggunaan:</b> <code>/setverifydelay DETIK</code>\n\n"
            f"<b>Delay saat ini:</b> {get_verification_delay_seconds()} detik",
            quote=True,
        )
        return

    seconds = max(3, min(120, int(message.command[1])))
    set_verification_delay_seconds(seconds)
    await message.reply_text(f"✅ <b>Delay verifikasi diset ke {seconds} detik!</b>", quote=True)
