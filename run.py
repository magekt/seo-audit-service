#!/usr/bin/env python3
"""
Enhanced SEO Audit Tool V3.0 - Application Runner
Production-ready startup script with enhanced configuration
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, logger
from config import get_config

def create_directories():
    """Create necessary directories for the application"""
    directories = [
        'logs',
        'reports', 
        'exports',
        'cache',
        'static/css',
        'static/js',
        'static/img',
        'templates'
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Directory ensured: {directory}")

def main():
    """Main application runner"""

    # Create necessary directories
    create_directories()

    # Get configuration
    config_class = get_config()
    config_instance = config_class()

    # Configure Flask app
    app.config.from_object(config_instance)

    # Determine host and port
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = config_instance.is_development

    # Print startup information
    logger.info("=" * 60)
    logger.info("🚀 Enhanced SEO Audit Tool V3.0 FUNCTIONAL")
    logger.info("=" * 60)
    logger.info(f"🌐 Environment: {config_instance.environment}")
    logger.info(f"🏠 Host: {host}")
    logger.info(f"🔌 Port: {port}")
    logger.info(f"🐛 Debug mode: {debug}")
    logger.info(f"📊 Enhanced features: SERP analysis, Smart caching, Whole website analysis")
    logger.info(f"⚡ Max concurrent requests: {config_instance.max_concurrent_requests}")
    logger.info(f"💾 Cache enabled: {config_instance.cache_enabled}")
    logger.info(f"🎯 Rate limiting: {config_instance.rate_limit_requests} requests per {config_instance.rate_limit_window} minutes")
    logger.info("=" * 60)

    if config_instance.is_development:
        logger.info("🔧 Development mode - Enhanced logging and debugging enabled")
        logger.info(f"🌍 Access the application at: http://localhost:{port}")
    else:
        logger.info("🚀 Production mode - Optimized for performance")

    logger.info("=" * 60)

    try:
        # Start the Flask development server
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=debug
        )
    except KeyboardInterrupt:
        logger.info("\n🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
