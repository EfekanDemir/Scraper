import requests
from bs4 import BeautifulSoup
import re
import json

# URL tanımlaması
url = 'https://www.local-rank.report/scan/97919fde-e478-4081-983f-7e0065b6b5bb'

def get_soup(url):
    """URL'den HTML içeriğini alıp BeautifulSoup objesi döndürür"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except Exception as e:
        print(f"Hata: URL'den veri alınamadı - {e}")
        return None

def scrape_ozet_bilgiler(soup):
    """Özet bilgileri (Scan Information ve Rank Summary) çeker"""
    ozet_bilgiler = {}
    
    try:
        # Scan Information Tablosu
        scan_info_header = soup.find('h4', string='Scan Information')
        if scan_info_header:
            scan_table = scan_info_header.find_next('table')
            if scan_table:
                # İşletme Adı
                try:
                    bizname = scan_table.find('span', class_='bizname')
                    ozet_bilgiler['isletme_adi'] = bizname.text.strip() if bizname else "N/A"
                except:
                    ozet_bilgiler['isletme_adi'] = "N/A"
                
                # Adres
                try:
                    address = scan_table.find('span', class_='center-block')
                    ozet_bilgiler['adres'] = address.text.strip() if address else "N/A"
                except:
                    ozet_bilgiler['adres'] = "N/A"
                
                # Yorum Sayısı
                try:
                    rating_container = scan_table.find('div', class_='rating-container')
                    if rating_container:
                        review_span = rating_container.find_next_sibling('span')
                        ozet_bilgiler['yorum_sayisi'] = review_span.text.strip() if review_span else "N/A"
                    else:
                        ozet_bilgiler['yorum_sayisi'] = "N/A"
                except:
                    ozet_bilgiler['yorum_sayisi'] = "N/A"
                
                # Anahtar Kelime ve Dil
                try:
                    keyword_td = scan_table.find('td', string=re.compile('Keyword'))
                    if keyword_td:
                        keyword_value = keyword_td.find_next_sibling('td')
                        ozet_bilgiler['anahtar_kelime_dil'] = keyword_value.text.strip() if keyword_value else "N/A"
                    else:
                        ozet_bilgiler['anahtar_kelime_dil'] = "N/A"
                except:
                    ozet_bilgiler['anahtar_kelime_dil'] = "N/A"
                
                # Tarih
                try:
                    date_td = scan_table.find('td', class_='cnv_dt_lcl')
                    ozet_bilgiler['tarih'] = date_td.text.strip() if date_td else "N/A"
                except:
                    ozet_bilgiler['tarih'] = "N/A"
        
        # Rank Summary Tablosu
        rank_summary_header = soup.find('h4', string='Rank Summary')
        if rank_summary_header:
            rank_table = rank_summary_header.find_next('table')
            if rank_table:
                rows = rank_table.find_all('tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 2:
                        key = tds[0].text.strip()
                        value = tds[1].text.strip()
                        ozet_bilgiler[key] = value
    
    except Exception as e:
        print(f"Özet bilgiler çekilirken hata: {e}")
    
    return ozet_bilgiler

def scrape_rakipler(soup):
    """Rakip listesini çeker"""
    rakipler = []
    
    try:
        # Rakipler tablosunu bul
        comp_table = soup.find('table', id='tbl_comp_rank')
        if comp_table:
            tbody = comp_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                
                for row in rows:
                    rakip = {}
                    
                    try:
                        # İsim
                        name_link = row.find('a', class_='ext')
                        rakip['isim'] = name_link.text.strip() if name_link else "N/A"
                        
                        # Puan/Yorum
                        rating_container = row.find('div', class_='rating-container')
                        if rating_container:
                            review_span = rating_container.find_next_sibling('span')
                            rakip['puan_yorum'] = review_span.text.strip() if review_span else "N/A"
                        else:
                            rakip['puan_yorum'] = "N/A"
                        
                        # Adres
                        address_span = row.find('i', class_='fa-map-marker')
                        if address_span:
                            address_parent = address_span.find_parent('span', class_='center-block')
                            rakip['adres'] = address_parent.text.strip() if address_parent else "N/A"
                        else:
                            rakip['adres'] = "N/A"
                        
                        # Kategoriler
                        categories_p = row.find('p', string=re.compile('Categories:'))
                        rakip['kategoriler'] = categories_p.text.strip() if categories_p else "N/A"
                        
                        # Web Sitesi
                        website_icon = row.find('i', class_='fa-globe')
                        if website_icon:
                            website_span = website_icon.find_parent('span')
                            if website_span:
                                website_link = website_span.find('a')
                                rakip['website'] = website_link.get('href', "N/A") if website_link else "N/A"
                            else:
                                rakip['website'] = "N/A"
                        else:
                            rakip['website'] = "N/A"
                        
                        # Fotoğraf Sayısı
                        photo_icon = row.find('i', class_='fa-photo')
                        if photo_icon:
                            photo_span = photo_icon.find_parent('span')
                            rakip['fotograf_sayisi'] = photo_span.text.strip() if photo_span else "N/A"
                        else:
                            rakip['fotograf_sayisi'] = "N/A"
                        
                        # Sahiplenme Durumu
                        claimed_span = row.find('span', string=re.compile('Claimed|Un Claimed'))
                        rakip['sahiplenme_durumu'] = claimed_span.text.strip() if claimed_span else "N/A"
                        
                        # Bulunduğu Konum Sayısı
                        location_td = row.find('td', class_='text-center')
                        if location_td:
                            location_h5 = location_td.find('h5')
                            rakip['konum_sayisi'] = location_h5.text.strip() if location_h5 else "N/A"
                        else:
                            rakip['konum_sayisi'] = "N/A"
                        
                        # Ortalama Sıralama (AR)
                        ar_span = row.find('span', class_='dotlg2')
                        rakip['ortalama_siralama'] = ar_span.text.strip() if ar_span else "N/A"
                        
                        rakipler.append(rakip)
                    
                    except Exception as e:
                        print(f"Rakip verisi çekilirken hata: {e}")
                        continue
    
    except Exception as e:
        print(f"Rakipler tablosu çekilirken hata: {e}")
    
    return rakipler

def scrape_sponsorlu_listeler(soup):
    """Sponsorlu listeleri çeker"""
    sponsorlu_listeler = []
    
    try:
        # Sponsorlu listeler tablosunu bul
        ads_table = soup.find('table', id='tbl_ads_rank')
        if ads_table:
            tbody = ads_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                
                for row in rows:
                    sponsor = {}
                    
                    try:
                        # İsim
                        name_link = row.find('a', class_='ext')
                        sponsor['isim'] = name_link.text.strip() if name_link else "N/A"
                        
                        # Puan/Yorum
                        rating_container = row.find('div', class_='rating-container')
                        if rating_container:
                            review_span = rating_container.find_next_sibling('span')
                            sponsor['puan_yorum'] = review_span.text.strip() if review_span else "N/A"
                        else:
                            sponsor['puan_yorum'] = "N/A"
                        
                        # Görülme Sayısı (son td)
                        tds = row.find_all('td')
                        if tds:
                            sponsor['gorulme_sayisi'] = tds[-1].text.strip() if tds[-1] else "N/A"
                        else:
                            sponsor['gorulme_sayisi'] = "N/A"
                        
                        sponsorlu_listeler.append(sponsor)
                    
                    except Exception as e:
                        print(f"Sponsorlu liste verisi çekilirken hata: {e}")
                        continue
    
    except Exception as e:
        print(f"Sponsorlu listeler tablosu çekilirken hata: {e}")
    
    return sponsorlu_listeler

def scrape_detayli_sonuclar(soup):
    """Detaylı sonuçları çeker"""
    detayli_sonuclar = []
    
    try:
        # resultModal içindeki results_body alanını bul
        result_modal = soup.find('div', id='resultModal')
        if result_modal:
            results_body = result_modal.find('div', class_='results_body')
            if results_body:
                # Her bir sonuç panelini bul
                panels = results_body.find_all('div', class_=['bg-light', 'panel-body'])
                
                for panel in panels:
                    sonuc = {}
                    
                    try:
                        # Sıra
                        sira_span = panel.find('span', class_='dot')
                        sonuc['sira'] = sira_span.text.strip() if sira_span else "N/A"
                        
                        # İsim
                        isim_h5 = panel.find('h5')
                        sonuc['isim'] = isim_h5.text.strip() if isim_h5 else "N/A"
                        
                        # Puan/Yorum
                        rating_container = panel.find('div', class_='rating-container')
                        if rating_container:
                            review_span = rating_container.find_next_sibling('span')
                            sonuc['puan_yorum'] = review_span.text.strip() if review_span else "N/A"
                        else:
                            sonuc['puan_yorum'] = "N/A"
                        
                        # Adres (Yorum sayısından sonraki div)
                        if rating_container:
                            parent_div = rating_container.find_parent('div')
                            if parent_div:
                                # Yorum sayısından sonraki div'i bul
                                next_div = parent_div.find_next_sibling('div')
                                sonuc['adres'] = next_div.text.strip() if next_div else "N/A"
                            else:
                                sonuc['adres'] = "N/A"
                        else:
                            sonuc['adres'] = "N/A"
                        
                        detayli_sonuclar.append(sonuc)
                    
                    except Exception as e:
                        print(f"Detaylı sonuç verisi çekilirken hata: {e}")
                        continue
    
    except Exception as e:
        print(f"Detaylı sonuçlar çekilirken hata: {e}")
    
    return detayli_sonuclar

def scrape_harita_verileri(soup):
    """Harita verilerini çeker"""
    harita_verileri = []
    
    try:
        # Tüm script etiketlerini bul
        scripts = soup.find_all('script')
        
        for script in scripts:
            script_text = script.string
            if script_text and 'var pinz = [' in script_text:
                try:
                    # Regex ile var pinz = [ ile ]; arasındaki içeriği yakala
                    match = re.search(r'var pinz = (\[.*?\]);', script_text, re.DOTALL)
                    if match:
                        pinz_data = match.group(1)
                        
                        # JSON olarak parse et
                        pinz_list = json.loads(pinz_data)
                        
                        # Her bir obje için temiz veri oluştur
                        for pin in pinz_list:
                            harita_noktasi = {}
                            
                            try:
                                harita_noktasi['lat'] = pin.get('lat', None)
                                harita_noktasi['lon'] = pin.get('lon', None)
                                harita_noktasi['lable'] = pin.get('lable', "N/A")
                                harita_noktasi['title'] = pin.get('title', "N/A")
                                
                                harita_verileri.append(harita_noktasi)
                            
                            except Exception as e:
                                print(f"Harita noktası işlenirken hata: {e}")
                                continue
                        
                        break  # pinz verisi bulundu, döngüden çık
                
                except Exception as e:
                    print(f"Harita verileri parse edilirken hata: {e}")
    
    except Exception as e:
        print(f"Script etiketleri aranırken hata: {e}")
    
    return harita_verileri

def main():
    """Ana fonksiyon - tüm veri çekme işlemlerini koordine eder"""
    print("Veri çekme işlemi başlatılıyor...")
    print(f"URL: {url}")
    
    # HTML içeriğini al
    soup = get_soup(url)
    if not soup:
        print("HTML içeriği alınamadı. İşlem sonlandırılıyor.")
        return
    
    # Tüm verileri çek
    tum_veriler = {}
    
    print("\n1. Özet bilgiler çekiliyor...")
    tum_veriler['ozet_bilgiler'] = scrape_ozet_bilgiler(soup)
    
    print("2. Rakipler çekiliyor...")
    tum_veriler['rakipler'] = scrape_rakipler(soup)
    
    print("3. Sponsorlu listeler çekiliyor...")
    tum_veriler['sponsorlu_listeler'] = scrape_sponsorlu_listeler(soup)
    
    print("4. Detaylı sonuçlar çekiliyor...")
    tum_veriler['detayli_sonuclar'] = scrape_detayli_sonuclar(soup)
    
    print("5. Harita verileri çekiliyor...")
    tum_veriler['harita_verileri'] = scrape_harita_verileri(soup)
    
    # Sonuçları JSON dosyasına kaydet
    with open('scraped_data.json', 'w', encoding='utf-8') as f:
        json.dump(tum_veriler, f, ensure_ascii=False, indent=2)
    
    print("\nVeri çekme işlemi tamamlandı!")
    print("Veriler 'scraped_data.json' dosyasına kaydedildi.")
    
    # Özet bilgi göster
    print("\n--- ÖZET BİLGİ ---")
    print(f"Toplam rakip sayısı: {len(tum_veriler['rakipler'])}")
    print(f"Sponsorlu liste sayısı: {len(tum_veriler['sponsorlu_listeler'])}")
    print(f"Detaylı sonuç sayısı: {len(tum_veriler['detayli_sonuclar'])}")
    print(f"Harita noktası sayısı: {len(tum_veriler['harita_verileri'])}")
    
    return tum_veriler

if __name__ == "__main__":
    # Script'i çalıştır
    veriler = main()
    
    # İsteğe bağlı: Örnek veri gösterimi
    if veriler and veriler.get('ozet_bilgiler'):
        print("\n--- ÖRNEK ÖZET BİLGİLER ---")
        for key, value in veriler['ozet_bilgiler'].items():
            print(f"{key}: {value}")