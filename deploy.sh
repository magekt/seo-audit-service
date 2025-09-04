#!/bin/bash

echo "🚀 Simple SEO Audit Tool Deployment"
echo "==================================="

# Update this with your actual ZenSERP API key
ZENSERP_API_KEY="your-actual-zenserp-api-key-here"

if [ "$ZENSERP_API_KEY" = "your-actual-zenserp-api-key-here" ]; then
    echo "❌ Please edit this script and add your actual ZenSERP API key!"
    echo "   Edit line 7 in simple-deploy.sh"
    exit 1
fi

echo "📋 Project: seo-audit-tool-2025"
echo "📋 API Key: ${ZENSERP_API_KEY:0:10}..."
echo ""

# Set project
gcloud config set project seo-audit-tool-2025

# Enable APIs with explicit confirmation
echo "🔌 Enabling required APIs..."
gcloud services enable run.googleapis.com --quiet
gcloud services enable cloudbuild.googleapis.com --quiet  
gcloud services enable containerregistry.googleapis.com --quiet

echo "⏱️ Waiting 30 seconds for APIs to be ready..."
sleep 30

# Deploy directly to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy seo-audit-tool \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 900 \
    --max-instances 10 \
    --set-env-vars ZENSERP_API_KEY="$ZENSERP_API_KEY",FLASK_ENV=production

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    SERVICE_URL=$(gcloud run services describe seo-audit-tool --region=us-central1 --format="value(status.url)")
    echo "🔗 Your SEO Audit Tool: $SERVICE_URL"
    echo ""
    echo "🎉 Test it now by opening the URL above!"
else
    echo "❌ Deployment failed. Check the errors above."
fi
