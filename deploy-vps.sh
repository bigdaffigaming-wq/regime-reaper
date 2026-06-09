#!/bin/bash
# REGIME REAPER — Full VPS Setup & Launch
# Run this AFTER cloning the repo and copying .env
# Ubuntu 24.04 | Hostinger VPS

set -e

REPO_DIR="/opt/reaper"
DOMAIN="regimereaper.com"
EMAIL="bigdaffigaming@gmail.com"

echo "☠️ REGIME REAPER — VPS SETUP & LAUNCH"
echo "======================================"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root"
   exit 1
fi

# Check if .env exists
if [ ! -f "$REPO_DIR/.env" ]; then
    echo "❌ ERROR: .env file not found in $REPO_DIR"
    echo "Copy your .env file with all API keys before running this script"
    exit 1
fi

echo "📁 Working directory: $REPO_DIR"
echo "🌐 Domain: $DOMAIN"
echo ""

# Create Python venv
echo "🐍 Setting up Python environment..."
cd "$REPO_DIR/backend"
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "from app.core.database import init_db; init_db(); print('✅ Database initialized')"

# Build frontend
echo "📦 Building frontend..."
cd "$REPO_DIR/frontend"
npm install -q
npm run build

# Start backend with PM2
echo "🚀 Starting backend with PM2..."
cd "$REPO_DIR/backend"
pm2 start app.main:app \
  --name "reaper-backend" \
  --interpreter python3 \
  --env "PATH=/opt/reaper/backend/venv/bin" \
  -- --host 0.0.0.0 --port 8000

# Start Discord bot with PM2
echo "🤖 Starting Discord bot with PM2..."
cd "$REPO_DIR"
pm2 start discord_bot/bot.py \
  --name "reaper-discord" \
  --interpreter python3 \
  --env "PATH=/opt/reaper/backend/venv/bin"

# Save PM2 config for restart on reboot
pm2 startup
pm2 save

echo ""
echo "✅ Services started!"
echo "   Backend:  http://localhost:8000"
echo "   Discord:  Running"
echo ""

# Configure Nginx
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/regimereaper << 'NGINX_CONF'
upstream reaper_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name regimereaper.com www.regimereaper.com;
    client_max_body_size 50M;

    root /opt/reaper/frontend/dist;
    index index.html;

    # Frontend — static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend — API proxy
    location /api {
        rewrite ^/api/(.*)$ /$1 break;
        proxy_pass http://reaper_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        proxy_pass http://reaper_backend;
    }
}
NGINX_CONF

# Enable site
ln -sf /etc/nginx/sites-available/regimereaper /etc/nginx/sites-enabled/regimereaper
rm -f /etc/nginx/sites-enabled/default

# Test Nginx config
nginx -t

# Start Nginx
systemctl restart nginx
systemctl enable nginx

echo "✅ Nginx configured"
echo ""

# Setup SSL with Certbot
echo "🔒 Setting up SSL certificate..."
certbot certonly --nginx \
  -d regimereaper.com \
  -d www.regimereaper.com \
  -n \
  --agree-tos \
  --email "$EMAIL" \
  --expand \
  2>/dev/null || echo "⚠️ SSL setup skipped (may already exist)"

# Update Nginx for HTTPS
cat > /etc/nginx/sites-available/regimereaper << 'NGINX_HTTPS'
upstream reaper_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name regimereaper.com www.regimereaper.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name regimereaper.com www.regimereaper.com;
    client_max_body_size 50M;

    ssl_certificate /etc/letsencrypt/live/regimereaper.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/regimereaper.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    root /opt/reaper/frontend/dist;
    index index.html;

    # Frontend — static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend — API proxy
    location /api {
        rewrite ^/api/(.*)$ /$1 break;
        proxy_pass http://reaper_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        proxy_pass http://reaper_backend;
    }
}
NGINX_HTTPS

nginx -t && systemctl restart nginx

echo "✅ HTTPS configured"
echo ""

# Setup auto-renewal
systemctl enable certbot.timer
systemctl start certbot.timer

echo ""
echo "==========================================="
echo "✅ REGIME REAPER IS LIVE!"
echo "==========================================="
echo ""
echo "🌐 URL: https://regimereaper.com"
echo ""
echo "📊 Status:"
pm2 status
echo ""
echo "📝 Logs:"
echo "   Backend:  pm2 logs reaper-backend"
echo "   Discord:  pm2 logs reaper-discord"
echo ""
echo "⚙️ Management:"
echo "   Restart:   pm2 restart all"
echo "   Stop:      pm2 stop all"
echo "   Restart on reboot: enabled (pm2 startup saved)"
echo ""
