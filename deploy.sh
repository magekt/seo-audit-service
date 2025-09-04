#!/bin/bash

# 🚀 Google Cloud Deployment Script for SEO Audit Tool

echo "🌐 SEO Audit Tool - Google Cloud Deployment"
echo "============================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set variables (UPDATE THESE)
PROJECT_ID="seo-audit-tool-2025"
REGION="us-central1"
SERVICE_NAME="seo-audit-tool"
ZENSERP_API_KEY="d913d650-897e-11f0-ac57-25719dc87a5e"

echo "📋 Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo ""

# Set the project
echo "🔧 Setting up project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔌 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Create secrets
echo "🔐 Creating secrets..."
echo -n "$ZENSERP_API_KEY" | gcloud secrets create zenserp-api-key --data-file=-
echo -n "$(openssl rand -base64 32)" | gcloud secrets create flask-secret --data-file=-

echo "🎯 Choose deployment option:"
echo "1) Google Cloud Run (Full Flask app)"
echo "2) Google Cloud Functions (Serverless function)"
read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo "🚀 Deploying to Google Cloud Run..."

    # Build and deploy to Cloud Run
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

    gcloud run deploy $SERVICE_NAME \
        --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --timeout 900 \
        --max-instances 10 \
        --set-secrets ZENSERP_API_KEY=zenserp-api-key:latest,SECRET_KEY=flask-secret:latest

elif [ "$choice" = "2" ]; then
    echo "⚡ Deploying to Google Cloud Functions..."

    # Enable Cloud Functions API
    gcloud services enable cloudfunctions.googleapis.com

    # Deploy Cloud Function
    gcloud functions deploy seo-audit \
        --runtime python39 \
        --trigger-http \
        --allow-unauthenticated \
        --memory 2048MB \
        --timeout 540s \
        --set-env-vars ZENSERP_API_KEY=$ZENSERP_API_KEY \
        --entry-point seo_audit_function \
        --source . \
        --requirements-file requirements-functions.txt

else
    echo "❌ Invalid choice. Exiting."
    exit 1
fi

echo "✅ Deployment completed!"
echo ""
echo "🌐 Your SEO Audit Tool is now live!"

if [ "$choice" = "1" ]; then
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
    echo "🔗 Cloud Run URL: $SERVICE_URL"
elif [ "$choice" = "2" ]; then
    FUNCTION_URL=$(gcloud functions describe seo-audit --format="value(httpsTrigger.url)")
    echo "🔗 Cloud Functions URL: $FUNCTION_URL"
fi

echo ""
echo "💰 Free Tier Limits:"
echo "  • Cloud Run: 2 million requests/month"
echo "  • Cloud Functions: 2 million invocations/month"
echo "  • Container Registry: 0.5GB storage"
echo ""
echo "🎉 Happy SEO auditing!"
