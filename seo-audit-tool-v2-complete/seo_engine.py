"""
SEO Engine - Comprehensive website analysis system
Production-ready SEO auditing with async crawling and advanced analysis
"""

import asyncio
import aiohttp
import time
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus
from urllib.robotparser import RobotFileParser
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
import logging
from datetime import datetime
import hashlib
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SEOPageData:
    """Comprehensive SEO data for a single page"""
    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    h1_tags: List[str] = field(default_factory=list)
    h2_tags: List[str] = field(default_factory=list)
    h3_tags: List[str] = field(default_factory=list)
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

@dataclass
class CrawlStats:
    """Crawling statistics and metrics"""
    total_pages: int = 0
    successful_pages: int = 0
    failed_pages: int = 0
    total_issues: int = 0
    average_load_time: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    crawl_duration: float = 0.0

class SEOCrawler:
    """Advanced SEO crawler with comprehensive analysis"""
    
    def __init__(self, config):
        self.config = config
        self.session = None
        self.crawled_urls: Set[str] = set()
        self.pages_data: List[SEOPageData] = []
        self.stats = CrawlStats()
        self.robots_cache: Dict[str, RobotFileParser] = {}
        
        # Modern browser headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent_requests,
            limit_per_host=2,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.config.request_timeout,
            connect=10
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
        self.stats.crawl_duration = (
            self.stats.end_time - self.stats.start_time
        ).total_seconds()
        
        if self.pages_data:
            self.stats.average_load_time = sum(
                page.load_time for page in self.pages_data
            ) / len(self.pages_data)
    
    async def check_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt - Fixed for Python 3.13+"""
        if not self.config.respect_robots_txt:
            return True

        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if base_url not in self.robots_cache:
            robots_url = urljoin(base_url, '/robots.txt')
            try:
                async with self.session.get(robots_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        rp = RobotFileParser()
                        rp.set_url(robots_url)
                        # Use parse() instead of deprecated feed() method
                        rp.parse(content.splitlines())
                        self.robots_cache[base_url] = rp
                    else:
                        # If robots.txt not accessible, allow crawling
                        return True
            except Exception as e:
                logger.warning(f"Could not fetch robots.txt for {base_url}: {e}")
                return True

        robot_parser = self.robots_cache.get(base_url)
        if robot_parser:
            return robot_parser.can_fetch(self.headers['User-Agent'], url)
        
        return True  # Default to allowing if no parser
    async def fetch_page(self, url: str, retries: int = 3) -> Tuple[Optional[str], int, float, str]:
        """Fetch a single page with error handling"""
        for attempt in range(retries):
            try:
                if not await self.check_robots_txt(url):
                    logger.info(f"Robots.txt disallows crawling: {url}")
                    return None, 403, 0.0, "text/html"
                
                start_time = time.time()
                async with self.session.get(url, allow_redirects=True) as response:
                    content = await response.text(errors='ignore')
                    load_time = time.time() - start_time
                    content_type = response.headers.get('content-type', '').lower()
                    return content, response.status, load_time, content_type
                    
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Error fetching {url} (attempt {attempt + 1}): {e}")
            
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        return None, 0, 0.0, ""
    
    def calculate_readability(self, text: str) -> float:
        """Calculate Flesch Reading Ease score"""
        if not text.strip():
            return 0.0
        
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(text.split())
        syllables = sum(self.count_syllables(word) for word in text.split())
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Flesch Reading Ease formula
        score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        return max(0, min(100, score))
    
    def count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower()
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
        
        if word.endswith('e'):
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def extract_schema_markup(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract structured data (JSON-LD, Microdata)"""
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
                'itemtype': item.get('itemtype', '')
            }
            schema_data.append(item_data)
        
        return schema_data
    
    def analyze_page_seo(self, url: str, html: str, target_keyword: str,
                        status_code: int, load_time: float, content_type: str) -> SEOPageData:
        """Comprehensive SEO analysis of a single page"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Basic elements
        title = soup.title.string.strip() if soup.title else None
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc.get('content', '').strip() if meta_desc else None
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        meta_keywords_content = meta_keywords.get('content', '').strip() if meta_keywords else None
        
        # Headings
        h1_tags = [h1.get_text().strip() for h1 in soup.find_all('h1')]
        h2_tags = [h2.get_text().strip() for h2 in soup.find_all('h2')]
        h3_tags = [h3.get_text().strip() for h3 in soup.find_all('h3')]
        
        # Content analysis
        text_content = soup.get_text()
        word_count = len(text_content.split())
        char_count = len(text_content)
        
        # Keyword analysis
        keyword_count = text_content.lower().count(target_keyword.lower())
        keyword_density = (keyword_count / word_count * 100) if word_count > 0 else 0
        
        # Readability
        readability_score = self.calculate_readability(text_content)
        
        # Links analysis
        internal_links = []
        external_links = []
        base_domain = urlparse(url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith(('http', 'https')):
                absolute_url = href
            else:
                absolute_url = urljoin(url, href)
            
            parsed_url = urlparse(absolute_url)
            if parsed_url.netloc == base_domain or not parsed_url.netloc:
                internal_links.append(absolute_url)
            else:
                external_links.append(absolute_url)
        
        # Images analysis
        images = []
        for img in soup.find_all('img'):
            img_data = {
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'has_alt': bool(img.get('alt', '').strip()),
                'loading': img.get('loading', ''),
                'width': img.get('width', ''),
                'height': img.get('height', '')
            }
            images.append(img_data)
        
        # Meta tags analysis
        canonical_url = None
        canonical_tag = soup.find('link', rel='canonical')
        if canonical_tag:
            canonical_url = canonical_tag.get('href')
        
        meta_robots = None
        robots_tag = soup.find('meta', attrs={'name': 'robots'})
        if robots_tag:
            meta_robots = robots_tag.get('content', '')
        
        # Open Graph tags
        og_tags = {}
        for og_tag in soup.find_all('meta', property=lambda x: x and x.startswith('og:')):
            og_tags[og_tag.get('property')] = og_tag.get('content', '')
        
        # Twitter Card tags
        twitter_tags = {}
        for twitter_tag in soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')}):
            twitter_tags[twitter_tag.get('name')] = twitter_tag.get('content', '')
        
        # Technical analysis
        viewport_tag = soup.find('meta', attrs={'name': 'viewport'})
        has_viewport = viewport_tag is not None
        mobile_friendly = has_viewport and 'width=device-width' in viewport_tag.get('content', '') if viewport_tag else False
        ssl_enabled = url.startswith('https://')
        
        # Schema markup
        schema_markup = self.extract_schema_markup(soup)
        
        # SEO Issues Detection
        seo_issues = []
        
        # Title issues
        if not title:
            seo_issues.append("Missing title tag")
        else:
            if len(title) < 30:
                seo_issues.append(f"Title too short ({len(title)} chars)")
            elif len(title) > 60:
                seo_issues.append(f"Title too long ({len(title)} chars)")
            if target_keyword.lower() not in title.lower():
                seo_issues.append("Target keyword not in title")
        
        # Meta description issues
        if not meta_description:
            seo_issues.append("Missing meta description")
        else:
            if len(meta_description) < 120:
                seo_issues.append(f"Meta description too short ({len(meta_description)} chars)")
            elif len(meta_description) > 160:
                seo_issues.append(f"Meta description too long ({len(meta_description)} chars)")
            if target_keyword.lower() not in meta_description.lower():
                seo_issues.append("Target keyword not in meta description")
        
        # Heading issues
        if not h1_tags:
            seo_issues.append("Missing H1 tag")
        elif len(h1_tags) > 1:
            seo_issues.append(f"Multiple H1 tags ({len(h1_tags)})")
        else:
            if target_keyword.lower() not in h1_tags[0].lower():
                seo_issues.append("Target keyword not in H1")
        
        # Content issues
        if word_count < 300:
            seo_issues.append(f"Thin content ({word_count} words)")
        
        # Image issues
        missing_alt_images = len([img for img in images if not img['has_alt']])
        if missing_alt_images > 0:
            seo_issues.append(f"{missing_alt_images} images missing alt text")
        
        # Technical issues
        if not has_viewport:
            seo_issues.append("Missing viewport meta tag")
        if not ssl_enabled:
            seo_issues.append("Not using HTTPS")
        if not canonical_url:
            seo_issues.append("Missing canonical URL")
        if readability_score < 60:
            seo_issues.append(f"Low readability score ({readability_score:.1f})")
        
        # Internal linking issues
        if len(internal_links) == 0:
            seo_issues.append("No internal links")
        elif len(internal_links) < 3:
            seo_issues.append("Few internal links")
        
        # Performance metrics
        performance_metrics = {
            'load_time': load_time,
            'page_size_chars': len(html),
            'images_count': len(images),
            'links_count': len(internal_links) + len(external_links)
        }
        
        return SEOPageData(
            url=url,
            title=title,
            meta_description=meta_description,
            meta_keywords=meta_keywords_content,
            h1_tags=h1_tags,
            h2_tags=h2_tags,
            h3_tags=h3_tags,
            word_count=word_count,
            char_count=char_count,
            internal_links=internal_links[:20],
            external_links=external_links[:10],
            images=images[:20],
            load_time=load_time,
            status_code=status_code,
            content_type=content_type,
            canonical_url=canonical_url,
            meta_robots=meta_robots,
            og_tags=og_tags,
            twitter_tags=twitter_tags,
            schema_markup=schema_markup,
            keyword_density=keyword_density,
            readability_score=readability_score,
            seo_issues=seo_issues,
            performance_metrics=performance_metrics,
            mobile_friendly=mobile_friendly,
            has_viewport=has_viewport,
            ssl_enabled=ssl_enabled
        )
    
    async def crawl_website(self, start_url: str, target_keyword: str, max_pages: int) -> Tuple[List[SEOPageData], CrawlStats]:
        """Main crawling method"""
        urls_to_crawl = [start_url]
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        logger.info(f"Starting crawl of {start_url} with keyword: {target_keyword}")
        
        while urls_to_crawl and len(self.pages_data) < max_pages:
            current_url = urls_to_crawl.pop(0)
            
            if current_url in self.crawled_urls or not current_url.startswith(('http', 'https')):
                continue
            
            self.crawled_urls.add(current_url)
            self.stats.total_pages += 1
            
            async with semaphore:
                logger.info(f"Crawling ({len(self.pages_data)+1}/{max_pages}): {current_url}")
                
                html, status_code, load_time, content_type = await self.fetch_page(current_url)
                
                if html and status_code == 200:
                    try:
                        page_data = self.analyze_page_seo(
                            current_url, html, target_keyword,
                            status_code, load_time, content_type
                        )
                        
                        page_data.page_depth = len(self.pages_data)
                        self.pages_data.append(page_data)
                        self.stats.successful_pages += 1
                        self.stats.total_issues += len(page_data.seo_issues)
                        
                        # Add internal links to crawl queue
                        for link in page_data.internal_links:
                            if (link not in self.crawled_urls and
                                len(urls_to_crawl) < 100 and
                                link.startswith(('http', 'https'))):
                                urls_to_crawl.append(link)
                                
                    except Exception as e:
                        logger.error(f"Error analyzing {current_url}: {e}")
                        self.stats.failed_pages += 1
                else:
                    self.stats.failed_pages += 1
                
                # Respectful delay
                if self.config.request_delay > 0:
                    await asyncio.sleep(self.config.request_delay)
        
        logger.info(f"Crawl completed: {self.stats.successful_pages} successful, {self.stats.failed_pages} failed")
        return self.pages_data, self.stats

class SEOEngine:
    """Main SEO analysis engine"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def analyze_website(self, website_url: str, target_keyword: str, max_pages: int = 10) -> Dict:
        """Analyze website and return comprehensive report"""
        return asyncio.run(self._analyze_website_async(website_url, target_keyword, max_pages))
    
    async def _analyze_website_async(self, website_url: str, target_keyword: str, max_pages: int) -> Dict:
        """Async website analysis"""
        self.logger.info(f"Starting SEO analysis for {website_url}")
        
        async with SEOCrawler(self.config) as crawler:
            pages_data, crawl_stats = await crawler.crawl_website(
                website_url, target_keyword, max_pages
            )
        
        if not pages_data:
            return {
                'report': self._generate_error_report(
                    "No pages could be crawled", website_url, target_keyword
                ),
                'metadata': {
                    'status': 'error',
                    'pages_analyzed': 0,
                    'issues_found': 0
                }
            }
        
        report = await self._generate_comprehensive_report(
            pages_data, crawl_stats, website_url, target_keyword
        )
        
        # Export issues to CSV
        await self._export_issues_to_csv(pages_data, target_keyword)
        
        # Generate metadata
        metadata = {
            'status': 'success',
            'pages_analyzed': len(pages_data),
            'issues_found': sum(len(page.seo_issues) for page in pages_data),
            'crawl_duration': crawl_stats.crawl_duration,
            'average_load_time': crawl_stats.average_load_time,
            'seo_score': self._calculate_seo_score(pages_data)
        }
        
        return {
            'report': report,
            'metadata': metadata
        }
    
    def _calculate_seo_score(self, pages_data: List[SEOPageData]) -> float:
        """Calculate overall SEO score (0-100)"""
        if not pages_data:
            return 0.0
        
        score = 100.0
        
        # Deduct points for issues by priority
        for page in pages_data:
            for issue in page.seo_issues:
                priority = self._get_issue_priority(issue)
                if priority == 'Critical':
                    score -= 15
                elif priority == 'High':
                    score -= 8
                elif priority == 'Medium':
                    score -= 4
                elif priority == 'Low':
                    score -= 1
        
        # Performance bonus/penalty
        avg_load_time = sum(page.load_time for page in pages_data) / len(pages_data)
        if avg_load_time > 3.0:
            score -= 10
        elif avg_load_time < 1.0:
            score += 5
        
        return max(0.0, min(100.0, score))
    
    def _get_issue_priority(self, issue: str) -> str:
        """Determine issue priority"""
        issue_lower = issue.lower()
        
        if any(keyword in issue_lower for keyword in ['missing title', 'missing h1', 'not using https']):
            return 'Critical'
        elif any(keyword in issue_lower for keyword in ['title too short', 'missing meta description', 'keyword not in']):
            return 'High'
        elif any(keyword in issue_lower for keyword in ['thin content', 'missing alt', 'few internal links']):
            return 'Medium'
        else:
            return 'Low'
    
    async def _generate_comprehensive_report(self, pages_data: List[SEOPageData],
                                           crawl_stats: CrawlStats, website_url: str,
                                           target_keyword: str) -> str:
        """Generate comprehensive SEO report"""
        # Calculate metrics
        total_issues = sum(len(page.seo_issues) for page in pages_data)
        total_words = sum(page.word_count for page in pages_data)
        avg_load_time = sum(page.load_time for page in pages_data) / len(pages_data) if pages_data else 0
        seo_score = self._calculate_seo_score(pages_data)
        
        # Issue breakdown
        issue_breakdown = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
        for page in pages_data:
            for issue in page.seo_issues:
                priority = self._get_issue_priority(issue)
                issue_breakdown[priority] += 1
        
        # Generate report
        report_lines = [
            "# 🔍 COMPREHENSIVE SEO AUDIT REPORT",
            "",
            f"**Website:** {website_url}",
            f"**Target Keyword:** \"{target_keyword}\"",
            f"**Audit Date:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            f"**Pages Analyzed:** {len(pages_data)}",
            "",
            "---",
            "",
            f"## 📊 SEO Score: {seo_score:.1f}/100 (Grade: {self._get_grade(seo_score)})",
            "",
            "### 🎯 Key Metrics at a Glance",
            f"- **Total Content:** {total_words:,} words across all pages",
            f"- **Average Load Time:** {avg_load_time:.2f} seconds",
            f"- **Issues Found:** {total_issues} total issues requiring attention",
            f"- **Crawl Efficiency:** {crawl_stats.successful_pages}/{crawl_stats.total_pages} pages successfully analyzed",
            f"- **SEO Health:** {'Excellent' if seo_score >= 80 else 'Good' if seo_score >= 60 else 'Needs Improvement' if seo_score >= 40 else 'Poor'}",
            "",
            "### 🚨 Issue Breakdown",
            "| Priority | Count | Impact |",
            "|----------|-------|---------|",
        ]
        
        # Add issue breakdown
        for priority in ['Critical', 'High', 'Medium', 'Low']:
            count = issue_breakdown.get(priority, 0)
            icon = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}[priority]
            impact = {
                'Critical': 'Immediate action required',
                'High': 'Address within 1-2 weeks',
                'Medium': 'Address within 1 month',
                'Low': 'Address when possible'
            }[priority]
            report_lines.append(f"| {icon} **{priority}** | {count} | {impact} |")
        
        # Add detailed analysis
        report_lines.extend([
            "",
            "",
            "## 🔍 Detailed Page Analysis",
            ""
        ])
        
        for i, page in enumerate(pages_data, 1):
            report_lines.extend([
                f"### Page {i}: {page.title or 'Untitled'}",
                f"**URL:** {page.url}",
                f"**Word Count:** {page.word_count} | **Load Time:** {page.load_time:.2f}s | **Issues:** {len(page.seo_issues)}",
                ""
            ])
            
            if page.seo_issues:
                report_lines.append("**Issues Found:**")
                for issue in page.seo_issues:
                    priority = self._get_issue_priority(issue) 
                    icon = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}[priority]
                    report_lines.append(f"- {icon} {issue}")
                report_lines.append("")
        
        # Summary
        report_lines.extend([
            "---",
            "",
            "## 📊 Analysis Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| **Pages Analyzed** | {len(pages_data)} |",
            f"| **Total Issues Found** | {total_issues} |",
            f"| **Analysis Duration** | {crawl_stats.crawl_duration:.0f}s |",
            f"| **Average Page Load Time** | {avg_load_time:.2f}s |",
            f"| **Total Content Words** | {total_words:,} |",
            "",
            "### 💡 Priority Action Items",
            "1. **Address Critical Issues** - These are blocking your SEO success",
            "2. **Optimize Page Speed** - Improve user experience and ranking",
            "3. **Enhance Content Strategy** - Focus on keyword optimization",
            "4. **Improve Technical SEO** - Fix structural issues",
            "",
            "---",
            "",
            f"*🤖 Report generated by SEO Audit Tool on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*",
            "",
            "**Next Steps:**",
            "1. 📥 Address Critical and High priority issues first",
            "2. 📈 Monitor your SEO progress over time",
            "3. 🔄 Run follow-up audits monthly",
            "",
            "*Happy optimizing! 🚀*"
        ])
        
        return "\n".join(report_lines)
    
    def _get_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90: return "A+"
        elif score >= 80: return "A"
        elif score >= 70: return "B"
        elif score >= 60: return "C"
        elif score >= 50: return "D"
        else: return "F"
    
    async def _export_issues_to_csv(self, pages_data: List[SEOPageData], target_keyword: str):
        """Export SEO issues to CSV file"""
        issues_data = []
        
        for page in pages_data:
            for issue in page.seo_issues:
                issues_data.append({
                    'url': page.url,
                    'issue': issue,
                    'priority': self._get_issue_priority(issue),
                    'target_keyword': target_keyword,
                    'word_count': page.word_count,
                    'load_time': page.load_time,
                    'status_code': page.status_code,
                    'title': page.title,
                    'meta_description': page.meta_description
                })
        
        if issues_data:
            df = pd.DataFrame(issues_data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"seo_issues_{timestamp}.csv"
            
            # Ensure exports directory exists
            exports_dir = Path(self.config.exports_dir)
            exports_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = exports_dir / filename
            df.to_csv(filepath, index=False)
            self.logger.info(f"Issues exported to CSV: {filepath}")
    
    def _generate_error_report(self, error_msg: str, website_url: str, target_keyword: str) -> str:
        """Generate error report when analysis fails"""
        return f"""# 🚨 SEO Audit Error Report

**Website:** {website_url}
**Target Keyword:** {target_keyword}
**Error:** {error_msg}
**Date:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

## Possible Solutions:

1. Check if the website is accessible
2. Verify the URL format is correct
3. Ensure the website allows crawling (robots.txt)
4. Try again later if the site is temporarily unavailable

Please contact support if the issue persists.
"""