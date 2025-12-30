# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import json
import os

CONTENT_FILE = "content_settings.json"

def load_content_settings():
    """Load content settings from file"""
    if os.path.exists(CONTENT_FILE):
        with open(CONTENT_FILE, 'r') as f:
            return json.load(f)
    return {
        "protected_files": [],
        "limited_content": {},
        "custom_messages": {}
    }

def save_content_settings(settings):
    """Save content settings to file"""
    with open(CONTENT_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def check_content_protection(message_id, user_id):
    """Check if content is protected and enforce limits"""
    settings = load_content_settings()
    message_id_str = str(message_id)

    # Check if this message is protected
    if message_id_str in settings["protected_files"]:
        # Check if there's a limit for this content
        if message_id_str in settings["limited_content"]:
            current_limit = settings["limited_content"][message_id_str]

            if current_limit <= 0:
                # Limit reached - block access
                return False, "protected_limit_exceeded"

            # Decrease the limit by 1
            settings["limited_content"][message_id_str] = current_limit - 1
            save_content_settings(settings)

            return True, f"OK Download berhasil!\nSisa limit: {current_limit - 1} kali"

    return True, None

def add_protected_file(file_id):
    """Add file to protected list"""
    settings = load_content_settings()
    if file_id not in settings["protected_files"]:
        settings["protected_files"].append(file_id)
        save_content_settings(settings)
    return settings

def remove_protected_file(file_id):
    """Remove file from protected list"""
    settings = load_content_settings()
    if file_id in settings["protected_files"]:
        settings["protected_files"].remove(file_id)
        save_content_settings(settings)
    return settings

def set_file_limit(file_id, limit):
    """Set limit for a file"""
    settings = load_content_settings()
    settings["limited_content"][file_id] = limit
    save_content_settings(settings)
    return settings

def get_protected_files():
    """Get list of protected files"""
    settings = load_content_settings()
    return settings["protected_files"]

def get_limited_content():
    """Get limited content settings"""
    settings = load_content_settings()
    return settings["limited_content"]
