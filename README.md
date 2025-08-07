# Web Scraping Scripti

Bu Python scripti, belirtilen URL'den veri çekmek için tasarlanmıştır. `requests`, `BeautifulSoup`, `re` ve `json` kütüphanelerini kullanarak web sayfasından yapılandırılmış veri çıkarır.

## Özellikler

Script aşağıdaki veri türlerini çeker:

1. **Özet Bilgiler** (`scrape_ozet_bilgiler`)
   - İşletme adı, adres, yorum sayısı
   - Anahtar kelime ve dil bilgisi
   - Tarih bilgisi
   - Rank Summary tablosu verileri

2. **Rakip Bilgileri** (`scrape_rakipler`)
   - Rakip işletme isimleri
   - Puan ve yorum bilgileri
   - Adres bilgileri
   - Kategoriler
   - Web siteleri
   - Fotoğraf sayıları
   - Sahiplenme durumları
   - Konum sayıları
   - Ortalama sıralama

3. **Sponsorlu Listeler** (`scrape_sponsorlu_listeler`)
   - Sponsorlu işletme isimleri
   - Puan ve yorum bilgileri
   - Görülme sayıları

4. **Detaylı Sonuçlar** (`scrape_detayli_sonuclar`)
   - Sıralama bilgileri
   - İşletme isimleri
   - Puan ve yorum bilgileri
   - Adres bilgileri

5. **Harita Verileri** (`scrape_harita_verileri`)
   - Enlem ve boylam koordinatları
   - Etiket ve başlık bilgileri

## Kurulum

### Gereksinimler

```bash
pip install requests beautifulsoup4 lxml
```

### Sistem Paketleri ile Kurulum (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3-requests python3-bs4 python3-lxml
```

### Sanal Ortam ile Kurulum

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

## Kullanım

### Temel Kullanım

```bash
python3 web_scraper.py
```

### Fonksiyonları Ayrı Ayrı Kullanma

```python
from web_scraper import *

# HTML içeriğini al
soup = get_html_content('https://www.local-rank.report/scan/97919fde-e478-4081-983f-7e0065b6b5bb')

# Özet bilgileri çek
ozet_bilgiler = scrape_ozet_bilgiler(soup)

# Rakip bilgilerini çek
rakipler = scrape_rakipler(soup)

# Sponsorlu listeleri çek
sponsorlu_listeler = scrape_sponsorlu_listeler(soup)

# Detaylı sonuçları çek
detayli_sonuclar = scrape_detayli_sonuclar(soup)

# Harita verilerini çek
harita_verileri = scrape_harita_verileri(soup)
```

## Çıktı Formatı

Script çalıştırıldığında `scraped_data.json` dosyası oluşturulur. Bu dosya şu yapıda veriler içerir:

```json
{
  "ozet_bilgiler": {
    "isletme_adi": "...",
    "adres": "...",
    "yorum_sayisi": "...",
    "anahtar_kelime_dil": "...",
    "tarih": "...",
    "rank_summary": {
      "key1": "value1",
      "key2": "value2"
    }
  },
  "rakipler": [
    {
      "isim": "...",
      "puan_yorum": "...",
      "adres": "...",
      "kategoriler": "...",
      "web_sitesi": "...",
      "fotograf_sayisi": "...",
      "sahiplenme_durumu": "...",
      "bulundugu_konum_sayisi": "...",
      "ortalama_siralama_ar": "..."
    }
  ],
  "sponsorlu_listeler": [
    {
      "isim": "...",
      "puan_yorum": "...",
      "gorulme_sayisi": "..."
    }
  ],
  "detayli_sonuclar": [
    {
      "sira": "...",
      "isim": "...",
      "puan_yorum": "...",
      "adres": "..."
    }
  ],
  "harita_verileri": [
    {
      "lat": "...",
      "lon": "...",
      "label": "...",
      "title": "..."
    }
  ]
}
```

## Hata Yönetimi

Script aşağıdaki hata yönetimi özelliklerine sahiptir:

- **Güvenli Veri Çıkarma**: Element bulunamadığında "N/A" değeri döndürür
- **Try-Except Blokları**: Her veri çekme işlemi için hata yakalama
- **Timeout Yönetimi**: HTTP istekleri için 30 saniye timeout
- **User-Agent**: Gerçekçi tarayıcı kimliği

## Güvenlik ve Etik

- Script sadece belirtilen URL'den veri çeker
- Rate limiting uygulanmamıştır (gerekirse eklenebilir)
- Robots.txt kontrolü yapılmamıştır
- Web sitesinin kullanım şartlarına uygun kullanım önerilir

## Sorun Giderme

### Yaygın Hatalar

1. **ModuleNotFoundError**: Gerekli kütüphaneler yüklü değil
2. **ConnectionError**: İnternet bağlantısı veya URL erişim sorunu
3. **TimeoutError**: Sunucu yanıt vermiyor
4. **JSONDecodeError**: Harita verileri ayrıştırılamıyor

### Çözümler

- Kütüphaneleri yeniden yükleyin
- İnternet bağlantınızı kontrol edin
- URL'nin erişilebilir olduğunu doğrulayın
- Timeout değerini artırın

## Lisans

Bu script eğitim amaçlı oluşturulmuştur. Ticari kullanım için gerekli izinleri alın.

## Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun