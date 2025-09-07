#!/usr/bin/env python3
"""
Enhanced SEO Audit Tool V3.0 - Application Entry Point
Production-ready launcher with enhanced configuration
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the Flask application
from app import app

def setup_production_logging():
    """Setup production-ready logging"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler('logs/seo_audit_tool.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def setup_directories():
    """Ensure all required directories exist"""
    directories = ['logs', 'reports', 'exports', 'cache', 'static/img']

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Directory ensured: {directory}")

def main():
    """Main application entry point"""
    print("🚀 Enhanced SEO Audit Tool V3.0")
    print("=" * 50)

    # Setup
    setup_production_logging()
    setup_directories()

    # Configuration
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'

    # Start info
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Enhanced SEO Audit Tool V3.0")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")

    print(f"🌐 Server starting on http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"📊 Enhanced features: SERP analysis, Smart caching, Whole website analysis")
    print("=" * 50)

    # Run application
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        print("\n👋 Enhanced SEO Audit Tool stopped")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
