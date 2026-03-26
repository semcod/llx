#!/usr/bin/env python3
"""
Example: Async Code Refactoring with Planfile
Demonstrates refactoring callback hell to proper async/await patterns
"""

import asyncio
import json
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.code import Syntax

console = Console()


def create_callback_hell_example():
    """Create an example of callback hell that needs refactoring."""
    
    callback_hell_code = '''
"""
Callback Hell Example - Web scraping with nested callbacks
This code needs to be refactored to use async/await properly
"""

import requests
from bs4 import BeautifulSoup
import json
import time

class WebScraper:
    """Scraper using callback-based approach - very hard to maintain"""
    
    def __init__(self):
        self.session = requests.Session()
        self.results = []
    
    def scrape_website(self, url, callback):
        """Start scraping with callback"""
        def handle_response(response):
            if response.status_code == 200:
                self.parse_links(response.text, url, callback)
            else:
                callback({"error": f"Failed to fetch {url}"})
        
        try:
            response = self.session.get(url, timeout=10)
            handle_response(response)
        except Exception as e:
            callback({"error": str(e)})
    
    def parse_links(self, html, base_url, callback):
        """Parse links with nested callbacks"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http'):
                links.append(href)
            elif href.startswith('/'):
                links.append(base_url + href)
        
        # Scrape each link with more callbacks
        def scrape_all_links(links_left, scraped_data):
            if not links_left:
                callback({"links": scraped_data})
                return
            
            current_link = links_left[0]
            remaining_links = links_left[1:]
            
            def handle_link_scrape(data):
                scraped_data.append(data)
                # Recursive callback - this is the hell!
                scrape_all_links(remaining_links, scraped_data)
            
            self.scrape_single_link(current_link, handle_link_scrape)
        
        scrape_all_links(links[:5], [])  # Limit to 5 links
    
    def scrape_single_link(self, url, callback):
        """Scrape individual link with error handling callback"""
        def handle_response(response):
            if response.status_code == 200:
                self.extract_content(response.text, url, callback)
            else:
                callback({"url": url, "error": "Failed to fetch"})
        
        try:
            response = self.session.get(url, timeout=5)
            handle_response(response)
        except Exception as e:
            callback({"url": url, "error": str(e)})
    
    def extract_content(self, html, url, callback):
        """Extract content with yet another callback"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text() if title else "No title"
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ""
        
        # Extract headings
        headings = []
        for h in soup.find_all(['h1', 'h2', 'h3']):
            headings.append({
                "tag": h.name,
                "text": h.get_text().strip()
            })
        
        # Extract images (with more callbacks!)
        def process_images(images, processed):
            if not images:
                callback({
                    "url": url,
                    "title": title_text,
                    "description": description,
                    "headings": headings,
                    "images": processed
                })
                return
            
            img = images[0]
            remaining = images[1:]
            
            def handle_image():
                processed.append({
                    "src": img.get('src', ''),
                    "alt": img.get('alt', ''),
                    "width": img.get('width', ''),
                    "height": img.get('height', '')
                })
                process_images(remaining, processed)
            
            # Simulate async image processing
            time.sleep(0.01)
            handle_image()
        
        images = soup.find_all('img')[:3]  # Limit images
        process_images(images, [])


class DataProcessor:
    """Another class with callback-based processing"""
    
    def __init__(self):
        self.processed_items = []
    
    def process_items(self, items, callback):
        """Process items with nested callbacks"""
        def process_single(items_left, results):
            if not items_left:
                callback(results)
                return
            
            item = items_left[0]
            remaining = items_left[1:]
            
            def validate_item(validated):
                if validated:
                    def transform_item(transformed):
                        results.append(transformed)
                        process_single(remaining, results)
                    self.transform_item(item, transform_item)
                else:
                    process_single(remaining, results)
            
            self.validate_item(item, validate_item)
        
        process_single(items[:], [])
    
    def validate_item(self, item, callback):
        """Validate with callback"""
        time.sleep(0.001)  # Simulate async validation
        callback(isinstance(item, dict) and 'id' in item)
    
    def transform_item(self, item, callback):
        """Transform with callback"""
        time.sleep(0.001)  # Simulate async transformation
        transformed = {
            "id": item["id"],
            "processed": True,
            "timestamp": time.time()
        }
        callback(transformed)


# Usage example with callback hell
def main():
    """Main function demonstrating callback hell"""
    scraper = WebScraper()
    processor = DataProcessor()
    
    def handle_scraped_data(data):
        if "error" in data:
            print(f"Scraping error: {data['error']}")
            return
        
        print(f"Scraped {len(data.get('links', []))} links")
        
        # Process scraped data with more callbacks!
        def process_links(links):
            def processed_results(results):
                print(f"Processed {len(results)} items")
                # Save results
                with open('results.json', 'w') as f:
                    json.dump(results, f)
            
            processor.process_items(links, processed_results)
        
        process_links(data.get('links', []))
    
    # Start the callback chain
    scraper.scrape_website('https://example.com', handle_scraped_data)


if __name__ == "__main__":
    main()
'''
    
    # Write the callback hell example
    callback_path = Path("callback_hell.py")
    callback_path.write_text(callback_hell_code)
    
    return callback_path


def create_async_refactored_version():
    """Show how the code should look after refactoring."""
    
    async_code = '''
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
'''
    
    # Write the async version
    async_path = Path("async_refactored.py")
    async_path.write_text(async_code)
    
    return async_path


async def demonstrate_async_refactoring():
    """Demonstrate async refactoring using planfile."""
    
    console.print("\n[bold cyan]Async Code Refactoring Demo[/bold cyan]")
    console.print("=" * 50)
    
    # Create examples
    console.print("\n[blue]Step 1: Creating callback hell example...[/blue]")
    callback_path = create_callback_hell_example()
    console.print(f"[green]✓ Created {callback_path}[/green]")
    
    # Show problematic code
    console.print("\n[yellow]Problematic Code Pattern:[/yellow]")
    console.print("""
    def scrape_links(self, links, callback):
        def handle_link(data):
            def process_more(more_data):
                def even_more(final_data):
                    callback(final_data)  # Deep nesting!
                process_more(even_more)
            handle_link(process_more)
    """)
    
    # Generate refactoring strategy
    console.print("\n[blue]Step 2: Generating async refactoring strategy...[/blue]")
    
    strategy_cmd = [
        "python3", "-m", "llx", "plan", "generate",
        ".",
        "--model", "qwen2.5-coder:7b",
        "--sprints", "2",
        "--focus", "complexity",
        "--output", "async-refactor-strategy.yaml"
    ]
    
    try:
        result = subprocess.run(strategy_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✓ Strategy generated successfully[/green]")
        else:
            console.print(f"[red]Strategy generation failed: {result.stderr}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    
    # Show expected refactored version
    console.print("\n[blue]Step 3: Showing expected refactored version...[/blue]")
    async_path = create_async_refactored_version()
    console.print(f"[green]✓ Created {async_path}[/green]")
    
    # Show improvement
    console.print("\n[yellow]Key Improvements:[/yellow]")
    improvements = [
        "✓ Eliminated callback hell with async/await",
        "✓ Proper error handling with try/except",
        "✓ Concurrent execution with asyncio.gather()",
        "✓ Type hints for better code clarity",
        "✓ Data classes for structured data",
        "✓ Context managers for resource management",
        "✓ Separation of concerns with private methods"
    ]
    
    for improvement in improvements:
        console.print(f"  {improvement}")
    
    # Show code comparison
    console.print("\n[blue]Code Comparison:[/blue]")
    
    # Callback hell snippet
    callback_syntax = Syntax('''
def scrape_all_links(self, links, callback):
    if not links:
        callback({"links": scraped_data})
        return
    
    current = links[0]
    remaining = links[1:]
    
    def handle_link(data):
        scraped_data.append(data)
        scrape_all_links(remaining, scraped_data)  # Recursion!
    
    self.scrape_link(current, handle_link)
    ''', 'python', theme="monokai", line_numbers=False)
    
    console.print("\n[red]Before (Callback Hell):[/red]")
    console.print(callback_syntax)
    
    # Async version snippet
    async_syntax = Syntax('''
async def scrape_all_links(self, links):
    tasks = [self.scrape_link(link) for link in links]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
    ''', 'python', theme="monokai", line_numbers=False)
    
    console.print("\n[green]After (Clean Async):[/green]")
    console.print(async_syntax)
    
    # Performance benefits
    console.print("\n[yellow]Performance Benefits:[/yellow]")
    console.print("• Concurrent execution: 5x faster for I/O bound tasks")
    console.print("• Memory efficient: No deep callback stacks")
    console.print("• Better error handling: Exceptions propagate naturally")
    console.print("• Easier testing: Can mock async methods")
    console.print("• Maintainable: Linear code flow")


async def main():
    """Main demonstration."""
    
    console.print(Panel(
        "[bold cyan]Async Refactoring with Planfile Demo[/bold cyan]\n"
        "Transforming callback hell to clean async/await code",
        title="Async Refactoring Demo"
    ))
    
    await demonstrate_async_refactoring()
    
    console.print("\n[green]Demo completed![/green]")
    console.print("\nTo try it yourself:")
    console.print("1. Run: python3 -m llx plan generate . --focus complexity")
    console.print("2. Review the generated strategy")
    console.print("3. Apply: python3 -m llx plan apply strategy.yaml .")


if __name__ == "__main__":
    asyncio.run(main())
