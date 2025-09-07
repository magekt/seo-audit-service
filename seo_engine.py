"""
SEO Engine - Enhanced Comprehensive Website Analysis System
Production-ready SEO auditing with advanced crawling, SERP analysis, and comprehensive reporting
Version: 3.0 Enhanced
"""

import asyncio
import aiohttp
import time
import json
import re
import os
import pickle
import hashlib
import xml.etree.ElementTree as ET  # ADD THIS LINE
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus, unquote
from urllib.robotparser import RobotFileParser
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, Any
import logging
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import csv
from collections import defaultdict, Counter
import sqlite3
import threading
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@dataclass
class SEOPageData:
    """Comprehensive SEO data for a single page with enhanced metrics"""
    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    h1_tags: List[str] = field(default_factory=list)
    h2_tags: List[str] = field(default_factory=list)
    h3_tags: List[str] = field(default_factory=list)
    h4_tags: List[str] = field(default_factory=list)
    h5_tags: List[str] = field(default_factory=list)
    h6_tags: List[str] = field(default_factory=list)
    word_count: int = 0
    char_count: int = 0
    internal_links: List[str] = field(default_factory=list)
    external_links: List[str] = field(default_factory=list)
    images: List[Dict] = field(default_factory=list)
    load_time: float = 0.0
    status_code: int = 0
    content_type: str = ""
    canonical_url: Optional[str] = None
    meta_robots: Optional[str] = None
    og_tags: Dict[str, str] = field(default_factory=dict)
    twitter_tags: Dict[str, str] = field(default_factory=dict)
    schema_markup: List[Dict] = field(default_factory=list)
    keyword_density: float = 0.0
    readability_score: float = 0.0
    seo_issues: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    mobile_friendly: bool = False
    has_viewport: bool = False
    ssl_enabled: bool = False
    page_depth: int = 0

    # Enhanced metrics
    text_to_html_ratio: float = 0.0
    compression_ratio: float = 0.0
    js_files: List[str] = field(default_factory=list)
    css_files: List[str] = field(default_factory=list)
    forms: List[Dict] = field(default_factory=list)
    meta_tags: Dict[str, str] = field(default_factory=dict)
    heading_structure: Dict[str, int] = field(default_factory=dict)
    content_language: Optional[str] = None
    page_size_bytes: int = 0
    response_headers: Dict[str, str] = field(default_factory=dict)
    crawl_timestamp: datetime = field(default_factory=datetime.now)

    # SERP-related data
    serp_position: Optional[int] = None
    serp_title: Optional[str] = None
    serp_snippet: Optional[str] = None
    serp_url: Optional[str] = None

@dataclass
class CrawlStats:
    """Enhanced crawling statistics and metrics"""
    total_pages: int = 0
    successful_pages: int = 0
    failed_pages: int = 0
    cached_pages: int = 0
    skipped_pages: int = 0
    total_issues: int = 0
    average_load_time: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    crawl_duration: float = 0.0
    total_data_transferred: int = 0
    unique_domains: Set[str] = field(default_factory=set)
    file_types: Dict[str, int] = field(default_factory=dict)

@dataclass
class SERPResult:
    """SERP analysis result data"""
    position: int
    title: str
    url: str
    snippet: str
    domain: str
    estimated_traffic: int = 0
    backlinks_estimate: int = 0
    domain_authority: int = 0

class CacheManager:
    """Advanced caching system for SEO analysis data"""

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "seo_cache.db"
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for caching"""
        with sqlite3.connect(self.db_path) as conn:
            # Create tables first
            conn.execute("""
                CREATE TABLE IF NOT EXISTS page_cache (
                    url TEXT PRIMARY KEY,
                    domain TEXT,
                    content_hash TEXT,
                    page_data BLOB,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    analysis_count INTEGER DEFAULT 1
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    domain TEXT,
                    target_keyword TEXT,
                    created_at TIMESTAMP,
                    last_updated TIMESTAMP,
                    page_count INTEGER,
                    status TEXT
                )
            """)
            
            # Create indexes separately - ONE AT A TIME
            conn.execute("CREATE INDEX IF NOT EXISTS idx_domain ON page_cache(domain)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON page_cache(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_domain ON analysis_sessions(domain)")


    def get_cached_page(self, url: str, max_age_hours: int = 24) -> Optional[SEOPageData]:
        """Retrieve cached page data if available and not expired"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT page_data, created_at FROM page_cache 
                    WHERE url = ? AND datetime(created_at) > datetime('now', '-{} hours')
                """.format(max_age_hours), (url,))

                result = cursor.fetchone()
                if result:
                    # Update last accessed
                    cursor.execute("""
                        UPDATE page_cache SET last_accessed = CURRENT_TIMESTAMP,
                        analysis_count = analysis_count + 1 WHERE url = ?
                    """, (url,))

                    return pickle.loads(result[0])

        except Exception as e:
            logger.warning(f"Cache retrieval error for {url}: {e}")
        return None

    def cache_page(self, page_data: SEOPageData, content_hash: str):
        """Cache page data"""
        try:
            domain = urlparse(page_data.url).netloc
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO page_cache 
                    (url, domain, content_hash, page_data, created_at, last_accessed)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (page_data.url, domain, content_hash, pickle.dumps(page_data)))

        except Exception as e:
            logger.warning(f"Cache storage error for {page_data.url}: {e}")

    def get_cached_urls_for_domain(self, domain: str) -> Set[str]:
        """Get all cached URLs for a domain"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT url FROM page_cache WHERE domain = ?", (domain,))
                return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            logger.warning(f"Error getting cached URLs for {domain}: {e}")
            return set()

    def cleanup_old_cache(self, days: int = 7):
        """Remove old cache entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    DELETE FROM page_cache 
                    WHERE datetime(created_at) < datetime('now', '-{} days')
                """.format(days))
                logger.info("Cache cleanup completed")
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

class SERPAnalyzer:
    """Manual SERP analysis without external API dependency"""

    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    async def analyze_serp(self, keyword: str, session: aiohttp.ClientSession) -> List[SERPResult]:
        """Analyze SERP results for a given keyword"""
        results = []

        try:
            # Construct Google search URL
            search_url = f"https://www.google.com/search?q={quote_plus(keyword)}&num=20"

            headers = {
                'User-Agent': self.user_agents[0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    results = self._parse_serp_results(html)

        except Exception as e:
            logger.warning(f"SERP analysis failed for keyword '{keyword}': {e}")

        return results

    def _parse_serp_results(self, html: str) -> List[SERPResult]:
        """Parse SERP results from Google search HTML"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')

        # Find search result containers
        search_results = soup.find_all('div', {'class': ['g', 'tF2Cxc', 'MjjYud']})

        for i, result in enumerate(search_results[:10], 1):
            try:
                # Extract title
                title_elem = result.find('h3') or result.find(['h1', 'h2', 'h3'])
                title = title_elem.get_text(strip=True) if title_elem else ""

                # Extract URL
                link_elem = result.find('a')
                url = link_elem.get('href', '') if link_elem else ""

                # Clean URL (remove Google redirect)
                if url.startswith('/url?q='):
                    url = unquote(url.split('&')[0][7:])

                # Extract snippet
                snippet_elem = result.find('span', {'class': ['st', 'aCOpRe']}) or result.find('div', {'class': ['s', 'VwiC3b']})
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if title and url:
                    domain = urlparse(url).netloc
                    results.append(SERPResult(
                        position=i,
                        title=title,
                        url=url,
                        snippet=snippet,
                        domain=domain
                    ))

            except Exception as e:
                logger.debug(f"Error parsing SERP result {i}: {e}")
                continue

        return results

class EnhancedSEOCrawler:
    """Advanced SEO crawler with comprehensive analysis capabilities"""

    def __init__(self, config, cache_manager: CacheManager):
        self.config = config
        self.cache_manager = cache_manager
        self.session = None
        self.crawled_urls: Set[str] = set()
        self.pages_data: List[SEOPageData] = []
        self.stats = CrawlStats()
        self.discovered_urls: Set[str] = set()
        self.sitemap_urls: Set[str] = set()
        self.serp_analyzer = SERPAnalyzer()

        # Enhanced browser headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }

    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent_requests * 2,
            limit_per_host=3,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
            ttl_dns_cache=300,
            use_dns_cache=True
        )

        timeout = aiohttp.ClientTimeout(
            total=self.config.request_timeout * 2,
            connect=15,
            sock_read=30
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )

        self.stats.start_time = datetime.now()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

        self.stats.end_time = datetime.now()
        self.stats.crawl_duration = (self.stats.end_time - self.stats.start_time).total_seconds()

        if self.pages_data:
            self.stats.average_load_time = sum(page.load_time for page in self.pages_data) / len(self.pages_data)

    async def discover_urls(self, start_url: str) -> Set[str]:
        """Discover all URLs associated with the domain"""
        logger.info(f"Starting URL discovery for {start_url}")

        parsed_url = urlparse(start_url)
        base_domain = parsed_url.netloc
        discovered = set()

        # Check sitemap
        await self._check_sitemaps(start_url, discovered)

        # Check robots.txt for additional sitemaps
        await self._check_robots_for_sitemaps(start_url, discovered)

        # Recursive crawling for link discovery
        await self._recursive_link_discovery(start_url, base_domain, discovered, max_depth=3)

        logger.info(f"Discovered {len(discovered)} URLs for domain {base_domain}")
        return discovered

    async def _check_sitemaps(self, base_url: str, discovered: Set[str]):
        """Check common sitemap locations"""
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        sitemap_paths = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemaps.xml',
            '/sitemap.txt',
            '/robots.txt'
        ]

        for path in sitemap_paths:
            try:
                sitemap_url = base + path
                async with self.session.get(sitemap_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        if path.endswith('.xml'):
                            urls = self._parse_xml_sitemap(content, base)
                        else:
                            urls = self._parse_text_sitemap(content, base)

                        discovered.update(urls)
                        self.sitemap_urls.update(urls)

            except Exception as e:
                logger.debug(f"Error checking sitemap {sitemap_url}: {e}")

    async def _check_robots_for_sitemaps(self, base_url: str, discovered: Set[str]):
        """Parse robots.txt for sitemap declarations"""
        try:
            parsed = urlparse(base_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    content = await response.text()
                    for line in content.split('\n'):
                        if line.lower().startswith('sitemap:'):
                            sitemap_url = line.split(':', 1)[1].strip()
                            async with self.session.get(sitemap_url) as sitemap_response:
                                if sitemap_response.status == 200:
                                    sitemap_content = await sitemap_response.text()
                                    urls = self._parse_xml_sitemap(sitemap_content, base_url)
                                    discovered.update(urls)

        except Exception as e:
            logger.debug(f"Error checking robots.txt for sitemaps: {e}")

    def _parse_xml_sitemap(self, content: str, base_url: str) -> Set[str]:
        """Parse XML sitemap content"""
        urls = set()
        try:
            soup = BeautifulSoup(content, 'xml')

            # Handle sitemap index
            sitemap_tags = soup.find_all('sitemap')
            for sitemap in sitemap_tags:
                loc = sitemap.find('loc')
                if loc:
                    urls.add(loc.get_text())

            # Handle URL entries
            url_tags = soup.find_all('url')
            for url_tag in url_tags:
                loc = url_tag.find('loc')
                if loc:
                    urls.add(loc.get_text())

        except Exception as e:
            logger.debug(f"Error parsing XML sitemap: {e}")

        return urls

    def _parse_text_sitemap(self, content: str, base_url: str) -> Set[str]:
        """Parse text sitemap content"""
        urls = set()
        for line in content.split('\n'):
            line = line.strip()
            if line and line.startswith('http'):
                urls.add(line)
        return urls

    async def _recursive_link_discovery(self, start_url: str, base_domain: str, discovered: Set[str], max_depth: int = 3, current_depth: int = 0):
        """Recursively discover links from pages"""
        if current_depth >= max_depth or len(discovered) > 1000:  # Limit to prevent infinite crawling
            return

        try:
            html, status_code, _, _ = await self.fetch_page(start_url)
            if html and status_code == 200:
                soup = BeautifulSoup(html, 'html.parser')

                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('/'):
                        full_url = urljoin(start_url, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue

                    parsed = urlparse(full_url)
                    if parsed.netloc == base_domain and full_url not in discovered:
                        discovered.add(full_url)

                        # Recursively crawl important pages (limit to prevent explosion)
                        if current_depth < 2 and len(discovered) < 500:
                            await self._recursive_link_discovery(full_url, base_domain, discovered, max_depth, current_depth + 1)

        except Exception as e:
            logger.debug(f"Error in recursive discovery from {start_url}: {e}")

    async def fetch_page(self, url: str, retries: int = 3) -> Tuple[Optional[str], int, float, str]:
        """Enhanced page fetching with better error handling"""
        headers = {}

        for attempt in range(retries):
            try:
                start_time = time.time()

                async with self.session.get(url, allow_redirects=True, headers=headers) as response:
                    content = await response.text(errors='ignore')
                    load_time = time.time() - start_time
                    content_type = response.headers.get('content-type', '').lower()

                    # Track data transfer
                    content_length = len(content.encode('utf-8'))
                    self.stats.total_data_transferred += content_length

                    return content, response.status, load_time, content_type

            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1})")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Error fetching {url} (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)

        return None, 0, 0.0, ""

    def analyze_page_seo_enhanced(self, url: str, html: str, target_keyword: str, 
                                status_code: int, load_time: float, content_type: str) -> SEOPageData:
        """Enhanced comprehensive SEO analysis of a single page"""

        soup = BeautifulSoup(html, 'html.parser')

        # Basic elements
        title = soup.title.string.strip() if soup.title else None
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc.get('content', '').strip() if meta_desc else None
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        meta_keywords_content = meta_keywords.get('content', '').strip() if meta_keywords else None

        # Enhanced heading analysis
        headings = {}
        for level in range(1, 7):
            tags = soup.find_all(f'h{level}')
            headings[f'h{level}_tags'] = [h.get_text().strip() for h in tags]
            headings[f'h{level}_count'] = len(tags)

        # Content analysis
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()

        text_content = soup.get_text()
        text_content = re.sub(r'\s+', ' ', text_content.strip())

        word_count = len(text_content.split())
        char_count = len(text_content)

        # Calculate text-to-HTML ratio
        html_size = len(html)
        text_to_html_ratio = len(text_content) / html_size * 100 if html_size > 0 else 0

        # Keyword analysis
        keyword_count = text_content.lower().count(target_keyword.lower())
        keyword_density = (keyword_count / word_count * 100) if word_count > 0 else 0

        # Enhanced readability analysis
        readability_score = self._calculate_enhanced_readability(text_content)

        # Links analysis
        internal_links, external_links = self._analyze_links(soup, url)

        # Enhanced image analysis
        images = self._analyze_images_enhanced(soup, url)

        # Technical SEO analysis
        technical_data = self._analyze_technical_seo(soup, url)

        # Performance metrics
        performance_metrics = self._calculate_performance_metrics(html, load_time)

        # SEO Issues Detection (Enhanced)
        seo_issues = self._detect_seo_issues_enhanced(
            soup, title, meta_description, headings['h1_tags'], 
            target_keyword, word_count, images, technical_data, url
        )

        # Create enhanced page data
        page_data = SEOPageData(
            url=url,
            title=title,
            meta_description=meta_description,
            meta_keywords=meta_keywords_content,
            h1_tags=headings['h1_tags'],
            h2_tags=headings['h2_tags'],
            h3_tags=headings['h3_tags'],
            h4_tags=headings['h4_tags'],
            h5_tags=headings['h5_tags'],
            h6_tags=headings['h6_tags'],
            word_count=word_count,
            char_count=char_count,
            internal_links=internal_links[:50],  # Limit for storage
            external_links=external_links[:20],
            images=images[:30],
            load_time=load_time,
            status_code=status_code,
            content_type=content_type,
            canonical_url=technical_data.get('canonical_url'),
            meta_robots=technical_data.get('meta_robots'),
            og_tags=technical_data.get('og_tags', {}),
            twitter_tags=technical_data.get('twitter_tags', {}),
            schema_markup=technical_data.get('schema_markup', []),
            keyword_density=keyword_density,
            readability_score=readability_score,
            seo_issues=seo_issues,
            performance_metrics=performance_metrics,
            mobile_friendly=technical_data.get('mobile_friendly', False),
            has_viewport=technical_data.get('has_viewport', False),
            ssl_enabled=url.startswith('https://'),

            # Enhanced fields
            text_to_html_ratio=text_to_html_ratio,
            js_files=technical_data.get('js_files', []),
            css_files=technical_data.get('css_files', []),
            forms=technical_data.get('forms', []),
            meta_tags=technical_data.get('all_meta_tags', {}),
            heading_structure={f'h{i}': headings[f'h{i}_count'] for i in range(1, 7)},
            content_language=technical_data.get('content_language'),
            page_size_bytes=len(html.encode('utf-8')),
            crawl_timestamp=datetime.now()
        )

        return page_data

    def _analyze_links(self, soup: BeautifulSoup, base_url: str) -> Tuple[List[str], List[str]]:
        """Enhanced link analysis"""
        internal_links = []
        external_links = []
        base_domain = urlparse(base_url).netloc

        for link in soup.find_all('a', href=True):
            href = link['href']

            # Skip javascript and mailto links
            if href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                continue

            try:
                if href.startswith('/'):
                    absolute_url = urljoin(base_url, href)
                elif href.startswith('http'):
                    absolute_url = href
                else:
                    absolute_url = urljoin(base_url, href)

                parsed_url = urlparse(absolute_url)
                if parsed_url.netloc == base_domain or not parsed_url.netloc:
                    internal_links.append(absolute_url)
                else:
                    external_links.append(absolute_url)

            except Exception:
                continue

        return internal_links, external_links

    def _analyze_images_enhanced(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Enhanced image analysis"""
        images = []

        for img in soup.find_all('img'):
            img_data = {
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'has_alt': bool(img.get('alt', '').strip()),
                'loading': img.get('loading', ''),
                'width': img.get('width', ''),
                'height': img.get('height', ''),
                'class': ' '.join(img.get('class', [])),
                'sizes': img.get('sizes', ''),
                'srcset': img.get('srcset', ''),
                'decoding': img.get('decoding', ''),
                'is_lazy_loaded': img.get('loading') == 'lazy' or 'lazy' in img.get('class', [])
            }

            # Calculate estimated file size from dimensions if available
            try:
                if img_data['width'] and img_data['height']:
                    w, h = int(img_data['width']), int(img_data['height'])
                    img_data['estimated_size_kb'] = (w * h * 3) // 1024  # Rough estimate
            except:
                pass

            images.append(img_data)

        return images

    def _analyze_technical_seo(self, soup: BeautifulSoup, url: str) -> Dict:
        """Comprehensive technical SEO analysis"""
        technical_data = {}

        # Canonical URL
        canonical_tag = soup.find('link', rel='canonical')
        technical_data['canonical_url'] = canonical_tag.get('href') if canonical_tag else None

        # Meta robots
        robots_tag = soup.find('meta', attrs={'name': 'robots'})
        technical_data['meta_robots'] = robots_tag.get('content', '') if robots_tag else None

        # Viewport
        viewport_tag = soup.find('meta', attrs={'name': 'viewport'})
        technical_data['has_viewport'] = viewport_tag is not None
        technical_data['mobile_friendly'] = viewport_tag and 'width=device-width' in viewport_tag.get('content', '') if viewport_tag else False

        # Open Graph tags
        og_tags = {}
        for og_tag in soup.find_all('meta', property=lambda x: x and x.startswith('og:')):
            og_tags[og_tag.get('property')] = og_tag.get('content', '')
        technical_data['og_tags'] = og_tags

        # Twitter Card tags
        twitter_tags = {}
        for twitter_tag in soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')}):
            twitter_tags[twitter_tag.get('name')] = twitter_tag.get('content', '')
        technical_data['twitter_tags'] = twitter_tags

        # All meta tags
        all_meta_tags = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
            content = meta.get('content')
            if name and content:
                all_meta_tags[name] = content
        technical_data['all_meta_tags'] = all_meta_tags

        # Language detection
        html_tag = soup.find('html')
        technical_data['content_language'] = html_tag.get('lang') if html_tag else None

        # JavaScript and CSS files
        js_files = [script.get('src') for script in soup.find_all('script', src=True)]
        css_files = [link.get('href') for link in soup.find_all('link', rel='stylesheet', href=True)]

        technical_data['js_files'] = js_files[:20]  # Limit for storage
        technical_data['css_files'] = css_files[:20]

        # Forms analysis
        forms = []
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'get').lower(),
                'inputs': len(form.find_all('input')),
                'has_validation': bool(form.find_all(['input'], required=True))
            }
            forms.append(form_data)
        technical_data['forms'] = forms

        # Schema markup
        technical_data['schema_markup'] = self._extract_schema_markup(soup)

        return technical_data

    def _calculate_enhanced_readability(self, text: str) -> float:
        """Enhanced readability calculation with multiple metrics"""
        if not text.strip():
            return 0.0

        sentences = max(1, len(re.findall(r'[.!?]+', text)))
        words = text.split()
        word_count = len(words)

        if word_count == 0:
            return 0.0

        # Calculate syllables
        syllables = sum(self._count_syllables(word) for word in words)

        # Flesch Reading Ease Score
        flesch_score = 206.835 - (1.015 * (word_count / sentences)) - (84.6 * (syllables / word_count))

        # Additional readability factors
        avg_word_length = sum(len(word) for word in words) / word_count
        complex_words = sum(1 for word in words if self._count_syllables(word) > 2)
        complex_word_ratio = complex_words / word_count

        # Adjust score based on additional factors
        if avg_word_length > 6:
            flesch_score -= 5
        if complex_word_ratio > 0.3:
            flesch_score -= 10

        return max(0, min(100, flesch_score))

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower().strip('.,!?";:')
        if not word:
            return 0

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

        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1

        return max(1, syllable_count)

    def _extract_schema_markup(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract structured data (JSON-LD, Microdata, RDFa)"""
        schema_data = []

        # JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                schema_data.append({'type': 'json-ld', 'data': data})
            except (json.JSONDecodeError, TypeError):
                continue

        # Microdata
        for item in soup.find_all(attrs={'itemscope': True}):
            item_data = {
                'type': 'microdata',
                'itemtype': item.get('itemtype', ''),
                'properties': {}
            }

            for prop in item.find_all(attrs={'itemprop': True}):
                prop_name = prop.get('itemprop')
                prop_value = prop.get('content') or prop.get_text(strip=True)
                item_data['properties'][prop_name] = prop_value

            schema_data.append(item_data)

        return schema_data

    def _calculate_performance_metrics(self, html: str, load_time: float) -> Dict[str, float]:
        """Calculate performance-related metrics"""
        html_size = len(html.encode('utf-8'))

        metrics = {
            'load_time': load_time,
            'page_size_bytes': html_size,
            'page_size_kb': html_size / 1024,
            'estimated_render_time': load_time * 1.2,  # Rough estimate
        }

        # Performance scoring
        if load_time < 2:
            metrics['speed_score'] = 90
        elif load_time < 4:
            metrics['speed_score'] = 70
        elif load_time < 6:
            metrics['speed_score'] = 50
        else:
            metrics['speed_score'] = 30

        return metrics

    def _detect_seo_issues_enhanced(self, soup: BeautifulSoup, title: str, meta_description: str,
                                  h1_tags: List[str], target_keyword: str, word_count: int,
                                  images: List[Dict], technical_data: Dict, url: str) -> List[str]:
        """Enhanced SEO issues detection with priority scoring"""
        issues = []

        # Title issues (Critical)
        if not title:
            issues.append("CRITICAL: Missing title tag")
        else:
            if len(title) < 30:
                issues.append(f"HIGH: Title too short ({len(title)} chars, recommended: 30-60)")
            elif len(title) > 60:
                issues.append(f"HIGH: Title too long ({len(title)} chars, recommended: 30-60)")

            if target_keyword.lower() not in title.lower():
                issues.append("HIGH: Target keyword not in title")

        # Meta description issues (High)
        if not meta_description:
            issues.append("HIGH: Missing meta description")
        else:
            if len(meta_description) < 120:
                issues.append(f"MEDIUM: Meta description too short ({len(meta_description)} chars)")
            elif len(meta_description) > 160:
                issues.append(f"MEDIUM: Meta description too long ({len(meta_description)} chars)")

            if target_keyword.lower() not in meta_description.lower():
                issues.append("MEDIUM: Target keyword not in meta description")

        # Heading issues (High)
        if not h1_tags:
            issues.append("CRITICAL: Missing H1 tag")
        elif len(h1_tags) > 1:
            issues.append(f"HIGH: Multiple H1 tags ({len(h1_tags)}) - should be unique")
        else:
            if target_keyword.lower() not in h1_tags[0].lower():
                issues.append("MEDIUM: Target keyword not in H1")

        # Content issues
        if word_count < 300:
            issues.append(f"HIGH: Thin content ({word_count} words, recommended: 300+)")
        elif word_count < 500:
            issues.append(f"MEDIUM: Short content ({word_count} words, recommended: 500+)")

        # Image issues
        missing_alt_images = len([img for img in images if not img['has_alt']])
        if missing_alt_images > 0:
            issues.append(f"MEDIUM: {missing_alt_images} images missing alt text")

        # Technical issues
        if not technical_data.get('has_viewport'):
            issues.append("HIGH: Missing viewport meta tag")

        if not url.startswith('https://'):
            issues.append("CRITICAL: Not using HTTPS")

        if not technical_data.get('canonical_url'):
            issues.append("MEDIUM: Missing canonical URL")

        # Performance issues
        if len(technical_data.get('js_files', [])) > 10:
            issues.append("MEDIUM: Too many JavaScript files (consider combining)")

        if len(technical_data.get('css_files', [])) > 5:
            issues.append("MEDIUM: Too many CSS files (consider combining)")

        # Social media optimization
        if not technical_data.get('og_tags'):
            issues.append("LOW: Missing Open Graph tags")

        if not technical_data.get('twitter_tags'):
            issues.append("LOW: Missing Twitter Card tags")

        # Structured data
        if not technical_data.get('schema_markup'):
            issues.append("LOW: No structured data (Schema.org) found")

        return issues

    async def crawl_website_enhanced(self, start_url: str, target_keyword: str, max_pages: int = None, 
                                   whole_website: bool = False) -> Tuple[List[SEOPageData], CrawlStats]:
        """Enhanced crawling with caching and comprehensive analysis"""

        logger.info(f"Starting enhanced crawl of {start_url} (whole_website: {whole_website})")

        # Get cached URLs to avoid re-crawling
        domain = urlparse(start_url).netloc
        cached_urls = self.cache_manager.get_cached_urls_for_domain(domain)

        if whole_website:
            # Discover all URLs for the domain
            urls_to_crawl = await self.discover_urls(start_url)
            max_pages = len(urls_to_crawl) if max_pages is None else max_pages
        else:
            urls_to_crawl = {start_url}
            max_pages = max_pages or 10

        # Process URLs with caching
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)

        for url in list(urls_to_crawl)[:max_pages]:
            if url in self.crawled_urls:
                continue

            self.stats.total_pages += 1

            # Check cache first
            cached_page = self.cache_manager.get_cached_page(url)
            if cached_page and url in cached_urls:
                self.pages_data.append(cached_page)
                self.stats.successful_pages += 1
                self.stats.cached_pages += 1
                logger.info(f"Using cached data for: {url}")
                continue

            async with semaphore:
                logger.info(f"Crawling ({len(self.pages_data)+1}/{max_pages}): {url}")

                html, status_code, load_time, content_type = await self.fetch_page(url)

                if html and status_code == 200:
                    try:
                        # Enhanced SEO analysis
                        page_data = self.analyze_page_seo_enhanced(
                            url, html, target_keyword, status_code, load_time, content_type
                        )

                        page_data.page_depth = len(self.pages_data)
                        self.pages_data.append(page_data)
                        self.stats.successful_pages += 1
                        self.stats.total_issues += len(page_data.seo_issues)

                        # Cache the page data
                        content_hash = hashlib.md5(html.encode()).hexdigest()
                        self.cache_manager.cache_page(page_data, content_hash)

                        # Discover more URLs from this page (if not whole website mode)
                        if not whole_website and len(self.pages_data) < max_pages:
                            soup = BeautifulSoup(html, 'html.parser')
                            for link in soup.find_all('a', href=True)[:10]:  # Limit discovery
                                href = link['href']
                                if href.startswith('/'):
                                    new_url = urljoin(start_url, href)
                                elif href.startswith('http') and urlparse(href).netloc == domain:
                                    new_url = href
                                else:
                                    continue

                                if new_url not in self.crawled_urls and len(urls_to_crawl) < max_pages * 2:
                                    urls_to_crawl.add(new_url)

                    except Exception as e:
                        logger.error(f"Error analyzing {url}: {e}")
                        self.stats.failed_pages += 1
                else:
                    self.stats.failed_pages += 1

                self.crawled_urls.add(url)

                # Respectful delay
                if self.config.request_delay > 0:
                    await asyncio.sleep(self.config.request_delay)

        logger.info(f"Enhanced crawl completed: {self.stats.successful_pages} successful, "
                   f"{self.stats.failed_pages} failed, {self.stats.cached_pages} from cache")

        return self.pages_data, self.stats

class EnhancedSEOEngine:
    """Enhanced SEO analysis engine with comprehensive features"""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.cache_manager = CacheManager()

        # Cleanup old cache on initialization
        self.cache_manager.cleanup_old_cache()

    def analyze_website(self, website_url: str, target_keyword: str, max_pages: int = 10, 
                       whole_website: bool = False) -> Dict:
        """Enhanced website analysis with caching and SERP analysis"""
        return asyncio.run(self._analyze_website_async(
            website_url, target_keyword, max_pages, whole_website
        ))

    async def _analyze_website_async(self, website_url: str, target_keyword: str, 
                                   max_pages: int, whole_website: bool = False) -> Dict:
        """Async enhanced website analysis"""

        self.logger.info(f"Starting enhanced SEO analysis for {website_url}")

        async with EnhancedSEOCrawler(self.config, self.cache_manager) as crawler:
            # Crawl website
            pages_data, crawl_stats = await crawler.crawl_website_enhanced(
                website_url, target_keyword, max_pages, whole_website
            )

            if not pages_data:
                return {
                    'report': self._generate_error_report(
                        "No pages could be crawled", website_url, target_keyword
                    ),
                    'metadata': {
                        'status': 'error',
                        'pages_analyzed': 0,
                        'issues_found': 0,
                        'cached_pages': 0
                    }
                }

            # SERP Analysis (if enabled)
            serp_results = []
            if self.config.serp_analysis_enabled:
                try:
                    async with aiohttp.ClientSession() as session:
                        serp_results = await crawler.serp_analyzer.analyze_serp(target_keyword, session)
                        self.logger.info(f"SERP analysis completed: {len(serp_results)} results")
                except Exception as e:
                    self.logger.warning(f"SERP analysis failed: {e}")

            # Generate comprehensive report
            report = await self._generate_enhanced_report(
                pages_data, crawl_stats, website_url, target_keyword, serp_results, whole_website
            )

            # Export comprehensive CSV
            csv_data = await self._export_comprehensive_csv(pages_data, target_keyword, serp_results)

            # Generate metadata
            metadata = {
                'status': 'success',
                'pages_analyzed': len(pages_data),
                'cached_pages': crawl_stats.cached_pages,
                'issues_found': sum(len(page.seo_issues) for page in pages_data),
                'crawl_duration': crawl_stats.crawl_duration,
                'average_load_time': crawl_stats.average_load_time,
                'seo_score': self._calculate_enhanced_seo_score(pages_data),
                'serp_results_count': len(serp_results),
                'total_data_transferred': crawl_stats.total_data_transferred,
                'whole_website_analysis': whole_website,
                'discovered_urls': len(crawler.discovered_urls),
                'sitemap_urls': len(crawler.sitemap_urls)
            }

            return {
                'report': report,
                'metadata': metadata,
                'csv_data': csv_data,
                'pages_data': pages_data,  # For advanced processing
                'serp_results': serp_results
            }

    def _calculate_enhanced_seo_score(self, pages_data: List[SEOPageData]) -> float:
        """Calculate enhanced SEO score with weighted factors"""
        if not pages_data:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for page in pages_data:
            page_score = 100.0
            page_weight = 1.0

            # Adjust weight based on page importance (homepage gets higher weight)
            if page.page_depth == 0:  # Homepage
                page_weight = 3.0
            elif page.page_depth <= 2:  # Important pages
                page_weight = 2.0

            # Deduct points based on issue severity
            for issue in page.seo_issues:
                if 'CRITICAL' in issue:
                    page_score -= 20
                elif 'HIGH' in issue:
                    page_score -= 10
                elif 'MEDIUM' in issue:
                    page_score -= 5
                elif 'LOW' in issue:
                    page_score -= 2

            # Performance bonuses/penalties
            if page.load_time < 2.0:
                page_score += 5
            elif page.load_time > 5.0:
                page_score -= 15

            # Content quality bonuses
            if page.word_count > 1000:
                page_score += 5
            elif page.word_count < 300:
                page_score -= 10

            # Technical SEO bonuses
            if page.ssl_enabled:
                page_score += 2
            if page.mobile_friendly:
                page_score += 3
            if page.schema_markup:
                page_score += 3

            page_score = max(0.0, min(100.0, page_score))
            total_score += page_score * page_weight
            total_weight += page_weight

        final_score = total_score / total_weight if total_weight > 0 else 0
        return round(final_score, 1)

    async def _generate_enhanced_report(self, pages_data: List[SEOPageData], crawl_stats: CrawlStats,
                                      website_url: str, target_keyword: str, serp_results: List[SERPResult],
                                      whole_website: bool = False) -> str:
        """Generate comprehensive enhanced SEO report"""

        # Calculate comprehensive metrics
        total_issues = sum(len(page.seo_issues) for page in pages_data)
        total_words = sum(page.word_count for page in pages_data)
        avg_load_time = sum(page.load_time for page in pages_data) / len(pages_data) if pages_data else 0
        seo_score = self._calculate_enhanced_seo_score(pages_data)

        # Generate comprehensive report
        report_lines = [
            "# 🔍 COMPREHENSIVE SEO AUDIT REPORT - ENHANCED V3.0",
            "",
            f"**Website:** {website_url}",
            f"**Target Keyword:** \"{target_keyword}\"",
            f"**Analysis Type:** {'Whole Website Analysis' if whole_website else 'Selective Page Analysis'}",
            f"**Audit Date:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            f"**Pages Analyzed:** {len(pages_data)} ({crawl_stats.cached_pages} from cache)",
            f"**Data Transfer:** {crawl_stats.total_data_transferred / 1024 / 1024:.2f} MB",
            "",
            "---",
            "",
            f"## 📊 OVERALL SEO SCORE: {seo_score:.1f}/100",
            "",
            f"### 🎯 Executive Summary",
            f"Your website scored **{seo_score:.1f}/100** in our comprehensive SEO analysis. "
            f"We analyzed {len(pages_data)} pages and found {total_issues} issues that need attention.",
            "",
            "### 📈 Key Performance Indicators",
            "",
            "| Metric | Value | Status |",
            "|--------|-------|--------|",
            f"| **SEO Score** | {seo_score:.1f}/100 | {'🟢 Excellent' if seo_score >= 80 else '🟡 Good' if seo_score >= 60 else '🔴 Needs Work'} |",
            f"| **Total Content** | {total_words:,} words | {'🟢 Rich' if total_words >= 5000 else '🟡 Moderate' if total_words >= 2000 else '🔴 Thin'} |",
            f"| **Average Load Time** | {avg_load_time:.2f}s | {'🟢 Fast' if avg_load_time < 2 else '🟡 Average' if avg_load_time < 4 else '🔴 Slow'} |",
            f"| **Mobile Friendly** | {sum(1 for p in pages_data if p.mobile_friendly)}/{len(pages_data)} pages | {'🟢 Excellent' if sum(1 for p in pages_data if p.mobile_friendly)/len(pages_data) >= 0.9 else '🟡 Good' if sum(1 for p in pages_data if p.mobile_friendly)/len(pages_data) >= 0.7 else '🔴 Needs Work'} |",
            f"| **HTTPS Usage** | {sum(1 for p in pages_data if p.ssl_enabled)}/{len(pages_data)} pages | {'🟢 Secure' if sum(1 for p in pages_data if p.ssl_enabled) == len(pages_data) else '🔴 Insecure'} |",
            f"| **Issues Found** | {total_issues} total | {'🟢 Clean' if total_issues == 0 else '🟡 Minor' if total_issues <= 10 else '🔴 Many'} |",
            "",
            "## 📄 Detailed Page Analysis",
            ""
        ]

        # Add detailed page analysis
        for i, page in enumerate(pages_data, 1):
            page_score = self._calculate_page_score(page)
            report_lines.extend([
                f"### Page {i}: {page.title or 'Untitled'}",
                f"**URL:** {page.url}",
                f"**Page Score:** {page_score:.1f}/100 | **Word Count:** {page.word_count} | **Load Time:** {page.load_time:.2f}s",
                ""
            ])

            if page.seo_issues:
                report_lines.append("**Issues Found:**")
                for issue in page.seo_issues[:10]:  # Limit to top 10 issues
                    if 'CRITICAL' in issue:
                        icon = '🔴'
                    elif 'HIGH' in issue:
                        icon = '🟠'
                    elif 'MEDIUM' in issue:
                        icon = '🟡'
                    else:
                        icon = '🟢'
                    report_lines.append(f"- {icon} {issue}")

                if len(page.seo_issues) > 10:
                    report_lines.append(f"- ... and {len(page.seo_issues) - 10} more issues")
            else:
                report_lines.append("- ✅ No issues found on this page!")

            report_lines.append("")

        # Final summary
        report_lines.extend([
            "",
            "---",
            "",
            "## 📊 Analysis Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| **Pages Analyzed** | {len(pages_data)} |",
            f"| **Cached Pages Used** | {crawl_stats.cached_pages} |",
            f"| **Total Issues Found** | {total_issues} |",
            f"| **Analysis Duration** | {crawl_stats.crawl_duration:.1f} seconds |",
            f"| **Average Page Load Time** | {avg_load_time:.2f} seconds |",
            f"| **Total Content Words** | {total_words:,} |",
            f"| **Data Analyzed** | {crawl_stats.total_data_transferred / 1024 / 1024:.2f} MB |",
            "",
            "### 🚀 Next Steps",
            "1. **📥 Address Critical and High priority issues immediately**",
            "2. **📊 Download the comprehensive CSV report for detailed analysis**",
            "3. **🔄 Re-run this audit monthly to track improvements**",
            "4. **📈 Focus on content expansion for thin pages**",
            "5. **⚡ Optimize page load speeds for better user experience**",
            "",
            "---",
            "",
            f"*🤖 Enhanced SEO Audit Report V3.0 generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*",
            "",
            f"**Analysis included:** {'Comprehensive site crawl' if whole_website else 'Selective page analysis'} | "
            f"SERP analysis: {'✅' if serp_results else '❌'} | "
            f"Caching: ✅ ({crawl_stats.cached_pages} pages from cache)",
            "",
            "*For questions or advanced SEO strategies, consult with an SEO professional.* 🚀"
        ])

        return "\n".join(report_lines)

    def _calculate_page_score(self, page: SEOPageData) -> float:
        """Calculate individual page SEO score"""
        score = 100.0

        for issue in page.seo_issues:
            if 'CRITICAL' in issue:
                score -= 20
            elif 'HIGH' in issue:
                score -= 10
            elif 'MEDIUM' in issue:
                score -= 5
            else:
                score -= 2

        return max(0.0, min(100.0, score))

    async def _export_comprehensive_csv(self, pages_data: List[SEOPageData], 
                                      target_keyword: str, serp_results: List[SERPResult]) -> str:
        """Export comprehensive CSV data"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"seo_comprehensive_analysis_{timestamp}.csv"

        # Prepare comprehensive data
        csv_data = []

        for page in pages_data:
            row = {
                'URL': page.url,
                'Title': page.title or '',
                'Meta_Description': page.meta_description or '',
                'H1_Count': len(page.h1_tags),
                'H2_Count': len(page.h2_tags),
                'H3_Count': len(page.h3_tags),
                'Word_Count': page.word_count,
                'Character_Count': page.char_count,
                'Load_Time_Seconds': page.load_time,
                'Status_Code': page.status_code,
                'Page_Size_KB': page.page_size_bytes / 1024,
                'Internal_Links_Count': len(page.internal_links),
                'External_Links_Count': len(page.external_links),
                'Images_Count': len(page.images),
                'Images_Missing_Alt': len([img for img in page.images if not img['has_alt']]),
                'Keyword_Density_Percent': page.keyword_density,
                'Readability_Score': page.readability_score,
                'Mobile_Friendly': page.mobile_friendly,
                'HTTPS_Enabled': page.ssl_enabled,
                'Has_Canonical': bool(page.canonical_url),
                'Has_Schema_Markup': bool(page.schema_markup),
                'Text_HTML_Ratio': page.text_to_html_ratio,
                'SEO_Issues_Count': len(page.seo_issues),
                'Critical_Issues': len([i for i in page.seo_issues if 'CRITICAL' in i]),
                'High_Issues': len([i for i in page.seo_issues if 'HIGH' in i]),
                'Medium_Issues': len([i for i in page.seo_issues if 'MEDIUM' in i]),
                'Low_Issues': len([i for i in page.seo_issues if 'LOW' in i]),
                'Page_Score': self._calculate_page_score(page),
                'Crawl_Date': page.crawl_timestamp.isoformat(),
                'Target_Keyword': target_keyword,
                'All_Issues': '; '.join(page.seo_issues),
                'Content_Language': page.content_language or '',
                'JS_Files_Count': len(page.js_files),
                'CSS_Files_Count': len(page.css_files),
                'Forms_Count': len(page.forms)
            }

            csv_data.append(row)

        # Save CSV file
        exports_dir = Path("exports")
        exports_dir.mkdir(parents=True, exist_ok=True)
        filepath = exports_dir / filename

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            if csv_data:
                writer = csv.DictWriter(csvfile, fieldnames=csv_data[0].keys())
                writer.writeheader()
                writer.writerows(csv_data)

        self.logger.info(f"Comprehensive CSV exported: {filepath}")
        return str(filepath)

    def _generate_error_report(self, error_msg: str, website_url: str, target_keyword: str) -> str:
        """Generate enhanced error report"""
        return f"""# 🚨 Enhanced SEO Audit Error Report V3.0

**Website:** {website_url}
**Target Keyword:** {target_keyword}
**Error:** {error_msg}
**Date:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

## 🔍 Troubleshooting Steps:

### 1. Website Accessibility
- Verify the website is online and accessible
- Check for server downtime or maintenance
- Ensure the URL format is correct (include https://)

### 2. Crawling Restrictions
- Review robots.txt file for crawling permissions
- Check for IP blocking or geographic restrictions
- Verify the website allows automated access

### 3. Technical Issues
- Test website loading in a regular browser
- Check for JavaScript-heavy content that may block crawling
- Verify SSL certificate is valid if using HTTPS

### 4. Alternative Solutions
- Try crawling individual pages instead of whole website
- Use a different target keyword
- Wait a few minutes and retry the analysis

## 📞 Support Options
If issues persist, this could indicate:
- Temporary server issues on the target website
- Network connectivity problems
- Advanced bot protection on the target site

**Recommendation:** Try again in 5-10 minutes or contact support for advanced troubleshooting.

---
*Enhanced SEO Audit Tool V3.0 - Built for comprehensive website analysis*
"""

# Replace the original SEOEngine class name for backward compatibility
SEOEngine = EnhancedSEOEngine
