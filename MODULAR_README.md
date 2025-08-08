# 🏗️ **Modüler Web Scraper - Dokümantasyon**

## 📋 **Proje Yapısı**

```
Scraper/
├── main_scraper.py              # Ana scraper dosyası
├── modules/                     # Yardımcı modüller
│   ├── __init__.py
│   ├── web_client.py           # Web istekleri
│   ├── html_parser.py          # HTML parsing
│   ├── js_extractor.py         # JavaScript veri çıkarma
│   ├── api_client.py           # API çağrıları
│   └── data_exporter.py        # Veri dışa aktarma
├── requirements.txt            # Gerekli kütüphaneler
└── MODULAR_README.md          # Bu dosya
```

## 🎯 **Modüler Yapının Avantajları**

### ✅ **Sorumluluk Ayrımı**
- Her modül tek bir işlevi yerine getirir
- Kod tekrarı önlenir
- Bakım ve güncelleme kolaylaşır

### ✅ **Yeniden Kullanılabilirlik**
- Modüller bağımsız olarak kullanılabilir
- Farklı projelerde tekrar kullanılabilir
- Test edilebilirlik artar

### ✅ **Genişletilebilirlik**
- Yeni modüller kolayca eklenebilir
- Mevcut modüller güncellenebilir
- Yeni özellikler modüler şekilde eklenebilir

## 🔧 **Modül Detayları**

### 1. **web_client.py** - Web İstekleri
```python
from modules.web_client import WebClient

# WebClient örneği oluştur
client = WebClient(
    user_agent="Custom User Agent",
    timeout=30,
    use_selenium=False,
    rate_limit=1.0
)

# HTML içeriği al
soup = client.get_soup("https://example.com")
```

**Özellikler:**
- Requests ve Selenium desteği
- Rate limiting
- Hata yönetimi
- Otomatik kaynak temizleme

### 2. **html_parser.py** - HTML Parsing
```python
from modules.html_parser import HTMLParser

# HTMLParser örneği oluştur
parser = HTMLParser()

# Veri çek
scan_info = parser.parse_scan_information(soup)
rank_summary = parser.parse_rank_summary(soup)
competitors = parser.parse_competitors(soup)
```

**Özellikler:**
- Scan Information parsing
- Rank Summary parsing
- Competitors parsing
- Sponsorlu listeler parsing
- Detaylı sonuçlar parsing

### 3. **js_extractor.py** - JavaScript Veri Çıkarma
```python
from modules.js_extractor import JSExtractor

# JSExtractor örneği oluştur
extractor = JSExtractor()

# JavaScript verilerini çıkar
js_data = extractor.extract_all_js_data(soup)
map_data = extractor.extract_map_data(js_data)
```

**Özellikler:**
- var pinz array çıkarma
- scan_guid çıkarma
- place_id çıkarma
- Harita verileri çıkarma
- Güvenli JSON parsing

### 4. **api_client.py** - API Çağrıları
```python
from modules.api_client import APIClient

# APIClient örneği oluştur
api_client = APIClient(
    user_agent="Custom User Agent",
    timeout=30,
    rate_limit=1.0
)

# API verilerini çek
api_data = api_client.get_all_api_data(base_url, js_data)
```

**Özellikler:**
- Competitors API çağrıları
- Analytics API çağrıları
- Rate limiting
- Hata yönetimi
- HTML/JSON response parsing

### 5. **data_exporter.py** - Veri Dışa Aktarma
```python
from modules.data_exporter import DataExporter

# DataExporter örneği oluştur
exporter = DataExporter()

# Verileri dışa aktar
exporter.save_to_json(data, "output.json")
exporter.save_to_excel(data, "output.xlsx")
exporter.save_to_csv(data, "output")
```

**Özellikler:**
- JSON formatında kaydetme
- Excel formatında kaydetme (çok sayfalı)
- CSV formatında kaydetme
- Otomatik sütun genişliği ayarlama
- Zaman damgalı dosya adları

## 🚀 **Kullanım Örnekleri**

### **Basit Kullanım**
```python
from main_scraper import MainScraper

# Scraper oluştur
scraper = MainScraper(
    use_selenium=False,
    rate_limit=1.0,
    timeout=30
)

# Tam işlemi çalıştır
success = scraper.run("https://example.com", "output_data")
```

### **Gelişmiş Kullanım**
```python
from main_scraper import MainScraper

# Özel ayarlarla scraper oluştur
scraper = MainScraper(
    user_agent="Custom Bot 1.0",
    use_selenium=True,
    headless=True,
    rate_limit=2.0,
    timeout=60
)

# Sadece veri çek
data = scraper.scrape_all("https://example.com")

# Manuel olarak dışa aktar
scraper.export_data(data, "custom_output")
```

### **Modül Bazlı Kullanım**
```python
# Sadece HTML parsing
from modules.html_parser import HTMLParser
from modules.web_client import WebClient

client = WebClient()
parser = HTMLParser()

soup = client.get_soup("https://example.com")
scan_info = parser.parse_scan_information(soup)
```

## 📊 **Çıktı Formatları**

### **JSON Formatı**
```json
{
  "ozet_bilgiler": {
    "İşletme Adı": "Kanal-Immobilien GmbH",
    "Adres": "Torstraße 18",
    "Ranked Locations": "1/49"
  },
  "rakipler": [...],
  "sponsorlu_listeler": [...],
  "metadata": {
    "scraped_at": "2025-08-07T19:31:35",
    "scraper_version": "4.0",
    "method": "modular_hybrid"
  }
}
```

### **Excel Formatı**
- **Özet Bilgiler** sayfası
- **Rakipler** sayfası
- **Sponsorlu Listeler** sayfası
- **Detaylı Sonuçlar** sayfası
- **Harita Verileri** sayfası

### **CSV Formatı**
- Her veri türü için ayrı CSV dosyası
- UTF-8 encoding
- Virgülle ayrılmış değerler

## ⚙️ **Konfigürasyon**

### **Rate Limiting**
```python
# Hızlı scraping (dikkatli kullanın)
scraper = MainScraper(rate_limit=0.5)

# Yavaş scraping (güvenli)
scraper = MainScraper(rate_limit=2.0)
```

### **Selenium Kullanımı**
```python
# Selenium ile (dinamik içerik için)
scraper = MainScraper(use_selenium=True, headless=True)

# Requests ile (statik içerik için)
scraper = MainScraper(use_selenium=False)
```

### **Timeout Ayarları**
```python
# Kısa timeout
scraper = MainScraper(timeout=10)

# Uzun timeout (yavaş siteler için)
scraper = MainScraper(timeout=60)
```

## 🛠️ **Hata Yönetimi**

### **Genel Hatalar**
```python
try:
    success = scraper.run(url, "output")
except Exception as e:
    print(f"Hata: {e}")
finally:
    scraper.cleanup()
```

### **Modül Bazlı Hata Yönetimi**
```python
# WebClient hataları
soup = client.get_soup(url)
if not soup:
    print("HTML içeriği alınamadı")

# API hataları
api_data = api_client.get_all_api_data(base_url, js_data)
if not api_data:
    print("API verileri alınamadı")
```

## 📈 **Performans Optimizasyonu**

### **Bellek Kullanımı**
- Her modül bağımsız çalışır
- Gereksiz veri saklanmaz
- Otomatik kaynak temizleme

### **Hız Optimizasyonu**
- Paralel işlemler mümkün
- Rate limiting ile sunucu yükü azaltılır
- Selenium sadece gerektiğinde kullanılır

### **Veri Doğruluğu**
- Çoklu doğrulama yöntemleri
- Hata durumunda varsayılan değerler
- Detaylı loglama

## 🔄 **Geliştirme ve Genişletme**

### **Yeni Modül Ekleme**
```python
# modules/new_module.py
class NewModule:
    def __init__(self):
        pass
    
    def process_data(self, data):
        # İşlem mantığı
        return processed_data
```

### **Ana Scraper'a Entegrasyon**
```python
# main_scraper.py
from modules.new_module import NewModule

class MainScraper:
    def __init__(self):
        self.new_module = NewModule()
    
    def scrape_all(self, url):
        # ... mevcut kod ...
        results["new_data"] = self.new_module.process_data(data)
        return results
```

## 🎉 **Sonuç**

Modüler yapı sayesinde:
- ✅ Kod daha organize ve anlaşılır
- ✅ Bakım ve güncelleme kolaylaşır
- ✅ Yeniden kullanılabilirlik artar
- ✅ Test edilebilirlik gelişir
- ✅ Genişletilebilirlik sağlanır

Bu yapı, büyük ölçekli scraping projeleri için ideal bir temel oluşturur.


