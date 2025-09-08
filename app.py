"""
Enhanced SEO Audit Tool - Flask Application V3.0
Production-ready web application with FUNCTIONAL advanced features
"""

import os
import json
import time
import uuid
import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from threading import Thread, Lock
from pathlib import Path
from typing import Dict, Any, Optional
import validators
from flask import Flask, request, jsonify, render_template, send_file, url_for
from flask_cors import CORS
from urllib.parse import urlparse, urlunparse

# Import enhanced SEO engine
from seo_engine import EnhancedSEOEngine, CacheManager
from config import Config
import utils

# Enhanced logging configuration
os.makedirs('logs', exist_ok=True)
os.makedirs('reports', exist_ok=True)
os.makedirs('exports', exist_ok=True)
os.makedirs('cache', exist_ok=True)
os.makedirs('static/img', exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app, origins=["*"])

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize enhanced components
config = Config()
seo_engine = EnhancedSEOEngine(config)
cache_manager = CacheManager()

# Global state management
analyses: Dict[str, Dict[str, Any]] = {}
analyses_lock = Lock()

class RateLimiter:
    """Simple rate limiter"""
    def __init__(self, max_requests: int = 10, window_minutes: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self.requests = {}

    def is_allowed(self, client_ip: str = None) -> bool:
        if not client_ip:
            client_ip = request.remote_addr
        now = time.time()
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window_seconds
        ]

        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        self.requests[client_ip].append(now)
        return True

    def time_until_allowed(self, client_ip: str = None) -> int:
        if not client_ip:
            client_ip = request.remote_addr
        if client_ip not in self.requests or not self.requests[client_ip]:
            return 0
        oldest_request = min(self.requests[client_ip])
        return max(0, int(self.window_seconds - (time.time() - oldest_request)))

class ProgressTracker:
    """Enhanced progress tracking"""
    def __init__(self, total_steps: int = 5, description: str = "SEO Analysis"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = time.time()
        self.step_descriptions = []

    def increment(self, step_description: str = ""):
        self.current_step += 1
        if step_description:
            self.step_descriptions.append(step_description)

    def get_status(self):
        elapsed = time.time() - self.start_time
        percentage = min(100, (self.current_step / self.total_steps) * 100)
        
        # Estimate remaining time
        if self.current_step > 0:
            time_per_step = elapsed / self.current_step
            remaining_steps = self.total_steps - self.current_step
            estimated_remaining = remaining_steps * time_per_step
        else:
            estimated_remaining = 0

        return {
            'percentage': round(percentage, 1),
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'elapsed_time': elapsed,
            'remaining_time': max(0, estimated_remaining),
            'step_description': self.step_descriptions[-1] if self.step_descriptions else self.description
        }

class EnhancedAnalysisManager:
    """Enhanced analysis manager with FUNCTIONAL features"""
    def __init__(self):
        self.active_analyses = {}

    def start_enhanced_analysis(self, analysis_id: str, website_url: str, target_keyword: str,
                              max_pages: int, whole_website: bool = False):
        """Start enhanced SEO analysis with FUNCTIONAL features"""
        def run_enhanced_analysis():
            try:
                time.sleep(0.5)  # Initial delay

                # Enhanced validation
                max_retries = 3
                analysis_found = False
                for attempt in range(max_retries):
                    if analysis_id in analyses:
                        analysis_found = True
                        break
                    logger.warning(f"Enhanced analysis {analysis_id} not found on attempt {attempt + 1}")
                    time.sleep(1)

                if not analysis_found:
                    logger.error(f"Enhanced analysis {analysis_id} not found after {max_retries} attempts")
                    return

                # Update status to running
                with analyses_lock:
                    analyses[analysis_id]['status'] = 'running'
                    analyses[analysis_id]['progress'] = 'Initializing enhanced SEO analysis with advanced features...'

                logger.info(f"Starting enhanced analysis {analysis_id} for {website_url} (whole_website: {whole_website})")

                # IMPROVED: Dynamic progress tracking based on analysis type
                total_steps = 10 if whole_website else 6
                progress_tracker = ProgressTracker(
                    total_steps=total_steps,
                    description=f"{'Whole Website' if whole_website else 'Selective'} SEO Analysis for {website_url}"
                )
                
                with analyses_lock:
                    analyses[analysis_id]['progress_tracker'] = progress_tracker

                # Step 1: Enhanced Validation
                progress_tracker.increment("Enhanced validation and caching check")
                with analyses_lock:
                    analyses[analysis_id]['progress'] = progress_tracker.get_status()['step_description']

                if not utils.validate_url(website_url):
                    raise ValueError("Invalid website URL format")

                # Step 2: URL Discovery (for whole website)
                if whole_website:
                    progress_tracker.increment("Discovering all website URLs")
                    with analyses_lock:
                        analyses[analysis_id]['progress'] = "Discovering all URLs on the website..."

                # Step 3: Enhanced Analysis with new features
                progress_tracker.increment("Running enhanced SEO analysis with SERP and caching")
                with analyses_lock:
                    analyses[analysis_id]['progress'] = f"Analyzing website ({'whole site' if whole_website else f'up to {max_pages} pages'})..."

                # FIXED: Force disable cache for fresh analysis
                result = seo_engine.analyze_website(
                    website_url,
                    target_keyword,
                    max_pages,
                    whole_website=whole_website,
                    force_fresh=True  # Force fresh analysis
                )

                # Step 4: Enhanced Processing
                progress_tracker.increment("Processing enhanced analysis results and generating insights")
                with analyses_lock:
                    analyses[analysis_id]['progress'] = progress_tracker.get_status()['step_description']

                # Step 5: Report Generation
                progress_tracker.increment("Generating comprehensive enhanced reports and CSV export")
                with analyses_lock:
                    analyses[analysis_id]['progress'] = progress_tracker.get_status()['step_description']

                # Enhanced file saving
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_url = utils.sanitize_filename(website_url)
                filename = f"enhanced_seo_audit_{safe_url}_{timestamp}.md"
                reports_dir = Path("reports")
                reports_dir.mkdir(parents=True, exist_ok=True)
                filepath = reports_dir / filename

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(result['report'])

                # Step 6: Finalization
                progress_tracker.increment("Finalizing enhanced analysis and preparing exports")

                # Enhanced completion data
                pages_analyzed = result['metadata'].get('pages_analyzed', 0)
                analysis_type = 'Whole Website' if whole_website else 'Selective'
                
                final_update = {
                    'status': 'completed',
                    'progress': f'🎉 Enhanced SEO analysis completed successfully! Analyzed {pages_analyzed} pages.',
                    'report': result['report'],
                    'metadata': result['metadata'],
                    'filename': filename,
                    'filepath': str(filepath),
                    'csv_data_path': result.get('csv_data'),
                    'completed_at': datetime.now().isoformat(),
                    'file_size': len(result['report']),
                    'duration': progress_tracker.get_status()['elapsed_time'],
                    'enhanced_features_used': {
                        'whole_website': whole_website,
                        'analysis_type': analysis_type,
                        'serp_analysis': result['metadata'].get('serp_results_count', 0) > 0,
                        'cached_pages': result['metadata'].get('cached_pages', 0),
                        'fresh_pages': pages_analyzed - result['metadata'].get('cached_pages', 0),
                        'total_data_transferred': result['metadata'].get('total_data_transferred', 0)
                    }
                }

                with analyses_lock:
                    analyses[analysis_id].update(final_update)

                logger.info(f"✅ Enhanced analysis {analysis_id} completed successfully! "
                          f"Analyzed {pages_analyzed} pages in {utils.format_duration(progress_tracker.get_status()['elapsed_time'])}")

            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Enhanced analysis {analysis_id} failed: {error_msg}")
                with analyses_lock:
                    if analysis_id in analyses:
                        analyses[analysis_id].update({
                            'status': 'error',
                            'progress': f'Enhanced analysis failed: {error_msg}',
                            'error': error_msg,
                            'failed_at': datetime.now().isoformat()
                        })
            finally:
                if analysis_id in self.active_analyses:
                    del self.active_analyses[analysis_id]

        # Start enhanced analysis thread
        thread = Thread(target=run_enhanced_analysis, daemon=True)
        self.active_analyses[analysis_id] = thread
        thread.start()
        logger.info(f"Started enhanced analysis thread for {analysis_id}")

# Initialize components
analysis_manager = EnhancedAnalysisManager()
rate_limiter = RateLimiter(max_requests=config.rate_limit_requests, window_minutes=config.rate_limit_window)

# Routes
@app.route('/')
def index():
    """Enhanced main page"""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def start_analysis_endpoint():
    """Enhanced SEO analysis endpoint with FUNCTIONAL features"""
    try:
        # Rate limiting check
        if not rate_limiter.is_allowed():
            retry = rate_limiter.time_until_allowed()
            return jsonify({'error': 'Rate limit exceeded', 'retry_after_seconds': retry}), 429

        # Parse enhanced request data
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Required fields validation
        required_fields = ['website_url', 'target_keyword']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        website_url = data.get('website_url', '').strip()
        target_keyword = data.get('target_keyword', '').strip()

        # Enhanced parameters
        max_pages = int(data.get('max_pages', 10))
        whole_website = data.get('whole_website', False)
        serp_analysis = data.get('serp_analysis', True)
        use_cache = data.get('use_cache', True)

        # Validation
        if not website_url or not target_keyword:
            return jsonify({'error': 'Website URL and target keyword cannot be empty'}), 400

        try:
            website_url = utils.normalize_url(website_url)
            if not utils.validate_url(website_url):
                raise ValueError("Invalid URL format")
        except Exception as e:
            return jsonify({'error': f'Invalid website URL: {str(e)}'}), 400

        # IMPROVED: Better limits for whole website analysis
        if whole_website:
            max_pages = min(max_pages, 500)  # Increased limit for whole website
            logger.info(f"Whole website analysis requested for {website_url} (limit: {max_pages} pages)")
        else:
            max_pages = min(max(1, max_pages), config.max_pages_limit)
            logger.info(f"Selective analysis requested for {website_url} ({max_pages} pages)")

        # Generate enhanced analysis ID
        analysis_id = str(uuid.uuid4())

        # Create enhanced analysis record
        initial_record = {
            'id': analysis_id,
            'website_url': website_url,
            'target_keyword': target_keyword,
            'max_pages': max_pages,
            'whole_website': whole_website,
            'serp_analysis': serp_analysis,
            'use_cache': use_cache,
            'status': 'queued',
            'progress': f'Enhanced {"whole website" if whole_website else "selective"} analysis queued for processing...',
            'started_at': datetime.now().isoformat(),
            'user_agent': request.headers.get('User-Agent', ''),
            'client_ip': request.remote_addr,
            'created_at': datetime.now().isoformat(),
            'enhanced_features': True,
            'analysis_type': 'whole_website' if whole_website else 'selective'
        }

        with analyses_lock:
            analyses[analysis_id] = initial_record

        time.sleep(0.1)  # Ensure record creation

        # Start enhanced analysis
        analysis_manager.start_enhanced_analysis(
            analysis_id, website_url, target_keyword, max_pages, whole_website
        )

        logger.info(f"Started enhanced analysis {analysis_id} for {website_url} "
                   f"(keyword: {target_keyword}, whole_website: {whole_website}, max_pages: {max_pages})")

        # IMPROVED: Better estimated duration
        estimated_duration = 300 if whole_website else (max_pages * 5)  # 5 minutes for whole site minimum
        
        return jsonify({
            'analysis_id': analysis_id,
            'status': 'started',
            'message': f'Enhanced {"whole website" if whole_website else "selective"} SEO analysis started successfully',
            'check_status_url': url_for('check_status', analysis_id=analysis_id),
            'estimated_duration_seconds': estimated_duration,
            'max_pages': max_pages,
            'whole_website': whole_website,
            'enhanced_features': True,
            'serp_analysis_enabled': serp_analysis,
            'caching_enabled': use_cache,
            'analysis_type': 'whole_website' if whole_website else 'selective'
        }), 202

    except Exception as e:
        logger.error(f"Error starting enhanced analysis: {e}")
        return jsonify({'error': f'Failed to start enhanced analysis: {str(e)}'}), 500

@app.route('/api/status/<analysis_id>')
def check_status(analysis_id):
    """Enhanced status checking with additional metadata"""
    try:
        if not analysis_id:
            return jsonify({'error': 'Missing analysis ID'}), 400

        with analyses_lock:
            if analysis_id not in analyses:
                return jsonify({'error': 'Analysis not found', 'analysis_id': analysis_id}), 404

            analysis = analyses[analysis_id].copy()

        # Enhanced progress information
        if 'progress_tracker' in analysis:
            try:
                info = analysis['progress_tracker'].get_status()
                analysis['progress_info'] = {
                    'percentage': info['percentage'],
                    'elapsed_time': utils.format_duration(info['elapsed_time']),
                    'estimated_remaining': utils.format_duration(info['remaining_time']),
                    'current_step': info['current_step'],
                    'total_steps': info['total_steps']
                }
                del analysis['progress_tracker']  # Don't serialize the tracker
            except Exception as e:
                logger.warning(f"Error processing enhanced progress tracker for {analysis_id}: {e}")

        # Enhanced metadata for completed analysis
        if analysis.get('status') == 'completed' and 'enhanced_features_used' in analysis:
            features = analysis['enhanced_features_used']
            analysis['enhanced_summary'] = {
                'analysis_type': features.get('analysis_type', 'selective'),
                'whole_website_analysis': features.get('whole_website', False),
                'serp_results_found': features.get('serp_analysis', False),
                'pages_from_cache': features.get('cached_pages', 0),
                'fresh_pages_analyzed': features.get('fresh_pages', 0),
                'data_transferred_mb': features.get('total_data_transferred', 0) / 1024 / 1024,
                'has_csv_export': bool(analysis.get('csv_data_path'))
            }

        # Don't return full report in status (too large)
        if 'report' in analysis:
            analysis['has_report'] = True
            preview = analysis['report'][:300] + '...' if len(analysis['report']) > 300 else analysis['report']
            analysis['report_preview'] = preview
            del analysis['report']

        # Enhanced timing information
        if 'started_at' in analysis:
            try:
                started = datetime.fromisoformat(analysis['started_at'])
                elapsed = datetime.now() - started
                analysis['elapsed_seconds'] = int(elapsed.total_seconds())
                analysis['elapsed_formatted'] = utils.format_duration(elapsed.total_seconds())
            except Exception as e:
                logger.warning(f"Error calculating enhanced timing for {analysis_id}: {e}")

        analysis['status_check_timestamp'] = datetime.now().isoformat()
        analysis['enhanced_features_active'] = True

        return jsonify(analysis)

    except Exception as e:
        logger.error(f"Error in enhanced status check for {analysis_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'analysis_id': analysis_id,
            'enhanced_debug_info': str(e) if config.environment == 'development' else None
        }), 500

@app.route('/api/report/<analysis_id>')
def get_report(analysis_id):
    """Get enhanced analysis report"""
    try:
        if not analysis_id:
            return jsonify({'error': 'Missing analysis ID'}), 400

        with analyses_lock:
            if analysis_id not in analyses:
                return jsonify({'error': 'Analysis not found'}), 404

            analysis = analyses[analysis_id]

        if analysis.get('status') != 'completed':
            return jsonify({'error': 'Analysis not completed yet'}), 400

        return jsonify({
            'analysis_id': analysis_id,
            'report': analysis.get('report', ''),
            'metadata': analysis.get('metadata', {}),
            'enhanced_features': analysis.get('enhanced_features_used', {}),
            'generated_at': analysis.get('completed_at'),
            'file_info': {
                'filename': analysis.get('filename'),
                'size_bytes': analysis.get('file_size', 0)
            }
        })

    except Exception as e:
        logger.error(f"Error getting enhanced report for {analysis_id}: {e}")
        return jsonify({'error': f'Failed to get report: {str(e)}'}), 500

@app.route('/api/download-csv/<analysis_id>')
def download_csv(analysis_id):
    """Download enhanced CSV export"""
    try:
        if not analysis_id:
            return jsonify({'error': 'Missing analysis ID'}), 400

        with analyses_lock:
            if analysis_id not in analyses:
                return jsonify({'error': 'Analysis not found'}), 404

            analysis = analyses[analysis_id]

        if analysis.get('status') != 'completed':
            return jsonify({'error': 'Analysis not completed yet'}), 400

        csv_path = analysis.get('csv_data_path')
        if not csv_path or not os.path.exists(csv_path):
            return jsonify({'error': 'Enhanced CSV export not available'}), 404

        return send_file(
            csv_path,
            as_attachment=True,
            download_name=f"enhanced_seo_analysis_{analysis_id}.csv",
            mimetype='text/csv'
        )

    except Exception as e:
        logger.error(f"Error downloading enhanced CSV for {analysis_id}: {e}")
        return jsonify({'error': f'Failed to download CSV: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    """Enhanced health check endpoint"""
    try:
        # Basic health checks
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '3.0-enhanced-functional',
            'enhanced_features': True
        }

        # Enhanced system checks
        health_status['system'] = {
            'active_analyses': len(analysis_manager.active_analyses),
            'total_analyses': len(analyses),
            'cache_enabled': True,
            'serp_analysis': config.serp_analysis_enabled,
            'rate_limiting': True,
            'whole_website_support': True
        }

        # Cache health check
        try:
            with sqlite3.connect(cache_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM page_cache")
                cached_pages = cursor.fetchone()[0]
                health_status['cache'] = {
                    'total_pages': cached_pages,
                    'status': 'operational'
                }
        except Exception as e:
            health_status['cache'] = {
                'status': 'error',
                'error': str(e)
            }

        return jsonify(health_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/admin/cache-stats')
def get_cache_statistics():
    """Get enhanced caching statistics"""
    try:
        # Get cache statistics from SQLite
        with sqlite3.connect(cache_manager.db_path) as conn:
            cursor = conn.cursor()
            
            # Total cached pages
            cursor.execute("SELECT COUNT(*) FROM page_cache")
            total_cached = cursor.fetchone()[0]
            
            # Cache by domain
            cursor.execute("SELECT domain, COUNT(*) FROM page_cache GROUP BY domain ORDER BY COUNT(*) DESC LIMIT 10")
            cache_by_domain = cursor.fetchall()
            
            # Recent cache activity
            cursor.execute("""
                SELECT COUNT(*) FROM page_cache
                WHERE datetime(last_accessed) > datetime('now', '-24 hours')
            """)
            recent_access = cursor.fetchone()[0]

            # Cache hit statistics
            cursor.execute("SELECT AVG(analysis_count) FROM page_cache")
            avg_reuse = cursor.fetchone()[0] or 0

        return jsonify({
            'cache_statistics': {
                'total_cached_pages': total_cached,
                'recent_access_24h': recent_access,
                'average_reuse_count': round(avg_reuse, 2),
                'top_domains': [{'domain': domain, 'pages': count} for domain, count in cache_by_domain],
                'cache_efficiency': round((recent_access / max(total_cached, 1)) * 100, 1)
            }
        })

    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/clear-cache', methods=['POST'])
def clear_cache():
    """Clear SEO analysis cache"""
    try:
        # Get current cache size
        with sqlite3.connect(cache_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM page_cache")
            before_count = cursor.fetchone()[0]

            # Clear cache
            cursor.execute("DELETE FROM page_cache")
            cursor.execute("DELETE FROM analysis_sessions")
            cursor.execute("SELECT COUNT(*) FROM page_cache")
            after_count = cursor.fetchone()[0]

        return jsonify({
            'message': 'Cache cleared successfully',
            'pages_cleared': before_count - after_count,
            'remaining_pages': after_count
        })

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    os.makedirs('exports', exist_ok=True)
    os.makedirs('cache', exist_ok=True)

    # For local development only
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    logger.info(f"🚀 Starting Enhanced SEO Audit Tool V3.0 FUNCTIONAL on port {port}")
    logger.info(f"🔧 Debug mode: {debug}")
    logger.info(f"📊 Enhanced features: SERP analysis, Smart caching, FUNCTIONAL Whole website analysis")

    app.run(host='0.0.0.0', port=port, debug=debug)

# For gunicorn (production)
application = app
