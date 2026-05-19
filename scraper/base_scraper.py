"""
Base scraper class for documentation scraping
"""
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import logging
from urllib.parse import urljoin, urlparse
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for documentation scrapers"""
    
    def __init__(
        self,
        base_url: str,
        source_type: str,
        max_concurrent: int = 5,
        timeout: int = 30
    ):
        """
        Initialize scraper
        
        Args:
            base_url: Base URL for the documentation
            source_type: Type of source (e.g., "IBM Cloud Docs")
            max_concurrent: Maximum concurrent requests
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.source_type = source_type
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.session = None
        self.visited_urls = set()
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a single page
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        async with self.semaphore:
            try:
                logger.info(f"Fetching: {url}")
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        self.visited_urls.add(url)
                        return content
                    else:
                        logger.warning(f"Failed to fetch {url}: Status {response.status}")
                        return None
                        
            except asyncio.TimeoutError:
                logger.error(f"Timeout fetching {url}")
                return None
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                return None
    
    def parse_html(self, html: str, url: str) -> Dict[str, Any]:
        """
        Parse HTML content
        
        Args:
            html: HTML content
            url: Source URL
            
        Returns:
            Parsed document dictionary
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract main content
        content = self._extract_content(soup)
        
        # Extract links
        links = self._extract_links(soup, url)
        
        return {
            "title": title,
            "content": content,
            "url": url,
            "links": links,
            "source_type": self.source_type,
            "scraped_at": datetime.utcnow().isoformat()
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        # Try h1 first
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        # Try title tag
        title = soup.find('title')
        if title:
            return title.get_text(strip=True)
        
        return "Untitled"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content"""
        # Try to find main content area
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_='content') or
            soup.find('div', id='content') or
            soup.body
        )
        
        if main_content:
            # Get text with proper spacing
            text = main_content.get_text(separator='\n', strip=True)
            # Clean up multiple newlines
            text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
            return text
        
        return ""
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract links from page"""
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Only include links from the same domain
            if self._is_same_domain(absolute_url, self.base_url):
                links.append(absolute_url)
        
        return list(set(links))  # Remove duplicates
    
    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain"""
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2
    
    async def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a single URL
        
        Args:
            url: URL to scrape
            
        Returns:
            Parsed document or None
        """
        if url in self.visited_urls:
            logger.debug(f"Already visited: {url}")
            return None
        
        html = await self.fetch_page(url)
        if not html:
            return None
        
        return self.parse_html(html, url)
    
    async def scrape_urls(
        self,
        urls: List[str],
        max_depth: int = 1,
        follow_links: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs
        
        Args:
            urls: List of URLs to scrape
            max_depth: Maximum depth for link following
            follow_links: Whether to follow links
            
        Returns:
            List of parsed documents
        """
        documents = []
        urls_to_scrape = set(urls)
        current_depth = 0
        
        while urls_to_scrape and current_depth <= max_depth:
            logger.info(f"Scraping depth {current_depth}: {len(urls_to_scrape)} URLs")
            
            # Scrape current batch
            tasks = [self.scrape_url(url) for url in urls_to_scrape]
            results = await asyncio.gather(*tasks)
            
            # Collect documents and new links
            new_links = set()
            for doc in results:
                if doc:
                    documents.append(doc)
                    
                    if follow_links and current_depth < max_depth:
                        new_links.update(doc.get('links', []))
            
            # Prepare next batch
            if follow_links:
                urls_to_scrape = new_links - self.visited_urls
            else:
                urls_to_scrape = set()
            
            current_depth += 1
        
        logger.info(f"Scraped {len(documents)} documents")
        return documents

# Made with Bob
