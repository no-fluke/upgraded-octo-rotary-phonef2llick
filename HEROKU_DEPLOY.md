# 🚀 Heroku Deployment Guide — RexBots File-to-Link Bot

---

## Prerequisites

Before you start, have these ready:

- A **Heroku account** (heroku.com)
- **Heroku CLI** installed on your machine
- A **MongoDB Atlas** database (free tier works fine)
- Your **Telegram API credentials** (api.telegram.org)
- A **Telegram Bot Token** (from @BotFather)
- Two private Telegram channels:
  - **BIN_CHANNEL** — where files are stored
  - **LOG_CHANNEL** — for bot logs

---

## Step 1 — Get Your Telegram Credentials

1. Go to https://my.telegram.org → Log in
2. Click **API development tools**
3. Create a new app → copy `api_id` and `api_hash`
4. Create a bot via **@BotFather** → copy the `BOT_TOKEN`
5. Make your bot an **admin** in both `BIN_CHANNEL` and `LOG_CHANNEL`
6. Get the channel IDs (send a message to @getmyid_bot or check the channel link)

---

## Step 2 — Set Up MongoDB Atlas

1. Go to https://cloud.mongodb.com → Create a free account
2. Create a **Free Cluster** (M0 tier)
3. Create a database user with a password
4. Whitelist `0.0.0.0/0` in Network Access (allows Heroku IPs)
5. Click **Connect → Connect your application**
6. Copy the connection string, it looks like:
   ```
   mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
   Replace `<user>` and `<password>` with your credentials.

---

## Step 3 — Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Ubuntu / Debian
curl https://cli-assets.heroku.com/install.sh | sh

# Windows — download the installer from:
# https://devcenter.heroku.com/articles/heroku-cli
```

Log in:
```bash
heroku login
```

---

## Step 4 — Prepare the Repo

```bash
# Clone / extract the fixed repo, then:
cd literate-octo-pancake-file2link-main

git init
git add .
git commit -m "Initial deploy"
```

---

## Step 5 — Create the Heroku App

```bash
heroku create your-bot-name
# Example: heroku create rexbots-filelink
```

This gives you a URL like `https://your-bot-name.herokuapp.com`

---

## Step 6 — Set Environment Variables

Run each line (replace the placeholder values):

```bash
heroku config:set API_ID=12345678
heroku config:set API_HASH=your_api_hash_here
heroku config:set BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ

heroku config:set ADMINS="123456789"          # your Telegram user ID
heroku config:set AUTH_CHANNEL="-1001234567890"  # force-sub channel ID (or leave blank)

heroku config:set BIN_CHANNEL=-1001234567890  # storage channel
heroku config:set LOG_CHANNEL=-1009876543210  # log channel
heroku config:set PREMIUM_LOGS=-1009876543210
heroku config:set VERIFIED_LOG=-1009876543210
heroku config:set SUPPORT_GROUP=-1009876543210

heroku config:set DATABASE_URI="mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true"
heroku config:set DATABASE_NAME=rexlinkbot

heroku config:set BOT_USERNAME=YourBotUsername   # without @
heroku config:set CHANNEL=https://t.me/YourChannel
heroku config:set SUPPORT=https://t.me/YourSupport

# Web server config
heroku config:set APP_NAME=your-bot-name        # must match your heroku app name
heroku config:set WEB_SERVER_BIND_ADDRESS=your-bot-name.herokuapp.com
heroku config:set HAS_SSL=true
heroku config:set NO_PORT=true
heroku config:set PORT=8080

# Optional
heroku config:set MAX_FILES=50
heroku config:set PING_INTERVAL=1200
```

---

## Step 7 — Add Heroku Buildpack

```bash
heroku buildpacks:set heroku/python
```

---

## Step 8 — Deploy

```bash
git push heroku main
# or if your branch is master:
git push heroku master
```

Watch the build logs. It should end with:
```
remote: -----> Launching...
remote:        Released v1
remote:        https://your-bot-name.herokuapp.com/ deployed to Heroku
```

---

## Step 9 — Scale the Dyno

Heroku free dynos sleep. Use the `web` dyno:

```bash
heroku ps:scale web=1
```

To keep it awake (Eco/Basic plan), set `PING_INTERVAL=1200` which pings
itself every 20 minutes.

---

## Step 10 — Check Logs

```bash
heroku logs --tail
```

You should see:
```
Initializing Your Bot
Imported => batch
Imported => broadcast
Imported => bulk_txt
...
```

---

## Common Issues & Fixes

| Problem | Fix |
|---|---|
| `H10 App crashed` | Run `heroku logs --tail` to see the real error |
| `FloodWait errors` | Bot is being rate-limited — this is normal, it retries automatically |
| `BIN_CHANNEL not found` | Make sure the bot is an admin in that channel |
| `Database connection error` | Check `DATABASE_URI` and MongoDB Network Access whitelist |
| `InvalidHash` on stream links | Make sure `WEB_SERVER_BIND_ADDRESS` is set correctly |
| App sleeping | Upgrade to Eco plan ($5/mo) or use UptimeRobot to ping your URL |

---

## Updating the Bot

```bash
git add .
git commit -m "Update"
git push heroku main
heroku restart
```

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `API_ID` | ✅ | Telegram API ID |
| `API_HASH` | ✅ | Telegram API Hash |
| `BOT_TOKEN` | ✅ | Bot token from @BotFather |
| `ADMINS` | ✅ | Space-separated admin user IDs |
| `BIN_CHANNEL` | ✅ | File storage channel ID (negative, e.g. -100xxx) |
| `LOG_CHANNEL` | ✅ | Log channel ID |
| `DATABASE_URI` | ✅ | MongoDB connection string |
| `APP_NAME` | ✅ | Your Heroku app name (for ping) |
| `WEB_SERVER_BIND_ADDRESS` | ✅ | `yourapp.herokuapp.com` (no https://) |
| `BOT_USERNAME` | ✅ | Bot username without @ |
| `AUTH_CHANNEL` | ❌ | Force-sub channel IDs (space-separated) |
| `PROTECT_CONTENT` | ❌ | `true` to prevent forwarding |
| `MAX_FILES` | ❌ | Files per rate-limit window (default: 50) |
| `PING_INTERVAL` | ❌ | Seconds between self-pings (default: 1200) |
| `FSUB` | ❌ | `true` to enable force subscribe |

