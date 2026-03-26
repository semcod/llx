
"""
Async/Await Refactored Version
Clean, maintainable async code without callback hell
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ScrapedContent:
    """Data class for scraped content"""
    url: str
    title: str
    description: str
    headings: List[Dict]
    images: List[Dict]
    error: Optional[str] = None


class AsyncWebScraper:
    """Modern async scraper using aiohttp and async/await"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape_website(self, url: str) -> Dict:
        """Scrape website and return structured data"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    links = await self._parse_links(html, url)
                    
                    # Scrape multiple links concurrently
                    scraped_links = await asyncio.gather(
                        *[self._scrape_single_link(link) for link in links[:5]],
                        return_exceptions=True
                    )
                    
                    # Filter out exceptions
                    valid_links = [
                        link for link in scraped_links 
                        if not isinstance(link, Exception)
                    ]
                    
                    return {"links": valid_links}
                else:
                    return {"error": f"Failed to fetch {url}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _parse_links(self, html: str, base_url: str) -> List[str]:
        """Parse links from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http'):
                links.append(href)
            elif href.startswith('/'):
                links.append(base_url + href)
        
        return links
    
    async def _scrape_single_link(self, url: str) -> ScrapedContent:
        """Scrape individual link"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    return await self._extract_content(html, url)
                else:
                    return ScrapedContent(
                        url=url,
                        title="",
                        description="",
                        headings=[],
                        images=[],
                        error="Failed to fetch"
                    )
        except Exception as e:
            return ScrapedContent(
                url=url,
                title="",
                description="",
                headings=[],
                images=[],
                error=str(e)
            )
    
    async def _extract_content(self, html: str, url: str) -> ScrapedContent:
        """Extract content from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text() if title else "No title"
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ""
        
        # Extract headings
        headings = [
            {
                "tag": h.name,
                "text": h.get_text().strip()
            }
            for h in soup.find_all(['h1', 'h2', 'h3'])
        ]
        
        # Extract images (no callbacks needed!)
        images = [
            {
                "src": img.get('src', ''),
                "alt": img.get('alt', ''),
                "width": img.get('width', ''),
                "height": img.get('height', '')
            }
            for img in soup.find_all('img')[:3]
        ]
        
        return ScrapedContent(
            url=url,
            title=title_text,
            description=description,
            headings=headings,
            images=images
        )


@dataclass
class ProcessedItem:
    """Data class for processed items"""
    id: str
    processed: bool
    timestamp: float


class AsyncDataProcessor:
    """Modern async processor"""
    
    async def process_items(self, items: List[Dict]) -> List[ProcessedItem]:
        """Process items concurrently"""
        # Validate all items concurrently
        validation_tasks = [self._validate_item(item) for item in items]
        validation_results = await asyncio.gather(*validation_tasks)
        
        # Filter valid items and transform them concurrently
        valid_items = [
            item for item, is_valid in zip(items, validation_results)
            if is_valid
        ]
        
        transformation_tasks = [
            self._transform_item(item) for item in valid_items
        ]
        
        return await asyncio.gather(*transformation_tasks)
    
    async def _validate_item(self, item: Dict) -> bool:
        """Validate item asynchronously"""
        await asyncio.sleep(0.001)  # Simulate async validation
        return isinstance(item, dict) and 'id' in item
    
    async def _transform_item(self, item: Dict) -> ProcessedItem:
        """Transform item asynchronously"""
        await asyncio.sleep(0.001)  # Simulate async transformation
        return ProcessedItem(
            id=item["id"],
            processed=True,
            timestamp=time.time()
        )


# Clean usage with async/await
async def main():
    """Main function using clean async code"""
    # Scrape website
    async with AsyncWebScraper() as scraper:
        scraped_data = await scraper.scrape_website('https://example.com')
    
    if "error" in scraped_data:
        print(f"Scraping error: {scraped_data['error']}")
        return
    
    print(f"Scraped {len(scraped_data.get('links', []))} links")
    
    # Process scraped data
    processor = AsyncDataProcessor()
    processed_results = await processor.process_items(scraped_data.get('links', []))
    
    print(f"Processed {len(processed_results)} items")
    
    # Save results
    with open('results.json', 'w') as f:
        json.dump([vars(r) for r in processed_results], f)


if __name__ == "__main__":
    asyncio.run(main())
