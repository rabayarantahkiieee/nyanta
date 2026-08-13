# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

"""Small shared helpers for prettifying stats-style text output."""

RANK_EMOJI = {
    "New": "🌱",
    "Beginner": "🔰",
    "Active": "⚡",
    "Regular": "🌟",
    "Power": "💪",
    "Legendary": "👑",
}


def make_bar(fraction, length=10, filled="█", empty="░"):
    """Render a simple block progress bar for the given 0.0-1.0 fraction."""
    fraction = max(0.0, min(1.0, fraction))
    filled_count = round(fraction * length)
    return filled * filled_count + empty * (length - filled_count)


def rank_emoji(rank_name):
    return RANK_EMOJI.get(rank_name, "🌱")
