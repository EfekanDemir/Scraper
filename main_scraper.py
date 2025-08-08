#!/usr/bin/env python3
"""
Main Scraper - Modüler Web Scraping Aracı
Local Rank Report sitesinden veri çekme aracı

Bu dosya tüm yardımcı modülleri kullanarak hibrit scraping yapar:
- modules/html_parser.py: HTML parsing işlemleri
- modules/js_extractor.py: JavaScript veri çıkarma
- modules/api_client.py: API çağrıları
- modules/web_client.py: Web istekleri
- modules/data_exporter.py: Veri dışa aktarma
"""

import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse

# Modules klasörünü Python path'ine ekle
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from web_client import WebClient
from html_parser import HTMLParser
from js_extractor import JSExtractor
from api_client import APIClient
from data_exporter import DataExporter
from bs4 import BeautifulSoup
import glob


class MainScraper:
    """Ana scraper sınıfı - tüm modülleri koordine eder"""
    
    def __init__(self, 
                 user_agent: str = None,
                 timeout: int = 30,
                 use_selenium: bool = False,
                 headless: bool = True,
                 rate_limit: float = 1.0,
                 supabase_url: Optional[str] = None,
                 supabase_key: Optional[str] = None):
        """
        MainScraper sınıfını başlatır.
        
        Args:
            user_agent: User-Agent string'i
            timeout: İstek zaman aşımı
            use_selenium: Selenium kullanımı
            headless: Selenium headless modu
            rate_limit: Rate limiting süresi
            supabase_url: Supabase proje URL'si
            supabase_key: Supabase anon/public API anahtarı
        """
        # Modülleri başlat
        self.web_client = WebClient(
            user_agent=user_agent,
            timeout=timeout,
            use_selenium=use_selenium,
            headless=headless,
            rate_limit=rate_limit
        )
        
        self.html_parser = HTMLParser()
        self.js_extractor = JSExtractor()
        self.api_client = APIClient(
            user_agent=user_agent,
            timeout=timeout,
            rate_limit=rate_limit
        )
        # Supabase kimlik bilgilerini doğrudan DataExporter'a geç
        self.data_exporter = DataExporter(
            supabase_url=supabase_url or os.getenv("SUPABASE_URL"),
            supabase_key=supabase_key or os.getenv("SUPABASE_ANON_KEY"),
        )
        
        # Ayarları sakla
        self.use_selenium = use_selenium
    
    def _load_local_fallback_soup(self) -> Optional[BeautifulSoup]:
        """Site Dosyaları altındaki kaydedilmiş HTML'den Soup üretir (varsa)."""
        base_dir = os.path.join(os.path.dirname(__file__), 'Site Dosyaları')
        try:
            candidates = glob.glob(os.path.join(base_dir, '*.html'))
            if not candidates:
                # Alt klasörlerde de ara
                candidates = glob.glob(os.path.join(base_dir, '**', '*.html'), recursive=True)
            if candidates:
                # En büyük dosyayı seç (tam sayfa olma olasılığı yüksek)
                candidates.sort(key=lambda p: os.path.getsize(p), reverse=True)
                with open(candidates[0], 'r', encoding='utf-8', errors='ignore') as f:
                    html = f.read()
                return BeautifulSoup(html, 'html.parser')
        except Exception:
            pass
        return None
    
    def scrape_all(self, url: str) -> Dict[str, Any]:
        """
        Tüm verileri hibrit yöntemle çeker.
        
        Args:
            url: Hedef URL
            
        Returns:
            Tüm çekilen veriler
        """
        print(f"Veri çekme işlemi başlatılıyor: {url}")
        
        # 1. HTML içeriğini al
        print("1. HTML içeriği alınıyor...")
        soup = self.web_client.get_soup(url)
        # Eğer eksik içerik geldiyse, local fallback dene
        if soup and not soup.find("h4", string=lambda s: s and "Scan Information" in s):
            local_soup = self._load_local_fallback_soup()
            if local_soup:
                print("ℹ️ Uzak sayfa sınırlı içerik döndü; yerel HTML fallback kullanılacak")
                soup = local_soup
        if not soup:
            print("❌ HTML içeriği alınamadı")
            return {}
        print("✅ HTML içeriği başarıyla alındı")
        
        # 2. JavaScript verilerini çıkar
        print("2. JavaScript verileri çıkarılıyor...")
        js_data = self.js_extractor.extract_all_js_data(soup)
        print(f"✅ JavaScript verileri çıkarıldı: {len(js_data)} alan")
        
        # 3. HTML parsing ile temel verileri çek
        results = {}
        
        print("3. Özet bilgiler çekiliyor...")
        scan_info = self.html_parser.parse_scan_information(soup)
        rank_summary = self.html_parser.parse_rank_summary(soup)
        results["ozet_bilgiler"] = {**scan_info, **rank_summary}
        
        print("4. Rakipler çekiliyor...")
        results["rakipler"] = self.html_parser.parse_competitors(soup)
        
        print("5. Sponsorlu listeler çekiliyor...")
        results["sponsorlu_listeler"] = self.html_parser.parse_sponsorlu_listeler(soup)
        
        print("6. Detaylı sonuçlar çekiliyor...")
        results["detayli_sonuclar"] = self.html_parser.parse_detayli_sonuclar(soup)
        
        print("7. Harita verileri çekiliyor...")
        map_data = self.js_extractor.extract_map_data(js_data)
        # JS ile gelmezse analytics fallback ile üret
        if not map_data:
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            try:
                fallback_points = self.api_client.get_map_points_from_page(
                    base_url,
                    soup,
                    default_pid=js_data.get("place_id") or None,
                )
                # normalize to similar structure as pins
                map_data = [
                    {
                        "lat": p.get("lat"),
                        "lon": p.get("lon"),
                        "label": None,
                        "title": None,
                        "url": p.get("url"),
                        "color": None,
                        "cid": None,
                        "search_guid": p.get("search_guid"),
                        "pid": p.get("pid"),
                    }
                    for p in fallback_points
                ]
            except Exception as e:
                print(f"Harita fallback hatası: {e}")
        results["harita_verileri"] = map_data
        
        # 4. API verilerini çek
        print("8. API verileri çekiliyor...")
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        results["api_verileri"] = self.api_client.get_all_api_data(base_url, js_data)
        
        # 5. JavaScript verilerini ekle
        results["javascript_verileri"] = js_data
        
        # 6. Metadata ekle
        results["metadata"] = {
            "scraped_at": datetime.now().isoformat(),
            "url": url,
            "scraper_version": "4.0",
            "method": "modular_hybrid",
            "selenium_used": self.use_selenium
        }
        
        return results
    
    def export_data(self, data: Dict[str, Any], base_filename: str = "modular_scraped_data") -> Dict[str, bool]:
        """
        Verileri Supabase'e dışa aktarır.
        
        Args:
            data: Çekilen veriler
            base_filename: (artık dosya üretilmiyor) uyumluluk için tutuldu
            
        Returns:
            Her format için başarı durumu
        """
        print("\n9. Veriler Supabase'e aktarılıyor...")
        
        # Tüm formatlarda dışa aktar (yalnızca Supabase)
        results = self.data_exporter.export_all_formats(data, base_filename)
        
        # Özet göster
        self.data_exporter.print_summary(data)
        
        return results
    
    def run(self, url: str, base_filename: str = "modular_scraped_data") -> bool:
        """
        Tam scraping işlemini çalıştırır.
        
        Args:
            url: Hedef URL
            base_filename: Temel dosya adı
            
        Returns:
            Başarı durumu
        """
        try:
            # Veri çek
            data = self.scrape_all(url)
            
            if not data:
                print("❌ Veri çekme işlemi başarısız oldu")
                return False
            
            # Dışa aktar
            export_results = self.export_data(data, base_filename)
            
            # Sonuçları göster
            print("\n" + "=" * 60)
            print("MODÜLER SCRAPER SONUÇLARI")
            print("=" * 60)
            
            success_count = sum(1 for v in export_results.values() if v)
            total_formats = len(export_results)
            
            print(f"Başarılı çıktı sayısı: {success_count}/{total_formats}")
            
            for format_name, success in export_results.items():
                status = "✅" if success else "❌"
                print(f"{status} {format_name.upper()}")
            
            print("=" * 60)
            print("🎉 Supabase aktarımı tamamlandı!")
            
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Hata: {e}")
            return False
        
        finally:
            # Kaynakları temizle
            self.web_client.cleanup()
    
    def cleanup(self):
        """Kaynakları temizler."""
        self.web_client.cleanup()


def main():
    """Ana fonksiyon - örnek kullanım"""
    url = "https://www.local-rank.report/scan/97919fde-e478-4081-983f-7e0065b6b5bb"
    
    # Supabase bilgileri:
    # NOT: Geliştirme aşamasında RLS sorunları yaşıyorsanız Service Key kullanabilirsiniz
    # URL: https://fmaqwwjilpcgjwzolrvf.supabase.co
    supabase_url = os.getenv("SUPABASE_URL") or "https://fmaqwwjilpcgjwzolrvf.supabase.co"
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or (
        # GELİŞTİRME İÇİN: Service Key kullanmak için aşağıdaki satırı açın
        # os.getenv("SUPABASE_SERVICE_KEY") or
        # "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZtYXF3d2ppbHBjZ2p3em9scnZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2Mzg1MzMsImV4cCI6MjA0OTIxNDUzM30.nMbOBF8S2-8vz41vP0Jvlvl4JHbP6IoCFhYHWbPY2z4"
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZtYXF3d2ppbHBjZ2p3em9scnZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2Mzg1MzMsImV4cCI6MjA0OTIxNDUzM30.nMbOBF8S2-8vz41vP0Jvlvl4JHbP6IoCFhYHWbPY2z4"
    )
    
    # MainScraper örneği oluştur
    scraper = MainScraper(
        use_selenium=False,  # Selenium kullanmadan başla
        rate_limit=1.0,      # 1 saniye bekleme
        timeout=30,
        supabase_url=supabase_url,
        supabase_key=supabase_key,
    )
    
    # Tam işlemi çalıştır
    success = scraper.run(url, "modular_scraped_data")
    
    if success:
        print("\n📦 Veriler Supabase'e aktarıldı. Yerel dosya üretilmedi.")
    else:
        print("\n❌ İşlem başarısız oldu")


if __name__ == "__main__":
    main()


