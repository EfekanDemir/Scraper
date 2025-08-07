# Web Scraper - Local Rank Report

Bu Python scripti, `https://www.local-rank.report` sitesinden işletme verilerini toplamak için geliştirilmiştir.

## Özellikler

Script aşağıdaki verileri çeker:

1. **Özet Bilgiler** (`scrape_ozet_bilgiler`)
   - İşletme adı
   - Adres
   - Yorum sayısı
   - Anahtar kelime ve dil
   - Tarih
   - Rank Summary verileri

2. **Rakipler** (`scrape_rakipler`)
   - İsim
   - Puan/Yorum
   - Adres
   - Kategoriler
   - Web sitesi
   - Fotoğraf sayısı
   - Sahiplenme durumu
   - Konum sayısı
   - Ortalama sıralama

3. **Sponsorlu Listeler** (`scrape_sponsorlu_listeler`)
   - İsim
   - Puan/Yorum
   - Görülme sayısı

4. **Detaylı Sonuçlar** (`scrape_detayli_sonuclar`)
   - Sıra
   - İsim
   - Puan/Yorum
   - Adres

5. **Harita Verileri** (`scrape_harita_verileri`)
   - Latitude
   - Longitude
   - Label
   - Title

## Gereksinimler

```bash
pip install -r requirements.txt
```

veya sistem paketleri:

```bash
sudo apt install python3-requests python3-bs4
```

## Kullanım

```bash
python3 web_scraper.py
```

Script çalıştığında:
- Belirtilen URL'den HTML içeriğini alır
- Tüm veri çekme fonksiyonlarını sırayla çalıştırır
- Sonuçları konsola yazdırır
- Tüm verileri `scraping_results.json` dosyasına kaydeder

## Çıktı

Script çalıştığında iki tür çıktı üretir:

1. **Konsol çıktısı**: Çekilen verilerin özetini gösterir
2. **JSON dosyası**: Tüm verileri `scraping_results.json` dosyasına kaydeder

## Hata Yönetimi

- Her veri çekme işlemi try-except blokları ile korunmuştur
- Veri bulunamadığında "N/A" değeri atanır
- Ağ hataları veya HTML yapısı değişiklikleri durumunda script çökmez

## Fonksiyonlar

- `get_html_content(url)`: URL'den HTML içeriğini alır
- `scrape_ozet_bilgiler(soup)`: Scan Information ve Rank Summary tablolarını çeker
- `scrape_rakipler(soup)`: Rakip bilgilerini çeker
- `scrape_sponsorlu_listeler(soup)`: Sponsorlu liste bilgilerini çeker  
- `scrape_detayli_sonuclar(soup)`: Detaylı sonuçları çeker
- `scrape_harita_verileri(soup)`: JavaScript'ten harita verilerini çeker

## Notlar

- Script, saygılı kullanım için User-Agent header'ı kullanır
- JSON parse hatası halinde harita verileri boş olabilir
- Tüm fonksiyonlar bağımsız çalışabilir