"""
Scraper for IBM Cloud documentation
"""
from typing import List, Dict, Any
import logging
from bs4 import BeautifulSoup

from backend.scraper.base_scraper import BaseScraper
from backend.scraper.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class IBMCloudScraper(BaseScraper):
    """Scraper for IBM Cloud documentation"""
    
    def __init__(self):
        """Initialize IBM Cloud scraper"""
        super().__init__(
            base_url="https://cloud.ibm.com/docs",
            source_type="IBM Cloud Docs"
        )
    
    def parse_html(self, html: str, url: str) -> Dict[str, Any]:
        """
        Parse IBM Cloud documentation HTML
        
        Args:
            html: HTML content
            url: Source URL
            
        Returns:
            Parsed document
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            element.decompose()
        
        # Remove navigation and sidebar
        for element in soup.find_all(['div'], class_=['navigation', 'sidebar', 'toc']):
            element.decompose()
        
        # Extract title
        title = self._extract_ibm_title(soup)
        
        # Extract main content
        content = self._extract_ibm_content(soup)
        
        # Extract breadcrumbs for context
        breadcrumbs = self._extract_breadcrumbs(soup)
        
        # Extract links
        links = self._extract_links(soup, url)
        
        return {
            "title": title,
            "content": content,
            "url": url,
            "links": links,
            "source_type": self.source_type,
            "breadcrumbs": breadcrumbs,
            "metadata": {
                "title": title,
                "url": url,
                "source_type": self.source_type,
                "breadcrumbs": " > ".join(breadcrumbs) if breadcrumbs else ""
            }
        }
    
    def _extract_ibm_title(self, soup: BeautifulSoup) -> str:
        """Extract title from IBM Cloud docs"""
        # Try different title locations
        title_selectors = [
            ('h1', {'class': 'title'}),
            ('h1', {}),
            ('title', {})
        ]
        
        for tag, attrs in title_selectors:
            element = soup.find(tag, attrs)
            if element:
                title = element.get_text(strip=True)
                # Clean up title
                title = title.replace(' - IBM Cloud Docs', '')
                title = title.replace(' | IBM Cloud', '')
                return title
        
        return "Untitled"
    
    def _extract_ibm_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from IBM Cloud docs"""
        # Try to find main content area
        content_selectors = [
            ('main', {}),
            ('article', {}),
            ('div', {'class': 'content'}),
            ('div', {'id': 'content'}),
            ('div', {'class': 'main-content'})
        ]
        
        for tag, attrs in content_selectors:
            main_content = soup.find(tag, attrs)
            if main_content:
                # Get text with proper spacing
                text = main_content.get_text(separator='\n', strip=True)
                # Clean up
                text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
                return text
        
        # Fallback to body
        if soup.body:
            text = soup.body.get_text(separator='\n', strip=True)
            text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
            return text
        
        return ""
    
    def _extract_breadcrumbs(self, soup: BeautifulSoup) -> List[str]:
        """Extract breadcrumb navigation"""
        breadcrumbs = []
        
        # Look for breadcrumb navigation
        breadcrumb_nav = soup.find('nav', {'aria-label': 'Breadcrumb'}) or soup.find('ol', class_='breadcrumb')
        
        if breadcrumb_nav:
            for link in breadcrumb_nav.find_all('a'):
                text = link.get_text(strip=True)
                if text:
                    breadcrumbs.append(text)
        
        return breadcrumbs
    
    async def scrape_section(
        self,
        section_url: str,
        max_pages: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Scrape a section of IBM Cloud documentation
        
        Args:
            section_url: Starting URL for the section
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of scraped documents
        """
        logger.info(f"Scraping IBM Cloud section: {section_url}")
        
        documents = await self.scrape_urls(
            urls=[section_url],
            max_depth=2,
            follow_links=True
        )
        
        # Limit to max_pages
        documents = documents[:max_pages]
        
        logger.info(f"Scraped {len(documents)} pages from IBM Cloud")
        
        return documents
    
    def process_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process scraped documents into chunks
        
        Args:
            documents: List of scraped documents
            
        Returns:
            List of processed document chunks
        """
        all_chunks = []
        
        # Filter out documents with empty content
        valid_documents = [doc for doc in documents if doc.get('content', '').strip()]
        
        if len(valid_documents) < len(documents):
            logger.warning(f"Filtered out {len(documents) - len(valid_documents)} documents with empty content")
        
        for doc in valid_documents:
            # Create chunks with metadata
            chunks = DocumentProcessor.create_chunks_with_metadata(
                document={
                    'content': doc['content'],
                    'metadata': doc['metadata']
                }
            )
            
            all_chunks.extend(chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(valid_documents)} documents")
        
        return all_chunks


# Predefined IBM Cloud documentation sections
# Using specific topic URLs that have static content instead of JS-rendered landing pages
IBM_CLOUD_SECTIONS = {
    "overview": "https://cloud.ibm.com/docs/overview?topic=overview-whatis-platform",
    "account": "https://cloud.ibm.com/docs/account?topic=account-account-getting-started",
    "iam": "https://cloud.ibm.com/docs/account?topic=account-iamoverview",
    "containers": "https://cloud.ibm.com/docs/containers?topic=containers-getting-started",
    "kubernetes": "https://cloud.ibm.com/docs/containers?topic=containers-cs_tech",
    "openshift": "https://cloud.ibm.com/docs/openshift?topic=openshift-getting-started",
    "vpc": "https://cloud.ibm.com/docs/vpc?topic=vpc-getting-started",
    "compute": "https://cloud.ibm.com/docs/virtual-servers?topic=virtual-servers-getting-started-tutorial",
    "storage": "https://cloud.ibm.com/docs/cloud-object-storage?topic=cloud-object-storage-getting-started-cloud-object-storage",
    "networking": "https://cloud.ibm.com/docs/vpc?topic=vpc-about-networking-for-vpc",
    "databases": "https://cloud.ibm.com/docs/databases-for-postgresql?topic=databases-for-postgresql-getting-started",
    "ai": "https://cloud.ibm.com/docs/watson?topic=watson-about",
    "devops": "https://cloud.ibm.com/docs/ContinuousDelivery?topic=ContinuousDelivery-getting-started",
    "security": "https://cloud.ibm.com/docs/security-compliance?topic=security-compliance-getting-started"
}

# Made with Bob
