# (©)Lunatic0de
# Recode by @yawrenmaru
# Developed By Soxmed

from bot import Bot
from config import ADMINS, LOGGER, admin_filter
from database.sql import add_admin_db, remove_admin_db
from pyrogram import filters
from pyrogram.types import Message


@Bot.on_message(filters.command("addadmin") & admin_filter)
async def add_admin(client: Bot, message: Message):
    """Tambahkan admin baru"""
    if len(message.command) != 2:
        await message.reply_text("❌ <b>Penggunaan:</b> /addadmin USER_ID", quote=True)
        return

    try:
        user_id = int(message.command[1])

        if user_id in ADMINS:
            await message.reply_text("❌ <b>User sudah menjadi admin!</b>", quote=True)
            return

        # Mutate the shared ADMINS list in place (not reassign) so
        # admin_filter - which reads this same list live - sees the change
        # immediately, without needing a bot restart.
        ADMINS.append(user_id)
        add_admin_db(user_id)

        # Get user info
        try:
            user = await client.get_users(user_id)
            user_info = f"@{user.username}" if user.username else user.first_name
        except:
            user_info = f"ID: {user_id}"

        await message.reply_text(
            f"✅ <b>Admin berhasil ditambahkan!</b>\n\n"
            f"<b>User:</b> {user_info}\n"
            f"<b>ID:</b> <code>{user_id}</code>",
            quote=True
        )

    except ValueError:
        await message.reply_text("❌ <b>User ID harus berupa angka!</b>", quote=True)
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("deladmin") & admin_filter)
async def del_admin(client: Bot, message: Message):
    """Hapus admin"""
    if len(message.command) != 2:
        await message.reply_text("❌ <b>Penggunaan:</b> /deladmin USER_ID", quote=True)
        return

    try:
        user_id = int(message.command[1])

        if user_id not in ADMINS:
            await message.reply_text("❌ <b>User bukan admin!</b>", quote=True)
            return

        ADMINS.remove(user_id)
        remove_admin_db(user_id)

        # Get user info
        try:
            user = await client.get_users(user_id)
            user_info = f"@{user.username}" if user.username else user.first_name
        except:
            user_info = f"ID: {user_id}"

        await message.reply_text(
            f"✅ <b>Admin berhasil dihapus!</b>\n\n"
            f"<b>User:</b> {user_info}\n"
            f"<b>ID:</b> <code>{user_id}</code>",
            quote=True
        )

    except ValueError:
        await message.reply_text("❌ <b>User ID harus berupa angka!</b>", quote=True)
    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)

@Bot.on_message(filters.command("getadmin") & admin_filter)
async def get_admin(client: Bot, message: Message):
    """Lihat daftar admin"""
    try:
        if not ADMINS:
            await message.reply_text("❌ <b>Belum ada admin yang ditambahkan!</b>", quote=True)
            return

        admin_list = []
        for admin_id in ADMINS:
            try:
                user = await client.get_users(admin_id)
                admin_info = f"@{user.username}" if user.username else user.first_name
                admin_list.append(f"├ <b>{admin_info}</b> - <code>{admin_id}</code>")
            except:
                admin_list.append(f"├ <b>Unknown</b> - <code>{admin_id}</code>")

        admin_text = "\n".join(admin_list)

        await message.reply_text(
            f"👥 <b>DAFTAR ADMIN</b>\n\n{admin_text}\n\n"
            f"<b>Total Admin:</b> {len(ADMINS)}",
            quote=True
        )

    except Exception as e:
        LOGGER(__name__).error(e)
        await message.reply_text(f"❌ <b>Error:</b> `{e}`", quote=True)
