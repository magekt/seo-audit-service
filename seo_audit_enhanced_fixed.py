
import requests
import time
import json
import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import re
from collections import Counter, defaultdict
import csv
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Set, Tuple
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from pathlib import Path
import yaml
from functools import wraps
import hashlib
import pickle
import os
from tqdm import tqdm
import pandas as pd

# Configure logging for Colab
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SEOIssue:
    """Data class representing an SEO issue found during audit."""
    category: str
    priority: str
    page: str
    issue: str
    recommendation: str
    impact: str
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class AuditConfig:
    """Configuration settings for SEO audit."""
    max_pages: int = 50
    max_concurrent_requests: int = 5
    request_delay: float = 1.0
    timeout: int = 30
    respect_robots_txt: bool = True
    max_retries: int = 3
    backoff_factor: float = 0.3
    cache_enabled: bool = True
    cache_duration: int = 3600  # 1 hour
    user_agents: List[str] = None

    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ]

class RequestCache:
    """Simple file-based cache for HTTP requests."""

    def __init__(self, cache_dir: str = ".seo_cache", duration: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.duration = duration

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL."""
        return hashlib.md5(url.encode()).hexdigest()

    def get(self, url: str) -> Optional[Dict]:
        """Retrieve cached response if available and not expired."""
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)

            # Check if cache is expired
            if datetime.now() - cached_data['timestamp'] > timedelta(seconds=self.duration):
                cache_file.unlink()  # Remove expired cache
                return None

            return cached_data['response']
        except Exception as e:
            logger.warning(f"Error reading cache for {url}: {e}")
            return None

    def set(self, url: str, response_data: Dict):
        """Cache response data."""
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            cached_data = {
                'timestamp': datetime.now(),
                'response': response_data
            }

            with open(cache_file, 'wb') as f:
                pickle.dump(cached_data, f)
        except Exception as e:
            logger.warning(f"Error caching {url}: {e}")

def retry_on_failure(max_retries: int = 3, backoff_factor: float = 0.3):
    """Decorator to retry function calls on failure with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = backoff_factor * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {wait_time:.2f}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")

            raise last_exception
        return wrapper
    return decorator

class ZenSERPManager:
    """Enhanced ZenSERP API manager with better error handling and rate limiting."""

    def __init__(self, api_key: str, max_requests: int = 50, config: AuditConfig = None):
        self.api_key = api_key
        self.base_url = 'https://app.zenserp.com/api/v2/search'
        self.request_count = 0
        self.max_requests = max_requests
        self.config = config or AuditConfig()
        self.cache = RequestCache() if self.config.cache_enabled else None
        self.rate_limiter = threading.Semaphore(1)

    def check_remaining_quota(self) -> Dict[str, int]:
        """Check remaining API quota."""
        return {
            'used': self.request_count,
            'remaining': self.max_requests - self.request_count,
            'total': self.max_requests
        }

    @retry_on_failure(max_retries=3, backoff_factor=0.5)
    def search_serp(self, keyword: str, location: str = 'United States', 
                    search_engine: str = 'google.com') -> Dict[str, Any]:
        """Search SERP with enhanced error handling and caching."""
        if self.request_count >= self.max_requests:
            raise Exception(f"API quota exceeded ({self.max_requests} requests)")

        # Check cache first
        cache_key = f"{keyword}_{location}_{search_engine}"
        if self.cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"Using cached SERP data for: {keyword}")
                return cached_result

        with self.rate_limiter:
            headers = {'apikey': self.api_key}
            params = {
                'q': keyword,
                'location': location,
                'search_engine': search_engine,
                'hl': 'en',
                'gl': 'US'
            }

            try:
                response = requests.get(
                    self.base_url, 
                    headers=headers, 
                    params=params, 
                    timeout=self.config.timeout
                )
                response.raise_for_status()

                self.request_count += 1
                result = response.json()

                # Cache the result
                if self.cache:
                    self.cache.set(cache_key, result)

                logger.info(f"SERP API call successful for: {keyword}")
                return result

            except requests.exceptions.RequestException as e:
                logger.error(f"SERP API request failed for {keyword}: {str(e)}")
                raise Exception(f"SERP API request failed: {str(e)}")

class WebsiteCrawler:
    """Enhanced website crawler with concurrent processing and better error handling."""

    def __init__(self, base_url: str, config: AuditConfig = None):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.config = config or AuditConfig()
        self.crawled_urls: Set[str] = set()
        self.sitemap: List[Dict[str, Any]] = []
        self.session = requests.Session()
        self.cache = RequestCache() if self.config.cache_enabled else None

    def _get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        return random.choice(self.config.user_agents)

    @retry_on_failure(max_retries=2)
    def get_page_content(self, url: str) -> Optional[Tuple[BeautifulSoup, Dict[str, Any]]]:
        """Get page content with performance metrics and caching."""
        # Check cache first
        if self.cache:
            cached_result = self.cache.get(url)
            if cached_result:
                return cached_result['soup'], cached_result['metrics']

        try:
            headers = {'User-Agent': self._get_random_user_agent()}

            start_time = time.time()
            response = self.session.get(url, headers=headers, timeout=self.config.timeout)
            response.raise_for_status()
            load_time = time.time() - start_time

            soup = BeautifulSoup(response.content, 'html.parser')

            metrics = {
                'load_time': load_time,
                'status_code': response.status_code,
                'content_length': len(response.content),
                'response_time': response.elapsed.total_seconds()
            }

            # Cache the result
            if self.cache:
                cache_data = {'soup': soup, 'metrics': metrics}
                self.cache.set(url, cache_data)

            logger.debug(f"Successfully crawled: {url} (Load time: {load_time:.2f}s)")
            return soup, metrics

        except Exception as e:
            logger.warning(f"Failed to crawl {url}: {e}")
            return None

    def find_internal_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Find internal links from the current page."""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            parsed_url = urlparse(full_url)

            # Clean URL (remove fragments and normalize)
            clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            if parsed_url.query:
                clean_url += f"?{parsed_url.query}"

            if (parsed_url.netloc == self.domain and 
                clean_url not in self.crawled_urls and 
                len(self.crawled_urls) < self.config.max_pages):
                links.append(clean_url)

        return links

    def extract_page_data(self, url: str, soup: BeautifulSoup, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive page data."""
        # Basic page information
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ''

        # Meta description
        meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc_tag.get('content', '') if meta_desc_tag else ''

        # Heading tags
        h1_tags = [h1.get_text().strip() for h1 in soup.find_all('h1')]
        h2_tags = [h2.get_text().strip() for h2 in soup.find_all('h2')]
        h3_tags = [h3.get_text().strip() for h3 in soup.find_all('h3')]

        # Images
        images = soup.find_all('img')
        images_without_alt = [img for img in images if not img.get('alt')]

        # Links
        all_links = soup.find_all('a', href=True)
        internal_links = [
            a for a in all_links 
            if urlparse(urljoin(url, a['href'])).netloc == self.domain
        ]
        external_links = [
            a for a in all_links 
            if urlparse(urljoin(url, a['href'])).netloc != self.domain and 
            urlparse(urljoin(url, a['href'])).netloc != ''
        ]

        # Content analysis
        content_text = soup.get_text()
        word_count = len(content_text.split())

        # Schema markup detection
        schema_scripts = soup.find_all('script', type='application/ld+json')
        has_schema = len(schema_scripts) > 0

        # Canonical URL
        canonical_tag = soup.find('link', rel='canonical')
        canonical_url = canonical_tag.get('href') if canonical_tag else None

        return {
            'url': url,
            'title': title,
            'title_length': len(title),
            'meta_description': meta_description,
            'meta_description_length': len(meta_description),
            'h1_tags': h1_tags,
            'h2_tags': h2_tags,
            'h3_tags': h3_tags,
            'images_total': len(images),
            'images_without_alt': len(images_without_alt),
            'internal_links_count': len(internal_links),
            'external_links_count': len(external_links),
            'word_count': word_count,
            'content': content_text,
            'has_schema_markup': has_schema,
            'schema_count': len(schema_scripts),
            'canonical_url': canonical_url,
            'load_time': metrics['load_time'],
            'status_code': metrics['status_code'],
            'content_length': metrics['content_length']
        }

    def crawl_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Crawl a single page and extract data."""
        result = self.get_page_content(url)
        if not result:
            return None

        soup, metrics = result
        page_data = self.extract_page_data(url, soup, metrics)

        # Add delay to be respectful
        time.sleep(self.config.request_delay)

        return page_data

    def crawl_site(self) -> List[Dict[str, Any]]:
        """Crawl the website with progress tracking."""
        logger.info(f"Starting site crawl: {self.base_url}")
        to_crawl = [self.base_url]
        self.crawled_urls.add(self.base_url)

        with tqdm(total=self.config.max_pages, desc="Crawling pages") as pbar:
            while to_crawl and len(self.sitemap) < self.config.max_pages:
                current_url = to_crawl.pop(0)

                page_data = self.crawl_page(current_url)
                if page_data:
                    self.sitemap.append(page_data)

                    # Find new links to crawl
                    result = self.get_page_content(current_url)
                    if result:
                        soup, _ = result
                        new_links = self.find_internal_links(soup, current_url)
                        for link in new_links:
                            if (link not in self.crawled_urls and 
                                len(self.crawled_urls) < self.config.max_pages):
                                to_crawl.append(link)
                                self.crawled_urls.add(link)

                    pbar.update(1)

        logger.info(f"Crawling completed. Total pages: {len(self.sitemap)}")
        return self.sitemap

class KeywordAnalyzer:
    """Enhanced keyword analyzer with advanced capabilities."""

    def __init__(self, target_keyword: str):
        self.target_keyword = target_keyword.lower()
        self.keyword_variations = self._generate_variations()

    def _generate_variations(self) -> List[str]:
        """Generate keyword variations including plurals, related terms."""
        variations = set([self.target_keyword])
        words = self.target_keyword.split()

        if len(words) > 1:
            # Add individual words
            variations.update(words)
            # Add reversed order
            variations.add(' '.join(reversed(words)))

        # Add common plurals
        if not self.target_keyword.endswith('s'):
            variations.add(self.target_keyword + 's')

        return list(variations)

    def calculate_keyword_density(self, content: str) -> Dict[str, Dict[str, float]]:
        """Calculate keyword density with position analysis."""
        if not content:
            return {}

        content_lower = content.lower()
        words = content_lower.split()
        total_words = len(words)

        if total_words == 0:
            return {}

        densities = {}

        for keyword in self.keyword_variations:
            count = content_lower.count(keyword)
            density = (count / total_words) * 100 if total_words > 0 else 0

            densities[keyword] = {
                'count': count,
                'density': round(density, 2)
            }

        return densities

    def analyze_keyword_placement(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze keyword placement across page elements."""
        placement = {
            'in_title': self._check_keyword_in_text(page_data.get('title', '')),
            'in_meta_description': self._check_keyword_in_text(page_data.get('meta_description', '')),
            'in_h1': any(self._check_keyword_in_text(h1) for h1 in page_data.get('h1_tags', [])),
            'in_h2': any(self._check_keyword_in_text(h2) for h2 in page_data.get('h2_tags', [])),
            'in_content': self._check_keyword_in_text(page_data.get('content', '')),
            'in_url': self._check_keyword_in_text(page_data.get('url', ''))
        }

        # Calculate overall optimization score
        weights = {
            'in_title': 25,
            'in_meta_description': 15,
            'in_h1': 20,
            'in_h2': 10,
            'in_content': 20,
            'in_url': 10
        }

        optimization_score = sum(
            weights[key] for key, value in placement.items() if value
        )

        placement['optimization_score'] = optimization_score

        return placement

    def _check_keyword_in_text(self, text: str) -> bool:
        """Check if target keyword or variations exist in text."""
        if not text:
            return False

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keyword_variations)

class SEOAuditor:
    """Enhanced SEO auditor with comprehensive analysis capabilities."""

    def __init__(self, zenserp_manager: ZenSERPManager, keyword_analyzer: KeywordAnalyzer):
        self.zenserp = zenserp_manager
        self.keyword_analyzer = keyword_analyzer
        self.issues: List[SEOIssue] = []

    def analyze_meta_tags(self, sitemap: List[Dict[str, Any]]) -> List[SEOIssue]:
        """Comprehensive meta tag analysis."""
        issues = []

        for page in sitemap:
            url = page['url']
            title = page.get('title', '')
            meta_desc = page.get('meta_description', '')
            title_length = page.get('title_length', 0)
            meta_desc_length = page.get('meta_description_length', 0)

            # Title tag analysis
            if not title:
                issues.append(SEOIssue(
                    category="Meta Tags",
                    priority="Critical",
                    page=url,
                    issue="Missing title tag",
                    recommendation="Add a descriptive title tag (50-60 characters)",
                    impact="Critical for search rankings and CTR"
                ))
            else:
                if title_length < 30:
                    issues.append(SEOIssue(
                        category="Meta Tags",
                        priority="High",
                        page=url,
                        issue=f"Title tag too short ({title_length} chars)",
                        recommendation="Expand title to 50-60 characters",
                        impact="Suboptimal search result presentation"
                    ))
                elif title_length > 60:
                    issues.append(SEOIssue(
                        category="Meta Tags",
                        priority="Medium",
                        page=url,
                        issue=f"Title tag too long ({title_length} chars)",
                        recommendation="Shorten title to under 60 characters",
                        impact="Title may be truncated in search results"
                    ))

            # Meta description analysis
            if not meta_desc:
                issues.append(SEOIssue(
                    category="Meta Tags",
                    priority="High",
                    page=url,
                    issue="Missing meta description",
                    recommendation="Add meta description (150-160 characters)",
                    impact="Reduced CTR from search results"
                ))
            elif meta_desc_length > 160:
                issues.append(SEOIssue(
                    category="Meta Tags",
                    priority="Medium",
                    page=url,
                    issue=f"Meta description too long ({meta_desc_length} chars)",
                    recommendation="Shorten description to under 160 characters",
                    impact="Description may be truncated"
                ))

        return issues

    def analyze_keyword_optimization(self, sitemap: List[Dict[str, Any]]) -> List[SEOIssue]:
        """Enhanced keyword optimization analysis."""
        issues = []

        for page in sitemap:
            url = page['url']
            keyword_density = self.keyword_analyzer.calculate_keyword_density(page['content'])
            keyword_placement = self.keyword_analyzer.analyze_keyword_placement(page)

            main_keyword = self.keyword_analyzer.target_keyword
            main_density = keyword_density.get(main_keyword, {}).get('density', 0)

            # Keyword density analysis
            if main_density == 0:
                issues.append(SEOIssue(
                    category="Keywords",
                    priority="High",
                    page=url,
                    issue="Target keyword not found",
                    recommendation="Include target keyword naturally in content",
                    impact="Page not optimized for target keyword"
                ))
            elif main_density > 4.0:
                issues.append(SEOIssue(
                    category="Keywords",
                    priority="Medium",
                    page=url,
                    issue=f"Keyword density too high ({main_density}%)",
                    recommendation="Reduce keyword density to 1-3%",
                    impact="Risk of keyword stuffing penalty"
                ))

            # Keyword placement analysis
            if not keyword_placement['in_title']:
                issues.append(SEOIssue(
                    category="Keywords",
                    priority="High",
                    page=url,
                    issue="Target keyword not in title",
                    recommendation="Include target keyword in title tag",
                    impact="Reduced relevance signal to search engines"
                ))

            if not keyword_placement['in_h1']:
                issues.append(SEOIssue(
                    category="Keywords",
                    priority="Medium",
                    page=url,
                    issue="Target keyword not in H1",
                    recommendation="Include target keyword in main heading",
                    impact="Missing important relevance signal"
                ))

        return issues

    def analyze_technical_seo(self, sitemap: List[Dict[str, Any]]) -> List[SEOIssue]:
        """Comprehensive technical SEO analysis."""
        issues = []

        # Check for duplicate titles
        titles = [page['title'] for page in sitemap if page['title']]
        duplicate_titles = [title for title, count in Counter(titles).items() if count > 1]

        for title in duplicate_titles:
            duplicate_pages = [page['url'] for page in sitemap if page['title'] == title]
            issues.append(SEOIssue(
                category="Technical SEO",
                priority="High",
                page=", ".join(duplicate_pages),
                issue="Duplicate title tags",
                recommendation="Create unique titles for each page",
                impact="Reduced search engine understanding"
            ))

        # Analyze individual pages
        for page in sitemap:
            url = page['url']

            # H1 tag analysis
            h1_tags = page.get('h1_tags', [])
            if not h1_tags:
                issues.append(SEOIssue(
                    category="Technical SEO",
                    priority="Medium",
                    page=url,
                    issue="Missing H1 tag",
                    recommendation="Add descriptive H1 tag",
                    impact="Reduced content structure clarity"
                ))
            elif len(h1_tags) > 1:
                issues.append(SEOIssue(
                    category="Technical SEO",
                    priority="Low",
                    page=url,
                    issue=f"Multiple H1 tags ({len(h1_tags)})",
                    recommendation="Use only one H1 per page",
                    impact="Diluted heading hierarchy"
                ))

            # Content length analysis
            word_count = page.get('word_count', 0)
            if word_count < 300:
                issues.append(SEOIssue(
                    category="Technical SEO",
                    priority="Medium",
                    page=url,
                    issue=f"Thin content ({word_count} words)",
                    recommendation="Expand content to at least 300 words",
                    impact="Reduced content authority and ranking potential"
                ))

            # Page load time analysis
            load_time = page.get('load_time', 0)
            if load_time > 3.0:
                issues.append(SEOIssue(
                    category="Performance",
                    priority="High",
                    page=url,
                    issue=f"Slow page load time ({load_time:.2f}s)",
                    recommendation="Optimize page speed to under 3 seconds",
                    impact="Poor user experience and ranking factor"
                ))

        return issues

    def analyze_images(self, sitemap: List[Dict[str, Any]]) -> List[SEOIssue]:
        """Enhanced image optimization analysis."""
        issues = []

        for page in sitemap:
            url = page['url']
            images_total = page.get('images_total', 0)
            images_without_alt = page.get('images_without_alt', 0)

            if images_without_alt > 0:
                issues.append(SEOIssue(
                    category="Images",
                    priority="Medium",
                    page=url,
                    issue=f"{images_without_alt} of {images_total} images missing alt text",
                    recommendation="Add descriptive alt text to all images",
                    impact="Reduced accessibility and SEO value"
                ))

        return issues

    def analyze_internal_linking(self, sitemap: List[Dict[str, Any]]) -> List[SEOIssue]:
        """Enhanced internal linking analysis."""
        issues = []

        for page in sitemap:
            url = page['url']
            internal_links = page.get('internal_links_count', 0)

            if internal_links == 0:
                issues.append(SEOIssue(
                    category="Internal Linking",
                    priority="Medium",
                    page=url,
                    issue="No internal links",
                    recommendation="Add relevant internal links",
                    impact="Poor link equity distribution"
                ))
            elif internal_links < 3:
                issues.append(SEOIssue(
                    category="Internal Linking",
                    priority="Low",
                    page=url,
                    issue=f"Few internal links ({internal_links})",
                    recommendation="Add more relevant internal links",
                    impact="Limited link equity flow"
                ))

        return issues

    @retry_on_failure(max_retries=2)
    def perform_serp_analysis(self, keyword: str) -> Dict[str, Any]:
        """Enhanced SERP analysis with competitor insights."""
        try:
            logger.info(f"Performing SERP analysis for: {keyword}")
            serp_data = self.zenserp.search_serp(keyword)

            competitors = []
            if 'organic' in serp_data:
                for i, result in enumerate(serp_data['organic'][:10], 1):
                    title = result.get('title', '')
                    snippet = result.get('snippet', '')
                    url = result.get('url', '')

                    competitors.append({
                        'rank': i,
                        'url': url,
                        'title': title,
                        'title_length': len(title),
                        'snippet': snippet,
                        'snippet_length': len(snippet),
                        'domain': urlparse(url).netloc if url else ''
                    })

            return {
                'keyword': keyword,
                'total_results': serp_data.get('total_results', ''),
                'competitors': competitors,
                'related_searches': [rs.get('query', '') for rs in serp_data.get('related_searches', [])],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"SERP analysis failed for {keyword}: {e}")
            return {'error': str(e), 'keyword': keyword}

class SEOReportGenerator:
    """Enhanced report generator with multiple export formats."""

    def __init__(self, website_url: str, target_keyword: str, config: AuditConfig = None):
        self.website_url = website_url
        self.target_keyword = target_keyword
        self.config = config or AuditConfig()
        self.timestamp = datetime.now()

    def calculate_seo_score(self, issues: List[SEOIssue], sitemap: List[Dict]) -> Dict[str, Any]:
        """Calculate overall SEO score based on issues found."""
        total_pages = len(sitemap)
        if total_pages == 0:
            return {'score': 0, 'grade': 'F', 'details': {}}

        # Weight penalties by priority
        penalty_weights = {
            'Critical': 20,
            'High': 10,
            'Medium': 5,
            'Low': 2
        }

        total_penalty = sum(penalty_weights.get(issue.priority, 0) for issue in issues)
        max_possible_penalty = total_pages * sum(penalty_weights.values())

        # Calculate score (100 - penalty percentage)
        penalty_percentage = (total_penalty / max_possible_penalty) * 100 if max_possible_penalty > 0 else 0
        score = max(0, 100 - penalty_percentage)

        # Assign grade
        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'

        issue_counts = Counter(issue.priority for issue in issues)

        return {
            'score': round(score, 1),
            'grade': grade,
            'total_penalty': total_penalty,
            'max_possible_penalty': max_possible_penalty,
            'issue_breakdown': dict(issue_counts),
            'total_issues': len(issues),
            'pages_analyzed': total_pages
        }

    def generate_executive_summary(self, issues: List[SEOIssue], sitemap: List[Dict], 
                                 serp_data: Dict[str, Any]) -> str:
        """Generate comprehensive executive summary."""
        seo_score = self.calculate_seo_score(issues, sitemap)

        critical_count = len([i for i in issues if i.priority == 'Critical'])
        high_count = len([i for i in issues if i.priority == 'High'])
        medium_count = len([i for i in issues if i.priority == 'Medium'])
        low_count = len([i for i in issues if i.priority == 'Low'])

        total_pages = len(sitemap)
        total_words = sum(p.get('word_count', 0) for p in sitemap)
        avg_load_time = sum(p.get('load_time', 0) for p in sitemap) / total_pages if total_pages > 0 else 0

        summary = f"""
# 🔍 SEO AUDIT REPORT

**Website:** {self.website_url}  
**Target Keyword:** "{self.target_keyword}"  
**Audit Date:** {self.timestamp.strftime('%B %d, %Y at %I:%M %p')}  
**Pages Analyzed:** {total_pages}  

---

## 📊 SEO Score: {seo_score['score']}/100 (Grade: {seo_score['grade']})

### 🎯 Key Metrics at a Glance
- **Total Content:** {total_words:,} words across all pages
- **Average Load Time:** {avg_load_time:.2f} seconds
- **Issues Found:** {len(issues)} total issues requiring attention
- **SEO Health:** {'Excellent' if seo_score['score'] >= 90 else 'Good' if seo_score['score'] >= 80 else 'Fair' if seo_score['score'] >= 60 else 'Poor'}

### 🚨 Issue Breakdown
| Priority | Count | Impact |
|----------|-------|---------|
| 🔴 **Critical** | {critical_count} | Immediate action required |
| 🟠 **High** | {high_count} | Address within 1-2 weeks |
| 🟡 **Medium** | {medium_count} | Address within 1 month |
| 🟢 **Low** | {low_count} | Address when possible |

### 📈 SERP Competition Analysis
"""

        if 'error' not in serp_data:
            competitors = serp_data.get('competitors', [])[:3]
            if competitors:
                summary += f"**Top 3 Competitors for '{self.target_keyword}':**\n"
                for comp in competitors:
                    summary += f"- **#{comp['rank']}** {comp['domain']} - {comp['title'][:50]}...\n"
        else:
            summary += f"⚠️ SERP data unavailable: {serp_data.get('error', 'Unknown error')}\n"

        summary += """
### 💡 Priority Action Items
1. **Address Critical Issues** - These are blocking your SEO success
2. **Optimize Page Speed** - Improve user experience and ranking
3. **Enhance Content Strategy** - Focus on keyword optimization
4. **Improve Technical SEO** - Fix structural issues

---
"""

        return summary

    def generate_detailed_findings(self, issues: List[SEOIssue]) -> str:
        """Generate detailed findings report with enhanced formatting."""
        if not issues:
            return "\n## ✅ No Issues Found\nCongratulations! Your website passed all SEO checks.\n"

        categories = defaultdict(list)
        for issue in issues:
            categories[issue.category].append(issue)

        detailed_report = "\n## 🔍 Detailed SEO Analysis\n"

        category_icons = {
            'Meta Tags': '🏷️',
            'Keywords': '🎯',
            'Technical SEO': '⚙️',
            'Images': '🖼️',
            'Internal Linking': '🔗',
            'Performance': '⚡',
            'Content': '📝'
        }

        priority_colors = {
            'Critical': '🔴',
            'High': '🟠',
            'Medium': '🟡',
            'Low': '🟢'
        }

        for category, category_issues in categories.items():
            icon = category_icons.get(category, '📋')
            detailed_report += f"\n### {icon} {category} ({len(category_issues)} issues)\n"

            for priority in ['Critical', 'High', 'Medium', 'Low']:
                priority_issues = [i for i in category_issues if i.priority == priority]

                if priority_issues:
                    color = priority_colors.get(priority, '⚪')
                    detailed_report += f"\n#### {color} {priority} Priority ({len(priority_issues)} issues)\n"

                    for i, issue in enumerate(priority_issues, 1):
                        pages = issue.page.split(', ')
                        page_display = pages[0] if len(pages) == 1 else f"{pages[0]} (+{len(pages)-1} more)"

                        detailed_report += f"""
**{i}. {issue.issue}**
- **Page(s):** {page_display}
- **Impact:** {issue.impact}
- **Recommendation:** {issue.recommendation}

---
"""

        return detailed_report

    def generate_serp_analysis_report(self, serp_data: Dict[str, Any]) -> str:
        """Generate comprehensive SERP analysis report."""
        if 'error' in serp_data:
            return f"\n## ❌ SERP Analysis Error\n\n**Error:** {serp_data['error']}\n"

        keyword = serp_data.get('keyword', '')
        total_results = serp_data.get('total_results', 'N/A')

        report = f"""
## 🎯 SERP Analysis for "{keyword}"

**Total Results:** {total_results}

### 🏆 Top 10 Competitors Analysis

"""

        competitors = serp_data.get('competitors', [])
        for comp in competitors:
            report += f"""
**Rank {comp['rank']}:** {comp['title']}
**URL:** {comp['url']}
**Domain:** {comp['domain']}

---
"""

        # Related Keywords
        related_searches = serp_data.get('related_searches', [])
        if related_searches:
            report += f"""
### 🔍 Related Keywords to Target
"""
            for i, related in enumerate(related_searches[:5], 1):
                report += f"{i}. {related}\n"

        return report

    def generate_recommendations(self, issues: List[SEOIssue], sitemap: List[Dict]) -> str:
        """Generate prioritized recommendations with implementation timeline."""
        if not issues:
            return "\n## 🎉 All Good!\nNo recommendations needed - your SEO is on point!\n"

        # Group issues by priority
        critical_high = [i for i in issues if i.priority in ['Critical', 'High']]
        medium = [i for i in issues if i.priority == 'Medium']
        low = [i for i in issues if i.priority == 'Low']

        report = """
## 📋 Prioritized SEO Recommendations

### 🚀 Phase 1: Critical & High Priority (Week 1-2)
"""

        for i, issue in enumerate(critical_high[:5], 1):
            report += f"{i}. **{issue.issue}** - {issue.recommendation}\n"

        if medium:
            report += """
### 📈 Phase 2: Medium Priority (Month 1)
"""
            for i, issue in enumerate(medium[:5], 1):
                report += f"{i}. **{issue.issue}** - {issue.recommendation}\n"

        if low:
            report += """
### 🔄 Phase 3: Long-term Improvements (Ongoing)
"""
            for i, issue in enumerate(low[:3], 1):
                report += f"{i}. **{issue.issue}** - {issue.recommendation}\n"

        return report

    def export_to_csv(self, issues: List[SEOIssue], filename: str):
        """Export issues to CSV with enhanced data."""
        try:
            df = pd.DataFrame([asdict(issue) for issue in issues])
            df['pages_affected'] = df['page'].apply(lambda x: len(x.split(', ')))
            df['priority_score'] = df['priority'].map({'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1})

            # Sort by priority and category
            df = df.sort_values(['priority_score', 'category'], ascending=[False, True])

            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Issues exported to CSV: {filename}")
        except Exception as e:
            logger.warning(f"Could not export CSV: {e}")

class SEOSleuth:
    """Enhanced main SEO audit class with comprehensive analysis capabilities."""

    def __init__(self, api_key: str, config: AuditConfig = None):
        self.config = config or AuditConfig()
        self.zenserp = ZenSERPManager(api_key, max_requests=50, config=self.config)
        self.issues: List[SEOIssue] = []

        # Setup progress tracking
        self.progress = {
            'total_steps': 7,
            'current_step': 0,
            'step_names': [
                'Initializing crawler',
                'Crawling website',
                'Analyzing SERP data',
                'Checking meta tags',
                'Analyzing keywords',
                'Technical SEO audit',
                'Generating report'
            ]
        }

    def _update_progress(self, step_name: str):
        """Update and display progress."""
        self.progress['current_step'] += 1
        current = self.progress['current_step']
        total = self.progress['total_steps']

        logger.info(f"📊 Progress: {current}/{total} - {step_name}")
        print(f"🔍 [{current}/{total}] {step_name}")

    def analyze_website(self, website_url: str, target_keyword: str) -> str:
        """Perform comprehensive SEO analysis with enhanced reporting."""
        print("🚀 SEOSleuth Enhanced Analysis Started")
        print("=" * 60)

        start_time = time.time()

        # Check API quota
        quota = self.zenserp.check_remaining_quota()
        print(f"📊 API Quota: {quota['used']}/{quota['total']} used, {quota['remaining']} remaining")

        if quota['remaining'] < 1:
            raise Exception("❌ Insufficient API quota for analysis")

        # Initialize components
        self._update_progress("Initializing crawler")
        keyword_analyzer = KeywordAnalyzer(target_keyword)
        crawler = WebsiteCrawler(website_url, self.config)
        auditor = SEOAuditor(self.zenserp, keyword_analyzer)

        # Crawl website
        self._update_progress("Crawling website")
        sitemap = crawler.crawl_site()

        if not sitemap:
            raise Exception("❌ No pages could be crawled. Please check the website URL.")

        print(f"✅ Successfully crawled {len(sitemap)} pages")

        # Perform SERP analysis
        self._update_progress("Analyzing SERP data")
        serp_data = auditor.perform_serp_analysis(target_keyword)
        if 'error' not in serp_data:
            print(f"✅ SERP analysis completed for '{target_keyword}'")
        else:
            print(f"⚠️ SERP analysis error: {serp_data['error']}")

        # Perform comprehensive SEO audit
        print("\n🔧 Performing comprehensive SEO audit...")

        self._update_progress("Checking meta tags")
        meta_issues = auditor.analyze_meta_tags(sitemap)

        self._update_progress("Analyzing keywords")
        keyword_issues = auditor.analyze_keyword_optimization(sitemap)

        self._update_progress("Technical SEO audit")
        technical_issues = auditor.analyze_technical_seo(sitemap)
        image_issues = auditor.analyze_images(sitemap)
        linking_issues = auditor.analyze_internal_linking(sitemap)

        # Combine all issues
        all_issues = (meta_issues + keyword_issues + technical_issues + 
                     image_issues + linking_issues)

        print(f"✅ Found {len(all_issues)} SEO issues across {len(sitemap)} pages")

        # Generate comprehensive report
        self._update_progress("Generating report")
        report_generator = SEOReportGenerator(website_url, target_keyword, self.config)

        # Build complete report
        report = ""
        report += report_generator.generate_executive_summary(all_issues, sitemap, serp_data)
        report += report_generator.generate_detailed_findings(all_issues)
        report += report_generator.generate_serp_analysis_report(serp_data)
        report += report_generator.generate_recommendations(all_issues, sitemap)

        # Add analysis summary
        analysis_time = time.time() - start_time
        final_quota = self.zenserp.check_remaining_quota()

        report += f"""
---

## 📊 Analysis Summary

| Metric | Value |
|--------|-------|
| **Pages Analyzed** | {len(sitemap)} |
| **Total Issues Found** | {len(all_issues)} |
| **Analysis Duration** | {analysis_time/60:.1f} minutes |
| **API Calls Used** | {final_quota['used']}/{final_quota['total']} |
| **API Calls Remaining** | {final_quota['remaining']} |
| **Average Page Load Time** | {sum(p.get('load_time', 0) for p in sitemap) / len(sitemap):.2f}s |
| **Total Content Words** | {sum(p.get('word_count', 0) for p in sitemap):,} |

---

*🤖 Report generated by SEOSleuth Enhanced v2.0 on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*

**Next Steps:**
1. 📥 Address Critical and High priority issues first
2. 📈 Monitor your SEO progress over time
3. 🔄 Run follow-up audits monthly

*Happy optimizing! 🚀*
"""

        # Export CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            csv_filename = f"seo_issues_{timestamp}.csv"
            report_generator.export_to_csv(all_issues, csv_filename)
            print(f"\n📁 CSV report created: {csv_filename}")
        except Exception as e:
            logger.warning(f"Could not create CSV export: {e}")

        print(f"\n🎉 Analysis completed in {analysis_time/60:.1f} minutes!")
        return report

# Simplified main function for Google Colab
def main():
    """Simple main function for Google Colab usage."""

    # These should be set by the user
    ZENSERP_API_KEY = "your_zenserp_api_key_here"
    WEBSITE_URL = "https://example.com"
    TARGET_KEYWORD = "your target keyword"

    # Colab-optimized configuration
    config = AuditConfig(
        max_pages=10,
        max_concurrent_requests=2,
        request_delay=2.0,
        respect_robots_txt=True,
        cache_enabled=True,
        max_retries=2
    )

    try:
        # Initialize SEO Sleuth
        seo_tool = SEOSleuth(ZENSERP_API_KEY, config)

        # Perform analysis
        report = seo_tool.analyze_website(WEBSITE_URL, TARGET_KEYWORD)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"seo_audit_{timestamp}.md"

        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n📄 Report saved to: {report_filename}")
        return report, report_filename

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"❌ Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
