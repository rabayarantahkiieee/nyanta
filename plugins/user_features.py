# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import json
import os
from datetime import datetime
from pyrogram import filters

from bot import Bot
from config import ADMINS
from database.sql import (
    full_userbase,
    get_user_stats as get_db_user_stats,
    get_user_join_info,
    get_user_profile_stats,
    get_user_rank_position,
    get_rank_info,
    set_user_profile_stats,
    add_feedback,
    get_recent_feedback,
    add_report,
    get_pending_reports,
    get_report_counts,
)
from .user_limits import get_user_stats as get_daily_download_stats
from .stats_utils import make_bar, rank_emoji

# Profile stats (total downloads, activity score, streak) are stored in the
# database (see database/sql.py) so they survive redeploys, instead of a
# local user_data.json file.
LEGACY_USER_DATA_FILE = "user_data.json"


def _migrate_legacy_user_data_if_needed():
    """One-time import of data from the old user_data.json into the database."""
    if not os.path.exists(LEGACY_USER_DATA_FILE):
        return
    try:
        with open(LEGACY_USER_DATA_FILE, "r") as f:
            legacy = json.load(f)

        for user_id_str, stats in legacy.items():
            try:
                user_id = int(user_id_str)
            except ValueError:
                continue
            set_user_profile_stats(
                user_id,
                total_downloads=stats.get("total_downloads", 0),
                activity_score=stats.get("activity_score", 0),
                streak_days=stats.get("streak_days", 1),
                last_active_date=stats.get("last_active_date"),
            )

        os.rename(LEGACY_USER_DATA_FILE, LEGACY_USER_DATA_FILE + ".migrated")
        print("[INFO] Migrated user_data.json into the database")
    except Exception as e:
        print(f"[WARNING] Failed to migrate legacy user_data.json: {e}")


_migrate_legacy_user_data_if_needed()

LEGACY_FEEDBACK_FILE = "user_feedback.json"
LEGACY_REPORTS_FILE = "user_reports.json"


def _migrate_legacy_feedback_and_reports_if_needed():
    """One-time import of data from the old feedback/report JSON files into the database."""
    if os.path.exists(LEGACY_FEEDBACK_FILE):
        try:
            with open(LEGACY_FEEDBACK_FILE, "r") as f:
                all_feedback = json.load(f)
            for fb in all_feedback:
                add_feedback(
                    user_id=fb.get("user_id"),
                    username=fb.get("username"),
                    name=fb.get("name"),
                    message=fb.get("feedback", ""),
                )
            os.rename(LEGACY_FEEDBACK_FILE, LEGACY_FEEDBACK_FILE + ".migrated")
            print("[INFO] Migrated user_feedback.json into the database")
        except Exception as e:
            print(f"[WARNING] Failed to migrate legacy user_feedback.json: {e}")

    if os.path.exists(LEGACY_REPORTS_FILE):
        try:
            with open(LEGACY_REPORTS_FILE, "r") as f:
                all_reports = json.load(f)
            for report in all_reports:
                add_report(
                    user_id=report.get("user_id"),
                    username=report.get("username"),
                    name=report.get("name"),
                    issue=report.get("issue", ""),
                )
            os.rename(LEGACY_REPORTS_FILE, LEGACY_REPORTS_FILE + ".migrated")
            print("[INFO] Migrated user_reports.json into the database")
        except Exception as e:
            print(f"[WARNING] Failed to migrate legacy user_reports.json: {e}")


_migrate_legacy_feedback_and_reports_if_needed()

@Bot.on_message(filters.command("profile"))
async def user_profile(client, message):
    """Show user profile with statistics"""
    try:
        user = message.from_user
        user_id = user.id

        profile_stats = get_user_profile_stats(user_id)
        total_downloads = profile_stats["total_downloads"]
        activity_score = profile_stats["activity_score"]
        streak_days = profile_stats["streak_days"]
        rank_info = get_rank_info(activity_score)

        # Get total users and stats
        users = await full_userbase()
        stats = get_db_user_stats()
        total_users = len(users)
        active_today = stats.get('active_today', 0)

        # Get join date
        join_info = get_user_join_info(user_id)
        days_active = (datetime.now() - join_info["first_seen"].replace(tzinfo=None)).days

        # Get user position by activity score
        user_position = get_user_rank_position(user_id) or "Unknown"

        # Get today's download count from the (correctly, daily-reset) limit tracker
        daily_stats = get_daily_download_stats(user_id)
        downloads_today = daily_stats["today_downloads"]
        daily_limit = daily_stats["daily_limit"]

        if rank_info["next_rank"]:
            rank_progress_line = (
                f"├ <b>Progress:</b> <code>{make_bar(rank_info['progress'])}</code> "
                f"{rank_info['progress'] * 100:.0f}% → {rank_emoji(rank_info['next_rank'])} {rank_info['next_rank']}"
            )
        else:
            rank_progress_line = "├ <b>Progress:</b> <code>██████████</code> MAX RANK"

        download_bar = make_bar(downloads_today / daily_limit if daily_limit else 0)

        profile = f"""<b>👤 YOUR PROFILE</b>

<b>📋 Basic Info</b>
├ <b>Name:</b> {user.first_name} {user.last_name or ''}
├ <b>Username:</b> @{user.username or 'None'}
├ <b>User ID:</b> <code>{user.id}</code>
└ <b>Member Since:</b> {days_active} hari lalu

<b>{rank_emoji(rank_info['rank'])} Rank: {rank_info['rank']}</b>
{rank_progress_line}
└ <b>Position:</b> #{user_position} dari {total_users:,} user

<b>📊 Your Stats</b>
├ <b>Total Downloads:</b> {total_downloads:,}
├ <b>Downloads Today:</b> <code>{download_bar}</code> {downloads_today}/{daily_limit}
├ <b>Activity Score:</b> {activity_score:,}
└ <b>Streak:</b> 🔥 {streak_days} hari

<b>🎯 Community</b>
├ <b>Total Users:</b> {total_users:,}
└ <b>Active Today:</b> {active_today:,}

<b>🏆 Achievements</b>
├ <b>Active User</b> (streak 7+): {"✅" if streak_days >= 7 else "❌"}
├ <b>Power User</b> (score 100+): {"✅" if activity_score >= 100 else "❌"}
└ <b>Legend</b> (score 1000+): {"✅" if activity_score >= 1000 else "❌"}"""

        await message.reply_text(profile, quote=True)

    except Exception as e:
        print(f"Profile error: {e}")
        await message.reply_text(f"❌ <b>Error loading profile:</b> {str(e)}", quote=True)


@Bot.on_message(filters.command("feedback"))
async def user_feedback(client, message):
    """Allow users to send feedback"""
    if len(message.command) < 2:
        await message.reply_text(
            "❌ <b>Penggunaan:</b> /feedback [pesan feedback Anda]\n\n"
            "<b>Contoh:</b> /feedback Bot sangat membantu dan cepat!",
            quote=True
        )
        return

    feedback_text = " ".join(message.command[1:])
    user = message.from_user

    add_feedback(
        user_id=user.id,
        username=user.username,
        name=f"{user.first_name} {user.last_name or ''}".strip(),
        message=feedback_text,
    )

    await message.reply_text(
        "✅ <b>Terima kasih atas feedback Anda!</b>\n\n"
        f"<b>Feedback:</b> {feedback_text[:100]}{'...' if len(feedback_text) > 100 else ''}\n\n"
        "💬 <b>Feedback Anda telah dicatat dan akan kami tinjau.</b>",
        quote=True
    )


@Bot.on_message(filters.command("report"))
async def report_issue(client, message):
    """Allow users to report issues"""
    if len(message.command) < 2:
        await message.reply_text(
            "❌ <b>Penggunaan:</b> /report [deskripsi masalah]\n\n"
            "<b>Contoh:</b> /report Link download tidak bisa diakses\n\n"
            "<b>Kami akan segera menindaklanjuti laporan Anda.</b>",
            quote=True
        )
        return

    issue_text = " ".join(message.command[1:])
    user = message.from_user

    add_report(
        user_id=user.id,
        username=user.username,
        name=f"{user.first_name} {user.last_name or ''}".strip(),
        issue=issue_text,
    )

    await message.reply_text(
        "📋 <b>Laporan Anda telah diterima!</b>\n\n"
        f"<b>Issue:</b> {issue_text[:100]}{'...' if len(issue_text) > 100 else ''}\n\n"
        "🔧 <b>Tim kami akan segera menindaklanjuti.</b>\n"
        "📞 <b>Untuk follow-up: @yawrenmaru</b>",
        quote=True
    )


@Bot.on_message(filters.command("tutorial"))
async def user_tutorial(client, message):
    """Show tutorial for new users"""
    tutorial_text = """
<b>📚 TUTORIAL - Cara Menggunakan File Sharing Bot</b>

<b>🎯 LANGKAH 1: Upload File Pertama Anda</b>
1. Kirim file apapun ke bot (foto, video, dokumen, dll)
2. Bot akan otomatis memproses dan memberikan link
3. Share link tersebut ke orang yang ingin download

<b>🔗 LANGKAH 2: Menggunakan Link Sharing</b>
• Link yang diberikan bot bersifat permanen
• Siapapun yang memiliki link bisa download
• Tidak ada batas waktu atau limit download
• File tetap aman dan terproteksi

<b>📁 LANGKAH 3: Fitur Advanced</b>

<b>Single File:</b>
• Kirim file → Dapat link langsung

<b>Multiple Files (Batch):</b>
• Forward beberapa file dari channel database
• Gunakan command /batch
• Dapat satu link untuk semua file

<b>Custom Link:</b>
• Gunakan /genlink untuk file spesifik
• Lebih fleksibel untuk management

<b>⚙️ LANGKAH 4: Tips & Trik</b>
• File size unlimited (sesuai Telegram limits)
• Support semua format file
• Link bekerja di semua device
• Download speed maksimal
• File tetap ada selama bot aktif

<b>🆘 BUTUH BANTUAN?</b>
• <b>Help:</b> /help - Semua perintah tersedia
• <b>Tutorial:</b> /tutorial - Panduan lengkap
• <b>Info:</b> /id - Informasi lengkap profile
• <b>Stats:</b> /stats - Statistik pengguna bot
• <b>Profile:</b> /profile - Lihat statistik Anda
• <b>Feedback:</b> /feedback [pesan] - Kirim feedback
• <b>Report:</b> /report [masalah] - Laporkan issue
• <b>Contact:</b> @yawrenmaru untuk support

<b>🚀 SELAMAT MENCOBA!</b>
"""

    await message.reply_text(tutorial_text, quote=True)




# Admin command to view user feedback
@Bot.on_message(filters.command("viewfeedback") & filters.user(ADMINS))
async def view_feedback(client, message):
    """Admin command to view user feedback"""
    try:
        recent_feedback = get_recent_feedback(limit=5)

        if not recent_feedback:
            await message.reply_text("❌ <b>Belum ada feedback dari user.</b>", quote=True)
            return

        feedback_text = "<b>💬 USER FEEDBACK (5 Terakhir)</b>\n\n"
        for i, fb in enumerate(recent_feedback, 1):
            feedback_text += f"<b>{i}. {fb['name']}</b> (@{fb['username'] or 'None'})\n"
            feedback_text += f"├ ID: <code>{fb['user_id']}</code>\n"
            feedback_text += f"├ Time: {fb['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            feedback_text += f"└ Feedback: {fb['message'][:100]}{'...' if len(fb['message']) > 100 else ''}\n\n"

        await message.reply_text(feedback_text, quote=True)

    except Exception as e:
        await message.reply_text(f"❌ <b>Error viewing feedback:</b> {str(e)}", quote=True)


# Admin command to view user reports
@Bot.on_message(filters.command("viewreports") & filters.user(ADMINS))
async def view_reports(client, message):
    """Admin command to view user reports"""
    try:
        pending_reports = get_pending_reports(limit=5)
        pending_count, total_count = get_report_counts()

        if total_count == 0:
            await message.reply_text("❌ <b>Belum ada laporan dari user.</b>", quote=True)
            return

        if not pending_reports:
            await message.reply_text("✅ <b>Semua laporan sudah ditangani.</b>", quote=True)
            return

        report_text = "<b>📋 PENDING USER REPORTS (5 Terakhir)</b>\n\n"
        for i, report in enumerate(pending_reports, 1):
            report_text += f"<b>{i}. {report['name']}</b> (@{report['username'] or 'None'})\n"
            report_text += f"├ ID: <code>{report['user_id']}</code>\n"
            report_text += f"├ Time: {report['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            report_text += f"└ Issue: {report['issue'][:100]}{'...' if len(report['issue']) > 100 else ''}\n\n"

        report_text += f"<b>Pending Reports: {pending_count}</b>\n"
        report_text += f"<b>Total Reports: {total_count}</b>"

        await message.reply_text(report_text, quote=True)

    except Exception as e:
        await message.reply_text(f"❌ <b>Error viewing reports:</b> {str(e)}", quote=True)