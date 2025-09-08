"""
Enhanced SEO Audit Tool - Utility Functions V3.0
Production-ready utility functions with comprehensive validation
"""

import re
import os
import time
from urllib.parse import urlparse, urlunparse
from pathlib import Path
from typing import Optional, Dict, Any
import validators
import logging

logger = logging.getLogger(__name__)

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
        elif max_pages > 100:
            max_pages = 100
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
