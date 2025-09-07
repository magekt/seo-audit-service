"""
Configuration Management for SEO Audit Tool
Handles loading and validation of configuration settings
"""

import os
import yaml
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path
import datetime

@dataclass
class Config:
    """Configuration class for SEO Audit Tool"""
    
    # Application Settings
    environment: str = "development"
    version: str = "2.0.0"
    secret_key: str = "change-this-in-production"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 10000
    
    # API Keys
    google_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None
    serp_api_key: Optional[str] = None
    
    # Feature Flags
    serp_analysis_enabled: bool = False
    advanced_crawling_enabled: bool = True
    admin_endpoints_enabled: bool = True
    caching_enabled: bool = True
    rate_limiting_enabled: bool = False
    
    # Crawling Configuration
    max_pages_limit: int = 987
    max_concurrent_requests: int = 3
    request_delay: float = 1.5
    request_timeout: int = 30
    respect_robots_txt: bool = True
    
    # Analysis Configuration
    min_word_count: int = 300
    max_title_length: int = 60
    min_title_length: int = 30
    max_meta_description_length: int = 160
    min_meta_description_length: int = 120
    
    # Directory Configuration
    reports_dir: str = "reports"
    exports_dir: str = "exports"
    logs_dir: str = "logs"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_to_file: bool = True
    log_rotation_size: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    # Performance Configuration
    cache_ttl: int = 3600
    max_concurrent_analyses: int = 5
    max_report_size: int = 10485760  # 10MB
    worker_timeout: int = 300
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    # Security Configuration
    allowed_origins: str = "*"
    cors_enabled: bool = True
    trusted_proxies: List[str] = field(default_factory=lambda: ["127.0.0.1", "::1"])
    
    # Custom User Agents
    custom_user_agents: List[str] = field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ])
    
    # Runtime tracking
    start_time: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    @property
    def flask_config(self) -> Dict[str, Any]:
        """Flask-specific configuration"""
        return {
            'SECRET_KEY': self.secret_key,
            'DEBUG': self.environment == 'development',
            'TESTING': self.environment == 'testing',
            'PREFERRED_URL_SCHEME': 'https' if self.environment == 'production' else 'http',
            'MAX_CONTENT_LENGTH': self.max_report_size,
            'JSON_SORT_KEYS': False,
            'JSONIFY_PRETTYPRINT_REGULAR': self.environment == 'development'
        }
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings/errors"""
        warnings = []
        
        # Security checks
        if self.secret_key == "change-this-in-production" and self.environment == 'production':
            warnings.append("WARNING: Using default SECRET_KEY in production environment")
        
        if len(self.secret_key) < 16:
            warnings.append("WARNING: SECRET_KEY should be at least 16 characters long")
        
        # Performance checks
        if self.max_concurrent_requests > 10:
            warnings.append("WARNING: High concurrent requests may impact target websites")
        
        if self.request_delay < 1.0:
            warnings.append("WARNING: Low request delay may be considered aggressive crawling")
        
        # Directory checks
        for directory in [self.reports_dir, self.exports_dir, self.logs_dir]:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # API key validation
        if self.serp_analysis_enabled and not (self.google_api_key and self.google_cse_id):
            warnings.append("WARNING: SERP analysis enabled but Google API keys not configured")
        
        return warnings

def load_config(config_file: str = None) -> Config:
    """Load configuration from environment variables and config file"""
    # Start with default configuration
    config = Config()
    
    # Load from environment variables first
    _load_from_env(config)
    
    # Load from YAML config file if provided
    if config_file and Path(config_file).exists():
        _load_from_yaml(config, config_file)
    elif Path("config.yaml").exists():
        _load_from_yaml(config, "config.yaml")
    
    # Validate configuration
    warnings = config.validate()
    if warnings:
        print("Configuration warnings:")
        for warning in warnings:
            print(f"  {warning}")
    
    return config

def _load_from_env(config: Config) -> None:
    """Load configuration from environment variables"""
    # Application Settings
    config.environment = os.getenv('FLASK_ENV', config.environment)
    config.version = os.getenv('APP_VERSION', config.version)
    config.secret_key = os.getenv('SECRET_KEY', config.secret_key)
    
    # Server Configuration
    config.host = os.getenv('HOST', config.host)
    config.port = int(os.getenv('PORT', str(config.port)))
    
    # API Keys
    config.google_api_key = os.getenv('GOOGLE_API_KEY')
    config.google_cse_id = os.getenv('GOOGLE_CSE_ID')
    config.serp_api_key = os.getenv('SERP_API_KEY')
    
    # Feature Flags
    config.serp_analysis_enabled = _env_bool('SERP_ANALYSIS_ENABLED', config.serp_analysis_enabled)
    config.advanced_crawling_enabled = _env_bool('ADVANCED_CRAWLING_ENABLED', config.advanced_crawling_enabled)
    config.admin_endpoints_enabled = _env_bool('ADMIN_ENDPOINTS_ENABLED', config.admin_endpoints_enabled)
    config.caching_enabled = _env_bool('CACHING_ENABLED', config.caching_enabled)
    config.rate_limiting_enabled = _env_bool('RATE_LIMITING_ENABLED', config.rate_limiting_enabled)
    
    # Crawling Configuration
    config.max_pages_limit = int(os.getenv('MAX_PAGES_LIMIT', str(config.max_pages_limit)))
    config.max_concurrent_requests = int(os.getenv('MAX_CONCURRENT_REQUESTS', str(config.max_concurrent_requests)))
    config.request_delay = float(os.getenv('REQUEST_DELAY', str(config.request_delay)))
    config.request_timeout = int(os.getenv('REQUEST_TIMEOUT', str(config.request_timeout)))
    config.respect_robots_txt = _env_bool('RESPECT_ROBOTS_TXT', config.respect_robots_txt)
    
    # Analysis Configuration
    config.min_word_count = int(os.getenv('MIN_WORD_COUNT', str(config.min_word_count)))
    config.max_title_length = int(os.getenv('MAX_TITLE_LENGTH', str(config.max_title_length)))
    config.min_title_length = int(os.getenv('MIN_TITLE_LENGTH', str(config.min_title_length)))
    config.max_meta_description_length = int(os.getenv('MAX_META_DESCRIPTION_LENGTH', str(config.max_meta_description_length)))
    config.min_meta_description_length = int(os.getenv('MIN_META_DESCRIPTION_LENGTH', str(config.min_meta_description_length)))
    
    # Directory Configuration
    config.reports_dir = os.getenv('REPORTS_DIR', config.reports_dir)
    config.exports_dir = os.getenv('EXPORTS_DIR', config.exports_dir)
    config.logs_dir = os.getenv('LOGS_DIR', config.logs_dir)
    
    # Logging Configuration
    config.log_level = os.getenv('LOG_LEVEL', config.log_level)
    config.log_to_file = _env_bool('LOG_TO_FILE', config.log_to_file)
    config.log_rotation_size = int(os.getenv('LOG_ROTATION_SIZE', str(config.log_rotation_size)))
    config.log_backup_count = int(os.getenv('LOG_BACKUP_COUNT', str(config.log_backup_count)))
    
    # Performance Configuration
    config.cache_ttl = int(os.getenv('CACHE_TTL', str(config.cache_ttl)))
    config.max_concurrent_analyses = int(os.getenv('MAX_CONCURRENT_ANALYSES', str(config.max_concurrent_analyses)))
    config.max_report_size = int(os.getenv('MAX_REPORT_SIZE', str(config.max_report_size)))
    config.worker_timeout = int(os.getenv('WORKER_TIMEOUT', str(config.worker_timeout)))
    
    # Rate Limiting
    config.rate_limit_requests = int(os.getenv('RATE_LIMIT_REQUESTS', str(config.rate_limit_requests)))
    config.rate_limit_window = int(os.getenv('RATE_LIMIT_WINDOW', str(config.rate_limit_window)))
    
    # Security Configuration
    config.allowed_origins = os.getenv('ALLOWED_ORIGINS', config.allowed_origins)
    config.cors_enabled = _env_bool('CORS_ENABLED', config.cors_enabled)
    
    trusted_proxies_env = os.getenv('TRUSTED_PROXIES')
    if trusted_proxies_env:
        config.trusted_proxies = [ip.strip() for ip in trusted_proxies_env.split(',')]
    
    # Custom User Agents
    custom_agents_env = os.getenv('CUSTOM_USER_AGENTS')
    if custom_agents_env:
        config.custom_user_agents = [ua.strip() for ua in custom_agents_env.split(',')]

def _load_from_yaml(config: Config, config_file: str) -> None:
    """Load configuration from YAML file"""
    try:
        with open(config_file, 'r') as f:
            yaml_config = yaml.safe_load(f) or {}
        
        # Update config from YAML
        for key, value in yaml_config.items():
            if hasattr(config, key):
                setattr(config, key, value)
                
    except Exception as e:
        print(f"Warning: Could not load config file {config_file}: {e}")

def _env_bool(key: str, default: bool) -> bool:
    """Convert environment variable to boolean"""
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on', 'enabled')

def save_config_template(output_file: str = "config.yaml") -> None:
    """Save a configuration template file"""
    template = {
        'environment': 'development',
        'version': '2.0.0',
        'secret_key': 'change-this-in-production',
        'host': '0.0.0.0',
        'port': 1000,
        
        # API Keys (optional)
        'google_api_key': None,
        'google_cse_id': None,
        'serp_api_key': None,
        
        # Feature Flags
        'serp_analysis_enabled': False,
        'advanced_crawling_enabled': True,
        'admin_endpoints_enabled': True,
        'caching_enabled': True,
        'rate_limiting_enabled': False,
        
        # Crawling Configuration
        'max_pages_limit': 987,
        'max_concurrent_requests': 3,
        'request_delay': 1.5,
        'request_timeout': 30,
        'respect_robots_txt': True,
        
        # Analysis Configuration
        'min_word_count': 300,
        'max_title_length': 60,
        'min_title_length': 30,
        'max_meta_description_length': 160,
        'min_meta_description_length': 120,
        
        # Directory Configuration
        'reports_dir': 'reports',
        'exports_dir': 'exports',
        'logs_dir': 'logs',
        
        # Logging Configuration
        'log_level': 'INFO',
        'log_to_file': True,
        'log_rotation_size': 10485760,
        'log_backup_count': 5,
        
        # Performance Configuration
        'cache_ttl': 3600,
        'max_concurrent_analyses': 5,
        'max_report_size': 10485760,
        'worker_timeout': 300,
        
        # Rate Limiting
        'rate_limit_requests': 100,
        'rate_limit_window': 3600,
        
        # Security Configuration
        'allowed_origins': '*',
        'cors_enabled': True,
        'trusted_proxies': ['127.0.0.1', '::1'],
        
        # Custom User Agents
        'custom_user_agents': [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
    }
    
    try:
        with open(output_file, 'w') as f:
            yaml.dump(template, f, default_flow_style=False, indent=2)
        print(f"Configuration template saved to {output_file}")
    except Exception as e:
        print(f"Error saving configuration template: {e}")

# Configuration validation functions
def validate_google_api_config(api_key: str, cse_id: str) -> bool:
    """Validate Google API configuration"""
    if not api_key or not api_key.startswith('AIza'):
        return False
    if not cse_id:
        return False
    return True

def validate_directories(config: Config) -> bool:
    """Ensure all required directories exist"""
    try:
        for directory in [config.reports_dir, config.exports_dir, config.logs_dir]:
            Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Failed to create directories: {e}")
        return False

def get_effective_config() -> Dict[str, Any]:
    """Get the current effective configuration (for debugging)"""
    config = load_config()
    
    # Remove sensitive information
    safe_config = {}
    for key, value in config.__dict__.items():
        if 'key' in key.lower() or 'secret' in key.lower():
            safe_config[key] = '***' if value else None
        else:
            safe_config[key] = value
    
    return safe_config

if __name__ == "__main__":
    # CLI for configuration management
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "template":
            output_file = sys.argv[2] if len(sys.argv) > 2 else "config.yaml"
            save_config_template(output_file)
        elif sys.argv[1] == "validate":
            config = load_config()
            warnings = config.validate()
            if warnings:
                print("Configuration issues found:")
                for warning in warnings:
                    print(f"  {warning}")
            else:
                print("Configuration is valid!")
        elif sys.argv[1] == "show":
            config_dict = get_effective_config()
            for key, value in sorted(config_dict.items()):
                print(f"{key}: {value}")
        else:
            print("Usage:")
            print("  python config.py template [file] - Generate configuration template")
            print("  python config.py validate - Validate current configuration")
            print("  python config.py show - Show effective configuration")
