# ☠️ REGIME REAPER — VPS DEPLOYMENT GUIDE

**Hostinger VPS | Ubuntu 24.04 | regimereaper.com**

---

## Prerequisites

✅ VPS IP: `147.93.44.83`
✅ Domain: `regimereaper.com`
✅ Root password: `waE&tDzgDUT,A/@Y(P.8`
✅ OS: Ubuntu 24.04
✅ GitHub repo: Ready to push

---

## Step 1: Push to GitHub

```bash
# In your local repo directory (d:\REGIME PROJECT\regime-reaper)
git remote add origin https://github.com/YOUR_USERNAME/regime-reaper.git
git branch -M main
git push -u origin main
```

**If you get auth error:**
1. Create a Personal Access Token at github.com/settings/tokens
2. Use the token as password when prompted

---

## Step 2: SSH into VPS

```bash
ssh root@147.93.44.83
# Password: waE&tDzgDUT,A/@Y(P.8
```

---

## Step 3: Install Dependencies

```bash
# Update system
apt-get update && apt-get upgrade -y

# Python
apt-get install -y python3 python3-pip python3-venv

# Node
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Other tools
apt-get install -y nginx git curl certbot python3-certbot-nginx

# PM2 (process manager)
npm install -g pm2
```

---

## Step 4: Clone Repo

```bash
cd /opt
git clone https://github.com/YOUR_USERNAME/regime-reaper.git reaper
cd reaper
```

---

## Step 5: Configure .env

Copy your `.env` file from your local machine. It should have all these keys:

```env
APP_NAME=REGIME REAPER
DEBUG=false
DATABASE_URL=sqlite:///./reaper.db

GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=llama-3.3-70b-versatile

SCRAPFLY_KEY=your_scrapfly_key_here

DISCORD_BOT_TOKEN=your_discord_token
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
DISCORD_HOT_DEALS_WEBHOOK=https://discord.com/api/webhooks/...
DISCORD_SCAN_LOG_WEBHOOK=https://discord.com/api/webhooks/...
DISCORD_INVENTORY_WEBHOOK=https://discord.com/api/webhooks/...
DISCORD_GUILD_ID=your_guild_id
```

**To copy the file via SCP:**
```bash
scp .env root@147.93.44.83:/opt/reaper/.env
```

---

## Step 6: Run Deployment Script

```bash
cd /opt/reaper
chmod +x deploy-vps.sh
./deploy-vps.sh
```

This will:
- ✅ Setup Python venv + install backend deps
- ✅ Initialize SQLite database
- ✅ Build React frontend
- ✅ Start backend with PM2
- ✅ Start Discord bot with PM2
- ✅ Configure Nginx reverse proxy
- ✅ Setup SSL with Certbot
- ✅ Enable auto-restart on VPS reboot

---

## Step 7: Point Domain DNS to VPS

In **Hostinger Dashboard:**
1. Go to **Domains** → **regimereaper.com** → **DNS Records**
2. Add/Update A record:
   - **Host:** @ (or regimereaper.com)
   - **Type:** A
   - **Value:** 147.93.44.83
   - **TTL:** 3600

3. Add www CNAME (optional):
   - **Host:** www
   - **Type:** CNAME
   - **Value:** regimereaper.com

**Wait 5-15 minutes for DNS to propagate**

---

## Step 8: Verify Deployment

```bash
# Check services
pm2 status

# View logs
pm2 logs reaper-backend
pm2 logs reaper-discord

# Test health endpoint
curl https://regimereaper.com/health

# View Nginx logs
tail -f /var/log/nginx/access.log
```

---

## What's Running

| Service | Port | Status Command |
|---|---|---|
| **Backend (FastAPI)** | 8000 (internal) | `pm2 logs reaper-backend` |
| **Discord Bot** | N/A | `pm2 logs reaper-discord` |
| **Nginx** | 80, 443 | `systemctl status nginx` |
| **Certbot SSL** | Auto-renew | `certbot renew --dry-run` |

---

## Management Commands

```bash
# Restart all services
pm2 restart all

# Stop all services
pm2 stop all

# View real-time logs
pm2 monit

# Restart after code update
cd /opt/reaper && git pull && npm run build && pm2 restart all
```

---

## Updating from GitHub

```bash
cd /opt/reaper
git pull origin main
cd frontend && npm run build
cd ../backend && pip install -r requirements.txt
pm2 restart reaper-backend reaper-discord
```

---

## Troubleshooting

### Backend won't start
```bash
pm2 logs reaper-backend
# Check .env has all required keys
# Check port 8000 is available
```

### Discord bot won't start
```bash
pm2 logs reaper-discord
# Check DISCORD_BOT_TOKEN is valid
# Check bot has correct intents and permissions
```

### Nginx 502 Bad Gateway
```bash
# Backend may be down
pm2 restart reaper-backend
# Or check it's listening on 8000
netstat -tuln | grep 8000
```

### SSL certificate issues
```bash
# Renew manually
certbot renew --force-renewal
# Or let the auto-renew cron handle it (runs monthly)
```

---

## Security Notes

- ✅ All traffic forced to HTTPS (SSL cert auto-renewed)
- ✅ PM2 auto-restarts services if they crash
- ✅ Auto-restart on VPS reboot enabled
- ✅ API keys stored in `.env` (not in git)
- ✅ Nginx reverse proxy hides FastAPI internals
- 🔲 **TODO:** Setup firewall (allow 22, 80, 443 only)

```bash
# Optional: Setup UFW firewall
ufw enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
```

---

## Summary

```
┌─────────────────────────────────────────┐
│ regimereaper.com (HTTPS)                │
│ ↓                                       │
│ Nginx Reverse Proxy (Port 443)          │
│ ↓                                       │
│ ├─ /api/* → Backend (localhost:8000)    │
│ └─ /* → Frontend (static React)         │
│ ↓                                       │
│ FastAPI (Python) + Discord Bot          │
│ ↓                                       │
│ SQLite Database + External APIs         │
│ (Groq, Scrapfly, Discord)              │
└─────────────────────────────────────────┘
```

---

**Deployment time: ~15 minutes**  
**Status: 🟢 Ready to deploy**

Next: Push code → SSH into VPS → Run script → Live!
