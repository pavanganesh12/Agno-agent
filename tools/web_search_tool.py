"""
Web Search Tool
Tool for searching the web for gym-interested leads
Supports: Brave Search (API), DuckDuckGo, Bing
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
import os
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from datetime import datetime

from tools.base import Tool


class WebSearchTool(Tool):
    """Tool that searches the web for people interested in gym/fitness"""
    
    def __init__(self, timeout: int = 10, brave_api_key: str = None):
        """
        Initialize the Web Search Tool
        
        Args:
            timeout: Request timeout in seconds
            brave_api_key: Brave Search API key (get free at https://brave.com/search/api/)
        """
        super().__init__()
        self.name = "web_search"
        self.description = (
            "Searches the web for gym/fitness interested leads. "
            "Finds contact information (name, email, phone) of people interested in "
            "gym, fitness, workouts, bodybuilding, personal training, etc. "
            "Uses Brave Search API for best results."
        )
        self.timeout = timeout
        
        # Brave API key - can be set via parameter or environment variable
        self.brave_api_key = brave_api_key or os.environ.get('BRAVE_API_KEY')
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        # Gym-related keywords
        self.gym_keywords = [
            'gym', 'fitness', 'workout', 'exercise', 'bodybuilding',
            'crossfit', 'personal trainer', 'health club', 'fitness center',
            'weight loss', 'muscle', 'strength training', 'yoga', 'pilates',
            'sports', 'athletic', 'wellness', 'nutrition'
        ]
        
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
    
    def set_brave_api_key(self, api_key: str):
        """Set Brave Search API key"""
        self.brave_api_key = api_key
    
    def _build_queries(self, location: str = "") -> List[str]:
        """Build search queries for gym leads"""
        queries = [
            "gym members contact email",
            "fitness enthusiasts directory",
            "gym owners contact information",
            "personal trainers email",
            "fitness influencers contact",
            "health club members directory",
            "crossfit members contact",
            "fitness studio owners email",
            "gym membership leads",
        ]
        if location:
            queries = [f"{q} {location}" for q in queries]
        return queries
    
    def _search_brave(self, query: str, max_results: int = 10) -> List[str]:
        """
        Search using Brave Search API
        Get free API key at: https://brave.com/search/api/
        """
        if not self.brave_api_key:
            print("[WebSearchTool] No Brave API key set. Get one free at https://brave.com/search/api/")
            return []
        
        search_url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'X-Subscription-Token': self.brave_api_key
        }
        params = {
            'q': query,
            'count': max_results
        }
        
        try:
            response = requests.get(search_url, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            urls = []
            web_results = data.get('web', {}).get('results', [])
            for result in web_results:
                url = result.get('url')
                if url:
                    urls.append(url)
            
            print(f"[WebSearchTool] Brave Search found {len(urls)} results")
            return urls
            
        except requests.RequestException as e:
            print(f"[WebSearchTool] Brave Search error: {e}")
            return []
    
    def _search_duckduckgo(self, query: str, max_results: int = 10) -> List[str]:
        """Search DuckDuckGo (fallback)"""
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            response = self.session.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            urls = []
            for result in soup.find_all('a', class_='result__a'):
                href = result.get('href', '')
                if href and href.startswith('http'):
                    urls.append(href)
                    if len(urls) >= max_results:
                        break
            return urls
        except:
            return []
    
    def _search_bing(self, query: str, max_results: int = 10) -> List[str]:
        """Search Bing (fallback)"""
        search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
        try:
            response = self.session.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            urls = []
            for result in soup.find_all('li', class_='b_algo'):
                link = result.find('a')
                if link and link.get('href'):
                    href = link['href']
                    if href.startswith('http'):
                        urls.append(href)
                        if len(urls) >= max_results:
                            break
            return urls
        except:
            return []
    
    def _is_gym_related(self, text: str) -> bool:
        """Check if text is gym-related"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.gym_keywords)
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract emails"""
        emails = list(set(self.email_pattern.findall(text)))
        return [e.lower() for e in emails if not any(
            skip in e.lower() for skip in ['example.', 'test.', 'domain.', 'sample.', 'your@', 'noreply']
        )]
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extract phones"""
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
        """Extract names"""
        names = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if 'name' in data:
                        names.append(data['name'])
                    if 'author' in data:
                        author = data['author']
                        if isinstance(author, dict) and 'name' in author:
                            names.append(author['name'])
                        elif isinstance(author, str):
                            names.append(author)
            except:
                pass
        return list(set(names))[:5]
    
    def _scrape_for_leads(self, url: str) -> Dict:
        """Scrape a URL for gym leads"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            html = response.text
        except:
            return {}
        
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        if not self._is_gym_related(text):
            return {}
        
        emails = self._extract_emails(text)
        phones = self._extract_phones(text)
        names = self._extract_names(soup)
        
        if not emails and not phones:
            return {}
        
        leads = []
        max_entries = max(len(emails), len(phones), 1)
        
        for i in range(max_entries):
            lead = {
                'name': names[i] if i < len(names) else None,
                'email': emails[i] if i < len(emails) else None,
                'phone': phones[i] if i < len(phones) else None,
                'source_url': url,
                'interest': 'gym/fitness'
            }
            if lead['email'] or lead['phone']:
                leads.append(lead)
        
        return {
            'url': url,
            'is_gym_related': True,
            'leads': leads
        }
    
    def run(
        self,
        location: str = "",
        max_searches: int = 5,
        custom_query: str = None,
        use_brave: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run the web search tool to find gym leads
        
        Args:
            location: Optional location to focus search
            max_searches: Maximum number of search queries
            custom_query: Custom search query (optional)
            use_brave: Use Brave Search API (recommended, requires API key)
        
        Returns:
            Dictionary with found leads
        """
        all_leads = []
        all_urls = set()
        searched_queries = []
        search_engine_used = []
        
        # Build queries
        if custom_query:
            queries = [custom_query]
        else:
            queries = self._build_queries(location)[:max_searches]
        
        # Search using available engines
        for query in queries:
            searched_queries.append(query)
            urls = []
            
            # Try Brave Search first (best results, no rate limiting with API key)
            if use_brave and self.brave_api_key:
                urls = self._search_brave(query, max_results=10)
                if urls and 'brave' not in search_engine_used:
                    search_engine_used.append('brave')
            
            # Fallback to DuckDuckGo and Bing if no Brave results
            if not urls:
                ddg_urls = self._search_duckduckgo(query, max_results=5)
                bing_urls = self._search_bing(query, max_results=5)
                urls = ddg_urls + bing_urls
                if ddg_urls and 'duckduckgo' not in search_engine_used:
                    search_engine_used.append('duckduckgo')
                if bing_urls and 'bing' not in search_engine_used:
                    search_engine_used.append('bing')
            
            all_urls.update(urls)
            time.sleep(0.5)  # Rate limiting
        
        # Scrape URLs for leads
        pages_scraped = 0
        for url in list(all_urls)[:20]:
            result = self._scrape_for_leads(url)
            if result and result.get('leads'):
                all_leads.extend(result['leads'])
                pages_scraped += 1
            time.sleep(0.3)
        
        # Deduplicate
        unique_leads = []
        seen = set()
        for lead in all_leads:
            key = (lead.get('email', ''), lead.get('phone', ''))
            if key not in seen and (lead.get('email') or lead.get('phone')):
                seen.add(key)
                unique_leads.append(lead)
        
        return {
            'success': True,
            'tool': self.name,
            'search_engines': search_engine_used or ['none - check API key'],
            'location': location or 'global',
            'queries_searched': len(searched_queries),
            'urls_found': len(all_urls),
            'pages_with_leads': pages_scraped,
            'total_leads': len(unique_leads),
            'leads': unique_leads,
            'timestamp': datetime.now().isoformat()
        }
