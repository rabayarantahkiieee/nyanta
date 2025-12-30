# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import os
import json
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from bot import Bot
from config import ADMINS
from database.sql import add_user, full_userbase, get_user_stats as get_db_user_stats


# File to store user preferences and data
USER_DATA_FILE = "user_data.json"

def load_user_data():
    """Load user data from file"""
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading user data: {e}")
    return {}

def save_user_data(data):
    """Save user data to file"""
    try:
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving user data: {e}")

def update_user_activity(user_id, user_data):
    """Update user activity and stats"""
    user_id_str = str(user_id)
    current_time = datetime.now().isoformat()
    
    if user_id_str not in user_data:
        user_data[user_id_str] = {
            'first_seen': current_time,
            'files_shared': 0,
            'downloads_today': 0,
            'total_downloads': 0,
            'last_activity': current_time,
            'notifications': 'Enabled',
            'preferred_language': 'en',
            'theme': 'Default',
            'activity_score': 0,
            'streak_days': 1,
            'last_active_date': datetime.now().date().isoformat()
        }
    else:
        user_data[user_id_str]['last_activity'] = current_time
        
        # Update streak
        last_active = user_data[user_id_str].get('last_active_date')
        today = datetime.now().date().isoformat()
        
        if last_active != today:
            try:
                last_date = datetime.fromisoformat(last_active).date()
                today_date = datetime.fromisoformat(today).date()
                
                if (today_date - last_date).days == 1:
                    # Consecutive day
                    user_data[user_id_str]['streak_days'] = user_data[user_id_str].get('streak_days', 0) + 1
                elif (today_date - last_date).days > 1:
                    # Streak broken
                    user_data[user_id_str]['streak_days'] = 1
                
                user_data[user_id_str]['last_active_date'] = today
            except:
                user_data[user_id_str]['streak_days'] = 1
                user_data[user_id_str]['last_active_date'] = today

@Bot.on_message(filters.command("profile"))
async def user_profile(client, message):
    """Show user profile with statistics"""
    try:
        user = message.from_user
        user_id = user.id

        # Load and update user data
        user_data = load_user_data()
        update_user_activity(user_id, user_data)
        
        user_stats = user_data.get(str(user_id), {})
        
        # Get total users and stats
        users = await full_userbase()
        stats = get_db_user_stats()
        total_users = len(users)
        active_today = stats.get('active_today', 0)

        # Calculate user rank
        user_rank = "New User"
        files_shared = user_stats.get('files_shared', 0)
        total_downloads = user_stats.get('total_downloads', 0)
        activity_score = user_stats.get('activity_score', 0)
        
        if activity_score >= 1000:
            user_rank = "Legendary User"
        elif activity_score >= 500:
            user_rank = "Power User"
        elif activity_score >= 200:
            user_rank = "Regular User"
        elif activity_score >= 50:
            user_rank = "Active User"
        elif activity_score >= 10:
            user_rank = "Beginner"

        # Get join date
        join_date = user_stats.get('first_seen', 'Unknown')
        days_active = 0
        streak_days = user_stats.get('streak_days', 0)
        
        if join_date != 'Unknown':
            try:
                join_dt = datetime.fromisoformat(join_date.replace('Z', '+00:00'))
                days_active = (datetime.now() - join_dt.replace(tzinfo=None)).days
            except:
                days_active = 0

        # Calculate user position (simplified)
        try:
            if user_data:
                all_users = sorted(user_data.items(), key=lambda x: x[1].get('activity_score', 0), reverse=True)
                user_position = next((i+1 for i, (uid, _) in enumerate(all_users) if uid == str(user_id)), "Unknown")
            else:
                user_position = "Unknown"
        except Exception:
            user_position = "Unknown"

        # Get daily downloads info
        downloads_today = user_stats.get('downloads_today', 0)
        daily_limit = user_stats.get('daily_limit', 2)

        profile = f"""<b>👤 YOUR PROFILE</b>

<b>📋 Basic Info:</b>
├ <b>Name:</b> {user.first_name} {user.last_name or ''}
├ <b>Username:</b> @{user.username or 'None'}
├ <b>User ID:</b> <code>{user.id}</code>
└ <b>Member Since:</b> {days_active} days ago

<b>📊 Your Stats:</b>
├ <b>Rank:</b> {user_rank}
├ <b>Files Shared:</b> {files_shared}
├ <b>Total Downloads:</b> {total_downloads}
├ <b>Downloads Today:</b> {downloads_today}/{daily_limit}
├ <b>Activity Score:</b> {activity_score}
├ <b>Streak:</b> {streak_days} days
└ <b>Position:</b> #{user_position}

<b>🎯 Community:</b>
├ <b>Total Users:</b> {total_users:,}
├ <b>Active Today:</b> {active_today}
└ <b>Last Active:</b> {user_stats.get('last_activity', 'Unknown')[:19]}

<b>⚙️ Settings:</b>
├ <b>Notifications:</b> {user_stats.get('notifications', 'Enabled')}
├ <b>Language:</b> {user_stats.get('preferred_language', 'Auto')}
└ <b>Theme:</b> {user_stats.get('theme', 'Default')}

<b>🏆 Achievements:</b>
├ <b>First Share:</b> {"✅" if files_shared > 0 else "❌"}
├ <b>Active User:</b> {"✅" if streak_days >= 7 else "❌"}
├ <b>Power User:</b> {"✅" if activity_score >= 100 else "❌"}
└ <b>Legend:</b> {"✅" if activity_score >= 1000 else "❌"}"""

        save_user_data(user_data)

        await message.reply_text(profile, quote=True)

    except Exception as e:
        print(f"Profile error: {e}")
        await message.reply_text(f"❌ <b>Error loading profile:</b> {str(e)}", quote=True)


@Bot.on_message(filters.command("help"))
async def enhanced_help(client, message):
    """Enhanced help command with all commands"""
    help_text = """
<b>🤖 File Sharing Bot v4.5.0 - Complete Commands Guide</b>

<b>🚀 NEW FEATURES:</b>
├ ✅ <b>Auto Command Menu</b> - Commands otomatis terdaftar di menu bot
├ ✅ <b>Real-time Subscription Tracking</b> - Status subscribe tersimpan real-time
├ ✅ <b>Enhanced Profile System</b> - Statistik & ranking lengkap
├ ✅ <b>Database Backup/Restore</b> - Backup data user aman
├ ✅ <b>Media Broadcasting</b> - /setmsg & /broadcast support media (photo/video/document)
├ ✅ <b>Advanced Broadcasting</b> - Broadcast dengan HTML formatting & media
├ ✅ <b>Personalized Messages</b> - Placeholder support: {ID},{NAME},{USERNAME}, dll
└ ✅ <b>Rich Text Formatting</b> - HTML tags & dynamic content

<b>📚 BASIC COMMANDS (User):</b>
├ /start - Mulai bot & generate file links
├ /help - Bantuan lengkap semua perintah
├ /about - Informasi lengkap tentang bot
├ /profile - Lihat profil & statistik pengguna
├ /id - Lihat informasi profile lengkap
├ /ping - Test respons bot
├ /uptime - Lihat status uptime bot
├ /stats - Lihat statistik bot
├ /feedback - Kirim feedback ke developer
├ /report - Laporkan masalah atau bug
└ /tutorial - Panduan lengkap penggunaan bot

<b>📁 FILE SHARING (Admin):</b>
├ /genlink - Generate link untuk single file
├ /batch - Generate link untuk multiple files
├ /users - Statistik pengguna bot
├ /broadcast - Kirim broadcast ke semua user
├ <i>Support: Media, HTML, Placeholders</i>
└ <i>Variables: {ID},{NAME},{USERNAME},{DATE}, dll</i>

<b>👥 USER MANAGEMENT (Admin):</b>
├ /setlimit JUMLAH - Set daily download limit
├ /getlimit - Lihat current daily limit
├ /userstats - Statistik semua user
├ /checkuser USER_ID - Check informasi user tertentu
├ /resetlimits - Reset semua user limits
├ /setuserlimit USER_ID LIMIT - Set custom limit per user
├ /deluserlimit USER_ID - Delete custom limit user
├ /getuserlimits - View all custom user limits
├ /addadmin USER_ID - Tambahkan admin baru
├ /deladmin USER_ID - Hapus admin dari daftar
└ /getadmin - Lihat daftar admin

<b>🛡️ CONTENT PROTECTION (Admin):</b>
├ /addkonten FILE_ID - Tambahkan file ke protected list
├ /delkonten FILE_ID - Hapus file dari protected list
├ /getkonten - Lihat daftar protected content
└ /limitkonten FILE_ID LIMIT - Set limit untuk konten tertentu

<b>🔘 CUSTOM BUTTONS (Admin):</b>
├ /addbutton TEXT URL - Tambahkan custom button
├ /delbutton BUTTON_ID - Hapus custom button
├ /getbutton - Lihat daftar custom buttons
├ /limitbutton on/off - Enable/disable custom buttons
└ /setmsg TYPE MESSAGE - Set custom messages

<b>💾 DATABASE MANAGEMENT (Admin):</b>
├ /getdb - Informasi database
├ /setdb DATABASE_URL - Set database URL
├ /backupdb - Backup database
├ /restoredb FILE - Restore database dari backup
└ /cleardb - Clear database (PERINGATAN!)

<b>⚙️ SYSTEM & MONITORING (Admin):</b>
├ /logs - Download file logs bot
├ /vars - Lihat semua config variables
├ /info - Informasi lengkap bot & statistik
├ /speedtest - Test kecepatan server
├ /setvar KEY VALUE - Set environment variable
├ /delvar KEY - Hapus environment variable
├ /getvar KEY - Lihat environment variable
├ /usage - Monitoring aplikasi Heroku
├ /update - Update bot dari GitHub
├ /restart - Restart bot
└ /pull - Pull update tanpa restart

<b>📝 FEEDBACK & SUPPORT:</b>
├ /viewfeedback - Lihat feedback dari pengguna (Admin)
└ /viewreports - Lihat laporan masalah dari pengguna (Admin)

<b>📖 HOW TO USE:</b>
• <b>Share Files:</b> Send file → Get sharing link
• <b>Batch Upload:</b> Forward files → /batch
• <b>Force Subscription:</b> Join channels/groups → Click "✅ Sudah Subscribe? Klik di sini"
• <b>Protect Content:</b> Use content protection commands
• <b>Manage Users:</b> Use user management commands (set custom limits per user)
• <b>Custom Buttons:</b> Add promotional links
• <b>Get Support:</b> Use feedback/report commands

<b>💡 IMPORTANT FEATURES:</b>
• <b>Daily Limits:</b> Each user has daily download limit
• <b>Custom User Limits:</b> Set individual limits per user (VIP, premium, etc.)
• <b>Content Protection:</b> Files can be protected with limits
• <b>Custom Buttons:</b> Add custom promotional buttons
• <b>Real-time Stats:</b> Track user activity & downloads
• <b>Database Backup:</b> Automatic backup & restore
• <b>Admin Panel:</b> Complete bot management

<b>🚀 READY TO USE!</b>
<b>📞 Support:</b> @yawrenmaru
<b>📚 Repository:</b> https://github.com/rabayarantahkiieee/File-Sharing-Mann"""

    await message.reply_text(help_text, quote=True, disable_web_page_preview=True)


@Bot.on_message(filters.command("about"))
async def about_bot(client, message):
    """Show information about the bot"""
    about_text = """
<b>🤖 ABOUT FILE SHARING BOT</b>

<b>📋 Bot Information:</b>
├ <b>Name:</b> File Sharing Bot
├ <b>Version:</b> v4.5.0
├ <b>Language:</b> Python (Pyrogram)
├ <b>Database:</b> PostgreSQL/SQLite
├ <b>Platform:</b> Telegram Bot API

<b>👨‍💻 Developer:</b>
├ <b>Original:</b> @mrismanaziz
├ <b>Recode:</b> @yawrenmaru
├ <b>Developed By:</b> Soxmed
├ <b>Support:</b> @yawrenmaru

<b>🚀 Features:</b>
├ ✅ <b>File Sharing</b> - Unlimited file sharing
├ ✅ <b>Batch Upload</b> - Multiple files at once
├ ✅ <b>Force Subscription</b> - Channel/Group protection
├ ✅ <b>User Management</b> - Admin controls & limits
├ ✅ <b>Content Protection</b> - File security & limits
├ ✅ <b>Custom Buttons</b> - Promotional links
├ ✅ <b>Real-time Stats</b> - User activity tracking
├ ✅ <b>Database Backup</b> - Data safety
├ ✅ <b>Media Broadcasting</b> - Rich media support
├ ✅ <b>Advanced Messages</b> - HTML formatting
├ ✅ <b>Personalized Messages</b> - Placeholder variables
└ ✅ <b>Dynamic Content</b> - {ID},{NAME},{USERNAME},{DATE}, dll

<b>📊 Statistics:</b>
├ <b>Total Users:</b> Growing community
├ <b>Files Shared:</b> Unlimited capacity
├ <b>Uptime:</b> 99.9% reliability
└ <b>Support:</b> 24/7 available

<b>📞 Contact & Support:</b>
├ <b>Developer:</b> @yawrenmaru
├ <b>Repository:</b> https://github.com/rabayarantahkiieee/File-Sharing-Mann
├ <b>Feedback:</b> /feedback [message]
└ <b>Report Issues:</b> /report [issue]

<b>💡 How to Use:</b>
• Send any file to get sharing link
• Use /help for complete commands
• Use /tutorial for user guide
• Contact support for assistance

<b>🚀 Stay Updated!</b>
<i>Follow @yawrenmaru for latest updates and features.</i>
"""

    await message.reply_text(about_text, quote=True, disable_web_page_preview=True)


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

    # Save feedback to file
    feedback_data = {
        'user_id': user.id,
        'username': user.username,
        'name': f"{user.first_name} {user.last_name or ''}".strip(),
        'feedback': feedback_text,
        'timestamp': datetime.now().isoformat(),
        'chat_type': message.chat.type
    }

    # Load existing feedback
    feedback_file = "user_feedback.json"
    if os.path.exists(feedback_file):
        with open(feedback_file, 'r') as f:
            all_feedback = json.load(f)
    else:
        all_feedback = []

    all_feedback.append(feedback_data)

    # Save feedback
    with open(feedback_file, 'w') as f:
        json.dump(all_feedback, f, indent=2, default=str)

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

    # Save report to file
    report_data = {
        'user_id': user.id,
        'username': user.username,
        'name': f"{user.first_name} {user.last_name or ''}".strip(),
        'issue': issue_text,
        'timestamp': datetime.now().isoformat(),
        'status': 'pending',
        'chat_type': message.chat.type
    }

    # Load existing reports
    report_file = "user_reports.json"
    if os.path.exists(report_file):
        with open(report_file, 'r') as f:
            all_reports = json.load(f)
    else:
        all_reports = []

    all_reports.append(report_data)

    # Save reports
    with open(report_file, 'w') as f:
        json.dump(all_reports, f, indent=2, default=str)

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
        feedback_file = "user_feedback.json"
        if not os.path.exists(feedback_file):
            await message.reply_text("❌ <b>Belum ada feedback dari user.</b>", quote=True)
            return

        with open(feedback_file, 'r') as f:
            all_feedback = json.load(f)

        if not all_feedback:
            await message.reply_text("❌ <b>Belum ada feedback dari user.</b>", quote=True)
            return

        # Show last 5 feedback
        recent_feedback = all_feedback[-5:]

        feedback_text = "<b>💬 USER FEEDBACK (5 Terakhir)</b>\n\n"
        for i, fb in enumerate(recent_feedback, 1):
            feedback_text += f"<b>{i}. {fb['name']}</b> (@{fb['username'] or 'None'})\n"
            feedback_text += f"├ ID: <code>{fb['user_id']}</code>\n"
            feedback_text += f"├ Time: {fb['timestamp'][:19]}\n"
            feedback_text += f"└ Feedback: {fb['feedback'][:100]}{'...' if len(fb['feedback']) > 100 else ''}\n\n"

        feedback_text += f"<b>Total Feedback: {len(all_feedback)}</b>"

        await message.reply_text(feedback_text, quote=True)

    except Exception as e:
        await message.reply_text(f"❌ <b>Error viewing feedback:</b> {str(e)}", quote=True)


# Admin command to view user reports
@Bot.on_message(filters.command("viewreports") & filters.user(ADMINS))
async def view_reports(client, message):
    """Admin command to view user reports"""
    try:
        report_file = "user_reports.json"
        if not os.path.exists(report_file):
            await message.reply_text("❌ <b>Belum ada laporan dari user.</b>", quote=True)
            return

        with open(report_file, 'r') as f:
            all_reports = json.load(f)

        if not all_reports:
            await message.reply_text("❌ <b>Belum ada laporan dari user.</b>", quote=True)
            return

        # Show pending reports
        pending_reports = [r for r in all_reports if r.get('status') == 'pending']

        if not pending_reports:
            await message.reply_text("✅ <b>Semua laporan sudah ditangani.</b>", quote=True)
            return

        # Show last 5 pending reports
        recent_reports = pending_reports[-5:]

        report_text = "<b>📋 PENDING USER REPORTS (5 Terakhir)</b>\n\n"
        for i, report in enumerate(recent_reports, 1):
            report_text += f"<b>{i}. {report['name']}</b> (@{report['username'] or 'None'})\n"
            report_text += f"├ ID: <code>{report['user_id']}</code>\n"
            report_text += f"├ Time: {report['timestamp'][:19]}\n"
            report_text += f"└ Issue: {report['issue'][:100]}{'...' if len(report['issue']) > 100 else ''}\n\n"

        report_text += f"<b>Pending Reports: {len(pending_reports)}</b>\n"
        report_text += f"<b>Total Reports: {len(all_reports)}</b>"

        await message.reply_text(report_text, quote=True)

    except Exception as e:
        await message.reply_text(f"❌ <b>Error viewing reports:</b> {str(e)}", quote=True)