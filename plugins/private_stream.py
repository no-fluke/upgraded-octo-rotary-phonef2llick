import asyncio
import time
import urllib.parse

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from info import URL, BOT_USERNAME, BIN_CHANNEL, CHANNEL, PROTECT_CONTENT, FSUB, MAX_FILES
from database.users_db import db
from web.utils.file_properties import get_hash
from utils import get_size
from plugins.rexbots import rx_verification, is_user_allowed, is_user_joined
from Script import script


# group=4 so bulk_txt.py (group=3) can intercept first when user is in bulk mode
@Client.on_message(
    filters.private & (filters.document | filters.video | filters.audio),
    group=4
)
async def private_receive_handler(c: Client, m: Message):
    user_id = m.from_user.id

    # ✅ Force subscription check
    if FSUB and not await is_user_joined(c, m):
        return

    # 🔒 Ban check
    is_banned = await db.is_user_blocked(user_id)
    if is_banned:
        await m.reply(
            "🚫 **Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜꜱɪɴɢ ᴛʜɪꜱ ʙᴏᴛ.**\n\n"
            "🔄 **Cᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ɪғ ʏᴏᴜ ᴛʜɪɴᴋ ᴛʜɪꜱ ɪꜱ ᴀ ᴍɪꜱᴛᴀᴋᴇ.**\n\n@RexBots_Official"
        )
        return

    is_allowed, remaining_time = await is_user_allowed(user_id)
    if not is_allowed:
        await m.reply_text(
            f"🚫 **Yᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ꜱᴇɴᴛ {MAX_FILES} ғɪʟᴇꜱ!**\n"
            f"Pʟᴇᴀꜱᴇ **{remaining_time} Sᴇᴄᴏɴᴅꜱ** ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.",
            quote=True
        )
        return

    file_obj = m.document or m.video or m.audio
    file_name = getattr(file_obj, 'file_name', None) or f"RexBots_{int(time.time())}.mkv"
    file_size = get_size(file_obj.file_size)

    verified = await rx_verification(c, m)
    if not verified:
        return

    try:
        forwarded = await m.forward(chat_id=BIN_CHANNEL)
        hash_str = get_hash(forwarded)
        stream    = f"{URL}watch/{forwarded.id}/RexBots_{int(time.time())}.mkv?hash={hash_str}"
        download  = f"{URL}{forwarded.id}?hash={hash_str}"
        file_link = f"https://t.me/{BOT_USERNAME}?start=file_{forwarded.id}"
        share_link = f"https://t.me/share/url?url={urllib.parse.quote(file_link)}"

        # Save to MongoDB
        await db.files.insert_one({
            "user_id":   user_id,
            "file_name": file_name,
            "file_size": file_size,
            "file_id":   forwarded.id,
            "hash":      hash_str,
            "timestamp": time.time(),
        })

        await forwarded.reply_text(
            f"Requested By: [{m.from_user.first_name}](tg://user?id={user_id})\n"
            f"User ID: {user_id}\nStream Link: {stream}",
            disable_web_page_preview=True,
            quote=True,
        )

        await m.reply_text(
            script.CAPTION_TXT.format(CHANNEL, file_name, file_size, stream, download),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(" ꜱᴛʀᴇᴀᴍ ", url=stream),
                 InlineKeyboardButton(" ᴅᴏᴡɴʟᴏᴀᴅ ", url=download)],
                [InlineKeyboardButton(" ᴄʟᴏꜱᴇ ", callback_data="close_data")],
            ]),
        )

    except FloodWait as e:
        await asyncio.sleep(e.value)
        await c.send_message(
            BIN_CHANNEL,
            f"⚠️ FloodWait: {e.value}s from {m.from_user.first_name}"
        )
    except Exception as e:
        await m.reply_text(f"❌ Error generating link: `{e}`")
