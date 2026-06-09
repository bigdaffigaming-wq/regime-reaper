#!/bin/bash
# REGIME REAPER — VPS Deployment Script
# Ubuntu 24.04 | Hostinger VPS | regimereaper.com

set -e

echo "☠️ REGIME REAPER — VPS DEPLOYMENT STARTING"
echo "==========================================="

# Update system
echo "📦 Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# Install Python 3.11+
echo "🐍 Installing Python..."
apt-get install -y -qq python3 python3-pip python3-venv

# Install Node 18+
echo "📦 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y -qq nodejs

# Install Nginx
echo "🌐 Installing Nginx..."
apt-get install -y -qq nginx

# Install PM2 globally
echo "⚙️ Installing PM2..."
npm install -g pm2 -q

# Install Certbot for SSL
echo "🔒 Installing Certbot..."
apt-get install -y -qq certbot python3-certbot-nginx

# Install git
echo "📂 Installing Git..."
apt-get install -y -qq git

echo ""
echo "✅ All dependencies installed!"
echo ""
echo "Next steps:"
echo "1. Clone the repo:    git clone https://github.com/YOUR_USERNAME/regime-reaper.git /opt/reaper"
echo "2. cd /opt/reaper"
echo "3. Copy .env with all API keys"
echo "4. Run: bash ./deploy-vps.sh"
