import os
import json
import sqlite3
import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
import time
from concurrent.futures import ThreadPoolExecutor
import threading

from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.exceptions import BadRequest, NotFound
import pandas as pd

# FIXED IMPORTS - Using correct class names and functions
from seo_engine import EnhancedSEOEngine  # Fixed: was EnhancedSEOAnalyzer
from utils import (
    sanitize_filename, validate_url, setup_directories,
    format_elapsed_time, get_client_ip, rate_limit_check,
    setup_logging, load_config, validate_analysis_params
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'seo-audit-secret-key-change-in-production')

# Load configuration - Fixed to handle the actual config structure
try:
    config_obj = load_config()
    # Convert config object to dictionary for easier access
    config = {
        'max_concurrent_requests': getattr(config_obj, 'max_concurrent_requests', 5),
        'request_timeout': getattr(config_obj, 'request_timeout', 30),
        'cache_enabled': getattr(config_obj, 'cache_enabled', True),
        'serp_analysis_enabled': getattr(config_obj, 'serp_analysis_enabled', True),
        'rate_limit_requests': getattr(config_obj, 'rate_limit_requests', 10),
        'rate_limit_window': getattr(config_obj, 'rate_limit_window', 60),
        'max_pages_limit': getattr(config_obj, 'max_pages_limit', 50),
        'whole_website_max_pages': getattr(config_obj, 'whole_website_max_pages', 500),
    }
except Exception as e:
    # Fallback configuration if loading fails
    config = {
        'max_concurrent_requests': 5,
        'request_timeout': 30,
        'cache_enabled': True,
        'serp_analysis_enabled': True,
        'rate_limit_requests': 10,
        'rate_limit_window': 60,
        'max_pages_limit': 50,
        'whole_website_max_pages': 500,
    }

setup_logging()
logger = logging.getLogger(__name__)

# Create necessary directories
setup_directories()

# Initialize database
def init_db():
    """Initialize SQLite database for analysis tracking and caching"""
    try:
        os.makedirs('cache', exist_ok=True)
        conn = sqlite3.connect('cache/seo_analysis.db')
        cursor = conn.cursor()

        # Analysis tracking table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_sessions (
            id TEXT PRIMARY KEY,
            website_url TEXT NOT NULL,
            target_keyword TEXT,
            analysis_type TEXT NOT NULL,
            status TEXT DEFAULT 'running',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            client_ip TEXT,
            result_data TEXT,
            csv_file_path TEXT,
            error_message TEXT,
            pages_analyzed INTEGER DEFAULT 0,
            total_pages INTEGER DEFAULT 0,
            enhanced_features TEXT
        )
        """)

        # Cache table for individual page data
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS page_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            url_hash TEXT UNIQUE NOT NULL,
            analysis_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 1
        )
        """)

        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_url ON analysis_sessions(website_url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_status ON analysis_sessions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_hash ON page_cache(url_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_created ON page_cache(created_at)')

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

# Global variables for analysis management
active_analyses = {}
analysis_lock = threading.Lock()

# FIXED: Replace deprecated @app.before_first_request with @app.before_request
@app.before_request
def initialize_once():
    """Initialize application before first request - FIXED deprecated decorator"""
    # Only initialize once
    if not hasattr(initialize_once, 'initialized'):
        init_db()
        initialize_once.initialized = True

@app.route('/')
def index():
    """Main application page"""
    try:
        # Get recent analyses for the current session
        recent_analyses = get_recent_analyses(limit=5)
        return render_template('index.html', recent_analyses=recent_analyses)
    except Exception as e:
        logger.error(f"Error loading index page: {str(e)}")
        return render_template('index.html', recent_analyses=[])

def get_recent_analyses(limit=10):
    """Get recent analyses from database"""
    try:
        conn = sqlite3.connect('cache/seo_analysis.db')
        cursor = conn.cursor()

        cursor.execute("""
        SELECT id, website_url, target_keyword, analysis_type, status, 
               created_at, completed_at, pages_analyzed, total_pages
        FROM analysis_sessions 
        WHERE status = 'completed'
        ORDER BY created_at DESC 
        LIMIT ?
        """, (limit,))

        analyses = []
        for row in cursor.fetchall():
            analysis = {
                'id': row[0],
                'website_url': row[1],
                'target_keyword': row[2],
                'analysis_type': row[3],
                'status': row[4],
                'created_at': row[5],
                'completed_at': row[6],
                'pages_analyzed': row[7],
                'total_pages': row[8]
            }
            analyses.append(analysis)

        conn.close()
        return analyses
    except Exception as e:
        logger.error(f"Error getting recent analyses: {str(e)}")
        return []

@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    """Start SEO analysis"""
    try:
        # Rate limiting check
        client_ip = get_client_ip(request)
        if not rate_limit_check(client_ip, limit=config.get('rate_limit_requests', 10)):
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': 'Please wait before starting another analysis'
            }), 429

        # Get and validate request data
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")

        # Validate parameters
        validation_result = validate_analysis_params(data)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['message']}), 400

        website_url = data['website_url']
        target_keyword = data.get('target_keyword', '')
        max_pages = int(data.get('max_pages', 10))
        whole_website = data.get('whole_website', False)
        serp_analysis = data.get('serp_analysis', True)
        use_cache = data.get('use_cache', True)

        # Check if analysis already exists and is running
        with analysis_lock:
            analysis_id = str(uuid.uuid4())

            # Store analysis info
            conn = sqlite3.connect('cache/seo_analysis.db')
            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO analysis_sessions 
            (id, website_url, target_keyword, analysis_type, client_ip, total_pages)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                analysis_id, website_url, target_keyword,
                'whole_website' if whole_website else 'selective',
                client_ip, max_pages
            ))
            conn.commit()
            conn.close()

            # Start analysis in background
            analysis_config = {
                'analysis_id': analysis_id,
                'website_url': website_url,
                'target_keyword': target_keyword,
                'max_pages': max_pages,
                'whole_website': whole_website,
                'serp_analysis': serp_analysis,
                'use_cache': use_cache,
                'client_ip': client_ip
            }

            active_analyses[analysis_id] = {
                'status': 'running',
                'progress': 0,
                'message': 'Starting analysis...',
                'created_at': datetime.now(),
                'config': analysis_config
            }

            # Start analysis in background thread
            executor = ThreadPoolExecutor(max_workers=1)
            executor.submit(run_analysis_background, analysis_config)

            return jsonify({
                'analysis_id': analysis_id,
                'status': 'started',
                'message': 'Analysis started successfully',
                'check_status_url': f'/api/status/{analysis_id}',
                'analysis_type': 'whole_website' if whole_website else 'selective',
                'enhanced_features': True,
                'caching_enabled': use_cache
            })

    except Exception as e:
        logger.error(f"Error starting analysis: {str(e)}")
        return jsonify({
            'error': 'Analysis failed to start',
            'message': str(e)
        }), 500

def run_analysis_background(analysis_config):
    """Run analysis in background thread - FIXED all method calls"""
    analysis_id = analysis_config['analysis_id']

    try:
        logger.info(f"Starting background analysis {analysis_id}")

        # Update status
        active_analyses[analysis_id]['status'] = 'running'
        active_analyses[analysis_id]['message'] = 'Initializing analyzer...'

        # FIXED: Initialize the correct analyzer with proper parameters
        analyzer = EnhancedSEOEngine(config_obj)  # Use the config object

        # Run analysis - FIXED: Use the correct method names and parameters
        active_analyses[analysis_id]['message'] = 'Running analysis...'

        # FIXED: Call the correct analyze_website method with proper parameters
        results = analyzer.analyze_website(
            website_url=analysis_config['website_url'],
            target_keyword=analysis_config['target_keyword'],
            max_pages=analysis_config['max_pages'],
            whole_website=analysis_config['whole_website'],
            force_fresh=not analysis_config['use_cache']
        )

        # FIXED: Handle the results structure properly
        if isinstance(results, dict) and 'pages_data' in results:
            pages_data = results['pages_data']
            report_data = results.get('report', '')
            metadata = results.get('metadata', {})
        else:
            # Fallback for different result structure
            pages_data = results if isinstance(results, list) else []
            report_data = ''
            metadata = {}

        # Generate CSV export - FIXED: Handle the proper data structure
        active_analyses[analysis_id]['message'] = 'Generating reports...'
        csv_path = generate_csv_report_fixed(pages_data, analysis_id)

        # Update database with results
        conn = sqlite3.connect('cache/seo_analysis.db')
        cursor = conn.cursor()

        # FIXED: Store results properly
        result_data = {
            'pages': [page.__dict__ if hasattr(page, '__dict__') else page for page in pages_data],
            'report': report_data,
            'metadata': metadata,
            'analysis_type': 'whole_website' if analysis_config['whole_website'] else 'selective'
        }

        cursor.execute("""
        UPDATE analysis_sessions 
        SET status = 'completed', completed_at = CURRENT_TIMESTAMP, 
            result_data = ?, csv_file_path = ?, pages_analyzed = ?
        WHERE id = ?
        """, (
            json.dumps(result_data, default=str),
            csv_path,
            len(pages_data),
            analysis_id
        ))
        conn.commit()
        conn.close()

        # Update active analysis
        active_analyses[analysis_id].update({
            'status': 'completed',
            'progress': 100,
            'message': 'Analysis completed successfully',
            'completed_at': datetime.now(),
            'results': result_data,
            'csv_path': csv_path
        })

        logger.info(f"Analysis {analysis_id} completed successfully")

    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {str(e)}")

        # Update database with error
        conn = sqlite3.connect('cache/seo_analysis.db')
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE analysis_sessions 
        SET status = 'failed', error_message = ?
        WHERE id = ?
        """, (str(e), analysis_id))
        conn.commit()
        conn.close()

        # Update active analysis
        active_analyses[analysis_id].update({
            'status': 'failed',
            'message': f'Analysis failed: {str(e)}',
            'error': str(e)
        })

def generate_csv_report_fixed(pages_data, analysis_id):
    """Generate CSV report from analysis results - FIXED to handle actual data structure"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"seo_comprehensive_analysis_{timestamp}.csv"
        filepath = os.path.join('exports', filename)

        # Ensure exports directory exists
        os.makedirs('exports', exist_ok=True)

        # FIXED: Handle the actual SEOPageData structure
        csv_data = []
        for page in pages_data:
            try:
                # Handle both object and dictionary formats
                if hasattr(page, '__dict__'):
                    # Object format (SEOPageData)
                    row = {
                        'URL': getattr(page, 'url', ''),
                        'Title': getattr(page, 'title', ''),
                        'Meta_Description': getattr(page, 'meta_description', ''),
                        'H1_Count': len(getattr(page, 'h1_tags', [])),
                        'Status_Code': getattr(page, 'status_code', ''),
                        'Word_Count': getattr(page, 'word_count', 0),
                        'Load_Time': getattr(page, 'load_time', 0),
                        'SEO_Issues_Count': len(getattr(page, 'seo_issues', [])),
                        'Keyword_Density': getattr(page, 'keyword_density', 0),
                        'Internal_Links': len(getattr(page, 'internal_links', [])),
                        'External_Links': len(getattr(page, 'external_links', [])),
                        'Images_Count': len(getattr(page, 'images', [])),
                        'Mobile_Friendly': getattr(page, 'mobile_friendly', False),
                        'HTTPS_Enabled': getattr(page, 'ssl_enabled', False),
                        'All_Issues': '; '.join(getattr(page, 'seo_issues', []))
                    }
                else:
                    # Dictionary format
                    row = {
                        'URL': page.get('url', ''),
                        'Title': page.get('title', ''),
                        'Meta_Description': page.get('meta_description', ''),
                        'H1_Count': len(page.get('h1_tags', [])),
                        'Status_Code': page.get('status_code', ''),
                        'Word_Count': page.get('word_count', 0),
                        'Load_Time': page.get('load_time', 0),
                        'SEO_Issues_Count': len(page.get('seo_issues', [])),
                        'Keyword_Density': page.get('keyword_density', 0),
                        'Internal_Links': len(page.get('internal_links', [])),
                        'External_Links': len(page.get('external_links', [])),
                        'Images_Count': len(page.get('images', [])),
                        'Mobile_Friendly': page.get('mobile_friendly', False),
                        'HTTPS_Enabled': page.get('ssl_enabled', False),
                        'All_Issues': '; '.join(page.get('seo_issues', []))
                    }
                csv_data.append(row)
            except Exception as e:
                logger.warning(f"Error processing page data for CSV: {e}")
                continue

        # Create DataFrame and save CSV
        if csv_data:
            df = pd.DataFrame(csv_data)
            df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"CSV report generated: {filepath}")
            return filepath
        else:
            logger.warning("No data to export to CSV")
            return None

    except Exception as e:
        logger.error(f"Error generating CSV report: {str(e)}")
        return None

@app.route('/api/status/<analysis_id>')
def get_analysis_status(analysis_id):
    """Get analysis status - FIXED route parameter"""
    try:
        # Check active analyses first
        if analysis_id in active_analyses:
            analysis = active_analyses[analysis_id]
            elapsed = datetime.now() - analysis['created_at']

            return jsonify({
                'analysis_id': analysis_id,
                'status': analysis['status'],
                'progress': analysis.get('progress', 0),
                'message': analysis.get('message', ''),
                'elapsed_seconds': int(elapsed.total_seconds()),
                'elapsed_formatted': format_elapsed_time(elapsed.total_seconds()),
                'created_at': analysis['created_at'].isoformat(),
                'analysis_type': analysis['config'].get('analysis_type', 'selective'),
                'client_ip': analysis['config'].get('client_ip', ''),
                'pages_analyzed': analysis.get('pages_analyzed', 0)
            })

        # Check database for completed analyses
        conn = sqlite3.connect('cache/seo_analysis.db')
        cursor = conn.cursor()

        cursor.execute("""
        SELECT status, created_at, completed_at, pages_analyzed, 
               total_pages, analysis_type, client_ip, error_message
        FROM analysis_sessions WHERE id = ?
        """, (analysis_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Analysis not found'}), 404

        created_at = datetime.fromisoformat(row[1])
        completed_at = datetime.fromisoformat(row[2]) if row[2] else None
        elapsed = (completed_at or datetime.now()) - created_at

        return jsonify({
            'analysis_id': analysis_id,
            'status': row[0],
            'pages_analyzed': row[3] or 0,
            'total_pages': row[4] or 0,
            'analysis_type': row[5],
            'client_ip': row[6],
            'created_at': row[1],
            'completed_at': row[2],
            'elapsed_seconds': int(elapsed.total_seconds()),
            'elapsed_formatted': format_elapsed_time(elapsed.total_seconds()),
            'error_message': row[7]
        })

    except Exception as e:
        logger.error(f"Error getting analysis status: {str(e)}")
        return jsonify({'error': 'Failed to get analysis status'}), 500

@app.route('/api/report/<analysis_id>')
def get_analysis_report(analysis_id):
    """Get analysis report - FIXED route parameter"""
    try:
        # Check active analyses first
        if analysis_id in active_analyses and 'results' in active_analyses[analysis_id]:
            results = active_analyses[analysis_id]['results']
            return jsonify({
                'analysis_id': analysis_id,
                'status': 'completed',
                'results': results,
                'generated_at': active_analyses[analysis_id]['completed_at'].isoformat(),
                'enhanced_features': True,
                'file_info': {
                    'csv_available': bool(active_analyses[analysis_id].get('csv_path')),
                    'csv_path': active_analyses[analysis_id].get('csv_path')
                }
            })

        # Check database
        conn = sqlite3.connect('cache/seo_analysis.db')
        cursor = conn.cursor()

        cursor.execute("""
        SELECT result_data, completed_at, csv_file_path, status 
        FROM analysis_sessions WHERE id = ?
        """, (analysis_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Analysis not found'}), 404

        if row[3] != 'completed':
            return jsonify({'error': 'Analysis not completed yet'}), 400

        results = json.loads(row[0]) if row[0] else {}

        return jsonify({
            'analysis_id': analysis_id,
            'status': 'completed',
            'results': results,
            'generated_at': row[1],
            'enhanced_features': True,
            'file_info': {
                'csv_available': bool(row[2]),
                'csv_path': row[2]
            },
            'metadata': {
                'total_pages': len(results.get('pages', [])),
                'analysis_type': results.get('analysis_type', 'unknown')
            }
        })

    except Exception as e:
        logger.error(f"Error getting analysis report: {str(e)}")
        return jsonify({'error': 'Failed to get analysis report'}), 500

@app.route('/api/recent-analyses')
def get_recent_analyses_api():
    """Get recent analyses via API"""
    try:
        limit = request.args.get('limit', 10, type=int)
        recent = get_recent_analyses(limit)
        return jsonify({'analyses': recent})
    except Exception as e:
        logger.error(f"Error getting recent analyses: {str(e)}")
        return jsonify({'error': 'Failed to get recent analyses'}), 500

@app.route('/api/cancel/<analysis_id>', methods=['POST'])
def cancel_analysis(analysis_id):
    """Cancel running analysis - FIXED route parameter"""
    try:
        if analysis_id in active_analyses:
            active_analyses[analysis_id]['status'] = 'cancelled'
            active_analyses[analysis_id]['message'] = 'Analysis cancelled by user'

            # Update database
            conn = sqlite3.connect('cache/seo_analysis.db')
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE analysis_sessions 
            SET status = 'cancelled' 
            WHERE id = ?
            """, (analysis_id,))
            conn.commit()
            conn.close()

            return jsonify({'message': 'Analysis cancelled successfully'})
        else:
            return jsonify({'error': 'Analysis not found or already completed'}), 404

    except Exception as e:
        logger.error(f"Error cancelling analysis: {str(e)}")
        return jsonify({'error': 'Failed to cancel analysis'}), 500

@app.route('/api/download-csv/<analysis_id>')
def download_csv(analysis_id):
    """Download CSV report - FIXED route parameter"""
    try:
        # Check active analyses first
        if analysis_id in active_analyses and 'csv_path' in active_analyses[analysis_id]:
            csv_path = active_analyses[analysis_id]['csv_path']
            if csv_path and os.path.exists(csv_path):
                return send_file(csv_path, as_attachment=True)

        # Check database
        conn = sqlite3.connect('cache/seo_analysis.db')
        cursor = conn.cursor()
        cursor.execute('SELECT csv_file_path FROM analysis_sessions WHERE id = ?', (analysis_id,))
        row = cursor.fetchone()
        conn.close()

        if row and row[0] and os.path.exists(row[0]):
            return send_file(row[0], as_attachment=True)
        else:
            return jsonify({'error': 'CSV file not found'}), 404

    except Exception as e:
        logger.error(f"Error downloading CSV: {str(e)}")
        return jsonify({'error': 'Failed to download CSV'}), 500

@app.route('/api/health')
def health_check():
    """System health check"""
    try:
        # Check database connection
        conn = sqlite3.connect('cache/seo_analysis.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM analysis_sessions')
        total_analyses = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM page_cache')
        cached_pages = cursor.fetchone()[0]
        conn.close()

        # Check active analyses
        active_count = len([a for a in active_analyses.values() if a['status'] == 'running'])

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'statistics': {
                'total_analyses': total_analyses,
                'cached_pages': cached_pages,
                'active_analyses': active_count,
                'config': {
                    'max_concurrent_requests': config.get('max_concurrent_requests', 5),
                    'cache_enabled': config.get('cache_enabled', True),
                    'serp_analysis_enabled': config.get('serp_analysis_enabled', True)
                }
            }
        })

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# FIXED: Ensure proper Flask app object for Gunicorn
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'

    logger.info(f"Starting Enhanced SEO Audit Tool v3.0 on port {port}")
    logger.info(f"Debug mode: {debug}")

    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)

# Ensure the app object is available for Gunicorn
application = app  # FIXED: Added for compatibility
