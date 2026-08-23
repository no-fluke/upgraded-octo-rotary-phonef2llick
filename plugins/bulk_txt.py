"""
plugins/bulk_txt.py

Bulk file-to-link processing for RexBots.

Commands (private chat):
  /bulk   – Start a bulk session
  /done   – Stop collecting, generate links.txt
  /cancel – Clear your current session
  /count  – See how many files are queued so far

Files sent while a bulk session is active are collected silently (no
individual link reply). Files sent outside a bulk session are handled
normally by private_stream.py.

Group order: this plugin registers media handlers at group=3, which
runs BEFORE private_stream.py (group=4), allowing it to intercept.
"""

import io
import asyncio
import logging
import time

from pyrogram import Client, filters, StopPropagation
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from info import BIN_CHANNEL, URL, FSUB, MAX_FILES
from database.users_db import db
from web.utils.file_properties import get_hash, get_media_from_message
from utils import get_size
from plugins.rexbots import is_user_joined, is_user_allowed

logger = logging.getLogger(__name__)

# ── In-memory session store ────────────────────────────────────────────────
# bulk_sessions[user_id] = list of {"msg": Message, "filename": str}
bulk_sessions: dict = {}
bulk_mode: set     = set()
bulk_locks: dict   = {}


def _get_lock(uid: int) -> asyncio.Lock:
    if uid not in bulk_locks:
        bulk_locks[uid] = asyncio.Lock()
    return bulk_locks[uid]


def _get_filename(msg: Message) -> str:
    """Extract the best filename from any media type."""
    for attr in ("document", "video", "audio"):
        media = getattr(msg, attr, None)
        if media:
            return getattr(media, "file_name", None) or f"{attr}_{msg.id}"
    if msg.photo:
        return f"photo_{msg.id}.jpg"
    if msg.voice:
        return f"voice_{msg.id}.ogg"
    if msg.video_note:
        return f"videonote_{msg.id}.mp4"
    return f"file_{msg.id}"


# ── /bulk ──────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("bulk") & filters.private)
async def cmd_bulk(client: Client, msg: Message):
    uid = msg.from_user.id

    if FSUB and not await is_user_joined(client, msg):
        return

    if uid in bulk_mode:
        count = len(bulk_sessions.get(uid, []))
        return await msg.reply_text(
            f"⚡ You already have an active bulk session with **{count}** file(s).\n"
            "Keep sending files or type /done to finish, /cancel to clear."
        )

    bulk_mode.add(uid)
    bulk_sessions[uid] = []

    await msg.reply_text(
        "📦 **Bulk session started!**\n\n"
        "Send me as many files as you want (documents, videos, audio, photos…).\n"
        "They'll be collected silently.\n\n"
        "When you're done, type /done — I'll send you a `.txt` file with all "
        "numbered streaming + download links.\n\n"
        "• /count — see how many files collected\n"
        "• /cancel — clear session and start over"
    )


# ── /cancel ────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("cancel") & filters.private)
async def cmd_cancel(client: Client, msg: Message):
    uid = msg.from_user.id
    bulk_mode.discard(uid)
    bulk_sessions.pop(uid, None)
    await msg.reply_text("🗑 Bulk session cleared. Send /bulk to start a new one.")


# ── /count ─────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("count") & filters.private)
async def cmd_count(client: Client, msg: Message):
    uid = msg.from_user.id
    if uid not in bulk_mode:
        return await msg.reply_text("⚠️ No active bulk session. Send /bulk to start one.")
    count = len(bulk_sessions.get(uid, []))
    await msg.reply_text(f"📦 **{count}** file(s) collected so far.")


# ── File collector (intercepts during active bulk sessions) ────────────────

@Client.on_message(
    filters.private
    & (
        filters.document
        | filters.video
        | filters.audio
        | filters.photo
        | filters.voice
        | filters.video_note
    ),
    group=3,   # runs BEFORE private_stream.py (group 4)
)
async def bulk_file_collector(client: Client, msg: Message):
    uid = msg.from_user.id

    # Only intercept if user is in bulk mode
    if uid not in bulk_mode:
        return  # let private_stream.py handle normally

    filename = _get_filename(msg)
    bulk_sessions[uid].append({"msg": msg, "filename": filename})
    count = len(bulk_sessions[uid])

    if count == 1:
        await msg.reply_text(
            "✅ Got file #1! Keep sending more.\n"
            "Type /done when finished or /count to check progress."
        )
    elif count % 50 == 0:
        await msg.reply_text(f"📦 **{count}** files collected so far. Keep going or /done.")

    # Raise StopPropagation AFTER replying so private_stream.py doesn't also handle it
    raise StopPropagation


# ── /done ──────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("done") & filters.private)
async def cmd_done(client: Client, msg: Message):
    uid = msg.from_user.id

    if uid not in bulk_mode:
        return await msg.reply_text(
            "⚠️ No active bulk session.\nSend /bulk first, then send your files."
        )

    items = bulk_sessions.get(uid, [])
    if not items:
        return await msg.reply_text("⚠️ Your bulk session is empty! Send some files first.")

    async with _get_lock(uid):
        total  = len(items)
        status = await msg.reply_text(
            f"⏳ Processing **{total}** file(s)…\n"
            "Forwarding to storage and generating links. Sit tight!"
        )

        # ── Step 1: Forward to BIN_CHANNEL ────────────────────────────────
        BATCH_SIZE  = 20
        BATCH_DELAY = 1.1   # stay within Telegram rate limits

        results = []   # list of {filename, stream_url, download_url}

        async def forward_one(item):
            try:
                fwd        = await item["msg"].forward(chat_id=BIN_CHANNEL)
                hash_str   = get_hash(fwd)
                fname      = item["filename"]
                stream_url   = f"{URL}watch/{fwd.id}/stream.mkv?hash={hash_str}"
                download_url = f"{URL}{fwd.id}?hash={hash_str}"

                # Mirror what private_stream.py saves to DB
                media     = get_media_from_message(fwd)
                file_size = get_size(getattr(media, "file_size", 0)) if media else "Unknown"
                await db.files.insert_one({
                    "user_id":   uid,
                    "file_name": fname,
                    "file_size": file_size,
                    "file_id":   fwd.id,
                    "hash":      hash_str,
                    "timestamp": time.time(),
                })
                return {"filename": fname, "stream_url": stream_url, "download_url": download_url}

            except FloodWait as e:
                logger.warning("FloodWait %ss — sleeping", e.value)
                await asyncio.sleep(e.value + 1)
                return None
            except Exception as e:
                logger.error("Forward failed for %s: %s", item["filename"], e)
                return None

        for batch_start in range(0, total, BATCH_SIZE):
            batch        = items[batch_start: batch_start + BATCH_SIZE]
            batch_results = await asyncio.gather(*[forward_one(i) for i in batch])
            results.extend([r for r in batch_results if r])

            done_so_far = min(batch_start + BATCH_SIZE, total)
            if done_so_far % 200 == 0 or done_so_far == total:
                try:
                    await status.edit_text(f"⏳ Forwarded **{done_so_far}/{total}** files…")
                except Exception:
                    pass

            if batch_start + BATCH_SIZE < total:
                await asyncio.sleep(BATCH_DELAY)

        if not results:
            await status.edit_text("❌ All forwards failed. Please try again.")
            bulk_mode.discard(uid)
            bulk_sessions.pop(uid, None)
            return

        # ── Step 2: Build .txt content ─────────────────────────────────────
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"  FILE LINKS  |  Total: {len(results)}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
        ]
        for idx, r in enumerate(results, start=1):
            lines.append(f"{idx}. {r['filename']}")
            lines.append(f"   🎬 Stream  : {r['stream_url']}")
            lines.append(f"   ⬇️ Download: {r['download_url']}")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("Generated by RexBots File-to-Link Bot")

        txt_io      = io.BytesIO("\n".join(lines).encode("utf-8"))
        txt_io.name = "links.txt"

        # ── Step 3: Send .txt to user ──────────────────────────────────────
        saved  = len(results)
        failed = total - saved
        caption = (
            f"✅ **Done! {saved} link(s) generated.**\n"
            + (f"⚠️ {failed} file(s) failed to process.\n" if failed else "")
            + "\n📄 Open `links.txt` — each file has a stream and download link."
        )

        await msg.reply_document(document=txt_io, caption=caption, file_name="links.txt")
        await status.delete()

        # Clear session
        bulk_mode.discard(uid)
        bulk_sessions.pop(uid, None)
