"""
Enhanced SEO Audit Tool - Utility Functions V3.0
"""

import re
import time
import validators
from urllib.parse import urlparse, urlunparse
from typing import Optional, Dict, Any

def validate_url(url: str) -> bool:
    """Enhanced URL validation"""
    try:
        if not url or not isinstance(url, str):
            return False

        # Basic validation
        if not validators.url(url):
            return False

        parsed = urlparse(url)

        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False

        # Only allow http and https
        if parsed.scheme not in ['http', 'https']:
            return False

        # Block localhost and private IPs in production
        if parsed.netloc.startswith(('localhost', '127.', '10.', '192.168.', '172.')):
            return False

        return True

    except Exception:
        return False

def normalize_url(url: str) -> str:
    """Normalize URL format"""
    try:
        url = url.strip()

        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        parsed = urlparse(url)

        # Rebuild URL with normalized components
        return urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))

    except Exception:
        return url

def sanitize_filename(text: str, max_length: int = 50) -> str:
    """Sanitize text for use as filename"""
    # Remove or replace invalid characters
    text = re.sub(r'[<>:"/\\|?*]', '_', text)  # FIXED: Added 'r' for raw string
    text = re.sub(r'[^\w\-_\.]', '_', text)     # FIXED: Added 'r' for raw string
    text = re.sub(r'_+', '_', text)
    text = text.strip('_')
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length].rstrip('_')
        
    return text or 'untitled'

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def format_file_size(bytes_size: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""

def is_valid_keyword(keyword: str) -> bool:
    """Validate target keyword"""
    if not keyword or not isinstance(keyword, str):
        return False
        
    keyword = keyword.strip()
    
    # Check length
    if len(keyword) < 2 or len(keyword) > 100:
        return False
        
    # Check for valid characters (allow letters, numbers, spaces, hyphens)
    if not re.match(r'^[a-zA-Z0-9\s\-\_\.]+$', keyword):  # FIXED: Added 'r' for raw string
        return False
        
    return True

def calculate_seo_score(issues: list) -> float:
    """Calculate SEO score based on issues"""
    base_score = 100.0

    for issue in issues:
        if 'CRITICAL' in issue:
            base_score -= 20
        elif 'HIGH' in issue:
            base_score -= 10
        elif 'MEDIUM' in issue:
            base_score -= 5
        elif 'LOW' in issue:
            base_score -= 2

    return max(0.0, min(100.0, base_score))

def get_status_emoji(score: float) -> str:
    """Get emoji based on score"""
    if score >= 80:
        return "🟢"
    elif score >= 60:
        return "🟡"
    elif score >= 40:
        return "🟠"
    else:
        return "🔴"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if not text or len(text) <= max_length:
        return text

    return text[:max_length-3] + "..."

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON with fallback"""
    try:
        import json
        return json.loads(json_str)
    except Exception:
        return default

def rate_limit_key(ip: str, endpoint: str = None) -> str:
    """Generate rate limit key"""
    if endpoint:
        return f"rate_limit:{ip}:{endpoint}"
    return f"rate_limit:{ip}"

class Timer:
    """Context manager for timing operations"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.end_time = time.time()

    @property
    def elapsed(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def __str__(self):
        return format_duration(self.elapsed)

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying failed operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator

def chunk_list(lst: list, chunk_size: int):
    """Split list into chunks"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def merge_dicts(*dicts) -> dict:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result

def clean_html_text(text: str) -> str:
    """Clean and normalize HTML text content"""
    if not text:
        return ""
        
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)  # Already correct with 'r'
    text = text.strip()
    
    # Remove non-printable characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # Already correct with 'r'
    
    return text

def extract_numbers(text: str) -> list:
    """Extract all numbers from text"""
    return [float(match) for match in re.findall(r'\d+\.?\d*', text)]  # Already correct with 'r'

def is_mobile_user_agent(user_agent: str) -> bool:
    """Check if user agent is mobile"""
    if not user_agent:
        return False

    mobile_patterns = [
        'Mobile', 'Android', 'iPhone', 'iPad', 'iPod',
        'BlackBerry', 'Windows Phone', 'webOS'
    ]

    return any(pattern in user_agent for pattern in mobile_patterns)
