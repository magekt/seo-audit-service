
# 🚀 SEO Audit Tool - Google Cloud Deployment

A powerful, serverless SEO audit tool that can be deployed on Google Cloud Platform with automatic GitHub integration.

## 🌟 Features

- **Comprehensive SEO Analysis**: Meta tags, keywords, technical SEO, images, internal linking
- **SERP Competition Analysis**: Analyze top 10 competitors for your target keywords
- **Performance Metrics**: Page load times, content analysis, optimization scoring
- **Multiple Export Formats**: Markdown reports, CSV data exports
- **Serverless Architecture**: Auto-scaling, pay-per-use pricing
- **GitHub Integration**: Automatic deployments on code changes

## 🏗️ Architecture Options

### Option 1: Google Cloud Run (Recommended)
- **Best for**: Full web applications, complex workflows
- **Features**: Complete Flask web app, background processing, file downloads
- **Timeout**: 15 minutes max per request
- **Cost**: ~$0.24 per million requests after free tier

### Option 2: Google Cloud Functions  
- **Best for**: Simple API endpoints, serverless functions
- **Features**: Direct API calls, immediate responses
- **Timeout**: 9 minutes max per request
- **Cost**: ~$0.40 per million invocations after free tier

### Option 3: Development with Google Colab
- **Best for**: Testing, development, prototyping
- **Features**: Full Python environment, easy sharing
- **Limitations**: Not for production, 12-hour sessions
- **Cost**: Free

## 📊 Google Cloud Free Tier Benefits

- **Cloud Run**: 2 million requests/month
- **Cloud Functions**: 2 million invocations/month  
- **Container Registry**: 0.5GB storage
- **Cloud Build**: 120 build-minutes/day
- **Secrets Manager**: 6 active secrets

## 🚀 Quick Start

### Prerequisites
1. Google Cloud Platform account
2. ZenSERP API key (get from https://zenserp.com)
3. GitHub repository
4. Google Cloud CLI installed

### 1-Click Deployment
```bash
# Clone the repository
git clone https://github.com/your-username/seo-audit-tool.git
cd seo-audit-tool

# Make deploy script executable
chmod +x deploy.sh

# Run deployment (follow the prompts)
./deploy.sh
```

### Manual Deployment

#### For Google Cloud Run:
```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# Deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/seo-audit-tool
gcloud run deploy seo-audit-tool --image gcr.io/$PROJECT_ID/seo-audit-tool --platform managed --region us-central1 --allow-unauthenticated
```

#### For Google Cloud Functions:
```bash
# Enable API
gcloud services enable cloudfunctions.googleapis.com

# Deploy function
gcloud functions deploy seo-audit --runtime python39 --trigger-http --allow-unauthenticated --entry-point seo_audit_function
```

## 🔧 Configuration

### Environment Variables
- `ZENSERP_API_KEY`: Your ZenSERP API key
- `SECRET_KEY`: Flask secret key (auto-generated)
- `FLASK_ENV`: Set to 'production' for deployment

### API Configuration
```python
config = AuditConfig(
    max_pages=10,                    # Maximum pages to crawl
    max_concurrent_requests=2,       # Concurrent HTTP requests  
    request_delay=1.5,              # Delay between requests
    respect_robots_txt=True,         # Follow robots.txt
    cache_enabled=True,             # Enable request caching
    timeout=30,                     # Request timeout
    max_retries=2                   # Retry attempts
)
```

## 📱 Usage

### Web Interface
1. Open your deployed URL
2. Enter website URL and target keyword
3. Select maximum pages to analyze
4. Click "Start SEO Analysis"
5. Download or view the generated report

### API Endpoints

#### Cloud Run Endpoints:
- `POST /analyze` - Start SEO analysis
- `GET /status/{analysis_id}` - Check analysis status  
- `GET /report/{analysis_id}` - Get analysis report
- `GET /download/{analysis_id}` - Download report file

#### Cloud Functions Endpoint:
- `POST /` - Direct SEO analysis (returns results immediately)

### Example API Call:
```javascript
const response = await fetch('https://your-service.run.app/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        website_url: 'https://example.com',
        target_keyword: 'digital marketing',
        max_pages: 10
    })
});
```

## 🔄 GitHub Integration

### Automatic Deployment
1. Fork this repository
2. Set up GitHub Secrets:
   - `GCP_SA_KEY`: Google Cloud service account key
   - `ZENSERP_API_KEY`: Your ZenSERP API key
3. Update project ID in `.github/workflows/deploy.yml`
4. Push to main branch → automatic deployment!

### GitHub Actions Workflow
```yaml
name: Deploy to Google Cloud
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: google-github-actions/setup-gcloud@v1
      - name: Deploy to Cloud Run
        run: gcloud run deploy...
```

## 💰 Cost Estimation

### Free Tier (Monthly)
- **2M requests**: $0
- **Basic usage**: Completely free

### Paid Usage (After free tier)
- **Cloud Run**: $0.24 per million requests
- **Cloud Functions**: $0.40 per million invocations
- **Storage**: $0.026 per GB-month
- **Network**: $0.12 per GB egress

### Example Costs:
- **10K requests/month**: $0 (within free tier)
- **1M requests/month**: $0 (within free tier)  
- **5M requests/month**: ~$0.72/month
- **Very affordable for most use cases!**

## 🛠️ Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ZENSERP_API_KEY="your-api-key"
export FLASK_ENV="development"

# Run locally
python app.py
```

### Testing with Google Colab
1. Upload `seo_audit_enhanced_fixed.py` to Colab
2. Install packages: `!pip install -r requirements.txt`
3. Run analysis directly in notebook
4. Perfect for testing and development!

## 📝 File Structure
```
seo-audit-tool/
├── app.py                          # Flask web application
├── main.py                         # Cloud Functions entry point
├── seo_audit_enhanced_fixed.py     # Core SEO audit engine
├── requirements.txt                # Dependencies
├── Dockerfile                      # Container configuration
├── deploy.sh                       # Deployment script
├── frontend.html                   # Universal web interface
├── templates/                      # Flask templates
│   ├── base.html
│   └── index.html
└── .github/workflows/
    └── deploy.yml                  # GitHub Actions workflow
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes  
4. Test with Google Colab
5. Submit a pull request

## 📜 License

MIT License - feel free to use for personal and commercial projects!

## 🆘 Support

- 📧 Email: your-email@example.com
- 🐛 Issues: https://github.com/your-username/seo-audit-tool/issues
- 📖 Docs: https://github.com/your-username/seo-audit-tool/wiki

## 🌟 Star this repository if it helped you!

---

**Built with ❤️ using Google Cloud Platform**
