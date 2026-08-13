# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

from pyrogram.types import ChatJoinRequest

from bot import Bot
from config import FORCE_SUB_CHANNELS, FORCE_SUB_GROUPS, LOGGER


@Bot.on_chat_join_request()
async def auto_approve_force_sub_join_request(client: Bot, request: ChatJoinRequest):
    """
    Auto-approve join requests to the configured force-subscribe
    channels/groups (FORCE_SUB_CHANNEL*/FORCE_SUB_GROUP*).

    Telegram's "Approve New Members" mode leaves a user who taps Join in a
    pending state until an admin manually approves them - they never
    actually become a chat member. Since the bot's force-subscribe check
    only looks at membership, that user would be stuck being told to
    "subscribe" forever even though they already requested to join. This
    lets admins turn approval mode on for their force-sub chats (e.g. for
    spam control) without breaking that automated flow - the bot itself
    needs to be an admin with the right to add/approve members in the
    chat for this to actually take effect.
    """
    if request.chat.id not in FORCE_SUB_CHANNELS and request.chat.id not in FORCE_SUB_GROUPS:
        return

    try:
        await client.approve_chat_join_request(request.chat.id, request.from_user.id)
        LOGGER(__name__).info(
            f"Auto-approved join request: user {request.from_user.id} -> chat {request.chat.id}"
        )
    except Exception as e:
        LOGGER(__name__).warning(
            f"Failed to auto-approve join request for user {request.from_user.id} "
            f"in chat {request.chat.id}: {e}"
        )
