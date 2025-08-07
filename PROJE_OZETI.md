# Web Scraping Projesi - Tamamlanan Özellikler

## 📋 Proje Özeti

Bu proje, belirtilen URL'den (`https://www.local-rank.report/scan/97919fde-e478-4081-983f-7e0065b6b5bb`) veri çekmek için tasarlanmış kapsamlı bir Python web scraping scriptidir.

## ✅ Tamamlanan Özellikler

### 1. **Ana Veri Çekme Fonksiyonları**

#### A. `scrape_ozet_bilgiler(soup)` ✅
- **Scan Information Tablosu** verilerini çeker:
  - İşletme Adı (`span.bizname`)
  - Adres (`span.center-block`)
  - Yorum Sayısı (`div.rating-container + span`)
  - Anahtar Kelime ve Dil (Keyword içeren td'nin kardeş td'si)
  - Tarih (`td.cnv_dt_lcl`)

- **Rank Summary Tablosu** verilerini çeker:
  - Her satırdaki ilk ve ikinci td'leri anahtar-değer çifti olarak alır
  - Dictionary formatında döndürür

#### B. `scrape_rakipler(soup)` ✅
- **table#tbl_comp_rank** içindeki tüm rakip verilerini çeker:
  - İsim (`a.ext`)
  - Puan/Yorum (`div.rating-container + span`)
  - Adres (`i.fa-map-marker` içeren `span.center-block`)
  - Kategoriler ("Categories:" içeren `p` etiketi)
  - Web Sitesi (`i.fa-globe` içeren `span > a` href)
  - Fotoğraf Sayısı (`i.fa-photo` içeren `span`)
  - Sahiplenme Durumu ("Claimed"/"Un Claimed" içeren `span`)
  - Bulunduğu Konum Sayısı (`td.text-center > h5`)
  - Ortalama Sıralama (AR) (`span.dotlg2`)

#### C. `scrape_sponsorlu_listeler(soup)` ✅
- **table#tbl_ads_rank** içindeki sponsorlu liste verilerini çeker:
  - İsim (`a.ext`)
  - Puan/Yorum (`div.rating-container + span`)
  - Görülme Sayısı (son `td`'nin metni)

#### D. `scrape_detayli_sonuclar(soup)` ✅
- **div#resultModal** içindeki `div.results_body` alanından veri çeker:
  - Her `div.bg-light.panel-body` için:
    - Sıra (`span.dot`)
    - İsim (`h5`)
    - Puan/Yorum (`div.rating-container + span`)
    - Adres (Yorum sayısından sonraki `div`)

#### E. `scrape_harita_verileri(soup)` ✅
- Script etiketlerinden `var pinz = [...]` array'ini bulur
- Regex ile JSON verisini yakalar (`re.search(r'var pinz = (\[.*?\]);', script_text, re.DOTALL)`)
- JSON ayrıştırma ile her pin objesi için:
  - `lat`, `lon`, `lable`, `title` bilgilerini çıkarır
  - Temiz bir liste formatında döndürür

### 2. **Yardımcı Fonksiyonlar**

#### A. `get_html_content(url)` ✅
- URL'den HTML içeriğini alır
- User-Agent header'ı ile gerçekçi tarayıcı kimliği
- 30 saniye timeout
- Hata yönetimi ile BeautifulSoup objesi döndürür

#### B. `safe_extract_text(element, default="N/A")` ✅
- Güvenli metin çıkarma
- Element bulunamazsa varsayılan değer döndürür
- Try-except blokları ile hata yönetimi

#### C. `safe_extract_attribute(element, attribute, default="N/A")` ✅
- Güvenli attribute çıkarma
- Element ve attribute varlığını kontrol eder
- Hata durumunda varsayılan değer döndürür

### 3. **Hata Yönetimi** ✅
- Her veri çekme işlemi için try-except blokları
- Element bulunamadığında "N/A" değeri atanması
- HTTP istekleri için timeout yönetimi
- JSON ayrıştırma hataları için özel yakalama
- Kapsamlı hata mesajları

### 4. **Ana Fonksiyon (`main()`)** ✅
- Tüm veri çekme fonksiyonlarını sırayla çalıştırır
- Sonuçları JSON dosyasına kaydeder (`scraped_data.json`)
- Özet istatistikler gösterir
- İlerleme durumu bildirimleri

## 📁 Proje Dosyaları

### 1. **web_scraper.py** (16KB, 443 satır)
- Ana scraping scripti
- Tüm veri çekme fonksiyonları
- Hata yönetimi ve güvenlik önlemleri
- Type hints ve dokümantasyon

### 2. **requirements.txt** (51B, 3 satır)
- Gerekli Python kütüphaneleri:
  - `requests>=2.31.0`
  - `beautifulsoup4>=4.12.0`
  - `lxml>=4.9.0`

### 3. **README.md** (4.5KB, 196 satır)
- Kapsamlı kullanım kılavuzu
- Kurulum talimatları
- Örnek kullanımlar
- Sorun giderme rehberi
- Güvenlik ve etik notlar

### 4. **test_scraper.py** (4.7KB, 159 satır)
- Kütüphane varlık testleri
- Script import testleri
- HTTP isteği testleri
- Detaylı test raporları

## 🚀 Kullanım

### Kurulum
```bash
# Sanal ortam ile
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Sistem paketleri ile (Ubuntu/Debian)
sudo apt install python3-requests python3-bs4 python3-lxml
```

### Çalıştırma
```bash
# Test
python3 test_scraper.py

# Ana script
python3 web_scraper.py
```

### Çıktı
- `scraped_data.json`: Tüm çekilen veriler JSON formatında
- Konsol çıktısı: İlerleme durumu ve özet istatistikler

## 🔧 Teknik Özellikler

### Kod Kalitesi
- ✅ Type hints kullanımı
- ✅ Kapsamlı dokümantasyon
- ✅ Modüler yapı
- ✅ Hata yönetimi
- ✅ Güvenli veri çıkarma

### Performans
- ✅ Timeout yönetimi
- ✅ Bellek verimli işlem
- ✅ Optimize edilmiş selector'lar
- ✅ Batch işlem desteği

### Güvenlik
- ✅ User-Agent header'ı
- ✅ Input validation
- ✅ Exception handling
- ✅ Safe default values

## 📊 Veri Yapısı

Script aşağıdaki yapıda veri döndürür:

```json
{
  "ozet_bilgiler": {
    "isletme_adi": "...",
    "adres": "...",
    "yorum_sayisi": "...",
    "anahtar_kelime_dil": "...",
    "tarih": "...",
    "rank_summary": {...}
  },
  "rakipler": [...],
  "sponsorlu_listeler": [...],
  "detayli_sonuclar": [...],
  "harita_verileri": [...]
}
```

## 🎯 Sonuç

Proje tamamen tamamlanmış ve kullanıma hazırdır. Tüm istenen fonksiyonlar implement edilmiş, hata yönetimi eklenmiş ve kapsamlı dokümantasyon sağlanmıştır. Script, belirtilen URL'den veri çekmek için gerekli tüm özelliklere sahiptir.