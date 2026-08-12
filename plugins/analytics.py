# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import asyncio
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pyrogram import filters
from pyrogram.types import Message

from bot import Bot
from config import ADMINS
from database.sql import (
    get_daily_downloads_range,
    get_user_growth_range,
    get_rank_distribution,
    get_top_users_by_activity,
    get_user_stats as get_db_user_stats,
)

BG_COLOR = "#0d1117"
PANEL_COLOR = "#161b22"
TEXT_COLOR = "#e6edf3"
GRID_COLOR = "#30363d"
ACCENT_BLUE = "#58a6ff"
ACCENT_GREEN = "#3fb950"
ACCENT_PURPLE = "#bc8cff"

RANK_ORDER = ["New", "Beginner", "Active", "Regular", "Power", "Legendary"]
RANK_COLORS = {
    "New": "#8b949e",
    "Beginner": "#58a6ff",
    "Active": "#3fb950",
    "Regular": "#e3b341",
    "Power": "#f0883e",
    "Legendary": "#bc8cff",
}


def _style_axis(ax, title):
    ax.set_facecolor(PANEL_COLOR)
    ax.set_title(title, color=TEXT_COLOR, fontsize=12, fontweight="bold", loc="left", pad=10)
    ax.tick_params(colors=TEXT_COLOR, labelsize=8)
    ax.grid(True, color=GRID_COLOR, linewidth=0.6, alpha=0.6)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)


def render_analytics_chart(bot_name):
    """Build the 2x2 analytics dashboard image and return it as a PNG BytesIO buffer."""
    growth = get_user_growth_range(days=14)
    downloads = get_daily_downloads_range(days=14)
    ranks = get_rank_distribution()
    top_users = get_top_users_by_activity(limit=8)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.patch.set_facecolor(BG_COLOR)
    # Matplotlib's default font can't render emoji glyphs (they'd show as
    # tofu boxes), so titles here stay plain text - the Telegram caption
    # sent alongside the image is where emoji actually render nicely.
    fig.suptitle(f"{bot_name} — Analytics Dashboard", color=TEXT_COLOR, fontsize=16, fontweight="bold")

    # 1. User growth
    ax = axes[0][0]
    dates = [d[5:] for d, _ in growth]  # MM-DD
    counts = [c for _, c in growth]
    ax.plot(range(len(dates)), counts, color=ACCENT_BLUE, marker="o", markersize=4, linewidth=2)
    ax.fill_between(range(len(dates)), counts, color=ACCENT_BLUE, alpha=0.15)
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(dates, rotation=45, ha="right")
    _style_axis(ax, "User Growth (14 hari)")

    # 2. Downloads per day
    ax = axes[0][1]
    dl_dates = [d[5:] for d, _ in downloads]
    dl_counts = [c for _, c in downloads]
    ax.bar(range(len(dl_dates)), dl_counts, color=ACCENT_GREEN)
    ax.set_xticks(range(len(dl_dates)))
    ax.set_xticklabels(dl_dates, rotation=45, ha="right")
    _style_axis(ax, "Downloads (14 hari)")

    # 3. Rank distribution
    ax = axes[1][0]
    values = [ranks.get(t, 0) for t in RANK_ORDER]
    colors = [RANK_COLORS[t] for t in RANK_ORDER]
    ax.barh(RANK_ORDER, values, color=colors)
    _style_axis(ax, "Rank Distribution")

    # 4. Top users leaderboard
    ax = axes[1][1]
    if top_users:
        ordered = list(reversed(top_users))
        names = [f"@{u['username']}" if u['username'] else str(u['user_id']) for u in ordered]
        scores = [u['activity_score'] for u in ordered]
        ax.barh(names, scores, color=ACCENT_PURPLE)
    else:
        ax.text(0.5, 0.5, "Belum ada data", ha="center", va="center", color=TEXT_COLOR, transform=ax.transAxes)
    _style_axis(ax, "Top Activity")

    plt.tight_layout(rect=[0, 0, 1, 0.94])

    buf = io.BytesIO()
    buf.name = "analytics.png"
    fig.savefig(buf, format="png", facecolor=BG_COLOR, dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


@Bot.on_message(filters.command("analytics") & filters.user(ADMINS))
async def analytics_command(client: Bot, message: Message):
    """Admin command: render a visual analytics dashboard and send it as a photo."""
    msg = await message.reply_text("<code>📊 Membuat grafik analytics...</code>", quote=True)
    try:
        buf = await asyncio.to_thread(render_analytics_chart, client.namebot)

        db_stats = get_db_user_stats()
        caption = (
            f"📊 <b>ANALYTICS DASHBOARD</b>\n\n"
            f"👥 <b>Total Users:</b> {db_stats['total_users']:,}\n"
            f"🔥 <b>Active Today:</b> {db_stats['active_today']:,}\n"
            f"🚫 <b>Blocked:</b> {db_stats['blocked_users']:,}"
        )

        await client.send_photo(
            chat_id=message.chat.id,
            photo=buf,
            caption=caption,
        )
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ <b>Gagal membuat analytics:</b> `{e}`")
