# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import json
import os
from datetime import datetime, date

from plugins.button_management import get_custom_message, send_custom_message

# User limit settings
USER_LIMITS_FILE = "user_limits.json"

def load_user_limits():
    """Load user limits from file"""
    if os.path.exists(USER_LIMITS_FILE):
        with open(USER_LIMITS_FILE, 'r') as f:
            return json.load(f)
    return {
        "daily_limits": {},
        "config": {
            "daily_download_limit": 2,
            "reset_hour": 0
        },
        "user_custom_limits": {}  # Custom limits per user
    }

def save_user_limits(settings):
    """Save user limits to file"""
    with open(USER_LIMITS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def get_today_key():
    """Get today's date key for tracking"""
    return date.today().isoformat()

def get_daily_limit_config():
    """Get daily limit configuration"""
    settings = load_user_limits()
    return settings["config"]["daily_download_limit"]

def get_user_custom_limit(user_id):
    """Get custom limit for specific user, fallback to global limit"""
    settings = load_user_limits()
    user_id_str = str(user_id)
    return settings["user_custom_limits"].get(user_id_str, settings["config"]["daily_download_limit"])

def set_user_custom_limit(user_id, limit):
    """Set custom limit for specific user"""
    settings = load_user_limits()
    user_id_str = str(user_id)
    settings["user_custom_limits"][user_id_str] = limit
    save_user_limits(settings)

def delete_user_custom_limit(user_id):
    """Delete custom limit for specific user (fallback to global)"""
    settings = load_user_limits()
    user_id_str = str(user_id)
    if user_id_str in settings["user_custom_limits"]:
        del settings["user_custom_limits"][user_id_str]
        save_user_limits(settings)

def get_all_user_custom_limits():
    """Get all users with custom limits"""
    settings = load_user_limits()
    return settings["user_custom_limits"]

def check_user_daily_limit(user_id):
    """Check if user has exceeded daily download limit"""
    settings = load_user_limits()
    today = get_today_key()
    user_id_str = str(user_id)
    
    # Initialize user data if not exists
    if user_id_str not in settings["daily_limits"]:
        settings["daily_limits"][user_id_str] = {
            "date": today,
            "download_count": 0
        }
        save_user_limits(settings)
    
    user_data = settings["daily_limits"][user_id_str]
    
    # Reset if new day
    if user_data["date"] != today:
        user_data["date"] = today
        user_data["download_count"] = 0
        save_user_limits(settings)
    
    # Use custom limit if exists, otherwise use global limit
    daily_limit = get_user_custom_limit(user_id)

    if user_data["download_count"] >= daily_limit:
        return False

    remaining = daily_limit - user_data["download_count"] - 1

    # Increment download count
    user_data["download_count"] += 1
    save_user_limits(settings)

    return True

def get_user_stats(user_id):
    """Get user's daily download statistics"""
    settings = load_user_limits()
    user_id_str = str(user_id)
    
    if user_id_str not in settings["daily_limits"]:
        daily_limit = get_user_custom_limit(user_id)
        return {
            "today_downloads": 0,
            "daily_limit": daily_limit,
            "remaining": daily_limit
        }
    
    user_data = settings["daily_limits"][user_id_str]
    today = get_today_key()
    
    # Reset if new day
    if user_data["date"] != today:
        user_data["date"] = today
        user_data["download_count"] = 0
        save_user_limits(settings)
    
    daily_limit = get_user_custom_limit(user_id)
    downloads = user_data["download_count"]
    
    return {
        "today_downloads": downloads,
        "daily_limit": daily_limit,
        "remaining": daily_limit - downloads
    }

def reset_all_user_limits():
    """Reset all user daily limits (admin function)"""
    settings = load_user_limits()
    for user_id in settings["daily_limits"]:
        settings["daily_limits"][user_id]["download_count"] = 0
        settings["daily_limits"][user_id]["date"] = get_today_key()
    save_user_limits(settings)

def set_daily_limit(new_limit):
    """Set new daily download limit (admin function)"""
    settings = load_user_limits()
    settings["config"]["daily_download_limit"] = new_limit
    save_user_limits(settings)
    return new_limit

def get_all_user_stats():
    """Get all user statistics for admin"""
    settings = load_user_limits()
    today = get_today_key()
    stats = []
    
    for user_id, user_data in settings["daily_limits"].items():
        # Reset if new day
        if user_data["date"] != today:
            user_data["date"] = today
            user_data["download_count"] = 0
        
        daily_limit = get_user_custom_limit(int(user_id))
        downloads = user_data["download_count"]
        remaining = daily_limit - downloads
        
        stats.append({
            "user_id": int(user_id),
            "today_downloads": downloads,
            "daily_limit": daily_limit,
            "remaining": remaining
        })
    
    save_user_limits(settings)
    return stats
