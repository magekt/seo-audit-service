"""
Utility Functions for SEO Audit Tool
Common helper functions, validation, and utilities
"""

import os
import re
import time
import uuid
import logging
import hashlib
from urllib.parse import urlparse
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
# import validators  # temporarily disabled
from logging.handlers import RotatingFileHandler

class AnalysisTimer:
    """Context manager for timing operations"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        logging.info(f"Starting {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type is None:
            logging.info(f"Completed {self.name} in {duration:.2f} seconds")
        else:
            logging.error(f"Failed {self.name} after {duration:.2f} seconds: {exc_val}")

def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> None:
    """Setup logging configuration with file rotation"""
    # Create logs directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Configure logging level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file = Path(log_dir) / "seo_audit.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Error-specific handler
    error_log_file = Path(log_dir) / "seo_audit_errors.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)

def validate_url(url: str) -> bool:
    """Validate if URL is properly formatted and represents a real URL"""
    if not url:
        return False

    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Simple URL validation using urlparse
    try:
        parsed = urlparse(url)

        if not (parsed.netloc and parsed.scheme in ('http', 'https')):
            return False

        # Additional validation for the netloc (domain)
        netloc = parsed.netloc.lower()

        # Must contain at least one dot (for domain.tld format)
        # But allow localhost and IP addresses as special cases
        if netloc not in ['localhost'] and not netloc.replace('.', '').isdigit():
            if '.' not in netloc:
                return False

            # Check that it has a reasonable TLD (at least 2 chars after last dot)
            parts = netloc.split('.')
            if len(parts) < 2:
                return False

            # Check TLD length (should be at least 2 characters)
            tld = parts[-1]
            if len(tld) < 2:
                return False

            # Check that domain parts don't contain invalid characters
            for part in parts:
                if not part:  # Empty part (like "example..com")
                    return False
                # Should only contain letters, numbers, and hyphens
                if not all(c.isalnum() or c == '-' for c in part):
                    return False
                # Shouldn't start or end with hyphen
                if part.startswith('-') or part.endswith('-'):
                    return False

        return True

    except Exception:
        return False
def normalize_url(url: str) -> str:
    """Normalize URL format"""
    if not url:
        return url
    
    # Clean the URL first (remove extra whitespace and handle edge cases)
    url = url.strip()
    
    # Remove any duplicate protocols
    if url.count('://') > 1:
        # Find the last occurrence of :// and use that
        parts = url.split('://')
        url = parts[0] + '://' + '://'.join(parts[1:])
    
    # Add protocol if missing
    # Add protocol if missing - check case insensitively!
    url_lower = url.lower()
    if not url_lower.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Parse and reconstruct
    try:
        parsed = urlparse(url)
        # Ensure we have a valid netloc
        if not parsed.netloc:
            return url
            
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # Remove trailing slash unless it's the root
        if normalized.endswith('/') and len(parsed.path) > 1:
            normalized = normalized[:-1]
        
        return normalized
    except Exception:
        # If parsing fails, return the cleaned URL
        return url

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return ""

def is_internal_url(url: str, base_domain: str) -> bool:
    """Check if URL belongs to the same domain"""
    try:
        url_domain = extract_domain(url)
        return url_domain == base_domain or url_domain.endswith(f".{base_domain}")
    except Exception:
        return False

def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    return text

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text with ellipsis if too long"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def get_file_info(filepath: str) -> Dict[str, Any]:
    """Get comprehensive file information"""
    try:
        path = Path(filepath)
        if not path.exists():
            return {'exists': False}
        
        stat = path.stat()
        return {
            'exists': True,
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'extension': path.suffix,
            'name': path.name,
            'stem': path.stem,
            'hash': generate_file_hash(filepath)
        }
    except Exception as e:
        logging.error(f"Error getting file info for {filepath}: {e}")
        return {'exists': False, 'error': str(e)}

def ensure_directory(directory: str) -> bool:
    """Ensure directory exists, create if it doesn't"""
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Failed to create directory {directory}: {e}")
        return False

def safe_filename_from_url(url: str) -> str:
    """Generate safe filename from URL"""
    # Extract domain and path
    parsed = urlparse(url)
    domain = parsed.netloc.replace('.', '_')
    path = parsed.path.strip('/').replace('/', '_')
    
    # Create filename
    if path:
        filename = f"{domain}_{path}"
    else:
        filename = domain
    
    # Sanitize
    filename = sanitize_filename(filename)
    
    # Add timestamp to ensure uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{filename}_{timestamp}"

class RateLimiter:
    """Simple rate limiter for API requests"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    def is_allowed(self) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        
        # Remove old requests outside the window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.window_seconds]
        
        # Check if under limit
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    def time_until_allowed(self) -> float:
        """Time in seconds until next request is allowed"""
        if not self.requests:
            return 0.0
        
        oldest_request = min(self.requests)
        return self.window_seconds - (time.time() - oldest_request)

class ProgressTracker:
    """Track progress of long-running operations"""
    
    def __init__(self, total_steps: int, description: str = "Processing"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = time.time()
        self.step_descriptions = {}
    
    def update(self, step: int, step_description: str = ""):
        """Update progress"""
        self.current_step = min(step, self.total_steps)
        if step_description:
            self.step_descriptions[step] = step_description
    
    def increment(self, step_description: str = ""):
        """Increment progress by one step"""
        self.update(self.current_step + 1, step_description)
    
    @property
    def percentage(self) -> float:
        """Get completion percentage"""
        return (self.current_step / self.total_steps) * 100 if self.total_steps > 0 else 0
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time
    
    @property
    def estimated_total_time(self) -> float:
        """Estimate total time based on current progress"""
        if self.current_step == 0:
            return 0
        return self.elapsed_time * (self.total_steps / self.current_step)
    
    @property
    def remaining_time(self) -> float:
        """Estimate remaining time"""
        return max(0, self.estimated_total_time - self.elapsed_time)
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status"""
        return {
            'description': self.description,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'percentage': round(self.percentage, 1),
            'elapsed_time': self.elapsed_time,
            'estimated_total_time': self.estimated_total_time,
            'remaining_time': self.remaining_time,
            'step_description': self.step_descriptions.get(self.current_step, ""),
            'is_complete': self.current_step >= self.total_steps
        }

def validate_keyword(keyword: str) -> bool:
    """Validate SEO target keyword"""
    if not keyword or not keyword.strip():
        return False
    
    # Check length
    if len(keyword.strip()) < 2:
        return False
    if len(keyword.strip()) > 100:
        return False
    
    # Check for valid characters (allow letters, numbers, spaces, basic punctuation)
    if not re.match(r'^[a-zA-Z0-9\s\-\'".,!?]+$', keyword):
        return False
    
    return True

def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Extract potential keywords from text"""
    if not text:
        return []
    
    # Clean text and convert to lowercase
    text = clean_text(text.lower())
    
    # Split into words
    words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + r',}\b', text)
    
    # Common stop words to filter out
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'about', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further',
        'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
        'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will',
        'just', 'should', 'now', 'are', 'was', 'were', 'been', 'have', 'has',
        'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should', 'may',
        'might', 'must', 'can', 'could', 'this', 'that', 'these', 'those'
    }
    
    # Filter stop words and return unique keywords
    keywords = [word for word in words if word not in stop_words]
    return list(set(keywords))

def calculate_text_readability(text: str) -> Dict[str, float]:
    """Calculate text readability metrics"""
    if not text:
        return {'flesch_score': 0.0, 'grade_level': 0.0}
    
    # Count sentences, words, and syllables
    sentences = len(re.findall(r'[.!?]+', text))
    words = len(text.split())
    
    # Simple syllable counting
    syllables = 0
    for word in text.split():
        word = word.lower().strip('.,!?";')
        syllable_count = len(re.findall(r'[aeiouAEIOU]', word))
        if word.endswith('e'):
            syllable_count -= 1
        syllables += max(1, syllable_count)
    
    if sentences == 0 or words == 0:
        return {'flesch_score': 0.0, 'grade_level': 0.0}
    
    # Flesch Reading Ease Score
    flesch_score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
    flesch_score = max(0, min(100, flesch_score))
    
    # Approximate grade level
    grade_level = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
    grade_level = max(0, grade_level)
    
    return {
        'flesch_score': round(flesch_score, 1),
        'grade_level': round(grade_level, 1),
        'sentences': sentences,
        'words': words,
        'syllables': syllables
    }

def get_system_info() -> Dict[str, Any]:
    """Get system information for debugging"""
    import sys
    import platform
    
    return {
        'python_version': sys.version,
        'platform': platform.platform(),
        'processor': platform.processor(),
        'architecture': platform.architecture(),
        'hostname': platform.node(),
        'username': os.getenv('USER', os.getenv('USERNAME', 'unknown')),
        'cwd': os.getcwd(),
        'pid': os.getpid()
    }

# Custom exception classes
class SEOAuditError(Exception):
    """Base exception for SEO Audit Tool"""
    pass

class CrawlingError(SEOAuditError):
    """Exception raised during web crawling"""
    pass

class AnalysisError(SEOAuditError):
    """Exception raised during SEO analysis"""
    pass

class ConfigurationError(SEOAuditError):
    """Exception raised for configuration issues"""
    pass

class ValidationError(SEOAuditError):
    """Exception raised for validation failures"""
    pass

# Debugging utilities
def debug_request(request_data: Dict[str, Any]) -> None:
    """Log request data for debugging"""
    logging.debug(f"Request data: {request_data}")

def debug_response(response_data: Dict[str, Any]) -> None:
    """Log response data for debugging"""
    logging.debug(f"Response data: {response_data}")

if __name__ == "__main__":
    # Test utilities
    print("Testing utility functions...")
    
    # Test URL validation
    test_urls = [
        "https://example.com",
        "http://test.com/path",
        "invalid-url",
        "example.com",
        ""
    ]
    
    for url in test_urls:
        valid = validate_url(url)
        normalized = normalize_url(url) if valid else "N/A"
        print(f"URL: {url:20} Valid: {valid:5} Normalized: {normalized}")
    
    # Test filename sanitization
    test_filenames = [
        "normal-filename.txt",
        "file with spaces.txt",
        "file<>with|bad*chars?.txt",
        "very_long_filename_that_exceeds_normal_limits_and_should_be_truncated.txt"
    ]
    
    for filename in test_filenames:
        sanitized = sanitize_filename(filename)
        print(f"Original: {filename}")
        print(f"Sanitized: {sanitized}")
        print()
    
    # Test readability calculation
    test_text = "This is a simple test sentence. It contains basic words and should be easy to read. The readability score should reflect this simplicity."
    readability = calculate_text_readability(test_text)
    print(f"Text: {test_text}")
    print(f"Readability: {readability}")
    
    print("\nUtility tests completed!")

def normalize_keyword(keyword: str) -> str:
    """Normalize keyword for analysis"""
    if not keyword:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = keyword.lower().strip()
    
    # Remove extra spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized

def calculate_keyword_density(text: str, keyword: str) -> float:
    """Calculate keyword density in text"""
    if not text or not keyword:
        return 0.0
    
    # Clean and normalize text and keyword
    text_clean = clean_text(text.lower())
    keyword_clean = normalize_keyword(keyword.lower())
    
    if not text_clean or not keyword_clean:
        return 0.0
    
    # Count words and keyword occurrences
    words = text_clean.split()
    total_words = len(words)
    
    if total_words == 0:
        return 0.0
    
    # Count keyword occurrences
    keyword_count = text_clean.count(keyword_clean)
    
    # Calculate density as percentage
    density = (keyword_count / total_words) * 100
    
    return round(density, 2)

def extract_readability_metrics(text: str) -> Dict[str, float]:
    """Extract comprehensive readability metrics from text"""
    if not text or not text.strip():
        return {
            'flesch_score': 0.0,
            'grade_level': 0.0,
            'sentences': 0,
            'words': 0,
            'syllables': 0,
            'avg_sentence_length': 0.0,
            'avg_syllables_per_word': 0.0
        }
    
    # Count sentences using regex
    sentences = len(re.findall(r'[.!?]+', text))
    if sentences == 0:
        sentences = 1  # Avoid division by zero
    
    # Count words
    words = len(text.split())
    if words == 0:
        return {
            'flesch_score': 0.0,
            'grade_level': 0.0,
            'sentences': sentences,
            'words': 0,
            'syllables': 0,
            'avg_sentence_length': 0.0,
            'avg_syllables_per_word': 0.0
        }
    
    # Count syllables
    syllables = 0
    for word in text.split():
        syllables += count_syllables(word)
    
    # Calculate averages
    avg_sentence_length = words / sentences
    avg_syllables_per_word = syllables / words if words > 0 else 0
    
    # Calculate Flesch Reading Ease Score
    # Formula: 206.835 - (1.015 × ASL) - (84.6 × ASW)
    # where ASL = average sentence length, ASW = average syllables per word
    flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    flesch_score = max(0, min(100, flesch_score))  # Clamp between 0-100
    
    # Calculate approximate grade level using Flesch-Kincaid formula
    # Formula: (0.39 × ASL) + (11.8 × ASW) - 15.59
    grade_level = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
    grade_level = max(0, grade_level)  # Don't allow negative grade levels
    
    return {
        'flesch_score': round(flesch_score, 1),
        'grade_level': round(grade_level, 1),
        'sentences': sentences,
        'words': words,
        'syllables': syllables,
        'avg_sentence_length': round(avg_sentence_length, 1),
        'avg_syllables_per_word': round(avg_syllables_per_word, 2)
    }

def count_syllables(word: str) -> int:
    """Count syllables in a word using vowel pattern matching"""
    if not word:
        return 0
    
    word = word.lower().strip()
    
    # Remove non-alphabetic characters
    word = re.sub(r'[^a-z]', '', word)
    
    if not word:
        return 0
    
    # Count vowel groups
    vowels = 'aeiouy'
    syllable_count = 0
    prev_was_vowel = False
    
    for char in word:
        if char in vowels:
            if not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = True
        else:
            prev_was_vowel = False
    
    # Handle silent 'e' at the end
    if word.endswith('e') and syllable_count > 1:
        syllable_count -= 1
    
    # Every word has at least one syllable
    return max(1, syllable_count)

def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename for safe file system usage - Updated version"""
    if not filename:
        return "default"
    
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\|?*]', '_', filename)
    filename = re.sub(r'\s+', '_', filename.strip())
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    
    # Ensure reasonable length
    if len(filename) > max_length:
        filename = filename[:max_length]
    
    # Ensure it's not empty
    if not filename:
        filename = "default"
    
    return filename

def format_duration(duration: float) -> str:
    """Format duration to hours, minutes, and seconds"""
    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
def generate_analysis_id() -> str:
    """Generate unique analysis ID"""
    # Create a unique ID using timestamp and random component
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_component = str(uuid.uuid4())[:8]
    return f"analysis_{timestamp}_{random_component}"

def format_file_size(bytes_value: int) -> str:
    """Format file size in human readable format"""
    if bytes_value == 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(bytes_value)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"

def generate_file_hash(filepath: str) -> str:
    """Generate MD5 hash of file for integrity checking"""
    try:
        import hashlib
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return "unknown"
