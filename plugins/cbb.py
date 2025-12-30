# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

from bot import Bot
from config import OWNER, Data
from database.sql import update_user_subscription_status
from pyrogram import filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, Message


@Bot.on_message(filters.private & filters.incoming & filters.command("about"))
async def _about(client: Bot, msg: Message):
    await client.send_message(
        msg.chat.id,
        Data.ABOUT.format(client.username, OWNER),
        reply_markup=InlineKeyboardMarkup(Data.mbuttons),
    )


@Bot.on_message(filters.private & filters.incoming & filters.command("help"))
async def _help(client: Bot, msg: Message):
    await client.send_message(
        msg.chat.id,
        "<b>Cara Menggunakan Bot ini</b>\n" + Data.HELP,
        reply_markup=InlineKeyboardMarkup(Data.buttons),
    )


@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    if data == "about":
        try:
            await query.message.edit_text(
                text=Data.ABOUT.format(client.username, OWNER),
                reply_markup=InlineKeyboardMarkup(Data.mbuttons),
            )
        except MessageNotModified:
            pass
    elif data == "help":
        try:
            await query.message.edit_text(
                text="<b>Cara Menggunakan Bot ini</b>\n" + Data.HELP,
                reply_markup=InlineKeyboardMarkup(Data.buttons),
            )
        except MessageNotModified:
            pass
    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except BaseException:
            pass
    elif data == "check_sub":
        # Check actual subscription status before updating
        user = query.from_user
        user_name = f"@{user.username}" if user.username else None

        # Import subscription check functions
        from config import FORCE_SUB_CHANNELS, FORCE_SUB_GROUPS, ADMINS
        from pyrogram.enums import ChatMemberStatus
        from pyrogram.errors import UserNotParticipant

        # Check if user is actually subscribed
        is_subscribed = True

        # Check channels
        for channel_id in FORCE_SUB_CHANNELS:
            try:
                member = await query.message._client.get_chat_member(chat_id=channel_id, user_id=user.id)
                if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                    is_subscribed = False
                    break
            except UserNotParticipant:
                is_subscribed = False
                break

        # Check groups if channels are OK
        if is_subscribed:
            for group_id in FORCE_SUB_GROUPS:
                try:
                    member = await query.message._client.get_chat_member(chat_id=group_id, user_id=user.id)
                    if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                        is_subscribed = False
                        break
                except UserNotParticipant:
                    is_subscribed = False
                    break

        if is_subscribed or user.id in ADMINS:
            # Update subscription status in database
            update_user_subscription_status(user.id, user_name, is_subscribed=True)

            # Send success message
            await query.answer("✅ Status subscription berhasil diperbarui!", show_alert=True)

            # Delete the force sub message and send start message
            try:
                await query.message.delete()
                # Send start message
                from .button import start_button
                from config import START_MSG
                buttons = start_button(query.message._client)
                await query.message._client.send_message(
                    chat_id=user.id,
                    text=START_MSG.format(
                        first=user.first_name,
                        last=user.last_name,
                        username=f"@{user.username}" if user.username else None,
                        mention=user.mention,
                        id=user.id,
                    ),
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            except Exception as e:
                print(f"Error in check_sub callback: {e}")
        else:
            # User is not actually subscribed
            await query.answer("❌ Anda belum subscribe ke semua channel/group yang diperlukan!", show_alert=True)
