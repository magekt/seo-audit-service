
import json
from flask import Flask, request, jsonify
import os
import datetime
from seo_audit_enhanced_fixed import SEOSleuth, AuditConfig

app = Flask(__name__)

def create_config():
    """Create Cloud Functions optimized configuration."""
    return AuditConfig(
        max_pages=10,  # Limit for Cloud Functions
        max_concurrent_requests=1,  # Single request processing
        request_delay=1.0,
        respect_robots_txt=True,
        cache_enabled=False,  # Stateless functions
        timeout=30,
        max_retries=2
    )

def seo_audit_function(request):
    """HTTP Cloud Function for SEO audit."""

    # Handle CORS preflight
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    if request.method != 'POST':
        return (jsonify({'error': 'Method not allowed'}), 405, headers)

    try:
        # Get request data
        request_json = request.get_json(silent=True)
        if not request_json:
            return (jsonify({'error': 'No JSON data provided'}), 400, headers)

        website_url = request_json.get('website_url', '').strip()
        target_keyword = request_json.get('target_keyword', '').strip()
        max_pages = min(int(request_json.get('max_pages', 5)), 20)  # Limit for functions

        if not website_url or not target_keyword:
            return (jsonify({'error': 'website_url and target_keyword required'}), 400, headers)

        # Get API key from environment
        api_key = os.environ.get('ZENSERP_API_KEY')
        if not api_key:
            return (jsonify({'error': 'API key not configured'}), 500, headers)

        # Run SEO analysis
        config = create_config()
        config.max_pages = max_pages

        seo_tool = SEOSleuth(api_key, config)
        report = seo_tool.analyze_website(website_url, target_keyword)

        # Return results
        result = {
            'success': True,
            'website_url': website_url,
            'target_keyword': target_keyword,
            'pages_analyzed': max_pages,
            'report': report,
            'timestamp': datetime.datetime.now().isoformat(),
            'analysis_duration': 'Completed'
        }

        return (jsonify(result), 200, headers)

    except Exception as e:
        error_result = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }
        return (jsonify(error_result), 500, headers)

# For local testing
if __name__ == '__main__':
    app.add_url_rule('/seo-audit', 'seo_audit', seo_audit_function, methods=['POST', 'OPTIONS'])
    app.run(debug=True, port=8080)
