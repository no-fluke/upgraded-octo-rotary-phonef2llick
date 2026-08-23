# 🐛 Bugs Fixed

## 1. `info.py` — Broken boolean parsing for env vars
**Before:** `FSUB = environ.get("FSUB", True)` → always a string, never `False`  
**Fixed:** Proper `.lower() not in ('false', '0', 'no')` parsing for all boolean flags

## 2. `info.py` — Crash on missing/malformed int env vars  
**Before:** `int(environ.get('LOG_CHANNEL', '-'))` → `ValueError` crash on startup  
**Fixed:** Added `_safe_int()` helper with a fallback value

## 3. `info.py` — URL missing trailing slash inconsistency  
**Fixed:** URL always ends with `/` to prevent double-slash in generated links

## 4. `bot.py` — `StreamBot.loop.create_task(...)` deprecated  
**Before:** `StreamBot.loop.create_task(check_expired_premium(StreamBot))`  
**Fixed:** `loop.create_task(check_expired_premium(StreamBot))`

## 5. `bot.py` — Unnecessary `asyncio.get_event_loop()` try/except  
**Fixed:** Removed fragile event-loop bootstrapping; `StreamBot.start()` already sets up the loop

## 6. `plugins/private_stream.py` — Missing `asyncio` import  
**Before:** `await asyncio.sleep(e.value)` would crash with `NameError`  
**Fixed:** Added `import asyncio` at top of file

## 7. `plugins/private_stream.py` — `file_id.file_name` crash on None  
**Before:** `file_name = file_id.file_name` crashes if attribute is `None`  
**Fixed:** `file_name = getattr(file_obj, 'file_name', None) or f"RexBots_{int(time.time())}.mkv"`

## 8. `plugins/commend.py` — `FloodWait.x` is deprecated  
**Before:** `await asyncio.sleep(e.x)` — `.x` was removed in newer pyrofork  
**Fixed:** `await asyncio.sleep(e.value)` (correct attribute)

## 9. `plugins/bulk_txt.py` — `dict[int, list]` type hints crash on Python <3.9  
**Fixed:** Changed to `dict` and `set` (plain generics) for Python 3.8/3.10 compatibility

## 10. `web/__init__.py` — `check_expired_premium` runs every 1 second with no sleep on errors  
**Fixed:** Already has `await sleep(1)` — kept as-is but confirmed

## 11. `Script.py` — Help text missing bulk commands  
**Fixed:** Added `/bulk`, `/done`, `/cancel`, `/count` to `HELP2_TXT` and `ADMIN_CMD_TXT`

## 12. `plugins/bulk_txt.py` — Session not cleared on all-failed forwards  
**Before:** Session stayed open forever if all forwards failed  
**Fixed:** `bulk_mode.discard(uid)` and `bulk_sessions.pop(uid, None)` called on failure too

