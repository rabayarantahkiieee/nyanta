# Credits: @mrismanaziz
# FROM File-Sharing-Man <https://github.com/mrismanaziz/File-Sharing-Man/>
# t.me/SharingUserbot & t.me/Lunatic0de

from config import FORCE_SUB_CHANNELS, FORCE_SUB_GROUPS
from pyrogram.types import InlineKeyboardButton


def start_button(client):
    has_channels = bool(FORCE_SUB_CHANNELS)
    has_groups = bool(FORCE_SUB_GROUPS)

    if not has_channels and not has_groups:
        buttons = [
            [
                InlineKeyboardButton(text="ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs", callback_data="help"),
                InlineKeyboardButton(text="ᴛᴜᴛᴜᴘ", callback_data="close"),
            ],
        ]
        return buttons

    # Build buttons for all channels and groups
    sub_buttons = []
    if has_channels:
        for i, link in enumerate(client.invitelinks, 1):
            sub_buttons.append(InlineKeyboardButton(text=f"ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ {i}", url=link))
    if has_groups:
        for i, link in enumerate(client.invitelinks2, 1):
            sub_buttons.append(InlineKeyboardButton(text=f"ᴊᴏɪɴ ɢʀᴏᴜᴘ {i}", url=link))

    buttons = [
        sub_buttons,
        [
            InlineKeyboardButton(text="ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs", callback_data="help"),
            InlineKeyboardButton(text="ᴛᴜᴛᴜᴘ", callback_data="close"),
        ],
    ]
    return buttons


def fsub_button(client, message):
    has_channels = bool(FORCE_SUB_CHANNELS)
    has_groups = bool(FORCE_SUB_GROUPS)

    # Build join buttons for all channels and groups
    join_buttons = []
    if has_channels:
        for i, link in enumerate(client.invitelinks, 1):
            join_buttons.append(InlineKeyboardButton(text=f"ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ {i}", url=link))
    if has_groups:
        for i, link in enumerate(client.invitelinks2, 1):
            join_buttons.append(InlineKeyboardButton(text=f"ᴊᴏɪɴ ɢʀᴏᴜᴘ {i}", url=link))

    buttons = [join_buttons]

    # Add check subscription button
    buttons.append(
        [
            InlineKeyboardButton(
                text="✅ sᴜᴅᴀʜ sᴜʙsᴄʀɪʙᴇ? ᴋʟɪᴋ ᴅɪ sɪɴɪ",
                callback_data="check_sub",
            )
        ]
    )

    # Add try again button
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="ɴᴏɴᴛᴏɴ ᴅɪꜱɪɴɪ",
                    url=f"https://t.me/{client.username}?start={message.command[1]}",
                )
            ]
        )
    except IndexError:
        pass

    return buttons
