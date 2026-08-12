# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import json
import os
from datetime import date

from database.sql import (
    get_daily_limit_config as _get_daily_limit_config,
    set_daily_limit_config,
    get_user_custom_limit_db,
    set_user_custom_limit_db,
    delete_user_custom_limit_db,
    get_all_user_custom_limits_db,
    try_consume_daily_download,
    get_daily_download_count,
    reset_all_daily_downloads,
    get_all_daily_downloads,
)

# Limit data now lives in the persistent database (see database/sql.py) so it
# survives redeploys, instead of a local JSON file that gets wiped on
# ephemeral hosts like Heroku.
LEGACY_USER_LIMITS_FILE = "user_limits.json"


def _migrate_legacy_json_if_needed():
    """One-time import of data from the old user_limits.json into the database."""
    if not os.path.exists(LEGACY_USER_LIMITS_FILE):
        return
    try:
        with open(LEGACY_USER_LIMITS_FILE, "r") as f:
            legacy = json.load(f)

        global_limit = legacy.get("config", {}).get("daily_download_limit")
        if global_limit is not None:
            set_daily_limit_config(global_limit)

        for user_id_str, limit in legacy.get("user_custom_limits", {}).items():
            try:
                set_user_custom_limit_db(int(user_id_str), limit)
            except (TypeError, ValueError):
                continue

        os.rename(LEGACY_USER_LIMITS_FILE, LEGACY_USER_LIMITS_FILE + ".migrated")
        print("[INFO] Migrated user_limits.json into the database")
    except Exception as e:
        print(f"[WARNING] Failed to migrate legacy user_limits.json: {e}")


_migrate_legacy_json_if_needed()


def get_today_key():
    """Get today's date key for tracking"""
    return date.today().isoformat()


def get_daily_limit_config():
    """Get global daily limit configuration"""
    return _get_daily_limit_config()


def get_user_custom_limit(user_id):
    """Get custom limit for specific user, fallback to global limit"""
    custom = get_user_custom_limit_db(user_id)
    return custom if custom is not None else _get_daily_limit_config()


def set_user_custom_limit(user_id, limit):
    """Set custom limit for specific user"""
    set_user_custom_limit_db(user_id, limit)


def delete_user_custom_limit(user_id):
    """Delete custom limit for specific user (fallback to global)"""
    delete_user_custom_limit_db(user_id)


def get_all_user_custom_limits():
    """Get all users with custom limits"""
    return get_all_user_custom_limits_db()


def check_user_daily_limit(user_id):
    """Check if user has exceeded daily download limit, consuming one download if not."""
    daily_limit = get_user_custom_limit(user_id)
    return try_consume_daily_download(user_id, get_today_key(), daily_limit)


def get_user_stats(user_id):
    """Get user's daily download statistics"""
    daily_limit = get_user_custom_limit(user_id)
    downloads = get_daily_download_count(user_id, get_today_key())
    return {
        "today_downloads": downloads,
        "daily_limit": daily_limit,
        "remaining": daily_limit - downloads,
    }


def reset_all_user_limits():
    """Reset all user daily limits (admin function)"""
    reset_all_daily_downloads(get_today_key())


def set_daily_limit(new_limit):
    """Set new daily download limit (admin function)"""
    set_daily_limit_config(new_limit)
    return new_limit


def get_all_user_stats():
    """Get all user statistics for admin"""
    today = get_today_key()
    stats = []
    for row in get_all_daily_downloads(today):
        user_id = row["user_id"]
        downloads = row["today_downloads"]
        daily_limit = get_user_custom_limit(user_id)
        stats.append({
            "user_id": user_id,
            "today_downloads": downloads,
            "daily_limit": daily_limit,
            "remaining": daily_limit - downloads,
        })
    return stats
