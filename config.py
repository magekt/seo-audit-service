"""
Configuration settings for Enhanced SEO Audit Tool V3.0
"""

import os
from pathlib import Path

class Config:
    """Enhanced SEO Audit Tool Configuration"""

    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'seo-audit-tool-v3-enhanced-secret-key-change-in-production'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'

    # Application Settings
    APP_NAME = "Enhanced SEO Audit Tool V3.0"
    VERSION = "3.0.0"

    # Analysis Configuration
    max_concurrent_requests = int(os.environ.get('MAX_CONCURRENT_REQUESTS', 5))
    request_timeout = int(os.environ.get('REQUEST_TIMEOUT', 30))
    request_delay = float(os.environ.get('REQUEST_DELAY', 0.5))  # Delay between requests
    max_pages_limit = int(os.environ.get('MAX_PAGES_LIMIT', 100))

    # Whole Website Analysis Settings
    whole_website_max_pages = int(os.environ.get('WHOLE_WEBSITE_MAX_PAGES', 1000))
    whole_website_timeout = int(os.environ.get('WHOLE_WEBSITE_TIMEOUT', 1800))  # 30 minutes

    # Cache Configuration
    cache_enabled = os.environ.get('CACHE_ENABLED', 'true').lower() == 'true'
    cache_max_age_hours = int(os.environ.get('CACHE_MAX_AGE_HOURS', 24))
    cache_cleanup_days = int(os.environ.get('CACHE_CLEANUP_DAYS', 7))

    # SERP Analysis Configuration
    serp_analysis_enabled = os.environ.get('SERP_ANALYSIS_ENABLED', 'true').lower() == 'true'
    serp_max_results = int(os.environ.get('SERP_MAX_RESULTS', 10))

    # Rate Limiting
    rate_limit_requests = int(os.environ.get('RATE_LIMIT_REQUESTS', 10))
    rate_limit_window = int(os.environ.get('RATE_LIMIT_WINDOW', 60))  # minutes

    # File Storage Configuration
    reports_dir = Path(os.environ.get('REPORTS_DIR', 'reports'))
    exports_dir = Path(os.environ.get('EXPORTS_DIR', 'exports'))
    cache_dir = Path(os.environ.get('CACHE_DIR', 'cache'))
    logs_dir = Path(os.environ.get('LOGS_DIR', 'logs'))

    # Database Configuration
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///seo_audit.db')

    # Performance Settings
    connection_pool_size = int(os.environ.get('CONNECTION_POOL_SIZE', 20))
    verify_ssl = os.environ.get('VERIFY_SSL', 'true').lower() == 'true'

    # Security Settings
    allowed_domains = os.environ.get('ALLOWED_DOMAINS', '').split(',') if os.environ.get('ALLOWED_DOMAINS') else []
    blocked_domains = os.environ.get('BLOCKED_DOMAINS', '').split(',') if os.environ.get('BLOCKED_DOMAINS') else []

    # Enhanced Features
    enhanced_reporting = os.environ.get('ENHANCED_REPORTING', 'true').lower() == 'true'
    comprehensive_analysis = os.environ.get('COMPREHENSIVE_ANALYSIS', 'true').lower() == 'true'

    # User Agent Configuration
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]

    # Environment-specific settings
    @property
    def environment(self):
        return self.FLASK_ENV

    @property
    def is_development(self):
        return self.FLASK_ENV == 'development'

    @property
    def is_production(self):
        return self.FLASK_ENV == 'production'

    def __init__(self):
        """Initialize configuration and create necessary directories"""
        self.ensure_directories()

    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.reports_dir,
            self.exports_dir,
            self.cache_dir,
            self.logs_dir,
            Path('static/img'),
            Path('templates')
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_user_agent(self, index=0):
        """Get user agent string"""
        return self.user_agents[index % len(self.user_agents)]

    def is_domain_allowed(self, domain):
        """Check if domain is allowed for analysis"""
        if not self.allowed_domains:
            return True
        return domain in self.allowed_domains

    def is_domain_blocked(self, domain):
        """Check if domain is blocked from analysis"""
        return domain in self.blocked_domains

    def get_analysis_timeout(self, whole_website=False):
        """Get appropriate timeout for analysis type"""
        if whole_website:
            return self.whole_website_timeout
        return self.request_timeout * 10  # 10x request timeout for regular analysis

    def get_max_pages(self, whole_website=False):
        """Get maximum pages for analysis type"""
        if whole_website:
            return self.whole_website_max_pages
        return self.max_pages_limit


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

    # More verbose logging in development
    max_concurrent_requests = 3
    request_delay = 1.0  # Slower for development
    cache_max_age_hours = 1  # Shorter cache for development


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'

    # Optimized for production
    max_concurrent_requests = 5
    request_delay = 0.5
    cache_max_age_hours = 24

    # Security enhancements
    verify_ssl = True
    rate_limit_requests = 5  # Stricter rate limiting


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    FLASK_ENV = 'testing'

    # Minimal settings for testing
    max_concurrent_requests = 2
    max_pages_limit = 5
    cache_enabled = False
    serp_analysis_enabled = False


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration class based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
