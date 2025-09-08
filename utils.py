"""
Enhanced SEO Audit Tool - Complete Utility Functions V3.0
Production-ready utility functions with comprehensive validation and all required functions
"""

import re
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse
from typing import Optional, Dict, Any, List
import validators

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis or database)
RATE_LIMIT_STORAGE = {}

def setup_logging():
    """Setup application logging"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/seo_audit.log', encoding='utf-8')
        ]
    )

    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)

def load_config():
    """Load configuration based on environment"""
    from config import get_config
    config_class = get_config()
    return config_class()

def setup_directories():
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

def get_client_ip(request) -> str:
    """Get client IP address from request"""
    # Check for forwarded IP first (behind proxy)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()

    # Check for real IP header
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip

    # Fall back to remote address
    return request.remote_addr or 'unknown'

def rate_limit_check(client_ip: str, limit: int = 10, window_minutes: int = 60) -> bool:
    """
    Check if client has exceeded rate limit
    Returns True if request is allowed, False if rate limited
    """
    now = datetime.now()
    window_start = now - timedelta(minutes=window_minutes)

    # Clean old entries
    if client_ip in RATE_LIMIT_STORAGE:
        RATE_LIMIT_STORAGE[client_ip] = [
            timestamp for timestamp in RATE_LIMIT_STORAGE[client_ip] 
            if timestamp > window_start
        ]
    else:
        RATE_LIMIT_STORAGE[client_ip] = []

    # Check current count
    current_count = len(RATE_LIMIT_STORAGE[client_ip])

    if current_count >= limit:
        return False

    # Add current request
    RATE_LIMIT_STORAGE[client_ip].append(now)
    return True

def format_elapsed_time(seconds: float) -> str:
    """Format elapsed time in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"

def validate_analysis_params(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate analysis parameters from request
    Returns: {'valid': bool, 'message': str, 'data': dict}
    """
    if not isinstance(data, dict):
        return {'valid': False, 'message': 'Invalid data format'}

    # Required fields
    required_fields = ['website_url', 'target_keyword']
    for field in required_fields:
        if field not in data or not data[field]:
            return {'valid': False, 'message': f'Missing required field: {field}'}

    website_url = data['website_url'].strip()
    target_keyword = data['target_keyword'].strip()

    # Validate URL format
    if not website_url.startswith(('http://', 'https://')):
        website_url = 'https://' + website_url
        data['website_url'] = website_url

    # Validate URL using existing function
    if not validate_url(website_url):
        return {'valid': False, 'message': 'Invalid website URL format'}

    # Validate keyword using existing function  
    if not is_valid_keyword(target_keyword):
        return {'valid': False, 'message': 'Invalid target keyword format'}

    # Validate optional numeric fields
    try:
        max_pages = int(data.get('max_pages', 10))
        if max_pages < 1 or max_pages > 1000:  # Using higher limit
            return {'valid': False, 'message': 'max_pages must be between 1 and 1000'}
        data['max_pages'] = max_pages
    except (ValueError, TypeError):
        return {'valid': False, 'message': 'max_pages must be a valid number'}

    # Validate boolean fields
    data['whole_website'] = bool(data.get('whole_website', False))
    data['serp_analysis'] = bool(data.get('serp_analysis', True)) 
    data['use_cache'] = bool(data.get('use_cache', True))

    return {'valid': True, 'message': 'Valid parameters', 'data': data}

def validate_url(url: str) -> bool:
    """
    Enhanced URL validation with comprehensive checks
    """
    if not url or not isinstance(url, str):
        return False

    # Ensure URL has protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Use validators library for basic validation
    if not validators.url(url):
        return False

    # Parse URL for additional checks
    try:
        parsed = urlparse(url)

        # Check for valid domain
        if not parsed.netloc:
            return False

        # Check for suspicious patterns
        suspicious_patterns = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            '192.168.',
            '10.0.',
            '172.'
        ]

        domain = parsed.netloc.lower()
        for pattern in suspicious_patterns:
            if pattern in domain:
                logger.warning(f"Suspicious domain pattern detected: {domain}")
                # Allow localhost for development
                if pattern == 'localhost' and os.getenv('FLASK_ENV') == 'development':
                    continue
                return False

        return True

    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False

def normalize_url(url: str) -> str:
    """
    Normalize URL to standard format
    """
    if not url:
        return url

    url = url.strip()

    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        parsed = urlparse(url)

        # Normalize the URL
        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip('/') if parsed.path != '/' else '/',
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))

        return normalized

    except Exception as e:
        logger.error(f"URL normalization error: {e}")
        return url

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system usage
    """
    if not filename:
        return "unnamed"

    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Remove protocol and www
    sanitized = re.sub(r'^https?://(www\.)?', '', sanitized)

    # Replace dots and other characters
    sanitized = re.sub(r'[./]', '_', sanitized)

    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)

    # Trim and limit length
    sanitized = sanitized.strip('_')[:50]

    # Ensure we have something
    if not sanitized:
        sanitized = "unnamed"

    return sanitized

def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"

def extract_domain(url: str) -> str:
    """
    Extract clean domain from URL
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        return domain
    except:
        return url

def is_valid_keyword(keyword: str) -> bool:
    """
    Validate SEO target keyword
    """
    if not keyword or not isinstance(keyword, str):
        return False

    keyword = keyword.strip()

    # Check length
    if len(keyword) < 2 or len(keyword) > 100:
        return False

    # Check for basic validity (letters, numbers, spaces, hyphens)
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', keyword):
        return False

    return True

def clean_text(text: str) -> str:
    """
    Clean and normalize text content
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())

    # Remove non-printable characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', text)

    return text

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple text similarity (Jaccard similarity)
    """
    if not text1 or not text2:
        return 0.0

    # Convert to lowercase and split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))

    if union == 0:
        return 0.0

    return intersection / union

def ensure_directory(directory: str) -> bool:
    """
    Ensure directory exists, create if necessary
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        return False

def safe_write_file(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    Safely write content to file with error handling
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(filepath)
        if directory:
            ensure_directory(directory)

        # Write file
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)

        return True

    except Exception as e:
        logger.error(f"Failed to write file {filepath}: {e}")
        return False

def get_file_extension(content_type: str) -> str:
    """
    Get appropriate file extension from content type
    """
    content_type_map = {
        'text/html': '.html',
        'text/css': '.css',
        'application/javascript': '.js',
        'application/json': '.json',
        'text/xml': '.xml',
        'application/xml': '.xml',
        'text/plain': '.txt',
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/svg+xml': '.svg'
    }

    return content_type_map.get(content_type.lower(), '.txt')

def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to specified length with suffix
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix

def parse_robots_txt(content: str) -> Dict[str, Any]:
    """
    Parse robots.txt content and extract useful information
    """
    result = {
        'sitemaps': [],
        'crawl_delay': None,
        'disallowed_paths': [],
        'allowed_paths': []
    }

    if not content:
        return result

    current_user_agent = None

    for line in content.splitlines():
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue

        # Parse directives
        if ':' in line:
            directive, value = line.split(':', 1)
            directive = directive.strip().lower()
            value = value.strip()

            if directive == 'user-agent':
                current_user_agent = value
            elif directive == 'sitemap':
                result['sitemaps'].append(value)
            elif directive == 'crawl-delay':
                try:
                    result['crawl_delay'] = float(value)
                except ValueError:
                    pass
            elif directive == 'disallow' and value:
                result['disallowed_paths'].append(value)
            elif directive == 'allow' and value:
                result['allowed_paths'].append(value)

    return result

def is_crawlable_url(url: str, robots_data: Dict[str, Any]) -> bool:
    """
    Check if URL is crawlable based on robots.txt data
    """
    if not robots_data or not url:
        return True

    parsed = urlparse(url)
    path = parsed.path

    # Check disallowed paths
    for disallowed in robots_data.get('disallowed_paths', []):
        if path.startswith(disallowed):
            return False

    # Check explicitly allowed paths
    for allowed in robots_data.get('allowed_paths', []):
        if path.startswith(allowed):
            return True

    return True

def extract_meta_info(html_content: str) -> Dict[str, str]:
    """
    Extract basic meta information from HTML content
    """
    meta_info = {}

    if not html_content:
        return meta_info

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            meta_info['title'] = clean_text(title_tag.get_text())

        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            meta_info['description'] = clean_text(meta_desc.get('content', ''))

        # Extract meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            meta_info['keywords'] = clean_text(meta_keywords.get('content', ''))

        # Extract canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical:
            meta_info['canonical'] = canonical.get('href', '')

        # Extract language
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            meta_info['language'] = html_tag.get('lang')

    except Exception as e:
        logger.warning(f"Error extracting meta info: {e}")

    return meta_info

def generate_report_filename(url: str, timestamp: str = None) -> str:
    """
    Generate a safe filename for SEO report
    """
    if not timestamp:
        timestamp = time.strftime("%Y%m%d_%H%M%S")

    safe_url = sanitize_filename(url)
    return f"seo_audit_{safe_url}_{timestamp}.md"

def validate_analysis_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize analysis configuration
    """
    validated = {}

    # Website URL (required)
    if 'website_url' in config:
        url = config['website_url']
        if validate_url(url):
            validated['website_url'] = normalize_url(url)
        else:
            raise ValueError("Invalid website URL")
    else:
        raise ValueError("Website URL is required")

    # Target keyword (required)
    if 'target_keyword' in config:
        keyword = config['target_keyword']
        if is_valid_keyword(keyword):
            validated['target_keyword'] = clean_text(keyword)
        else:
            raise ValueError("Invalid target keyword")
    else:
        raise ValueError("Target keyword is required")

    # Max pages (optional, with limits)
    max_pages = config.get('max_pages', 10)
    try:
        max_pages = int(max_pages)
        if max_pages < 1:
            max_pages = 1
        elif max_pages > 1000:  # Increased limit
            max_pages = 1000
        validated['max_pages'] = max_pages
    except (ValueError, TypeError):
        validated['max_pages'] = 10

    # Whole website flag
    validated['whole_website'] = bool(config.get('whole_website', False))

    # SERP analysis flag
    validated['serp_analysis'] = bool(config.get('serp_analysis', True))

    # Use cache flag
    validated['use_cache'] = bool(config.get('use_cache', True))

    return validated

# Cache cleanup function
def cleanup_old_files(directory: str, days: int = 7):
    """Clean up old files from specified directory"""
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return

        cutoff_time = time.time() - (days * 24 * 60 * 60)

        for file_path in dir_path.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    logger.info(f"Cleaned up old file: {file_path}")
                except Exception as e:
                    logger.warning(f"Error cleaning up {file_path}: {e}")

    except Exception as e:
        logger.error(f"Error in cleanup_old_files: {e}")

# Enhanced error reporting
def create_error_response(error_message: str, status_code: int = 500) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        'error': True,
        'message': error_message,
        'status_code': status_code,
        'timestamp': datetime.now().isoformat(),
        'suggestions': [
            'Check your internet connection',
            'Verify the website URL is correct',
            'Try again in a few minutes',
            'Contact support if the issue persists'
        ]
    }

# Health check utilities
def check_system_health() -> Dict[str, Any]:
    """Perform system health checks"""
    health_status = {
        'status': 'healthy',
        'checks': {},
        'timestamp': datetime.now().isoformat()
    }

    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage('.')
        health_status['checks']['disk_space'] = {
            'status': 'healthy' if free > 1024*1024*1024 else 'warning',  # 1GB free
            'free_gb': free / (1024**3),
            'total_gb': total / (1024**3)
        }
    except Exception as e:
        health_status['checks']['disk_space'] = {'status': 'error', 'error': str(e)}

    # Check directories
    required_dirs = ['logs', 'reports', 'exports', 'cache']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        health_status['checks'][f'{dir_name}_dir'] = {
            'status': 'healthy' if dir_path.exists() else 'error',
            'exists': dir_path.exists()
        }

    return health_status

# Data export utilities  
def safe_json_serialize(obj):
    """Safely serialize objects to JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)

# Error handling utilities
class SEOAnalysisError(Exception):
    """Custom exception for SEO analysis errors"""
    pass

class URLValidationError(SEOAnalysisError):
    """Exception for URL validation errors"""
    pass

class CrawlingError(SEOAnalysisError):
    """Exception for crawling errors"""
    pass

class AnalysisConfigError(SEOAnalysisError):
    """Exception for configuration errors"""
    pass
