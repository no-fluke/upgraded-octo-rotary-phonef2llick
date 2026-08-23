from os import environ

# 🚀 Bot Configuration
SESSION  = environ.get('SESSION', 'RexBots')
API_ID   = int(environ.get('API_ID', '0'))
API_HASH = environ.get('API_HASH', '')
BOT_TOKEN = environ.get('BOT_TOKEN', '')

# 👑 Owner & Admins
ADMINS       = [int(i) for i in environ.get('ADMINS', '').split() if i]
AUTH_CHANNEL = [int(i) for i in environ.get('AUTH_CHANNEL', '').split() if i]
OWNER_USERNAME = environ.get('OWNER_USERNAME', 'RexBots_Official')
BOT_USERNAME   = environ.get('BOT_USERNAME', 'RexBots_Official')

# 🔗 Channel & Support Links
CHANNEL       = environ.get('CHANNEL', 'https://t.me/RexBots_Official')
SUPPORT       = environ.get('SUPPORT', 'https://t.me/RexBots_Official')
HOW_TO_VERIFY = environ.get('HOW_TO_VERIFY', 'https://t.me/RexBots_Official')
HOW_TO_OPEN   = environ.get('HOW_TO_OPEN', 'https://t.me/RexBots_Official')

# 📢 Log Channels  (safe int conversion with fallback)
def _safe_int(key, fallback):
    val = environ.get(key, '')
    try:
        return int(val)
    except ValueError:
        return fallback

BIN_CHANNEL   = _safe_int('BIN_CHANNEL', 0)
LOG_CHANNEL   = _safe_int('LOG_CHANNEL', 0)
PREMIUM_LOGS  = _safe_int('PREMIUM_LOGS', 0)
VERIFIED_LOG  = _safe_int('VERIFIED_LOG', 0)
SUPPORT_GROUP = _safe_int('SUPPORT_GROUP', 0)

# ✅ Feature Toggles
VERIFY             = False
FSUB               = environ.get('FSUB', 'True').lower() not in ('false', '0', 'no')
ENABLE_LIMIT       = environ.get('ENABLE_LIMIT', 'True').lower() not in ('false', '0', 'no')
BATCH_VERIFY       = False
IS_SHORTLINK       = False
MAINTENANCE_MODE   = environ.get('MAINTENANCE_MODE', 'False').lower() in ('true', '1', 'yes')
PROTECT_CONTENT    = environ.get('PROTECT_CONTENT', 'False').lower() in ('true', '1', 'yes')
PUBLIC_FILE_STORE  = environ.get('PUBLIC_FILE_STORE', 'True').lower() not in ('false', '0', 'no')
BATCH_PROTECT_CONTENT = environ.get('BATCH_PROTECT_CONTENT', 'False').lower() in ('true', '1', 'yes')

# 🔗 Shortlink
SHORTLINK_URL = environ.get('SHORTLINK_URL', '')
SHORTLINK_API = environ.get('SHORTLINK_API', '')

# 💾 Database
DB_URL  = environ.get('DATABASE_URI', '')
DB_NAME = environ.get('DATABASE_NAME', 'rexlinkbot')

# 📸 Media & Images
QR_CODE    = environ.get('QR_CODE',    'https://ibb.co/mVkSySr7')
VERIFY_IMG = environ.get('VERIFY_IMG', 'https://ibb.co/mVkSySr7')
AUTH_PICS  = environ.get('AUTH_PICS',  'https://ibb.co/mVkSySr7')
PICS       = environ.get('PICS',       'https://ibb.co/mVkSySr7')
FILE_PIC   = environ.get('FILE_PIC',   'https://ibb.co/mVkSySr7')

# 📝 Captions — imported after Script to avoid circular import
from Script import script
FILE_CAPTION         = environ.get('FILE_CAPTION',         script.CAPTION)
BATCH_FILE_CAPTION   = environ.get('BATCH_FILE_CAPTION',   script.CAPTION)
CHANNEL_FILE_CAPTION = environ.get('CHANNEL_FILE_CAPTION', script.CAPTION)

# ⏱️ Time & Limits
PING_INTERVAL    = int(environ.get('PING_INTERVAL',    '1200'))
SLEEP_THRESHOLD  = int(environ.get('SLEEP_THRESHOLD',  '60'))
RATE_LIMIT_TIMEOUT = int(environ.get('RATE_LIMIT_TIMEOUT', '600'))
MAX_FILES        = int(environ.get('MAX_FILES',        '50'))
VERIFY_EXPIRE    = int(environ.get('VERIFY_EXPIRE',    '60'))   # hours

# ⚙️ Worker & App Config
WORKERS      = int(environ.get('WORKERS', '10'))
MULTI_CLIENT = False
NAME         = environ.get('name', 'rexbots_official')

# 🌐 Web Server
ON_HEROKU = 'DYNO' in environ
APP_NAME  = environ.get('APP_NAME') if ON_HEROKU else None
# Heroku dynamically assigns PORT — always read from env
PORT      = int(environ.get('PORT', '8080'))
NO_PORT   = environ.get('NO_PORT',  'true').lower() in ('true', '1', 'yes')
HAS_SSL   = environ.get('HAS_SSL',  'true').lower() in ('true', '1', 'yes')

# URL Generation
# Priority: FQDN (Cloudflare custom domain) → WEB_SERVER_BIND_ADDRESS (legacy) → Heroku APP_NAME fallback
BIND_ADDRESS = environ.get('WEB_SERVER_BIND_ADDRESS', '')
_fqdn_raw    = environ.get('FQDN', BIND_ADDRESS)

# Auto-fallback: if nothing set but we're on Heroku, derive from APP_NAME
if not _fqdn_raw and ON_HEROKU and APP_NAME:
    _fqdn_raw = f'{APP_NAME}.herokuapp.com'

FQDN = _fqdn_raw

if not FQDN.startswith('http'):
    PROTOCOL     = 'https' if HAS_SSL else 'http'
    PORT_SEGMENT = '' if NO_PORT else f':{PORT}'
    FQDN         = FQDN.rstrip('/')
    URL          = f'{PROTOCOL}://{FQDN}{PORT_SEGMENT}/'
else:
    URL = FQDN if FQDN.endswith('/') else FQDN + '/'
