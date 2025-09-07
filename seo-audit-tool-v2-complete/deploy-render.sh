#!/bin/bash

# 🚀 SEO Audit Tool v2.0 - Render.com Deployment Script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║ 🚀 SEO AUDIT TOOL v2.0 - RENDER DEPLOYMENT                  ║"
echo "║ Fast, reliable deployment with zero networking issues         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

log_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }

# Check if this is a git repository
if [ ! -d ".git" ]; then
    log_info "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit - SEO Audit Tool v2.0"
fi

log_info "Files ready for Render deployment"
log_success "🌐 Next steps:"
echo "1. Push this code to GitHub"
echo "2. Connect your GitHub repo to Render"
echo "3. Render will automatically deploy using render.yaml"
echo ""
echo "📋 Manual Render Setup:"
echo "   • Runtime: Python"
echo "   • Build Command: pip install -r requirements.txt"  
echo "   • Start Command: gunicorn --bind 0.0.0.0:\$PORT --workers 1 --threads 8 --timeout 180 app:app"
echo "   • Health Check Path: /api/health"
echo ""
log_success "🎉 Ready for deployment!"
