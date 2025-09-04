
from flask import Flask, render_template, request, jsonify, send_file
import os
import datetime
import json
from threading import Thread
import uuid
from werkzeug.utils import secure_filename

# Import our SEO tool (we'll need to modify it slightly)
from seo_audit_enhanced_fixed import SEOSleuth, AuditConfig

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Store for ongoing analyses (in production, use Redis or database)
analyses = {}

class WebSEOAnalyzer:
    def __init__(self):
        self.zenserp_api_key = os.environ.get('ZENSERP_API_KEY')

    def create_web_config(self, max_pages=10):
        """Create web-optimized configuration."""
        return AuditConfig(
            max_pages=max_pages,
            max_concurrent_requests=2,
            request_delay=1.5,
            respect_robots_txt=True,
            cache_enabled=True,
            timeout=30,
            max_retries=2
        )

    def run_analysis(self, analysis_id, website_url, target_keyword, max_pages=10):
        """Run SEO analysis in background thread."""
        try:
            analyses[analysis_id]['status'] = 'running'
            analyses[analysis_id]['progress'] = 'Initializing...'

            config = self.create_web_config(max_pages)
            seo_tool = SEOSleuth(self.zenserp_api_key, config)

            analyses[analysis_id]['progress'] = 'Analyzing website...'
            report = seo_tool.analyze_website(website_url, target_keyword)

            # Save report
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"seo_audit_{analysis_id}_{timestamp}.md"
            filepath = os.path.join('reports', filename)

            os.makedirs('reports', exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)

            analyses[analysis_id].update({
                'status': 'completed',
                'progress': 'Analysis completed!',
                'report': report,
                'filename': filename,
                'filepath': filepath,
                'completed_at': datetime.datetime.now().isoformat()
            })

        except Exception as e:
            analyses[analysis_id].update({
                'status': 'error',
                'progress': f'Error: {str(e)}',
                'error': str(e)
            })

# Initialize analyzer
analyzer = WebSEOAnalyzer()

@app.route('/')
def index():
    """Main page with SEO audit form."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def start_analysis():
    """Start SEO analysis."""
    data = request.get_json()

    website_url = data.get('website_url', '').strip()
    target_keyword = data.get('target_keyword', '').strip()
    max_pages = min(int(data.get('max_pages', 10)), 50)  # Limit to 50 pages

    if not website_url or not target_keyword:
        return jsonify({'error': 'Website URL and target keyword are required'}), 400

    if not analyzer.zenserp_api_key:
        return jsonify({'error': 'ZenSERP API key not configured'}), 500

    # Generate unique analysis ID
    analysis_id = str(uuid.uuid4())

    # Initialize analysis record
    analyses[analysis_id] = {
        'id': analysis_id,
        'website_url': website_url,
        'target_keyword': target_keyword,
        'max_pages': max_pages,
        'status': 'queued',
        'progress': 'Queued for analysis...',
        'started_at': datetime.datetime.now().isoformat()
    }

    # Start analysis in background thread
    thread = Thread(target=analyzer.run_analysis, args=(analysis_id, website_url, target_keyword, max_pages))
    thread.daemon = True
    thread.start()

    return jsonify({
        'analysis_id': analysis_id,
        'status': 'started',
        'message': 'SEO analysis started. Please wait...'
    })

@app.route('/status/<analysis_id>')
def check_status(analysis_id):
    """Check analysis status."""
    if analysis_id not in analyses:
        return jsonify({'error': 'Analysis not found'}), 404

    analysis = analyses[analysis_id].copy()

    # Don't return the full report in status checks
    if 'report' in analysis:
        analysis['has_report'] = True
        del analysis['report']

    return jsonify(analysis)

@app.route('/report/<analysis_id>')
def get_report(analysis_id):
    """Get analysis report."""
    if analysis_id not in analyses:
        return jsonify({'error': 'Analysis not found'}), 404

    analysis = analyses[analysis_id]

    if analysis['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed yet'}), 400

    return jsonify({
        'analysis_id': analysis_id,
        'report': analysis.get('report', ''),
        'website_url': analysis['website_url'],
        'target_keyword': analysis['target_keyword'],
        'completed_at': analysis.get('completed_at')
    })

@app.route('/download/<analysis_id>')
def download_report(analysis_id):
    """Download report as file."""
    if analysis_id not in analyses:
        return jsonify({'error': 'Analysis not found'}), 404

    analysis = analyses[analysis_id]

    if analysis['status'] != 'completed' or 'filepath' not in analysis:
        return jsonify({'error': 'Report not available'}), 400

    try:
        return send_file(
            analysis['filepath'],
            as_attachment=True,
            download_name=analysis['filename'],
            mimetype='text/markdown'
        )
    except FileNotFoundError:
        return jsonify({'error': 'Report file not found'}), 404

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'api_configured': bool(analyzer.zenserp_api_key)
    })

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🚀 Starting Flask app on port {port}")
    print(f"🔑 ZenSERP API: {'✅ Configured' if analyzer.zenserp_api_key else '❌ Missing'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
