#!/usr/bin/env python3
"""
Multi-Level Government Legislative Scraper
Checks for new legislative activity at:
1. Alberta Legislature (Provincial)
2. House of Commons (Federal)
3. Strathcona County Council (Municipal)
"""

import re
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
import json


class GovernmentScraper:
    """Base class for government legislative scrapers"""
    
    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Legislative Monitor Bot)'
        })
    
    def get_latest_info(self) -> Dict:
        """Override in subclasses"""
        raise NotImplementedError
    
    def check_for_new(self, last_check_date: Optional[str] = None) -> Tuple[bool, List[Dict]]:
        """Override in subclasses"""
        raise NotImplementedError


class AlbertaLegislatureScraper(GovernmentScraper):
    """Scraper for Alberta Legislature Hansard transcripts"""
    
    BASE_URL = "https://www.assembly.ab.ca"
    TRANSCRIPTS_URL = f"{BASE_URL}/assembly-business/transcripts/transcripts-by-type"
    
    def __init__(self):
        super().__init__("Alberta Legislature")
    
    def get_latest_info(self) -> Dict:
        """Fetch information about the most recent Hansard transcripts"""
        try:
            response = self.session.get(self.TRANSCRIPTS_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            transcript_entries = []
            
            # Look for entries with date format like "Dec 10, 2025, aft."
            for element in soup.find_all(text=re.compile(r'\w+\s+\d+,\s+\d{4}')):
                parent = element.parent
                
                # Try to find the PDF link nearby
                pdf_link = None
                for link in parent.find_all('a', href=True):
                    if 'pdf' in link['href'].lower():
                        pdf_link = self.BASE_URL + link['href'] if not link['href'].startswith('http') else link['href']
                        break
                
                if pdf_link:
                    date_match = re.search(r'(\w+)\s+(\d+),\s+(\d{4})', element)
                    if date_match:
                        transcript_entries.append({
                            'full_text': element.strip(),
                            'pdf_url': pdf_link,
                            'month': date_match.group(1),
                            'day': int(date_match.group(2)),
                            'year': int(date_match.group(3)),
                            'government': 'Alberta Legislature'
                        })
            
            # Sort by date (newest first)
            transcript_entries.sort(
                key=lambda x: (x['year'], x['month'], x['day']), 
                reverse=True
            )
            
            return {
                'latest_items': transcript_entries[:5],
                'fetched_at': datetime.now().isoformat(),
                'government': self.name
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'fetched_at': datetime.now().isoformat(),
                'government': self.name
            }
    
    def check_for_new(self, last_check_date: Optional[str] = None) -> Tuple[bool, List[Dict]]:
        """Check if there are new transcripts since last_check_date"""
        info = self.get_latest_info()
        
        if 'error' in info:
            return False, []
        
        if not last_check_date:
            latest = info['latest_items'][0] if info['latest_items'] else None
            return True, [latest] if latest else []
        
        # Compare dates
        last_check = datetime.fromisoformat(last_check_date)
        new_items = []
        
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        for item in info['latest_items']:
            try:
                item_date = datetime(
                    item['year'],
                    month_map.get(item['month'], 1),
                    item['day']
                )
                
                if item_date > last_check:
                    new_items.append(item)
            except:
                continue
        
        return len(new_items) > 0, new_items


class HouseOfCommonsScraper(GovernmentScraper):
    """Scraper for Canadian House of Commons Hansard"""
    
    BASE_URL = "https://www.ourcommons.ca"
    DEBATES_URL = f"{BASE_URL}/documentviewer/en/house/latest/hansard"
    
    def __init__(self):
        super().__init__("House of Commons (Canada)")
    
    def get_latest_info(self) -> Dict:
        """Fetch information about recent House of Commons debates"""
        try:
            response = self.session.get(self.DEBATES_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # The page title usually contains the date
            # e.g., "Debates (Hansard) No. 39 - October 20, 2025"
            title = soup.find('title')
            
            items = []
            if title:
                title_text = title.get_text()
                # Extract date from title
                date_match = re.search(r'(\w+)\s+(\d+),\s+(\d{4})', title_text)
                if date_match:
                    items.append({
                        'full_text': title_text,
                        'url': self.DEBATES_URL,
                        'month': date_match.group(1),
                        'day': int(date_match.group(2)),
                        'year': int(date_match.group(3)),
                        'government': 'House of Commons (Canada)'
                    })
            
            return {
                'latest_items': items,
                'fetched_at': datetime.now().isoformat(),
                'government': self.name
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'fetched_at': datetime.now().isoformat(),
                'government': self.name
            }
    
    def check_for_new(self, last_check_date: Optional[str] = None) -> Tuple[bool, List[Dict]]:
        """Check if there are new debates since last_check_date"""
        info = self.get_latest_info()
        
        if 'error' in info:
            return False, []
        
        if not last_check_date:
            latest = info['latest_items'][0] if info['latest_items'] else None
            return True, [latest] if latest else []
        
        last_check = datetime.fromisoformat(last_check_date)
        new_items = []
        
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4, 
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        
        for item in info['latest_items']:
            try:
                item_date = datetime(
                    item['year'],
                    month_map.get(item['month'], 1),
                    item['day']
                )
                
                if item_date > last_check:
                    new_items.append(item)
            except:
                continue
        
        return len(new_items) > 0, new_items


class StrathconaCountyScraper(GovernmentScraper):
    """Scraper for Strathcona County Council meetings"""
    
    BASE_URL = "https://pub-strathcona.escribemeetings.com"
    MEETINGS_URL = f"{BASE_URL}/meetingscalendarview.aspx"
    
    def __init__(self):
        super().__init__("Strathcona County Council")
    
    def get_latest_info(self) -> Dict:
        """Fetch information about recent council meetings"""
        try:
            response = self.session.get(self.MEETINGS_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            items = []
            
            # Look for meeting entries
            # The Strathcona site uses eScribe system
            # Find all links that might be agendas or minutes
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().strip()
                
                # Look for council meetings
                if 'council' in text.lower() and ('agenda' in text.lower() or 'minutes' in text.lower()):
                    # Try to extract date from surrounding text
                    parent_text = link.parent.get_text() if link.parent else ''
                    date_match = re.search(r'(\w+)\s+(\d+),\s+(\d{4})', parent_text)
                    
                    if date_match:
                        full_url = self.BASE_URL + href if not href.startswith('http') else href
                        items.append({
                            'full_text': text,
                            'url': full_url,
                            'month': date_match.group(1),
                            'day': int(date_match.group(2)),
                            'year': int(date_match.group(3)),
                            'government': 'Strathcona County Council'
                        })
            
            # Sort by date (newest first)
            items.sort(
                key=lambda x: (x['year'], x['month'], x['day']), 
                reverse=True
            )
            
            return {
                'latest_items': items[:5],
                'fetched_at': datetime.now().isoformat(),
                'government': self.name
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'fetched_at': datetime.now().isoformat(),
                'government': self.name
            }
    
    def check_for_new(self, last_check_date: Optional[str] = None) -> Tuple[bool, List[Dict]]:
        """Check if there are new meetings since last_check_date"""
        info = self.get_latest_info()
        
        if 'error' in info:
            return False, []
        
        if not last_check_date:
            latest = info['latest_items'][0] if info['latest_items'] else None
            return True, [latest] if latest else []
        
        last_check = datetime.fromisoformat(last_check_date)
        new_items = []
        
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12,
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        for item in info['latest_items']:
            try:
                item_date = datetime(
                    item['year'],
                    month_map.get(item['month'], 1),
                    item['day']
                )
                
                if item_date > last_check:
                    new_items.append(item)
            except:
                continue
        
        return len(new_items) > 0, new_items


class MultiGovernmentMonitor:
    """Coordinates checking all three levels of government"""
    
    def __init__(self):
        self.scrapers = [
            AlbertaLegislatureScraper(),
            HouseOfCommonsScraper(),
            StrathconaCountyScraper()
        ]
    
    def check_all(self, last_check_date: Optional[str] = None) -> Dict:
        """Check all government levels for new activity"""
        results = {
            'checked_at': datetime.now().isoformat(),
            'governments': []
        }
        
        for scraper in self.scrapers:
            has_new, new_items = scraper.check_for_new(last_check_date)
            
            results['governments'].append({
                'name': scraper.name,
                'has_new_content': has_new,
                'new_items': new_items
            })
        
        return results
    
    def generate_summary(self, results: Dict) -> str:
        """Generate a formatted summary of all government activity"""
        summary_lines = []
        summary_lines.append("=== LEGISLATIVE ACTIVITY UPDATE ===")
        summary_lines.append(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        summary_lines.append("=" * 50)
        
        has_any_content = any(
            gov['has_new_content'] 
            for gov in results['governments']
        )
        
        if not has_any_content:
            summary_lines.append("\nNo new legislative activity at any level.")
            return "\n".join(summary_lines)
        
        # Alberta Legislature
        alberta = results['governments'][0]
        summary_lines.append("\n📍 ALBERTA LEGISLATURE")
        summary_lines.append("-" * 50)
        if alberta['has_new_content']:
            for item in alberta['new_items']:
                summary_lines.append(f"• {item['full_text']}")
                summary_lines.append(f"  📄 PDF: {item.get('pdf_url', 'N/A')}")
        else:
            summary_lines.append("  No new sessions")
        
        # House of Commons
        canada = results['governments'][1]
        summary_lines.append("\n🍁 HOUSE OF COMMONS (CANADA)")
        summary_lines.append("-" * 50)
        if canada['has_new_content']:
            for item in canada['new_items']:
                summary_lines.append(f"• {item['full_text']}")
                summary_lines.append(f"  🔗 URL: {item.get('url', 'N/A')}")
        else:
            summary_lines.append("  No new debates")
        
        # Strathcona County
        strathcona = results['governments'][2]
        summary_lines.append("\n🏘️  STRATHCONA COUNTY COUNCIL")
        summary_lines.append("-" * 50)
        if strathcona['has_new_content']:
            for item in strathcona['new_items']:
                summary_lines.append(f"• {item['full_text']}")
                summary_lines.append(f"  🔗 URL: {item.get('url', 'N/A')}")
        else:
            summary_lines.append("  No new meetings")
        
        summary_lines.append("\n" + "=" * 50)
        summary_lines.append("\nNote: Full content analysis requires document parsing.")
        
        return "\n".join(summary_lines)


def main():
    """Test the multi-government monitor"""
    monitor = MultiGovernmentMonitor()
    
    print("Checking all three levels of government...\n")
    
    results = monitor.check_all()
    summary = monitor.generate_summary(results)
    
    print(summary)


if __name__ == "__main__":
    main()
