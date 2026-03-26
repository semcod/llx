"""Utility functions for creating example code files."""

from pathlib import Path
from typing import Optional


def create_example_file(
    filename: str,
    code_content: str,
    description: str,
    output_dir: Optional[Path] = None
) -> Path:
    """Create an example Python file with the given content.
    
    Args:
        filename: Name of the file to create
        code_content: Python code content to write
        description: Description comment to add at the top
        output_dir: Directory to create file in (default: current)
        
    Returns:
        Path to created file
    """
    if output_dir is None:
        output_dir = Path(".")
    
    file_path = output_dir / filename
    
    # Add header comment if description provided
    if description and not code_content.strip().startswith('"""'):
        full_content = f'"""\n{description}\n"""\n\n{code_content}'
    else:
        full_content = code_content
    
    file_path.write_text(full_content)
    return file_path


# Template for callback-based scraper
CALLBACK_SCRAPER_TEMPLATE = '''
import requests
from bs4 import BeautifulSoup
import json
import time

class WebScraper:
    """Scraper using callback-based approach"""
    
    def __init__(self):
        self.session = requests.Session()
        self.results = []
    
    def scrape_website(self, url, callback):
        """Start scraping with callback"""
        def handle_response(response):
            if response.status_code == 200:
                self.parse_links(response.text, url, callback)
            else:
                callback({{"error": f"Failed to fetch {{url}}"}})
        
        try:
            response = self.session.get(url, timeout=10)
            handle_response(response)
        except Exception as e:
            callback({{"error": str(e)}})
    
    def parse_links(self, html, base_url, callback):
        """Parse links from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http'):
                links.append({{
                    'url': href,
                    'text': link.get_text(strip=True)
                }})
        
        callback({{
            'base_url': base_url,
            'links': links,
            'count': len(links)
        }})
'''


# Template for async refactored scraper
ASYNC_SCRAPER_TEMPLATE = '''
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
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
    """Modern async scraper using aiohttp"""
    
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
                    return await self._parse_content(html, url)
                else:
                    return {{
                        'url': url,
                        'error': f'HTTP {{response.status}}'
                    }}
        except Exception as e:
            return {{
                'url': url,
                'error': str(e)
            }}
    
    async def _parse_content(self, html: str, url: str) -> ScrapedContent:
        """Parse HTML content"""
        soup = BeautifulSoup(html, 'html.parser')
        
        title = soup.title.string if soup.title else 'No title'
        
        headings = []
        for h in soup.find_all(['h1', 'h2', 'h3']):
            headings.append({{
                'level': h.name,
                'text': h.get_text(strip=True)
            }})
        
        images = []
        for img in soup.find_all('img', src=True):
            images.append({{
                'src': img['src'],
                'alt': img.get('alt', '')
            }})
        
        return ScrapedContent(
            url=url,
            title=title,
            description=soup.get('meta', {{}}).get('description', ''),
            headings=headings,
            images=images
        )


async def scrape_multiple(urls: List[str]) -> List[Dict]:
    """Scrape multiple URLs concurrently"""
    async with AsyncWebScraper() as scraper:
        tasks = [scraper.scrape_website(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            r if not isinstance(r, Exception) else {{
                'error': str(r)
            }}
            for r in results
        ]
'''
