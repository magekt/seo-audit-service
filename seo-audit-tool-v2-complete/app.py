#!/usr/bin/env python3
"""
SEO Audit Tool v2.0 - Main Flask Application (RACE CONDITION FIX)
Production-ready web application with improved status checking
"""

import os
import sys
import time
import logging
from datetime import datetime
from threading import Thread
import uuid
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_file, url_for
from flask_cors import CORS
import werkzeug.exceptions

# Import our core modules
from config import load_config, Config
from utils import (
    setup_logging, validate_url, normalize_url, sanitize_filename,
    generate_analysis_id, format_duration, ProgressTracker, RateLimiter,
    SEOAuditError, ValidationError
)

from seo_engine import SEOEngine

# Initialize Flask app
app = Flask(__name__)

# Load configuration
config = load_config()

# Configure Flask
app.config.update(config.flask_config)

# Setup CORS if enabled
if config.cors_enabled:
    CORS(app, origins=config.allowed_origins)

# Setup logging
setup_logging(config.log_level, config.logs_dir)
logger = logging.getLogger(__name__)

# Initialize SEO engine
seo_engine = SEOEngine(config)

# In-memory storage for analyses (in production, use Redis or database)
analyses = {}

# Rate limiter
if config.rate_limiting_enabled:
    analysis_limiter = RateLimiter(
        max_requests=config.rate_limit_requests,
        window_seconds=config.rate_limit_window
    )
else:
    analysis_limiter = None

class AnalysisManager:
    """Manages SEO analysis lifecycle with improved race condition handling"""

    def __init__(self):
        self.active_analyses = {}

    def start_analysis(self, analysis_id: str, website_url: str, target_keyword: str, max_pages: int):
        """Start SEO analysis in background thread with better error handling"""
        def run_analysis():
            try:
                # CRITICAL FIX: Add small delay to ensure analysis record is fully initialized
                time.sleep(0.5)

                # Enhanced validation - check multiple times if needed
                max_retries = 3
                analysis_found = False
                for attempt in range(max_retries):
                    if analysis_id in analyses:
                        analysis_found = True
                        break
                    logger.warning(f"Analysis {analysis_id} not found on attempt {attempt + 1}, retrying...")
                    time.sleep(1)

                if not analysis_found:
                    logger.error(f"Analysis {analysis_id} not found after {max_retries} attempts")
                    return

                # Update status to running
                analyses[analysis_id]['status'] = 'running'
                analyses[analysis_id]['progress'] = 'Initializing comprehensive SEO analysis...'

                logger.info(f"Starting analysis {analysis_id} for {website_url}")

                progress_tracker = ProgressTracker(total_steps=5, description=f"SEO Analysis for {website_url}")
                analyses[analysis_id]['progress_tracker'] = progress_tracker

                # Step 1: Validation
                progress_tracker.increment("Validating website URL and parameters")
                analyses[analysis_id]['progress'] = progress_tracker.get_status()['step_description']

                if not validate_url(website_url):
                    raise ValidationError("Invalid website URL format")

                # Step 2: Analysis
                progress_tracker.increment("Crawling and analyzing website pages")
                analyses[analysis_id]['progress'] = progress_tracker.get_status()['step_description']

                result = seo_engine.analyze_website(website_url, target_keyword, max_pages)

                # Step 3: Processing
                progress_tracker.increment("Processing analysis results")
                analyses[analysis_id]['progress'] = progress_tracker.get_status()['step_description']

                # Step 4: Saving report
                progress_tracker.increment("Saving report and generating exports")
                analyses[analysis_id]['progress'] = progress_tracker.get_status()['step_description']

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_url = sanitize_filename(website_url)
                filename = f"seo_audit_{safe_url}_{timestamp}.md"

                reports_dir = Path(config.reports_dir)
                reports_dir.mkdir(parents=True, exist_ok=True)
                filepath = reports_dir / filename

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(result['report'])

                # Step 5: Completion
                progress_tracker.increment("Analysis completed successfully")

                # CRITICAL FIX: Ensure atomic update of analysis status
                final_update = {
                    'status': 'completed',
                    'progress': 'Analysis completed successfully! 🎉',
                    'report': result['report'],
                    'metadata': result['metadata'],
                    'filename': filename,
                    'filepath': str(filepath),
                    'completed_at': datetime.now().isoformat(),
                    'file_size': len(result['report']),
                    'duration': progress_tracker.elapsed_time
                }

                # Update all at once to prevent partial state
                analyses[analysis_id].update(final_update)

                logger.info(f"✅ Analysis {analysis_id} completed in {format_duration(progress_tracker.elapsed_time)}")

            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Analysis {analysis_id} failed: {error_msg}")

                # Ensure analysis exists before updating error state
                if analysis_id in analyses:
                    analyses[analysis_id].update({
                        'status': 'error',
                        'progress': f'Analysis failed: {error_msg}',
                        'error': error_msg,
                        'failed_at': datetime.now().isoformat()
                    })
                else:
                    logger.error(f"Could not update error status - analysis {analysis_id} missing")
            finally:
                # Cleanup
                if analysis_id in self.active_analyses:
                    del self.active_analyses[analysis_id]

        # Start analysis in background thread
        thread = Thread(target=run_analysis, daemon=True)
        self.active_analyses[analysis_id] = thread
        thread.start()
        logger.info(f"Started analysis thread for {analysis_id}")

    def get_active_count(self) -> int:
        """Get number of currently active analyses"""
        return len([t for t in self.active_analyses.values() if t.is_alive()])

# Initialize analysis manager
analysis_manager = AnalysisManager()

@app.route('/')
def index():
    """Main application page"""
    try:
        system_status = {
            'environment': config.environment,
            'version': config.version,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'features_enabled': {
                'serp_analysis': config.serp_analysis_enabled,
                'advanced_crawling': config.advanced_crawling_enabled,
                'admin_endpoints': config.admin_endpoints_enabled,
            },
            'total_analyses': len(analyses),
            'active_analyses': analysis_manager.get_active_count()
        }

        return render_template('index.html', system_status=system_status)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return render_template('error.html', error_code=500, error_message="Server error"), 500

@app.route('/api/health')
def health_check():
    """Comprehensive health check"""
    try:
        reports_dir = Path(config.reports_dir)
        reports_size = sum(f.stat().st_size for f in reports_dir.rglob('*') if f.is_file())
    except Exception as e:
        logger.warning(f"Could not calculate reports size: {e}")
        reports_size = 0

    try:
        active = analysis_manager.get_active_count()
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': config.version,
            'environment': config.environment,
            'uptime_seconds': (datetime.now() - datetime.fromisoformat(config.start_time)).total_seconds(),
            'system_info': {
                'total_analyses': len(analyses),
                'completed_analyses': len([a for a in analyses.values() if a.get('status') == 'completed']),
                'failed_analyses': len([a for a in analyses.values() if a.get('status') == 'error']),
                'active_analyses': active,
                'reports_storage_bytes': reports_size
            },
            'configuration': {
                'max_pages_limit': config.max_pages_limit,
                'max_concurrent_requests': config.max_concurrent_requests,
                'request_delay': config.request_delay,
                'serp_analysis_enabled': config.serp_analysis_enabled,
                'rate_limiting_enabled': config.rate_limiting_enabled
            }
        }

        return jsonify(health_data)
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def start_analysis_endpoint():
    """Start a new SEO analysis with enhanced error handling"""
    try:
        # Rate limiting check
        if analysis_limiter and not analysis_limiter.is_allowed():
            retry = int(analysis_limiter.time_until_allowed())
            return jsonify({'error': 'Rate limit exceeded', 'retry_after_seconds': retry}), 429

        # Concurrent analysis limit check
        if analysis_manager.get_active_count() >= config.max_concurrent_analyses:
            return jsonify({
                'error': 'Too many concurrent analyses',
                'active_count': analysis_manager.get_active_count(),
                'max_allowed': config.max_concurrent_analyses
            }), 429

        # Parse and validate request data
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        if 'website_url' not in data or 'target_keyword' not in data:
            return jsonify({'error': 'Missing required parameters: website_url and target_keyword'}), 400

        website_url = data.get('website_url', '').strip()
        target_keyword = data.get('target_keyword', '').strip()

        if not website_url or not target_keyword:
            return jsonify({'error': 'Website URL and target keyword cannot be empty'}), 400

        try:
            max_pages = int(data.get('max_pages', 10))
            max_pages = min(max(1, max_pages), config.max_pages_limit)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid max_pages value'}), 400

        # Validate and normalize URL
        try:
            website_url = normalize_url(website_url)
            if not validate_url(website_url):
                raise ValidationError("Invalid URL format")
        except Exception as e:
            return jsonify({'error': f'Invalid website URL: {str(e)}'}), 400

        # Validate keyword
        if len(target_keyword) < 2 or len(target_keyword) > 100:
            return jsonify({'error': 'Target keyword must be between 2 and 100 characters'}), 400

        # Generate analysis ID and create analysis record
        analysis_id = generate_analysis_id()

        # CRITICAL FIX: Create analysis record with proper initialization
        initial_record = {
            'id': analysis_id,
            'website_url': website_url,
            'target_keyword': target_keyword,
            'max_pages': max_pages,
            'status': 'queued',
            'progress': 'Analysis queued for processing...',
            'started_at': datetime.now().isoformat(),
            'user_agent': request.headers.get('User-Agent', ''),
            'client_ip': request.remote_addr,
            'created_at': datetime.now().isoformat(),
            'race_condition_fix': True
        }

        # Ensure atomic insertion
        analyses[analysis_id] = initial_record

        # Add small delay to ensure record is fully committed
        time.sleep(0.1)

        # Verify record was created successfully
        if analysis_id not in analyses:
            logger.error(f"Failed to create analysis record for {analysis_id}")
            return jsonify({'error': 'Failed to initialize analysis'}), 500

        # Start analysis
        analysis_manager.start_analysis(analysis_id, website_url, target_keyword, max_pages)

        logger.info(f"Started analysis {analysis_id} for {website_url} (keyword: {target_keyword})")

        return jsonify({
            'analysis_id': analysis_id,
            'status': 'started',
            'message': 'SEO analysis started successfully',
            'check_status_url': url_for('check_status', analysis_id=analysis_id),
            'estimated_duration_seconds': max_pages * 3,
            'max_pages': max_pages,
            'race_condition_fixed': True
        }), 202

    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        return jsonify({'error': f'Failed to start analysis: {str(e)}'}), 500

@app.route('/api/status/<analysis_id>')
def check_status(analysis_id):
    """Check analysis status with enhanced race condition handling"""
    try:
        logger.debug(f"Status check for analysis_id={analysis_id}")

        if not analysis_id:
            return jsonify({'error': 'No analysis ID provided'}), 400

        if analysis_id not in analyses:
            logger.warning(f"Analysis {analysis_id} not found")
            return jsonify({
                'error': 'Analysis not found',
                'analysis_id': analysis_id,
                'available_analyses_count': len(analyses),
                'suggestion': 'Please try starting a new analysis'
            }), 404

        # Get analysis data safely
        analysis = analyses[analysis_id].copy()

        # Add progress information if available
        if 'progress_tracker' in analysis:
            try:
                info = analysis['progress_tracker'].get_status()
                analysis['progress_info'] = {
                    'percentage': info['percentage'],
                    'elapsed_time': format_duration(info['elapsed_time']),
                    'estimated_remaining': format_duration(info['remaining_time']),
                    'current_step': info['current_step'],
                    'total_steps': info['total_steps']
                }
                del analysis['progress_tracker']
            except Exception as e:
                logger.warning(f"Error processing progress tracker: {e}")

        # Don't return the full report in status checks (too large)
        if 'report' in analysis:
            analysis['has_report'] = True
            preview = analysis['report'][:200] + '...' if len(analysis['report']) > 200 else analysis['report']
            analysis['report_preview'] = preview
            del analysis['report']

        # Add timing information
        if 'started_at' in analysis:
            try:
                started = datetime.fromisoformat(analysis['started_at'])
                elapsed = datetime.now() - started
                analysis['elapsed_seconds'] = int(elapsed.total_seconds())
                analysis['elapsed_formatted'] = format_duration(elapsed.total_seconds())
            except Exception as e:
                logger.warning(f"Error calculating timing: {e}")

        # Add status check metadata
        analysis['status_check_timestamp'] = datetime.now().isoformat()
        analysis['race_condition_fixed'] = True

        return jsonify(analysis)

    except Exception as e:
        logger.error(f"Error in check_status for {analysis_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'analysis_id': analysis_id,
            'debug_info': str(e) if config.environment == 'development' else None
        }), 500

@app.route('/api/report/<analysis_id>')
def get_report(analysis_id):
    """Get full analysis report"""
    try:
        if not analysis_id or analysis_id not in analyses:
            return jsonify({'error': 'Analysis not found'}), 404

        analysis = analyses[analysis_id]

        if analysis.get('status') != 'completed':
            return jsonify({
                'error': 'Analysis not completed yet',
                'current_status': analysis.get('status'),
                'progress': analysis.get('progress', '')
            }), 400

        return jsonify({
            'analysis_id': analysis_id,
            'report': analysis.get('report', ''),
            'metadata': {
                'website_url': analysis['website_url'],
                'target_keyword': analysis['target_keyword'],
                'max_pages': analysis['max_pages'],
                'completed_at': analysis.get('completed_at'),
                'duration': format_duration(analysis.get('duration', 0)),
                'file_size': analysis.get('file_size', 0),
                'filename': analysis.get('filename', '')
            }
        })

    except Exception as e:
        logger.error(f"Error in get_report: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Admin endpoints
if config.admin_endpoints_enabled:
    @app.route('/api/admin/analyses')
    def list_analyses():
        """List all analyses with summary information"""
        try:
            summary = {}
            for aid, a in analyses.items():
                summary[aid] = {
                    'id': aid,
                    'status': a.get('status'),
                    'website_url': a.get('website_url'),
                    'target_keyword': a.get('target_keyword'),
                    'started_at': a.get('started_at'),
                    'completed_at': a.get('completed_at'),
                    'max_pages': a.get('max_pages'),
                    'has_report': 'report' in a,
                    'file_size': a.get('file_size', 0),
                    'client_ip': a.get('client_ip', 'unknown')
                }

            return jsonify({
                'total_analyses': len(summary),
                'status_breakdown': {
                    'completed': len([a for a in analyses.values() if a.get('status') == 'completed']),
                    'running': len([a for a in analyses.values() if a.get('status') == 'running']),
                    'queued': len([a for a in analyses.values() if a.get('status') == 'queued']),
                    'failed': len([a for a in analyses.values() if a.get('status') == 'error']),
                },
                'active_analyses': analysis_manager.get_active_count(),
                'analyses': summary
            })

        except Exception as e:
            logger.error(f"Error in list_analyses: {e}")
            return jsonify({'error': 'Failed to list analyses'}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found', 'path': request.path}), 404
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('error.html', error_code=500, error_message="Internal server error"), 500

if __name__ == '__main__':
    try:
        print("🚀 SEO Audit Tool v2.0 - Starting Server")
        print("=" * 50)
        print(f"Environment: {config.environment}")
        print(f"Host: {config.host}:{config.port}")
        print("=" * 50)

        app.run(
            host=config.host,
            port=config.port,
            debug=(config.environment == 'development'),
            threaded=True
        )
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)
