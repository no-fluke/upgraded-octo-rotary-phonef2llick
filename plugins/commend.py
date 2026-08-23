import os, random, asyncio, time, re, pytz
from Script import script
from database.users_db import db
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton
)
from info import (
    BOT_USERNAME, URL, BATCH_PROTECT_CONTENT, ADMINS, PROTECT_CONTENT,
    OWNER_USERNAME, SUPPORT, PICS, FILE_PIC, CHANNEL, VERIFIED_LOG,
    LOG_CHANNEL, FSUB, BIN_CHANNEL, VERIFY_EXPIRE, BATCH_FILE_CAPTION,
    FILE_CAPTION, VERIFY_IMG, QR_CODE
)
from datetime import datetime
from web.utils.file_properties import get_hash
from utils import get_readable_time, verify_user, check_token, get_size
from web.utils import StartTime, __version__
from plugins.rexbots import is_user_joined, rx_verification, rx_x_verification
import json
import logging

logger = logging.getLogger(__name__)
BATCH_FILES = {}


# ── /start ─────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    user_id = message.from_user.id
    mention = message.from_user.mention
    me2     = (await client.get_me()).mention

    if FSUB and not await is_user_joined(client, message):
        return

    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT.format(me2, user_id, mention))

    if len(message.command) == 1 or message.command[1] == "start":
        buttons = [
            [
                InlineKeyboardButton('• ᴜᴘᴅᴀᴛᴇᴅ •', url=CHANNEL),
                InlineKeyboardButton('• sᴜᴘᴘᴏʀᴛ •', url=SUPPORT),
            ],
            [
                InlineKeyboardButton('• ʜᴇʟᴘ •', callback_data='help'),
                InlineKeyboardButton('• ᴀʙᴏᴜᴛ •', callback_data='about'),
            ],
        ]
        await message.reply_photo(
            photo=PICS,
            caption=script.START_TXT.format(message.from_user.mention, BOT_USERNAME),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    msg = message.command[1]

    # ── /start file_<id> ───────────────────────────────────────────────────
    if msg.startswith("file_"):
        _, file_id = msg.split("_", 1)
        original_message = await client.get_messages(int(BIN_CHANNEL), int(file_id))
        media   = original_message.document or original_message.video or original_message.audio
        caption = None
        if media:
            file_name = getattr(media, 'file_name', None) or "Unnamed File"
            caption   = FILE_CAPTION.format(CHANNEL, file_name)
        return await client.copy_message(
            chat_id=message.from_user.id,
            from_chat_id=int(BIN_CHANNEL),
            message_id=int(file_id),
            caption=caption,
            protect_content=PROTECT_CONTENT,
        )

    # ── /start BATCH-<file_id> ─────────────────────────────────────────────
    if msg.startswith("BATCH-"):
        file_id = msg.split("-", 1)[1]
        uid     = message.from_user.id

        verified = await rx_x_verification(client, message)
        if not verified:
            return

        sts  = await message.reply("<b>Please wait...</b>")
        msgs = BATCH_FILES.get(file_id)

        if not msgs:
            try:
                downloaded_file = await client.download_media(file_id)
                with open(downloaded_file, "r", encoding="utf-8") as f:
                    msgs = json.load(f)
                os.remove(downloaded_file)
                BATCH_FILES[file_id] = msgs
            except Exception as e:
                await sts.edit("❌ FAILED to load file.")
                logger.exception("Unable to open batch JSON file.")
                await client.send_message(LOG_CHANNEL, f"❌ UNABLE TO OPEN FILE: {e}")
                return

        for m in msgs:
            title     = m.get("title")
            size      = get_size(int(m.get("size", 0)))
            f_caption = m.get("caption", "")

            if BATCH_FILE_CAPTION:
                try:
                    f_caption = BATCH_FILE_CAPTION.format(
                        CHANNEL,
                        file_name=title or "",
                        file_size=size or "",
                        file_caption=f_caption or "",
                    )
                except Exception as e:
                    logger.warning(f"Caption formatting error: {e}")
                    f_caption = f_caption or title or ""

            if not f_caption:
                f_caption = title or "Untitled"

            try:
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=m.get("file_id"),
                    caption=f_caption,
                    protect_content=BATCH_PROTECT_CONTENT,
                )
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=m.get("file_id"),
                    caption=f_caption,
                    protect_content=BATCH_PROTECT_CONTENT,
                )
            except Exception as e:
                logger.error(f"❌ Failed to send media: {e}", exc_info=True)
                continue

            await asyncio.sleep(1)

        await sts.delete()
        return


# ── Callback query handler ─────────────────────────────────────────────────

@Client.on_callback_query()
async def cb_handler(client, query):
    data = query.data

    if data == "close_data":
        await query.message.delete()

    elif data == "about":
        buttons = [
            [InlineKeyboardButton('💻', url='https://t.me/RexBots_Official')],
            [
                InlineKeyboardButton('• ʜᴏᴍᴇ •', callback_data='start'),
                InlineKeyboardButton('• ᴄʟᴏsᴇ •', callback_data='close_data'),
            ],
        ]
        me2 = (await client.get_me()).mention
        await query.message.edit_caption(
            caption=script.ABOUT_TXT.format(
                me2, me2, get_readable_time(time.time() - StartTime), __version__
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML,
        )

    elif data == "start":
        buttons = [
            [
                InlineKeyboardButton(' ᴜᴘᴅᴀᴛᴇᴅ ', url=CHANNEL),
                InlineKeyboardButton(' sᴜᴘᴘᴏʀᴛ ', url=SUPPORT),
            ],
            [
                InlineKeyboardButton(' ʜᴇʟᴘ ', callback_data='help'),
                InlineKeyboardButton(' ᴀʙᴏᴜᴛ ', callback_data='about'),
            ],
        ]
        await query.message.edit_caption(
            caption=script.START_TXT.format(query.from_user.mention, BOT_USERNAME),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML,
        )

    elif data == "help":
        buttons = [
            [InlineKeyboardButton('• ᴀᴅᴍɪɴ •', callback_data='admincmd')],
            [
                InlineKeyboardButton('• ʜᴏᴍᴇ •', callback_data='start'),
                InlineKeyboardButton('• ᴄʟᴏsᴇ •', callback_data='close_data'),
            ],
        ]
        await query.message.edit_caption(
            caption=script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML,
        )

    elif data == "admincmd":
        if query.from_user.id not in ADMINS:
            return await query.answer('This Feature Is Only For Admins!', show_alert=True)
        buttons = [[InlineKeyboardButton('• ʜᴏᴍᴇ •', callback_data='start')]]
        await query.message.edit_caption(
            caption=script.ADMIN_CMD_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML,
        )

    # ── Pagination: files list ─────────────────────────────────────────────
    elif data.startswith("filespage_"):
        page     = int(data.split("_")[1])
        uid      = query.from_user.id
        files    = await db.files.find({"user_id": uid}).to_list(length=100)
        per_page = 7
        total_pages = (len(files) + per_page - 1) // per_page
        if not files or page < 1 or page > total_pages:
            return await query.answer("⚠️ Nᴏ ᴍᴏʀᴇ ғɪʟᴇꜱ.", show_alert=True)
        start = (page - 1) * per_page
        btns  = [[InlineKeyboardButton(f["file_name"][:40], callback_data=f"sendfile_{f['file_id']}")] for f in files[start:start + per_page]]
        nav   = []
        if page > 1:
            nav.append(InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data=f"filespage_{page - 1}"))
        if page < total_pages:
            nav.append(InlineKeyboardButton("➡️ Nᴇxᴛ", callback_data=f"filespage_{page + 1}"))
        nav.append(InlineKeyboardButton("❌ ᴄʟᴏsᴇ ❌", callback_data="close_data"))
        btns.append(nav)
        await query.message.edit_caption(
            caption=f"📁 Tᴏᴛᴀʟ ғɪʟᴇꜱ: {len(files)} | Pᴀɢᴇ {page}/{total_pages}",
            reply_markup=InlineKeyboardMarkup(btns),
        )
        return await query.answer()

    elif data.startswith("delfilespage_"):
        page     = int(data.split("_")[1])
        uid      = query.from_user.id
        files    = await db.files.find({"user_id": uid}).to_list(length=100)
        per_page = 7
        total_pages = (len(files) + per_page - 1) // per_page
        if not files or page < 1 or page > total_pages:
            return await query.answer("⚠️ Nᴏ ᴍᴏʀᴇ ғɪʟᴇꜱ.", show_alert=True)
        start = (page - 1) * per_page
        btns  = [[InlineKeyboardButton(f["file_name"][:40], callback_data=f"deletefile_{f['file_id']}")] for f in files[start:start + per_page]]
        nav   = []
        if page > 1:
            nav.append(InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data=f"delfilespage_{page - 1}"))
        if page < total_pages:
            nav.append(InlineKeyboardButton("➡️ Nᴇxᴛ", callback_data=f"delfilespage_{page + 1}"))
        nav.append(InlineKeyboardButton("❌ ᴄʟᴏsᴇ ❌", callback_data="close_data"))
        btns.append(nav)
        await query.message.edit_caption(
            caption=f"📁 Tᴏᴛᴀʟ ғɪʟᴇꜱ: {len(files)} | Pᴀɢᴇ {page}/{total_pages}",
            reply_markup=InlineKeyboardMarkup(btns),
        )
        return await query.answer()

    elif data.startswith("sendfile_"):
        file_id  = int(data.split("_")[1])
        uid      = query.from_user.id
        file_data = await db.files.find_one({"file_id": file_id, "user_id": uid})
        if not file_data:
            return await query.answer("⚠️ Nᴏ ᴍᴏʀᴇ ғɪʟᴇꜱ.", show_alert=True)
        try:
            original = await client.get_messages(BIN_CHANNEL, file_id)
            media    = original.document or original.video or original.audio
            caption  = None
            if media:
                fname   = getattr(media, 'file_name', None) or "Unnamed"
                caption = FILE_CAPTION.format(CHANNEL, fname)
            await client.copy_message(
                chat_id=uid,
                from_chat_id=BIN_CHANNEL,
                message_id=file_id,
                caption=caption,
                protect_content=PROTECT_CONTENT,
            )
            return await query.answer()
        except Exception:
            return await query.answer("⚠️ Failed to send file.", show_alert=True)

    elif data.startswith("deletefile_"):
        file_msg_id = int(data.split("_")[1])
        uid         = query.from_user.id
        file_data   = await db.files.find_one({"file_id": file_msg_id})
        if not file_data:
            return await query.answer("❌ Fɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ ᴏʀ ᴀʟʀᴇᴀᴅʏ ᴅᴇʟᴇᴛᴇᴅ.", show_alert=True)
        if file_data["user_id"] != uid:
            return await query.answer("⚠️ Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜɪꜱ ғɪʟᴇ!", show_alert=True)
        await db.files.delete_one({"file_id": file_msg_id})
        try:
            await client.delete_messages(BIN_CHANNEL, file_msg_id)
        except Exception:
            pass
        await query.answer("✅ Fɪʟᴇ ᴅᴇʟᴇᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ!", show_alert=True)
        await query.message.edit_caption("🗑️ Fɪʟᴇ ʜᴀs ʙᴇᴇɴ ᴅᴇʟᴇᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ.")


# ── /files ─────────────────────────────────────────────────────────────────

@Client.on_message(filters.private & filters.command("files"))
async def list_user_files(client, message: Message):
    uid   = message.from_user.id
    files = await db.files.find({"user_id": uid}).to_list(length=100)
    if not files:
        return await message.reply_text("❌ Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴜᴘʟᴏᴀᴅᴇᴅ ᴀɴʏ ғɪʟᴇꜱ.")
    page        = 1
    per_page    = 7
    total_pages = (len(files) + per_page - 1) // per_page
    start       = 0
    btns        = [[InlineKeyboardButton(f["file_name"][:40], callback_data=f"sendfile_{f['file_id']}")] for f in files[start:start + per_page]]
    nav         = []
    if page < total_pages:
        nav.append(InlineKeyboardButton("➡️ Nᴇxᴛ", callback_data=f"filespage_{page + 1}"))
    nav.append(InlineKeyboardButton("❌ ᴄʟᴏsᴇ ❌", callback_data="close_data"))
    btns.append(nav)
    await message.reply_photo(
        photo=FILE_PIC,
        caption=f"📁 Tᴏᴛᴀʟ ғɪʟᴇꜱ: {len(files)} | Pᴀɢᴇ {page}/{total_pages}",
        reply_markup=InlineKeyboardMarkup(btns),
    )


@Client.on_message(filters.private & filters.command("del_files"))
async def delete_files_list(client, message):
    uid   = message.from_user.id
    files = await db.files.find({"user_id": uid}).to_list(length=100)
    if not files:
        return await message.reply_text("❌ Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴜᴘʟᴏᴀᴅᴇᴅ ᴀɴʏ ғɪʟᴇꜱ.")
    page        = 1
    per_page    = 7
    total_pages = (len(files) + per_page - 1) // per_page
    start       = 0
    btns        = [[InlineKeyboardButton(f["file_name"][:40], callback_data=f"deletefile_{f['file_id']}")] for f in files[start:start + per_page]]
    nav         = []
    if page < total_pages:
        nav.append(InlineKeyboardButton("➡️ Nᴇxᴛ", callback_data=f"delfilespage_{page + 1}"))
    nav.append(InlineKeyboardButton("❌ ᴄʟᴏsᴇ ❌", callback_data="close_data"))
    btns.append(nav)
    await message.reply_photo(
        photo=FILE_PIC,
        caption=f"📁 Tᴏᴛᴀʟ ғɪʟᴇꜱ: {len(files)} | Pᴀɢᴇ {page}/{total_pages}",
        reply_markup=InlineKeyboardMarkup(btns),
    )


# ── /about ─────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("about"))
async def about(client, message):
    buttons = [
        [InlineKeyboardButton('💻', url='https://t.me/RexBots_Official')],
        [InlineKeyboardButton('• ᴄʟᴏsᴇ •', callback_data='close_data')],
    ]
    me2 = (await client.get_me()).mention
    await message.reply_text(
        text=script.ABOUT_TXT.format(
            me2, me2, get_readable_time(time.time() - StartTime), __version__
        ),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@Client.on_message(filters.command("help"))
async def help_cmd(client, message):
    btn = [[InlineKeyboardButton('• ᴄʟᴏsᴇ •', callback_data='close_data')]]
    await message.reply_text(
        text=script.HELP2_TXT,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(btn),
    )


@Client.on_message(filters.command("set_expiry") & filters.user(ADMINS))
async def set_expiry_command(client, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "Usage: `/set_expiry <minutes>`\n"
            "Example: `/set_expiry 10` for 10 minutes.\n"
            "Use `0` to disable expiry."
        )
    try:
        minutes = int(message.command[1])
        if minutes < 0:
            return await message.reply_text("❌ Time must be a positive integer.")
        seconds = minutes * 60
        await db.set_link_expiry(seconds)
        if seconds == 0:
            await message.reply_text("✅ **Link Expiry Disabled.** Links will never expire.")
        else:
            await message.reply_text(
                f"✅ **Link Expiry Set to {minutes} minutes.**\n"
                f"Links generated from now will expire after {minutes} minutes."
            )
    except ValueError:
        await message.reply_text("❌ Invalid number format.")
