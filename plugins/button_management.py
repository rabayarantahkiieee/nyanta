# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

import json
import os

from bot import Bot
from config import ADMINS, LOGGER
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

BUTTON_FILE = "button_settings.json"

def load_button_settings():
    """Load button settings from file"""
    if os.path.exists(BUTTON_FILE):
        with open(BUTTON_FILE, 'r') as f:
            return json.load(f)
    return {
        "custom_buttons": {},
        "default_buttons": True,
        "custom_messages": {}
    }

def save_button_settings(settings):
    """Save button settings to file"""
    with open(BUTTON_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def get_custom_message(msg_type):
    """Get custom message with media support"""
    settings = load_button_settings()
    message_data = settings.get("custom_messages", {}).get(msg_type)

    if not message_data:
        return None

    # Backward compatibility: if it's a string, convert to dict format
    if isinstance(message_data, str):
        return {
            "type": "text",
            "content": message_data,
            "media_id": None,
            "media_type": None
        }

    return message_data

async def send_custom_message(client, chat_id, msg_type, **kwargs):
    """Send custom message with media support"""
    try:
        message_data = get_custom_message(msg_type)
        if not message_data:
            return False

        # Extract common parameters
        quote = kwargs.get('quote', True)
        protect_content = kwargs.get('protect_content', False)

        # Get default messages for fallback
        default_messages = {
            "limit": "X LIMIT HARIAN HABIS!\n\nAnda sudah mencapai batas download harian.\nCoba lagi besok!",
            "error": "<b>Telah Terjadi Error </b>🥺",
            "protected": "X LIMIT DOWNLOAD HABIS!\n\nKonten ini sudah mencapai batas download maksimal.",
            "welcome": "Selamat datang! Gunakan /start untuk memulai.",
            "custom": "Pesan custom"
        }

        # Process content for newlines
        def process_content(text):
            if text:
                return text.replace('\\n', '\n')
            return text

        # Prepare buttons if they exist
        reply_markup = None
        if message_data.get("buttons"):
            buttons = []
            current_row = []
            
            for button in message_data["buttons"]:
                try:
                    if button.get("text") and button.get("url"):
                        current_row.append(
                            InlineKeyboardButton(
                                text=button["text"],
                                url=button["url"]
                            )
                        )
                        
                        # For now, we'll put 2 buttons per row
                        # In a more advanced implementation, we could parse the original text
                        # to detect && separators and group accordingly
                        if len(current_row) == 2:
                            buttons.append(current_row)
                            current_row = []
                    else:
                        print(f"Invalid button in message data: {button}")
                except Exception as e:
                    print(f"Error creating button: {e}")
            
            # Add any remaining buttons in the current row
            if current_row:
                buttons.append(current_row)
            
            if buttons:
                reply_markup = InlineKeyboardMarkup(buttons)
        
        # Send based on message type
        if message_data["type"] == "photo" and message_data.get("media_id"):
            caption = process_content(message_data.get("content", ""))
            # Only set caption if content is not empty
            if caption:
                await client.send_photo(
                    chat_id=chat_id,
                    photo=message_data["media_id"],
                    caption=caption,
                    protect_content=protect_content,
                    reply_markup=reply_markup
                )
            else:
                await client.send_photo(
                    chat_id=chat_id,
                    photo=message_data["media_id"],
                    protect_content=protect_content,
                    reply_markup=reply_markup
                )
        elif message_data["type"] == "video" and message_data.get("media_id"):
            caption = process_content(message_data.get("content", ""))
            if caption:
                await client.send_video(
                    chat_id=chat_id,
                    video=message_data["media_id"],
                    caption=caption,
                    protect_content=protect_content,
                    reply_markup=reply_markup
                )
            else:
                await client.send_video(
                    chat_id=chat_id,
                    video=message_data["media_id"],
                    protect_content=protect_content,
                    reply_markup=reply_markup
                )
        elif message_data["type"] == "document" and message_data.get("media_id"):
            caption = process_content(message_data.get("content", ""))
            if caption:
                await client.send_document(
                    chat_id=chat_id,
                    document=message_data["media_id"],
                    caption=caption,
                    protect_content=protect_content,
                    reply_markup=reply_markup
                )
            else:
                await client.send_document(
                    chat_id=chat_id,
                    document=message_data["media_id"],
                    protect_content=protect_content,
                    reply_markup=reply_markup
                )
        elif message_data["type"] == "audio" and message_data.get("media_id"):
            caption = process_content(message_data.get("content", ""))
            if caption:
                await client.send_audio(
                    chat_id=chat_id,
                    audio=message_data["media_id"],
                    caption=caption,
                    protect_content=protect_content,
                    reply_markup=reply_markup
                )
            else:
                await client.send_audio(
                    chat_id=chat_id,
                    audio=message_data["media_id"],
                    protect_content=protect_content,
                    reply_markup=reply_markup
                )
        else:
            # Default to text message
            content = process_content(message_data.get("content", ""))
            if content:
                await client.send_message(
                    chat_id=chat_id,
                    text=content,
                    parse_mode="HTML",
                    protect_content=protect_content,
                    reply_markup=reply_markup
                )
            else:
                # If no content for text message, send default message
                default_content = process_content(default_messages.get(msg_type, ""))
                if default_content:
                    await client.send_message(
                        chat_id=chat_id,
                        text=default_content,
                        parse_mode="HTML",
                        protect_content=protect_content,
                        reply_markup=reply_markup
                    )

        return True

    except Exception as e:
        print(f"Error sending custom message {msg_type}: {e}")
        return False

@Bot.on_message(filters.command("addbutton") & filters.user(ADMINS))
async def add_button(client: Bot, message: Message):
    """Tambahkan custom button"""
    if len(message.command) < 3:
        await message.reply_text(
            "❌ <b>Penggunaan:</b> /addbutton BUTTON_TEXT BUTTON_URL",
            quote=True
        )
        return
    
    try:
        button_text = message.command[1]
        button_url = " ".join(message.command[2:])
        
        settings = load_button_settings()
        button_id = f"btn_{len(settings['custom_buttons']) + 1}"
        
        settings["custom_buttons"][button_id] = {
            "text": button_text,
            "url": button_url
        }
        
        save_button_settings(settings)
        
        await message.reply_text(
            f"✅ <b>Button berhasil ditambahkan!</b>\n\n"
            f"<b>Button ID:</b> <code>{button_id}</code>\n"
            f"<b>Text:</b> {button_text}\n"
            f"<b>URL:</b> {button_url}",
            quote=True
        )
        
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("delbutton") & filters.user(ADMINS))
async def del_button(client: Bot, message: Message):
    """Hapus custom button"""
    if len(message.command) != 2:
        await message.reply_text("❌ <b>Penggunaan:</b> /delbutton BUTTON_ID", quote=True)
        return
    
    try:
        button_id = message.command[1]
        settings = load_button_settings()
        
        if button_id not in settings["custom_buttons"]:
            await message.reply_text("❌ <b>Button tidak ditemukan!</b>", quote=True)
            return
        
        button_info = settings["custom_buttons"][button_id]
        del settings["custom_buttons"][button_id]
        save_button_settings(settings)
        
        await message.reply_text(
            f"✅ <b>Button berhasil dihapus!</b>\n\n"
            f"<b>Button ID:</b> <code>{button_id}</code>\n"
            f"<b>Text:</b> {button_info['text']}",
            quote=True
        )
        
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("getbutton") & filters.user(ADMINS))
async def get_button(client: Bot, message: Message):
    """Lihat daftar custom buttons"""
    try:
        settings = load_button_settings()
        custom_buttons = settings["custom_buttons"]
        
        if not custom_buttons:
            await message.reply_text("❌ <b>Belum ada custom button!</b>", quote=True)
            return
        
        button_list = []
        for btn_id, btn_data in custom_buttons.items():
            button_list.append(f"├ <b>{btn_id}:</b> {btn_data['text']} → {btn_data['url']}")
        
        button_text = "\n".join(button_list)
        
        await message.reply_text(
            f"🔘 <b>CUSTOM BUTTONS</b>\n\n{button_text}\n\n"
            f"<b>Total Custom Buttons:</b> {len(custom_buttons)}",
            quote=True
        )
        
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("limitbutton") & filters.user(ADMINS))
async def limit_button(client: Bot, message: Message):
    """Enable/disable custom button feature"""
    if len(message.command) != 2:
        await message.reply_text("❌ <b>Penggunaan:</b> /limitbutton on/off", quote=True)
        return
    
    try:
        action = message.command[1].lower()
        settings = load_button_settings()
        
        if action == "on":
            settings["default_buttons"] = False
            status = "🔒 <b>Custom Buttons Only</b>"
        elif action == "off":
            settings["default_buttons"] = True
            status = "🔓 <b>Default Buttons Enabled</b>"
        else:
            await message.reply_text("❌ <b>Status harus 'on' atau 'off'!</b>", quote=True)
            return
        
        save_button_settings(settings)
        
        await message.reply_text(
            f"✅ <b>Button setting berhasil diupdate!</b>\n\n"
            f"<b>Status:</b> {status}",
            quote=True
        )
        
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("setmsg") & filters.user(ADMINS))
async def set_custom_message(client: Bot, message: Message):
    """Set custom message untuk berbagai situasi dengan support media"""
    if len(message.command) < 2:
        await message.reply_text(
            "❌ <b>Penggunaan:</b> /setmsg TYPE MESSAGE_TEXT\n\n"
            "<b>Atau reply ke pesan/media:</b> /setmsg TYPE (reply ke pesan/media yang ingin diset)\n\n"
            "<b>Types:</b> welcome, error, limit, protected, custom\n\n"
            "<b>Media Support:</b> Photo, Video, Document, Audio\n"
            "<b>Max File Size:</b> 50MB\n\n"
            "<b>Button Support:</b> [Button Text](Button URL)\n"
            "<b>Multiple Buttons in One Row:</b> [Button1](URL1) && [Button2](URL2)\n"
            "<b>Example:</b> /setmsg welcome Hello [Click Here](https://example.com) && [Another Button](https://example.org)",
            quote=True
        )
        return

    try:
        msg_type = message.command[1].lower()

        # Initialize message data
        msg_data = {
            "type": "text",
            "content": "",
            "media_id": None,
            "media_type": None,
            "buttons": []
        }

        if message.reply_to_message:
            # Handle replied message (text or media)
            replied = message.reply_to_message

            # Check for media content
            if replied.photo:
                msg_data["type"] = "photo"
                msg_data["media_id"] = replied.photo.file_id
                msg_data["media_type"] = "photo"
                msg_data["content"] = replied.caption or ""
            elif replied.video:
                msg_data["type"] = "video"
                msg_data["media_id"] = replied.video.file_id
                msg_data["media_type"] = "video"
                msg_data["content"] = replied.caption or ""
            elif replied.document:
                msg_data["type"] = "document"
                msg_data["media_id"] = replied.document.file_id
                msg_data["media_type"] = "document"
                msg_data["content"] = replied.caption or ""
            elif replied.audio:
                msg_data["type"] = "audio"
                msg_data["media_id"] = replied.audio.file_id
                msg_data["media_type"] = "audio"
                msg_data["content"] = replied.caption or ""
            elif replied.text:
                msg_data["type"] = "text"
                msg_data["content"] = replied.text
            else:
                await message.reply_text("❌ <b>Tipe media tidak didukung!</b>\n\n<b>Supported:</b> Text, Photo, Video, Document, Audio", quote=True)
                return

            # Parse buttons from caption if they exist
            # Format: [Button Text](Button URL) && [Button Text](Button URL)
            import re
            button_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
            try:
                buttons = re.findall(button_pattern, msg_data["content"])
                
                if buttons:
                    # Check for && separator to group buttons in the same row
                    button_rows = []
                    current_row = []
                    
                    for button_text, button_url in buttons:
                        # Validate button text and URL
                        if button_text and button_url:
                            current_row.append({
                                "text": button_text,
                                "url": button_url
                            })
                        else:
                            print(f"Invalid button: text='{button_text}', url='{button_url}'")
                        
                        # Check if we need to start a new row (based on && separator)
                        # This is a simplified approach; for exact && handling, we'd need to parse the original text
                        if len(current_row) == 2:
                            button_rows.append(current_row)
                            current_row = []
                    
                    # Add any remaining buttons in the current row
                    if current_row:
                        button_rows.append(current_row)
                    
                    # Flatten button_rows for storage (we'll reconstruct rows when sending)
                    for row in button_rows:
                        msg_data["buttons"].extend(row)
                    
                    # Remove button markup from content
                    msg_data["content"] = re.sub(button_pattern, '', msg_data["content"]).strip()
                    # Also remove && separators
                    msg_data["content"] = msg_data["content"].replace("&&", "").strip()
            except Exception as e:
                print(f"Error parsing buttons from caption: {e}")

            # Validate file size for media
            if msg_data["media_id"]:
                try:
                    if replied.photo and replied.photo.file_size > 50 * 1024 * 1024:
                        await message.reply_text("❌ <b>File size terlalu besar!</b>\n<b>Max:</b> 50MB", quote=True)
                        return
                    elif replied.video and replied.video.file_size > 50 * 1024 * 1024:
                        await message.reply_text("❌ <b>File size terlalu besar!</b>\n<b>Max:</b> 50MB", quote=True)
                        return
                    elif replied.document and replied.document.file_size > 50 * 1024 * 1024:
                        await message.reply_text("❌ <b>File size terlalu besar!</b>\n<b>Max:</b> 50MB", quote=True)
                        return
                    elif replied.audio and replied.audio.file_size > 50 * 1024 * 1024:
                        await message.reply_text("❌ <b>File size terlalu besar!</b>\n<b>Max:</b> 50MB", quote=True)
                        return
                except AttributeError:
                    pass  # Some media types might not have file_size
        else:
            # Handle text command
            if len(message.command) < 3:
                await message.reply_text("❌ <b>Harus ada MESSAGE_TEXT atau reply ke pesan/media!</b>", quote=True)
                return
            msg_data["type"] = "text"
            msg_data["content"] = " ".join(message.command[2:])
            
            # Parse buttons from content if they exist
            # Format: [Button Text](Button URL) && [Button Text](Button URL)
            import re
            button_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
            try:
                buttons = re.findall(button_pattern, msg_data["content"])
                
                if buttons:
                    # Check for && separator to group buttons in the same row
                    button_rows = []
                    current_row = []
                    
                    for button_text, button_url in buttons:
                        # Validate button text and URL
                        if button_text and button_url:
                            current_row.append({
                                "text": button_text,
                                "url": button_url
                            })
                        else:
                            print(f"Invalid button: text='{button_text}', url='{button_url}'")
                        
                        # Check if we need to start a new row (based on && separator)
                        # This is a simplified approach; for exact && handling, we'd need to parse the original text
                        if len(current_row) == 2:
                            button_rows.append(current_row)
                            current_row = []
                    
                    # Add any remaining buttons in the current row
                    if current_row:
                        button_rows.append(current_row)
                    
                    # Flatten button_rows for storage (we'll reconstruct rows when sending)
                    for row in button_rows:
                        msg_data["buttons"].extend(row)
                    
                    # Remove button markup from content
                    msg_data["content"] = re.sub(button_pattern, '', msg_data["content"]).strip()
                    # Also remove && separators
                    msg_data["content"] = msg_data["content"].replace("&&", "").strip()
            except Exception as e:
                print(f"Error parsing buttons from content: {e}")

        # Save to settings
        settings = load_button_settings()
        settings["custom_messages"][msg_type] = msg_data
        save_button_settings(settings)

        type_names = {
            "welcome": "Welcome Message",
            "error": "Error Message",
            "limit": "Limit Message",
            "protected": "Protected Content Message",
            "custom": "Custom Message"
        }

        display_name = type_names.get(msg_type, msg_type.title())

        # Create confirmation message
        confirm_msg = f"✅ <b>{display_name} berhasil diset!</b>\n\n"
        confirm_msg += f"<b>Type:</b> {msg_type}\n"
        confirm_msg += f"<b>Content Type:</b> {msg_data['type']}\n"

        if msg_data["content"]:
            confirm_msg += f"<b>Content:</b> {msg_data['content'][:100]}{'...' if len(msg_data['content']) > 100 else ''}\n"

        if msg_data["media_id"]:
            confirm_msg += f"<b>Media:</b> {msg_data['media_type']} attached\n"

        if msg_data["buttons"]:
            confirm_msg += f"<b>Buttons:</b> {len(msg_data['buttons'])} button(s) attached\n"
            # Display buttons in rows of 2 (as they would appear in the message)
            for i in range(0, len(msg_data["buttons"]), 2):
                row_buttons = msg_data["buttons"][i:i+2]
                button_line = "  - "
                for j, button in enumerate(row_buttons):
                    if j > 0:
                        button_line += " && "
                    button_line += f"{button['text']} → {button['url']}"
                confirm_msg += button_line + "\n"

        await message.reply_text(confirm_msg, quote=True)

    except Exception as e:
        LOGGER(__name__).error(f"Set message error: {e}")
        await message.reply_text(f"❌ <b>Error:</b> `{str(e)}`", quote=True)