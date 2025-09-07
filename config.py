"""
Enhanced SEO Audit Tool - Configuration Settings V3.0
"""

import os
from dataclasses import dataclass, field
from typing import List

@dataclass
class Config:
    """Enhanced configuration class with all settings"""
    
    # Basic settings
    environment: str = os.getenv('FLASK_ENV', 'production')
    secret_key: str = os.getenv('SECRET_KEY', 'enhanced-seo-audit-tool-v3-secret-key-change-in-production')
    
    # Enhanced SEO Engine settings
    max_concurrent_requests: int = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
    request_timeout: int = int(os.getenv('REQUEST_TIMEOUT', '30'))
    request_delay: float = float(os.getenv('REQUEST_DELAY', '1.0'))
    max_pages_limit: int = int(os.getenv('MAX_PAGES_LIMIT', '50'))
    
    # Enhanced caching settings
    cache_enabled: bool = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    cache_max_age_hours: int = int(os.getenv('CACHE_MAX_AGE_HOURS', '24'))
    cache_cleanup_days: int = int(os.getenv('CACHE_CLEANUP_DAYS', '7'))
    
    # SERP analysis settings
    serp_analysis_enabled: bool = os.getenv('SERP_ANALYSIS_ENABLED', 'true').lower() == 'true'
    serp_max_results: int = int(os.getenv('SERP_MAX_RESULTS', '10'))
    
    # Rate limiting
    rate_limit_requests: int = int(os.getenv('RATE_LIMIT_REQUESTS', '10'))
    rate_limit_window: int = int(os.getenv('RATE_LIMIT_WINDOW', '60'))
    
    # File paths
    reports_dir: str = os.getenv('REPORTS_DIR', 'reports')
    exports_dir: str = os.getenv('EXPORTS_DIR', 'exports')
    cache_dir: str = os.getenv('CACHE_DIR', 'cache')
    logs_dir: str = os.getenv('LOGS_DIR', 'logs')
    
    # Enhanced features
    whole_website_max_pages: int = int(os.getenv('WHOLE_WEBSITE_MAX_PAGES', '1000'))
    enhanced_reporting: bool = os.getenv('ENHANCED_REPORTING', 'true').lower() == 'true'
    csv_export_enabled: bool = os.getenv('CSV_EXPORT_ENABLED', 'true').lower() == 'true'
    
    # Database settings (for future use)
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///cache/seo_audit.db')
    
    # Security settings - FIXED WITH default_factory
    allowed_domains: List[str] = field(default_factory=lambda: os.getenv('ALLOWED_DOMAINS', '').split(',') if os.getenv('ALLOWED_DOMAINS') else [])
    blocked_domains: List[str] = field(default_factory=lambda: os.getenv('BLOCKED_DOMAINS', '').split(',') if os.getenv('BLOCKED_DOMAINS') else [])
    
    # Advanced settings
    user_agent: str = os.getenv('USER_AGENT', 'Enhanced-SEO-Audit-Tool/3.0')
    max_redirects: int = int(os.getenv('MAX_REDIRECTS', '5'))
    verify_ssl: bool = os.getenv('VERIFY_SSL', 'true').lower() == 'true'
    
    # Performance settings
    connection_pool_size: int = int(os.getenv('CONNECTION_POOL_SIZE', '20'))
    connection_timeout: int = int(os.getenv('CONNECTION_TIMEOUT', '10'))
    read_timeout: int = int(os.getenv('READ_TIMEOUT', '30'))

    def __post_init__(self):
        """Post-initialization validation and setup"""
        # Ensure directories exist
        import os
        for directory in [self.reports_dir, self.exports_dir, self.cache_dir, self.logs_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Validate settings
        if self.max_concurrent_requests > 20:
            self.max_concurrent_requests = 20
            
        if self.request_timeout > 120:
            self.request_timeout = 120
            
        if self.max_pages_limit > 100:
            self.max_pages_limit = 100
