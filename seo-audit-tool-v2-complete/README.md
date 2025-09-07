# SEO Audit Tool v2.0 🚀

A comprehensive, production-ready SEO analysis tool with advanced crawling capabilities and detailed reporting.

## ✨ Features

- **Technical SEO Analysis**: Meta tags, headers, SSL, mobile-friendly checks
- **Content Analysis**: Keyword density, readability scores, word count optimization  
- **Performance Metrics**: Page load times, Core Web Vitals, image optimization
- **SEO Scoring**: Overall health score with prioritized recommendations
- **Advanced Reporting**: Comprehensive markdown reports with export options
- **Issue Detection**: Automatic identification of SEO problems with severity levels

## 🏗️ Architecture

- **Backend**: Python Flask with async crawling
- **Frontend**: Vanilla JavaScript with Bootstrap 5
- **Analysis Engine**: Custom SEO crawler with BeautifulSoup
- **Deployment**: Docker containers, Cloud Run, or Render.com ready

## 🚀 Quick Deployment

### Option 1: Render.com (Recommended - Free Tier)
```bash
# 1. Push to GitHub
git add .
git commit -m "Deploy SEO Audit Tool v2.0"
git push origin main

# 2. Connect GitHub repo to Render
# 3. Render auto-deploys using render.yaml
```

### Option 2: Google Cloud Run
```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Deploy
./deploy-gcp.sh
```

### Option 3: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
# Visit: http://localhost:8080
```

## ⚙️ Configuration

Edit `config.yaml` or set environment variables:

```yaml
# Core settings
max_pages_limit: 10
max_concurrent_requests: 2
request_delay: 1.5
request_timeout: 30

# Features
serp_analysis_enabled: true
admin_endpoints_enabled: true
rate_limiting_enabled: false
```

## 📊 API Endpoints

- `POST /api/analyze` - Start SEO analysis
- `GET /api/status/<id>` - Check analysis progress  
- `GET /api/report/<id>` - Get full report
- `GET /api/health` - System health check
- `GET /api/admin/analyses` - Admin panel (if enabled)

## 🔧 Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run in development mode
FLASK_ENV=development python app.py

# Run tests (if available)
python -m pytest tests/
```

## 🐳 Docker

```bash
# Build image
docker build -t seo-audit-tool-v2 .

# Run container
docker run -p 8080:8080 seo-audit-tool-v2
```

## 📝 Usage Example

```bash
# Start analysis via API
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"website_url": "https://example.com", "target_keyword": "digital marketing", "max_pages": 10}'

# Check status
curl http://localhost:8080/api/status/<analysis_id>

# Get report
curl http://localhost:8080/api/report/<analysis_id>
```

## 🛡️ Security Features

- Input validation and sanitization
- Rate limiting (configurable)
- CORS protection
- Secure headers
- Non-root container user

## 📈 Performance

- Async crawling with configurable concurrency
- Respectful crawling delays
- Memory-efficient processing
- Progress tracking with real-time updates
- Race condition fixes

## 🆘 Troubleshooting

### Common Issues

1. **Analysis stuck in "queued"**: Race condition fix applied in v2.0
2. **Networking issues on Cloud Run**: Use render.yaml deployment
3. **Memory errors**: Reduce max_pages_limit in config
4. **SSL errors**: Check target website's SSL configuration

### Support

- Check `/api/health` endpoint for system status
- View logs for detailed error information
- Use admin endpoints for analysis management

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Version**: 2.0.0  
**Build Date**: 2025-09-07 15:23:21  
**Status**: Production Ready ✅
