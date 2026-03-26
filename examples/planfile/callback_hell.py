"""
Callback Hell Example - Web scraping with nested callbacks
"""


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
