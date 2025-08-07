#!/usr/bin/env python3
"""
Web Scraping Script Test Dosyası
Bu dosya, web_scraper.py dosyasındaki fonksiyonları test etmek için kullanılır.
"""

import sys
import os

def test_imports():
    """Gerekli kütüphanelerin yüklü olup olmadığını test eder."""
    print("Kütüphane testleri başlatılıyor...")
    
    try:
        import requests
        print("✓ requests kütüphanesi yüklü")
    except ImportError:
        print("✗ requests kütüphanesi yüklü değil")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✓ beautifulsoup4 kütüphanesi yüklü")
    except ImportError:
        print("✗ beautifulsoup4 kütüphanesi yüklü değil")
        return False
    
    try:
        import re
        print("✓ re kütüphanesi yüklü (built-in)")
    except ImportError:
        print("✗ re kütüphanesi yüklü değil")
        return False
    
    try:
        import json
        print("✓ json kütüphanesi yüklü (built-in)")
    except ImportError:
        print("✗ json kütüphanesi yüklü değil")
        return False
    
    return True

def test_web_scraper_import():
    """web_scraper.py dosyasının import edilip edilemediğini test eder."""
    print("\nWeb scraper modülü test ediliyor...")
    
    try:
        # web_scraper.py dosyasının varlığını kontrol et
        if not os.path.exists('web_scraper.py'):
            print("✗ web_scraper.py dosyası bulunamadı")
            return False
        
        # Dosyayı import et
        import web_scraper
        print("✓ web_scraper.py dosyası başarıyla import edildi")
        
        # Fonksiyonların varlığını kontrol et
        required_functions = [
            'get_html_content',
            'scrape_ozet_bilgiler',
            'scrape_rakipler',
            'scrape_sponsorlu_listeler',
            'scrape_detayli_sonuclar',
            'scrape_harita_verileri',
            'main'
        ]
        
        for func_name in required_functions:
            if hasattr(web_scraper, func_name):
                print(f"✓ {func_name} fonksiyonu mevcut")
            else:
                print(f"✗ {func_name} fonksiyonu bulunamadı")
                return False
        
        return True
        
    except ImportError as e:
        print(f"✗ web_scraper.py import edilemedi: {e}")
        return False
    except Exception as e:
        print(f"✗ Beklenmeyen hata: {e}")
        return False

def test_simple_request():
    """Basit bir HTTP isteği test eder."""
    print("\nHTTP isteği test ediliyor...")
    
    try:
        import requests
        
        # Basit bir test URL'si
        test_url = "https://httpbin.org/get"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print("✓ HTTP isteği başarılı")
        print(f"  Status Code: {response.status_code}")
        print(f"  Content Length: {len(response.content)} bytes")
        
        return True
        
    except requests.RequestException as e:
        print(f"✗ HTTP isteği başarısız: {e}")
        return False
    except Exception as e:
        print(f"✗ Beklenmeyen hata: {e}")
        return False

def main():
    """Ana test fonksiyonu."""
    print("=" * 50)
    print("WEB SCRAPING SCRIPT TEST SÜRECİ")
    print("=" * 50)
    
    tests = [
        ("Kütüphane Testleri", test_imports),
        ("Web Scraper Import Testi", test_web_scraper_import),
        ("HTTP İsteği Testi", test_simple_request)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} BAŞARILI")
            else:
                print(f"✗ {test_name} BAŞARISIZ")
        except Exception as e:
            print(f"✗ {test_name} HATA: {e}")
    
    print("\n" + "=" * 50)
    print(f"TEST SONUÇLARI: {passed}/{total} başarılı")
    print("=" * 50)
    
    if passed == total:
        print("🎉 Tüm testler başarılı! Script kullanıma hazır.")
        print("\nKullanım:")
        print("python3 web_scraper.py")
    else:
        print("⚠️  Bazı testler başarısız. Lütfen gerekli kütüphaneleri yükleyin.")
        print("\nKurulum:")
        print("pip install requests beautifulsoup4 lxml")
        print("veya")
        print("sudo apt install python3-requests python3-bs4 python3-lxml")

if __name__ == "__main__":
    main()