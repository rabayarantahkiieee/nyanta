# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import json
import os

from database.sql import (
    is_file_protected,
    add_protected_file_db,
    remove_protected_file_db,
    get_all_protected_message_ids,
    sync_protected_files,
    set_content_limit_db,
    try_consume_content_limit,
    get_all_content_limits,
    sync_content_limits,
)

# Protected file flags and per-file download limits are stored in the
# database (see database/sql.py) so they survive redeploys, instead of a
# local content_settings.json file.
LEGACY_CONTENT_FILE = "content_settings.json"


def _migrate_legacy_json_if_needed():
    """One-time import of data from the old content_settings.json into the database."""
    if not os.path.exists(LEGACY_CONTENT_FILE):
        return
    try:
        with open(LEGACY_CONTENT_FILE, "r") as f:
            legacy = json.load(f)

        sync_protected_files(legacy.get("protected_files", []))
        sync_content_limits(legacy.get("limited_content", {}))

        os.rename(LEGACY_CONTENT_FILE, LEGACY_CONTENT_FILE + ".migrated")
        print("[INFO] Migrated content_settings.json into the database")
    except Exception as e:
        print(f"[WARNING] Failed to migrate legacy content_settings.json: {e}")


_migrate_legacy_json_if_needed()


def load_content_settings():
    """Load content settings from the database, shaped like the old JSON file."""
    return {
        "protected_files": [str(mid) for mid in get_all_protected_message_ids()],
        "limited_content": {str(mid): limit for mid, limit in get_all_content_limits().items()},
        "custom_messages": {},
    }

def save_content_settings(settings):
    """Persist a full settings dict (as produced by load_content_settings) to the database."""
    sync_protected_files(settings.get("protected_files", []))
    sync_content_limits(settings.get("limited_content", {}))

def check_content_protection(message_id, user_id):
    """Check if content is protected and enforce limits"""
    if not is_file_protected(message_id):
        return True, None

    allowed, remaining = try_consume_content_limit(message_id)
    if not allowed:
        return False, "protected_limit_exceeded"
    if remaining is None:
        return True, None
    return True, f"OK Download berhasil!\nSisa limit: {remaining} kali"

def add_protected_file(file_id):
    """Add file to protected list"""
    add_protected_file_db(int(file_id))
    return load_content_settings()

def remove_protected_file(file_id):
    """Remove file from protected list"""
    remove_protected_file_db(int(file_id))
    return load_content_settings()

def set_file_limit(file_id, limit):
    """Set limit for a file"""
    set_content_limit_db(int(file_id), limit)
    return load_content_settings()

def get_protected_files():
    """Get list of protected files"""
    return load_content_settings()["protected_files"]

def get_limited_content():
    """Get limited content settings"""
    return load_content_settings()["limited_content"]
