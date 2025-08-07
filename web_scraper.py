import requests
from bs4 import BeautifulSoup
import re
import json


def get_html_content(url):
    """URL'den HTML içeriğini al ve BeautifulSoup ile ayrıştır"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except Exception as e:
        print(f"HTML içeriği alınırken hata oluştu: {e}")
        return None


def scrape_ozet_bilgiler(soup):
    """Scan Information ve Rank Summary tablolarından özet bilgileri çek"""
    ozet_data = {}
    
    try:
        # Scan Information Tablosu
        scan_info_section = soup.find('h4', string='Scan Information')
        if scan_info_section:
            scan_table = scan_info_section.find_next('table')
            if scan_table:
                # İşletme Adı
                try:
                    bizname = scan_table.find('span', class_='bizname')
                    ozet_data['isletme_adi'] = bizname.get_text(strip=True) if bizname else 'N/A'
                except:
                    ozet_data['isletme_adi'] = 'N/A'
                
                # Adres
                try:
                    address = scan_table.find('span', class_='center-block')
                    ozet_data['adres'] = address.get_text(strip=True) if address else 'N/A'
                except:
                    ozet_data['adres'] = 'N/A'
                
                # Yorum Sayısı
                try:
                    rating_container = scan_table.find('div', class_='rating-container')
                    if rating_container:
                        rating_span = rating_container.find_next_sibling('span')
                        ozet_data['yorum_sayisi'] = rating_span.get_text(strip=True) if rating_span else 'N/A'
                    else:
                        ozet_data['yorum_sayisi'] = 'N/A'
                except:
                    ozet_data['yorum_sayisi'] = 'N/A'
                
                # Anahtar Kelime ve Dil
                try:
                    keyword_td = scan_table.find('td', string=lambda text: text and 'Keyword' in text)
                    if keyword_td:
                        keyword_value_td = keyword_td.find_next_sibling('td')
                        ozet_data['anahtar_kelime'] = keyword_value_td.get_text(strip=True) if keyword_value_td else 'N/A'
                    else:
                        ozet_data['anahtar_kelime'] = 'N/A'
                except:
                    ozet_data['anahtar_kelime'] = 'N/A'
                
                # Tarih
                try:
                    date_td = scan_table.find('td', class_='cnv_dt_lcl')
                    ozet_data['tarih'] = date_td.get_text(strip=True) if date_td else 'N/A'
                except:
                    ozet_data['tarih'] = 'N/A'
        
        # Rank Summary Tablosu
        rank_summary_section = soup.find('h4', string='Rank Summary')
        if rank_summary_section:
            rank_table = rank_summary_section.find_next('table')
            if rank_table:
                rank_data = {}
                try:
                    rows = rank_table.find_all('tr')
                    for row in rows:
                        tds = row.find_all('td')
                        if len(tds) >= 2:
                            key = tds[0].get_text(strip=True)
                            value = tds[1].get_text(strip=True)
                            if key and value:
                                rank_data[key] = value
                    ozet_data['rank_summary'] = rank_data
                except:
                    ozet_data['rank_summary'] = {}
            else:
                ozet_data['rank_summary'] = {}
        else:
            ozet_data['rank_summary'] = {}
            
    except Exception as e:
        print(f"Özet bilgiler çekilirken hata oluştu: {e}")
    
    return ozet_data


def scrape_rakipler(soup):
    """table#tbl_comp_rank'dan rakip bilgilerini çek"""
    rakipler = []
    
    try:
        comp_table = soup.find('table', id='tbl_comp_rank')
        if comp_table:
            tbody = comp_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    rakip_data = {}
                    
                    try:
                        # İsim
                        name_link = row.find('a', class_='ext')
                        rakip_data['isim'] = name_link.get_text(strip=True) if name_link else 'N/A'
                    except:
                        rakip_data['isim'] = 'N/A'
                    
                    try:
                        # Puan/Yorum
                        rating_container = row.find('div', class_='rating-container')
                        if rating_container:
                            rating_span = rating_container.find_next_sibling('span')
                            rakip_data['puan_yorum'] = rating_span.get_text(strip=True) if rating_span else 'N/A'
                        else:
                            rakip_data['puan_yorum'] = 'N/A'
                    except:
                        rakip_data['puan_yorum'] = 'N/A'
                    
                    try:
                        # Adres
                        map_marker = row.find('i', class_='fa-map-marker')
                        if map_marker:
                            address_span = map_marker.find_parent('span', class_='center-block')
                            rakip_data['adres'] = address_span.get_text(strip=True) if address_span else 'N/A'
                        else:
                            rakip_data['adres'] = 'N/A'
                    except:
                        rakip_data['adres'] = 'N/A'
                    
                    try:
                        # Kategoriler
                        categories_p = row.find('p', string=lambda text: text and 'Categories:' in text)
                        rakip_data['kategoriler'] = categories_p.get_text(strip=True) if categories_p else 'N/A'
                    except:
                        rakip_data['kategoriler'] = 'N/A'
                    
                    try:
                        # Web Sitesi
                        globe_icon = row.find('i', class_='fa-globe')
                        if globe_icon:
                            website_span = globe_icon.find_parent('span')
                            if website_span:
                                website_link = website_span.find('a')
                                rakip_data['web_sitesi'] = website_link.get('href') if website_link else 'N/A'
                            else:
                                rakip_data['web_sitesi'] = 'N/A'
                        else:
                            rakip_data['web_sitesi'] = 'N/A'
                    except:
                        rakip_data['web_sitesi'] = 'N/A'
                    
                    try:
                        # Fotoğraf Sayısı
                        photo_icon = row.find('i', class_='fa-photo')
                        if photo_icon:
                            photo_span = photo_icon.find_parent('span')
                            rakip_data['fotograf_sayisi'] = photo_span.get_text(strip=True) if photo_span else 'N/A'
                        else:
                            rakip_data['fotograf_sayisi'] = 'N/A'
                    except:
                        rakip_data['fotograf_sayisi'] = 'N/A'
                    
                    try:
                        # Sahiplenme Durumu
                        claimed_span = row.find('span', string=lambda text: text and ('Claimed' in text or 'Un Claimed' in text))
                        rakip_data['sahiplenme_durumu'] = claimed_span.get_text(strip=True) if claimed_span else 'N/A'
                    except:
                        rakip_data['sahiplenme_durumu'] = 'N/A'
                    
                    try:
                        # Bulunduğu Konum Sayısı
                        center_h5 = row.find('td', class_='text-center')
                        if center_h5:
                            h5 = center_h5.find('h5')
                            rakip_data['konum_sayisi'] = h5.get_text(strip=True) if h5 else 'N/A'
                        else:
                            rakip_data['konum_sayisi'] = 'N/A'
                    except:
                        rakip_data['konum_sayisi'] = 'N/A'
                    
                    try:
                        # Ortalama Sıralama (AR)
                        dotlg2_span = row.find('span', class_='dotlg2')
                        rakip_data['ortalama_siralama'] = dotlg2_span.get_text(strip=True) if dotlg2_span else 'N/A'
                    except:
                        rakip_data['ortalama_siralama'] = 'N/A'
                    
                    rakipler.append(rakip_data)
    
    except Exception as e:
        print(f"Rakip bilgileri çekilirken hata oluştu: {e}")
    
    return rakipler


def scrape_sponsorlu_listeler(soup):
    """table#tbl_ads_rank'dan sponsorlu liste bilgilerini çek"""
    sponsorlu_listeler = []
    
    try:
        ads_table = soup.find('table', id='tbl_ads_rank')
        if ads_table:
            tbody = ads_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    sponsorlu_data = {}
                    
                    try:
                        # İsim
                        name_link = row.find('a', class_='ext')
                        sponsorlu_data['isim'] = name_link.get_text(strip=True) if name_link else 'N/A'
                    except:
                        sponsorlu_data['isim'] = 'N/A'
                    
                    try:
                        # Puan/Yorum
                        rating_container = row.find('div', class_='rating-container')
                        if rating_container:
                            rating_span = rating_container.find_next_sibling('span')
                            sponsorlu_data['puan_yorum'] = rating_span.get_text(strip=True) if rating_span else 'N/A'
                        else:
                            sponsorlu_data['puan_yorum'] = 'N/A'
                    except:
                        sponsorlu_data['puan_yorum'] = 'N/A'
                    
                    try:
                        # Görülme Sayısı (son td)
                        tds = row.find_all('td')
                        if tds:
                            last_td = tds[-1]
                            sponsorlu_data['gorulme_sayisi'] = last_td.get_text(strip=True)
                        else:
                            sponsorlu_data['gorulme_sayisi'] = 'N/A'
                    except:
                        sponsorlu_data['gorulme_sayisi'] = 'N/A'
                    
                    sponsorlu_listeler.append(sponsorlu_data)
    
    except Exception as e:
        print(f"Sponsorlu liste bilgileri çekilirken hata oluştu: {e}")
    
    return sponsorlu_listeler


def scrape_detayli_sonuclar(soup):
    """div#resultModal'dan detaylı sonuçları çek"""
    detayli_sonuclar = []
    
    try:
        result_modal = soup.find('div', id='resultModal')
        if result_modal:
            results_body = result_modal.find('div', class_='results_body')
            if results_body:
                panels = results_body.find_all('div', class_='bg-light panel-body')
                for panel in panels:
                    sonuc_data = {}
                    
                    try:
                        # Sıra
                        dot_span = panel.find('span', class_='dot')
                        sonuc_data['sira'] = dot_span.get_text(strip=True) if dot_span else 'N/A'
                    except:
                        sonuc_data['sira'] = 'N/A'
                    
                    try:
                        # İsim
                        h5 = panel.find('h5')
                        sonuc_data['isim'] = h5.get_text(strip=True) if h5 else 'N/A'
                    except:
                        sonuc_data['isim'] = 'N/A'
                    
                    try:
                        # Puan/Yorum
                        rating_container = panel.find('div', class_='rating-container')
                        if rating_container:
                            rating_span = rating_container.find_next_sibling('span')
                            sonuc_data['puan_yorum'] = rating_span.get_text(strip=True) if rating_span else 'N/A'
                        else:
                            sonuc_data['puan_yorum'] = 'N/A'
                    except:
                        sonuc_data['puan_yorum'] = 'N/A'
                    
                    try:
                        # Adres (Yorum sayısından sonraki div)
                        rating_container = panel.find('div', class_='rating-container')
                        if rating_container:
                            # Yorum span'ını bul
                            rating_span = rating_container.find_next_sibling('span')
                            if rating_span:
                                # Yorum span'ından sonraki div'i bul
                                address_div = rating_span.find_next_sibling('div')
                                sonuc_data['adres'] = address_div.get_text(strip=True) if address_div else 'N/A'
                            else:
                                sonuc_data['adres'] = 'N/A'
                        else:
                            sonuc_data['adres'] = 'N/A'
                    except:
                        sonuc_data['adres'] = 'N/A'
                    
                    detayli_sonuclar.append(sonuc_data)
    
    except Exception as e:
        print(f"Detaylı sonuçlar çekilirken hata oluştu: {e}")
    
    return detayli_sonuclar


def scrape_harita_verileri(soup):
    """Sayfadaki var pinz = [...] script'inden harita verilerini çek"""
    harita_verileri = []
    
    try:
        # Tüm script etiketlerini bul
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string:
                # var pinz = [ içeren script'i bul
                if 'var pinz = [' in script.string:
                    script_text = script.string
                    
                    # Regex ile [ ile ]; arasındaki içeriği yakala
                    match = re.search(r'var pinz = (\[.*?\]);', script_text, re.DOTALL)
                    if match:
                        pinz_data = match.group(1)
                        
                        try:
                            # JSON'a dönüştür
                            pinz_list = json.loads(pinz_data)
                            
                            # Her obje için lat, lon, lable ve title bilgilerini ayıkla
                            for item in pinz_list:
                                if isinstance(item, dict):
                                    harita_data = {
                                        'lat': item.get('lat', 'N/A'),
                                        'lon': item.get('lon', 'N/A'),
                                        'lable': item.get('lable', 'N/A'),
                                        'title': item.get('title', 'N/A')
                                    }
                                    harita_verileri.append(harita_data)
                        except json.JSONDecodeError as e:
                            print(f"JSON parse hatası: {e}")
                        
                        break  # İlk match'i bulduk, çıkalım
    
    except Exception as e:
        print(f"Harita verileri çekilirken hata oluştu: {e}")
    
    return harita_verileri


def main():
    """Ana fonksiyon - tüm veri çekme işlemlerini koordine eder"""
    url = 'https://www.local-rank.report/scan/97919fde-e478-4081-983f-7e0065b6b5bb'
    
    print("HTML içeriği alınıyor...")
    soup = get_html_content(url)
    
    if soup is None:
        print("HTML içeriği alınamadı. Script sonlandırılıyor.")
        return
    
    print("Veri çekme işlemleri başlatılıyor...")
    
    # Tüm veri çekme fonksiyonlarını çalıştır
    ozet_bilgiler = scrape_ozet_bilgiler(soup)
    rakipler = scrape_rakipler(soup)
    sponsorlu_listeler = scrape_sponsorlu_listeler(soup)
    detayli_sonuclar = scrape_detayli_sonuclar(soup)
    harita_verileri = scrape_harita_verileri(soup)
    
    # Sonuçları göster
    print("\n=== ÖZET BİLGİLER ===")
    print(json.dumps(ozet_bilgiler, indent=2, ensure_ascii=False))
    
    print(f"\n=== RAKİPLER ({len(rakipler)} adet) ===")
    for i, rakip in enumerate(rakipler, 1):
        print(f"{i}. {rakip}")
    
    print(f"\n=== SPONSORLU LİSTELER ({len(sponsorlu_listeler)} adet) ===")
    for i, sponsorlu in enumerate(sponsorlu_listeler, 1):
        print(f"{i}. {sponsorlu}")
    
    print(f"\n=== DETAYLI SONUÇLAR ({len(detayli_sonuclar)} adet) ===")
    for i, sonuc in enumerate(detayli_sonuclar, 1):
        print(f"{i}. {sonuc}")
    
    print(f"\n=== HARİTA VERİLERİ ({len(harita_verileri)} adet) ===")
    for i, konum in enumerate(harita_verileri, 1):
        print(f"{i}. {konum}")
    
    # Tüm verileri tek bir dictionary'de topla
    tum_veriler = {
        'ozet_bilgiler': ozet_bilgiler,
        'rakipler': rakipler,
        'sponsorlu_listeler': sponsorlu_listeler,
        'detayli_sonuclar': detayli_sonuclar,
        'harita_verileri': harita_verileri
    }
    
    # JSON dosyasına kaydet
    with open('/workspace/scraping_results.json', 'w', encoding='utf-8') as f:
        json.dump(tum_veriler, f, indent=2, ensure_ascii=False)
    
    print(f"\nTüm veriler 'scraping_results.json' dosyasına kaydedildi.")


if __name__ == "__main__":
    main()