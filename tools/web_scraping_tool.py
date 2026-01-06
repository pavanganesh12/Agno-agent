"""
Web Scraping Tool
Tool for scraping websites and extracting contact information
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from typing import Any, Dict, List, Set
from urllib.parse import urljoin, urlparse
from datetime import datetime

from tools.base import Tool


class WebScrapingTool(Tool):
    """Tool that scrapes websites for contact information (name, email, phone)"""
    
    def __init__(self, timeout: int = 10):
        super().__init__()
        self.name = "web_scraping"
        self.description = (
            "Scrapes websites to extract contact information including names, "
            "email addresses, and phone numbers. Provide URLs to scrape."
        )
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Regex patterns
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            re.IGNORECASE
        )
        self.phone_patterns = [
            re.compile(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'),
            re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            re.compile(r'\+?[1-9]\d{9,14}'),
        ]
    
    def _fetch_page(self, url: str) -> str:
        """Fetch page content"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            return ""
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract emails from text"""
        emails = list(set(self.email_pattern.findall(text)))
        return [e.lower() for e in emails if not any(
            skip in e.lower() for skip in ['example.', 'test.', 'domain.', 'sample.', 'your@', 'noreply']
        )]
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        phones = set()
        for pattern in self.phone_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    phone = ''.join(str(m) for m in match if m)
                else:
                    phone = match
                cleaned = re.sub(r'[^\d+]', '', phone)
                if 10 <= len(cleaned) <= 15:
                    phones.add(cleaned)
        return list(phones)
    
    def _extract_names(self, soup: BeautifulSoup) -> List[str]:
        """Extract names from HTML"""
        names = []
        
        # Check structured data
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'name' in data:
                    names.append(data['name'])
            except:
                pass
        
        # Check meta tags
        for meta in soup.find_all('meta', attrs={'name': re.compile(r'author|owner', re.I)}):
            content = meta.get('content', '')
            if content and 2 <= len(content.split()) <= 4:
                names.append(content)
        
        return list(set(names))[:5]
    
    def _scrape_url(self, url: str) -> Dict:
        """Scrape a single URL"""
        html = self._fetch_page(url)
        if not html:
            return {'url': url, 'error': 'Failed to fetch page', 'contacts': []}
        
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        emails = self._extract_emails(text)
        phones = self._extract_phones(text)
        names = self._extract_names(soup)
        
        # Build contacts
        contacts = []
        max_entries = max(len(emails), len(phones), len(names), 1)
        
        for i in range(max_entries):
            contact = {
                'name': names[i] if i < len(names) else None,
                'email': emails[i] if i < len(emails) else None,
                'phone': phones[i] if i < len(phones) else None,
                'source_url': url
            }
            if contact['name'] or contact['email'] or contact['phone']:
                contacts.append(contact)
        
        return {
            'url': url,
            'contacts': contacts,
            'emails_found': len(emails),
            'phones_found': len(phones),
            'names_found': len(names)
        }
    
    def run(self, urls: List[str] = None, url: str = None, **kwargs) -> Dict[str, Any]:
        """
        Run the web scraping tool
        
        Args:
            urls: List of URLs to scrape
            url: Single URL to scrape (alternative to urls)
        
        Returns:
            Dictionary with scraped contacts
        """
        if url and not urls:
            urls = [url]
        
        if not urls:
            return {
                'success': False,
                'error': 'No URLs provided',
                'contacts': []
            }
        
        all_contacts = []
        results = []
        
        for u in urls:
            result = self._scrape_url(u)
            results.append(result)
            all_contacts.extend(result.get('contacts', []))
        
        # Deduplicate contacts
        unique_contacts = []
        seen = set()
        for contact in all_contacts:
            key = (contact.get('email', ''), contact.get('phone', ''))
            if key not in seen and (contact.get('email') or contact.get('phone')):
                seen.add(key)
                unique_contacts.append(contact)
        
        return {
            'success': True,
            'tool': self.name,
            'urls_scraped': len(urls),
            'total_contacts': len(unique_contacts),
            'contacts': unique_contacts,
            'details': results,
            'timestamp': datetime.now().isoformat()
        }

