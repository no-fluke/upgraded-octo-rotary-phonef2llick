# 🤖 RexBots File-to-Link Bot

A Telegram bot that generates streaming/download links for files stored in a private Telegram channel.

---

## 🚀 One-Click Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/no-fluke/scaling-octo-winnerf2l)

> **Replace** `YOUR_USERNAME/YOUR_REPO` in the button URL above with your actual GitHub repo path before pushing.

---

## ⚙️ Required Environment Variables

| Variable | Description |
|---|---|
| `API_ID` | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | Telegram API Hash |
| `BOT_TOKEN` | Bot token from @BotFather |
| `ADMINS` | Space-separated Telegram user IDs |
| `BIN_CHANNEL` | File storage channel ID (e.g. `-1001234567890`) |
| `LOG_CHANNEL` | Log channel ID |
| `DATABASE_URI` | MongoDB Atlas connection string |
| `BOT_USERNAME` | Your bot username (without `@`) |

---

## 🌐 Cloudflare Custom Domain Setup

This bot works behind Cloudflare so your stream links always use your own domain
(e.g. `https://stream.yourdomain.com/watch/...`) instead of the raw Heroku URL.

### Step 1 — Cloudflare DNS

Add a CNAME record in Cloudflare:

| Type | Name | Target | Proxy |
|---|---|---|---|
| CNAME | `stream` | `your-app-name.herokuapp.com` | Proxied (orange cloud) |

### Step 2 — Heroku Custom Domain

```bash
heroku domains:add stream.yourdomain.com
heroku domains        # copy the DNS target shown, update Cloudflare CNAME to it
```

### Step 3 — SSL

- Cloudflare SSL/TLS → set to **Full** (not Full Strict)
- Set in Heroku: `HAS_SSL=true` and `NO_PORT=true`

### Step 4 — Set FQDN

```
FQDN=stream.yourdomain.com
```

That's it. All links will be generated as `https://stream.yourdomain.com/watch/...`

---

## 🛠️ Manual Deploy

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO && cd YOUR_REPO
heroku login
heroku create your-app-name
heroku stack:set container -a your-app-name
heroku config:set API_ID=xx API_HASH=xx BOT_TOKEN=xx ADMINS=xx \
  BIN_CHANNEL=xx LOG_CHANNEL=xx DATABASE_URI=xx BOT_USERNAME=xx \
  FQDN=stream.yourdomain.com HAS_SSL=true NO_PORT=true APP_NAME=your-app-name
git push heroku main
heroku ps:scale web=1
```

---

## 📋 Notes

- **PORT**: Heroku assigns `$PORT` dynamically — the bot reads it automatically.
- **heroku.yml**: Uses container stack (Docker) — no Python buildpack needed.
- **Ping**: `PING_INTERVAL=1200` keeps the dyno awake (pings every 20 mins).
- **MongoDB**: Use Atlas free tier, whitelist `0.0.0.0/0` in Network Access.

---

## 🐛 Common Issues

| Error | Fix |
|---|---|
| `H10 App crashed` | `heroku logs --tail` |
| Links use wrong domain | Set `FQDN=your.domain.com` |
| `InvalidHash` on stream | `FQDN` must match what was set when the link was generated |
| App sleeping | Eco/Basic plan + `PING_INTERVAL=1200` |
| Database error | Check `DATABASE_URI` and MongoDB Network Access |
