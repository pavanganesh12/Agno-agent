"""
Agno Agent
Main agent that uses tools to find gym-interested leads
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from tools import Tool, ToolRegistry, WebScrapingTool, WebSearchTool, ExcelReaderTool


class AgnoAgent:
    """
    Agno Agent - Uses tools to find contact information
    
    Tools:
    - web_scraping: Scrapes websites for contact info
    - web_search: Searches web for gym-interested leads
    - excel_reader: Reads contact data from Excel files
    """
    
    def __init__(self):
        self.name = "Agno Agent"
        self.tools = ToolRegistry()
        self.results: List[Dict] = []
        self.all_leads: List[Dict] = []
        
        # Register tools
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register the default tools"""
        self.tools.register(WebScrapingTool())
        self.tools.register(WebSearchTool())
        self.tools.register(ExcelReaderTool())
    
    def add_tool(self, tool: Tool):
        """Add a custom tool to the agent"""
        self.tools.register(tool)
    
    def list_tools(self) -> List[Dict]:
        """List all available tools"""
        return self.tools.list_tools()
    
    def log(self, message: str):
        """Log agent activity"""
        print(f"[{self.name}] {message}")
    
    def use_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Use a specific tool
        
        Args:
            tool_name: Name of the tool to use
            **kwargs: Arguments to pass to the tool
        
        Returns:
            Tool output
        """
        tool = self.tools.get(tool_name)
        
        if not tool:
            return {
                'success': False,
                'error': f"Tool '{tool_name}' not found. Available tools: {[t['name'] for t in self.list_tools()]}"
            }
        
        self.log(f"Using tool: {tool_name}")
        result = tool.run(**kwargs)
        
        # Store results
        self.results.append({
            'tool': tool_name,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        # Collect leads
        if result.get('contacts'):
            self.all_leads.extend(result['contacts'])
        if result.get('leads'):
            self.all_leads.extend(result['leads'])
        
        return result
    
    def scrape(self, urls: List[str]) -> Dict[str, Any]:
        """
        Scrape websites using the web_scraping tool
        
        Args:
            urls: List of URLs to scrape
        
        Returns:
            Scraping results with contacts
        """
        return self.use_tool('web_scraping', urls=urls)
    
    def search(self, location: str = "", max_searches: int = 5) -> Dict[str, Any]:
        """
        Search for gym leads using the web_search tool
        
        Args:
            location: Optional location to focus search
            max_searches: Maximum search queries
        
        Returns:
            Search results with leads
        """
        return self.use_tool('web_search', location=location, max_searches=max_searches)
    
    def read_excel(self, file_path: str, sheet_name: Optional[str] = None, extract_urls_only: bool = False) -> Dict[str, Any]:
        """
        Read contacts from Excel file using the excel_reader tool
        
        Args:
            file_path: Path to Excel file
            sheet_name: Specific sheet name (optional)
            extract_urls_only: If True, only extract URLs for scraping
        
        Returns:
            Excel reading results with contacts or URLs
        """
        return self.use_tool('excel_reader', file_path=file_path, sheet_name=sheet_name, extract_urls_only=extract_urls_only)
    
    def run(
        self,
        task: str = "search",
        urls: Optional[List[str]] = None,
        location: str = "",
        max_searches: int = 5
    ) -> Dict[str, Any]:
        """
        Run the agent with a specific task
        
        Args:
            task: Task to perform - "search", "scrape", or "both"
            urls: URLs for scraping (required if task is "scrape" or "both")
            location: Location for search
            max_searches: Max search queries
        
        Returns:
            Combined results
        """
        self.log(f"Starting task: {task}")
        
        results = {
            'task': task,
            'scraping_result': None,
            'search_result': None
        }
        
        if task in ('scrape', 'both'):
            if urls:
                results['scraping_result'] = self.scrape(urls)
            else:
                self.log("No URLs provided for scraping")
        
        if task in ('search', 'both'):
            results['search_result'] = self.search(location, max_searches)
        
        # Get unique leads
        unique_leads = self.get_unique_leads()
        results['total_unique_leads'] = len(unique_leads)
        results['leads'] = unique_leads
        
        self.log(f"Task complete. Found {len(unique_leads)} unique leads.")
        
        return results
    
    def get_unique_leads(self) -> List[Dict]:
        """Get all unique leads collected"""
        unique = []
        seen = set()
        
        for lead in self.all_leads:
            email = lead.get('email', '').lower() if lead.get('email') else ''
            phone = lead.get('phone', '') if lead.get('phone') else ''
            key = (email, phone)
            
            if key not in seen and (email or phone):
                seen.add(key)
                unique.append(lead)
        
        return unique
    
    def display_results(self):
        """Display all collected leads"""
        leads = self.get_unique_leads()
        
        print("\n" + "="*60)
        print("            AGNO AGENT - RESULTS")
        print("="*60)
        print(f"\nTools used: {[r['tool'] for r in self.results]}")
        print(f"Total unique leads: {len(leads)}")
        print("-"*60)
        
        for i, lead in enumerate(leads, 1):
            print(f"\n[Lead #{i}]")
            print(f"   Name:   {lead.get('name') or 'N/A'}")
            print(f"   Email:  {lead.get('email') or 'N/A'}")
            print(f"   Phone:  {lead.get('phone') or 'N/A'}")
            print(f"   Source: {lead.get('source_url') or 'N/A'}")
        
        print("\n" + "="*60)
    
    def export_json(self, filename: str = 'agno_leads.json') -> str:
        """Export leads to JSON"""
        leads = self.get_unique_leads()
        
        output = {
            'agent': self.name,
            'tools_used': [r['tool'] for r in self.results],
            'total_leads': len(leads),
            'leads': leads,
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        self.log(f"Exported to {filename}")
        return filename
    
    def export_csv(self, filename: str = 'agno_leads.csv') -> str:
        """Export leads to CSV"""
        leads = self.get_unique_leads()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Name,Email,Phone,Source URL,Interest\n")
            for lead in leads:
                name = (lead.get('name') or '').replace('"', "'")
                email = lead.get('email') or ''
                phone = lead.get('phone') or ''
                source = (lead.get('source_url') or '').replace('"', "'")
                interest = lead.get('interest', 'gym/fitness')
                f.write(f'"{name}","{email}","{phone}","{source}","{interest}"\n')
        
        self.log(f"Exported to {filename}")
        return filename


def main():
    """Main entry point"""
    import sys
    
    print("""
    ============================================================
                          AGNO AGENT                           
             Lead Generation with Tool-Based Architecture      
    ============================================================
      Tools:                                                   
        - web_scraping : Scrape websites for contacts          
        - web_search   : Search web for gym leads              
        - excel_reader : Read contacts from Excel files        
    ============================================================
    """)
    
    agent = AgnoAgent()
    
    # Show available tools
    print("Available tools:")
    for tool in agent.list_tools():
        print(f"  • {tool['name']}: {tool['description'][:50]}...")
    print()
    
    # Parse arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == '--search':
            location = sys.argv[2] if len(sys.argv) > 2 else ""
            agent.run(task='search', location=location)
        
        elif command == '--scrape':
            urls = sys.argv[2:]
            if urls:
                agent.run(task='scrape', urls=urls)
            else:
                print("Please provide URLs to scrape")
                return
        
        elif command == '--both':
            location = sys.argv[2] if len(sys.argv) > 2 else ""
            urls = sys.argv[3:] if len(sys.argv) > 3 else None
            agent.run(task='both', urls=urls, location=location)
        
        elif command == '--excel':
            file_path = sys.argv[2] if len(sys.argv) > 2 else None
            if file_path:
                sheet_name = sys.argv[3] if len(sys.argv) > 3 else None
                result = agent.read_excel(file_path, sheet_name=sheet_name)
                if result.get('success'):
                    # Add contacts to leads
                    for contact in result.get('contacts', []):
                        agent.all_leads.append(contact)
                    print(f"Read {result.get('total_contacts', 0)} contacts from Excel")
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
            else:
                print("Please provide Excel file path")
                print("Usage: python agent.py --excel <file_path> [sheet_name]")
                return
        
        elif command == '--help':
            print("Usage:")
            print("  python agent.py --search [location]")
            print("  python agent.py --scrape <url1> <url2> ...")
            print("  python agent.py --excel <file_path> [sheet_name]")
            print("  python agent.py --both [location] [urls...]")
            return
        
        else:
            # Assume it's a URL
            agent.run(task='scrape', urls=[command])
    else:
        # Default: search for gym leads
        agent.run(task='search', max_searches=3)
    
    # Display and export results
    agent.display_results()
    agent.export_json()
    agent.export_csv()
    
    print("\nResults saved to:")
    print("  - agno_leads.json")
    print("  - agno_leads.csv")


if __name__ == "__main__":
    main()

