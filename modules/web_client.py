#!/usr/bin/env python3
"""
Web Client Module
Web istekleri için yardımcı modül
"""

import time
import random
from typing import Optional
import requests
from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class WebClient:
    """Web istekleri için sınıf"""
    
    def __init__(self, 
                 user_agent: str = None,
                 timeout: int = 30,
                 use_selenium: bool = False,
                 headless: bool = True,
                 rate_limit: float = 1.0):
        """
        WebClient sınıfını başlatır.
        
        Args:
            user_agent: User-Agent string'i
            timeout: İstek zaman aşımı
            use_selenium: Selenium kullanımı
            headless: Selenium headless modu
            rate_limit: Rate limiting süresi
        """
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.use_selenium = use_selenium
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        
        # Selenium setup
        self.driver = None
        if use_selenium and SELENIUM_AVAILABLE:
            self._setup_selenium(headless)
        elif use_selenium and not SELENIUM_AVAILABLE:
            print("Selenium kullanılamıyor, requests moduna geçiliyor")
            self.use_selenium = False
        
        # Session for requests
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _setup_selenium(self, headless: bool = True):
        """Selenium driver'ı kurar."""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"--user-agent={self.user_agent}")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            print("Selenium driver başarıyla kuruldu")
        except Exception as e:
            print(f"Selenium kurulumu başarısız: {e}")
            self.use_selenium = False
    
    def _rate_limit(self):
        """Rate limiting uygular."""
        if self.rate_limit > 0:
            time.sleep(self.rate_limit + random.uniform(0, 0.5))
    
    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """
        URL'den HTML içeriğini alır.
        
        Args:
            url: Hedef URL
            
        Returns:
            BeautifulSoup objesi veya None
        """
        try:
            if self.use_selenium and self.driver:
                return self._get_soup_selenium(url)
            else:
                return self._get_soup_requests(url)
        except Exception as e:
            print(f"HTML içeriği alınamadı: {e}")
            return None
    
    def _get_soup_requests(self, url: str) -> Optional[BeautifulSoup]:
        """Requests ile HTML içeriği alır."""
        self._rate_limit()
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            resp.raise_for_status()
            
            # Content-Type kontrolü
            content_type = resp.headers.get('content-type', '').lower()
            if 'text/html' not in content_type and 'text/plain' not in content_type:
                print(f"Uyarı: Beklenmeyen content-type: {content_type}")
            
            return BeautifulSoup(resp.text, "html.parser")
            
        except requests.exceptions.RequestException as e:
            print(f"Request hatası: {e}")
            return None
        except Exception as e:
            print(f"HTML parsing hatası: {e}")
            return None
    
    def _get_soup_selenium(self, url: str) -> Optional[BeautifulSoup]:
        """Selenium ile HTML içeriği alır."""
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            return BeautifulSoup(self.driver.page_source, "html.parser")
        except Exception as e:
            print(f"Selenium ile HTML alınamadı: {e}")
            return None
    
    def cleanup(self):
        """Kaynakları temizler."""
        if self.driver:
            self.driver.quit()
            print("Selenium driver kapatıldı")


