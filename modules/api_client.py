#!/usr/bin/env python3
"""
API Client Module
API çağrıları için yardımcı modül
"""

import time
import random
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup


class APIClient:
    """API çağrıları için sınıf"""
    
    def __init__(self, 
                 user_agent: str = None,
                 timeout: int = 30,
                 rate_limit: float = 1.0):
        """
        APIClient sınıfını başlatır.
        
        Args:
            user_agent: User-Agent string'i
            timeout: İstek zaman aşımı
            rate_limit: Rate limiting süresi
        """
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0 Safari/537.36"
        )
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        # Session for API calls
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _rate_limit(self):
        """Rate limiting uygular."""
        if self.rate_limit > 0:
            time.sleep(self.rate_limit + random.uniform(0, 0.5))
    
    def _get_text(self, elem, default: str = "N/A") -> str:
        """Güvenli bir şekilde element metnini çıkarır."""
        try:
            if elem is None:
                return default
            return elem.get_text(strip=True)
        except Exception:
            return default
    
    def call_endpoint(self, base_url: str, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        API endpoint'ini çağırır.
        
        Args:
            base_url: Temel URL
            endpoint: Endpoint yolu
            params: Query parametreleri
            
        Returns:
            API response verisi
        """
        try:
            url = urljoin(base_url, endpoint)
            self._rate_limit()
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # JSON response kontrolü
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                # HTML response ise parse et
                soup = BeautifulSoup(response.text, "html.parser")
                return self._parse_html_response(soup)
                
        except Exception as e:
            print(f"API çağrısı hatası {endpoint}: {e}")
            return None
    
    def _parse_html_response(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        HTML response'unu parse eder.
        
        Args:
            soup: BeautifulSoup objesi
            
        Returns:
            Parse edilmiş veri
        """
        data = {}
        
        try:
            # Modal içeriğini çıkar
            modal_body = soup.select_one(".modal-body")
            if modal_body:
                data["modal_content"] = str(modal_body)
            
            # Tablo verilerini çıkar
            tables = soup.find_all("table")
            for i, table in enumerate(tables):
                table_data = []
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    if cells:
                        table_data.append([self._get_text(cell) for cell in cells])
                data[f"table_{i}"] = table_data
                
        except Exception as e:
            print(f"HTML response parse hatası: {e}")
        
        return data
    
    def get_competitors_data(self, base_url: str, scan_guid: str) -> Optional[Dict[str, Any]]:
        """
        Competitors API'sini çağırır.
        
        Args:
            base_url: Temel URL
            scan_guid: Scan GUID
            
        Returns:
            Competitors verisi
        """
        if not scan_guid:
            return None
        
        competitors_url = f"/scans/get-competitors-list?scan_guid={scan_guid}"
        return self.call_endpoint(base_url, competitors_url)
    
    def get_analytics_data(self, base_url: str, pinz_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analytics API'lerini çağırır.
        
        Args:
            base_url: Temel URL
            pinz_data: pinz array verisi
            
        Returns:
            Analytics verileri listesi
        """
        analytics_data = []
        
        try:
            for pin in pinz_data:
                if isinstance(pin, dict) and "url" in pin:
                    analytics_url = pin["url"]
                    if analytics_url.startswith("/analytics/"):
                        analytics_response = self.call_endpoint(base_url, analytics_url)
                        if analytics_response:
                            analytics_data.append({
                                "pin_data": pin,
                                "analytics_response": analytics_response
                            })
                            
        except Exception as e:
            print(f"Analytics API çağrısı hatası: {e}")
        
        return analytics_data
    
    def get_all_api_data(self, base_url: str, js_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tüm API verilerini çeker.
        
        Args:
            base_url: Temel URL
            js_data: JavaScript verileri
            
        Returns:
            Tüm API verileri
        """
        api_data = {}
        
        try:
            # Competitors list API
            if "scan_guid" in js_data and js_data["scan_guid"]:
                competitors_data = self.get_competitors_data(base_url, js_data["scan_guid"])
                if competitors_data:
                    api_data["competitors_api"] = competitors_data
            
            # Analytics API calls
            if "pinz" in js_data:
                analytics_data = self.get_analytics_data(base_url, js_data["pinz"])
                api_data["analytics_data"] = analytics_data
                
        except Exception as e:
            print(f"API veri çekme hatası: {e}")
        
        return api_data


