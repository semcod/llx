
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
