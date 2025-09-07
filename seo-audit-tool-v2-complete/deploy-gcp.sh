#!/bin/bash

# 🚀 SEO Audit Tool v2.0 - Google Cloud Run Deployment

set -e

PROJECT_ID="${PROJECT_ID:-seo-audit-tool-2025}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-seo-audit-tool-v2}"

echo "🚀 Deploying SEO Audit Tool v2.0 to Google Cloud Run"
echo "=================================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "=================================================="

# Set project
gcloud config set project $PROJECT_ID

# Deploy
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 900 \
    --max-instances 100 \
    --min-instances 0 \
    --concurrency 1000 \
    --set-env-vars "FLASK_ENV=production,APP_VERSION=2.0.0" \
    --port 8080

echo "🎉 Deployment completed!"
