import requests
from bs4 import BeautifulSoup
import re
import json
from typing import Dict, List, Optional, Any


def get_html_content(url: str) -> Optional[BeautifulSoup]:
    """
    URL'den HTML içeriğini alır ve BeautifulSoup objesi olarak döndürür.
    
    Args:
        url (str): Veri çekilecek URL
        
    Returns:
        BeautifulSoup: Ayrıştırılmış HTML içeriği veya None (hata durumunda)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        print(f"HTML içeriği alınırken hata oluştu: {e}")
        return None
    except Exception as e:
        print(f"Beklenmeyen hata: {e}")
        return None


def safe_extract_text(element, default: str = "N/A") -> str:
    """
    Güvenli bir şekilde element metnini çıkarır.
    
    Args:
        element: BeautifulSoup elementi
        default (str): Element bulunamazsa döndürülecek varsayılan değer
        
    Returns:
        str: Çıkarılan metin veya varsayılan değer
    """
    try:
        if element:
            return element.get_text(strip=True)
        return default
    except Exception:
        return default


def safe_extract_attribute(element, attribute: str, default: str = "N/A") -> str:
    """
    Güvenli bir şekilde element attribute'unu çıkarır.
    
    Args:
        element: BeautifulSoup elementi
        attribute (str): Çıkarılacak attribute adı
        default (str): Attribute bulunamazsa döndürülecek varsayılan değer
        
    Returns:
        str: Çıkarılan attribute değeri veya varsayılan değer
    """
    try:
        if element and element.has_attr(attribute):
            return element[attribute]
        return default
    except Exception:
        return default


def scrape_ozet_bilgiler(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Scan Information ve Rank Summary tablolarından özet bilgileri çeker.
    
    Args:
        soup (BeautifulSoup): Ayrıştırılmış HTML içeriği
        
    Returns:
        Dict[str, Any]: Özet bilgileri içeren dictionary
    """
    ozet_bilgiler = {}
    
    try:
        # Scan Information tablosunu bul
        scan_info_section = soup.find('h4', string='Scan Information')
        if scan_info_section:
            scan_table = scan_info_section.find_next('table')
            if scan_table:
                # İşletme Adı
                bizname_span = scan_table.find('span', class_='bizname')
                ozet_bilgiler['isletme_adi'] = safe_extract_text(bizname_span)
                
                # Adres
                address_span = scan_table.find('span', class_='center-block')
                ozet_bilgiler['adres'] = safe_extract_text(address_span)
                
                # Yorum Sayısı
                rating_container = scan_table.find('div', class_='rating-container')
                if rating_container:
                    rating_span = rating_container.find_next_sibling('span')
                    ozet_bilgiler['yorum_sayisi'] = safe_extract_text(rating_span)
                else:
                    ozet_bilgiler['yorum_sayisi'] = "N/A"
                
                # Anahtar Kelime ve Dil
                keyword_td = scan_table.find('td', string=lambda text: text and 'Keyword' in text)
                if keyword_td:
                    keyword_value_td = keyword_td.find_next_sibling('td')
                    ozet_bilgiler['anahtar_kelime_dil'] = safe_extract_text(keyword_value_td)
                else:
                    ozet_bilgiler['anahtar_kelime_dil'] = "N/A"
                
                # Tarih
                date_td = scan_table.find('td', class_='cnv_dt_lcl')
                ozet_bilgiler['tarih'] = safe_extract_text(date_td)
        
        # Rank Summary tablosunu bul
        rank_summary_section = soup.find('h4', string='Rank Summary')
        if rank_summary_section:
            rank_table = rank_summary_section.find_next('table')
            if rank_table:
                rank_data = {}
                rows = rank_table.find_all('tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 2:
                        key = safe_extract_text(tds[0])
                        value = safe_extract_text(tds[1])
                        if key and value:
                            rank_data[key] = value
                ozet_bilgiler['rank_summary'] = rank_data
            else:
                ozet_bilgiler['rank_summary'] = {}
        else:
            ozet_bilgiler['rank_summary'] = {}
            
    except Exception as e:
        print(f"Özet bilgiler çekilirken hata oluştu: {e}")
        ozet_bilgiler = {
            'isletme_adi': "N/A",
            'adres': "N/A", 
            'yorum_sayisi': "N/A",
            'anahtar_kelime_dil': "N/A",
            'tarih': "N/A",
            'rank_summary': {}
        }
    
    return ozet_bilgiler


def scrape_rakipler(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Rakip işletmelerin bilgilerini çeker.
    
    Args:
        soup (BeautifulSoup): Ayrıştırılmış HTML içeriği
        
    Returns:
        List[Dict[str, Any]]: Rakip bilgilerini içeren liste
    """
    rakipler = []
    
    try:
        # Rakip tablosunu bul
        rakip_table = soup.find('table', id='tbl_comp_rank')
        if rakip_table:
            tbody = rakip_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    rakip = {}
                    
                    # İsim
                    name_link = row.find('a', class_='ext')
                    rakip['isim'] = safe_extract_text(name_link)
                    
                    # Puan/Yorum
                    rating_container = row.find('div', class_='rating-container')
                    if rating_container:
                        rating_span = rating_container.find_next_sibling('span')
                        rakip['puan_yorum'] = safe_extract_text(rating_span)
                    else:
                        rakip['puan_yorum'] = "N/A"
                    
                    # Adres
                    address_span = row.find('span', class_='center-block')
                    if address_span and address_span.find('i', class_='fa-map-marker'):
                        rakip['adres'] = safe_extract_text(address_span)
                    else:
                        rakip['adres'] = "N/A"
                    
                    # Kategoriler
                    categories_p = row.find('p', string=lambda text: text and 'Categories:' in text)
                    rakip['kategoriler'] = safe_extract_text(categories_p)
                    
                    # Web Sitesi
                    website_link = row.find('span').find('a') if row.find('span') else None
                    if website_link and website_link.find('i', class_='fa-globe'):
                        rakip['web_sitesi'] = safe_extract_attribute(website_link, 'href')
                    else:
                        rakip['web_sitesi'] = "N/A"
                    
                    # Fotoğraf Sayısı
                    photo_span = row.find('span')
                    if photo_span and photo_span.find('i', class_='fa-photo'):
                        rakip['fotograf_sayisi'] = safe_extract_text(photo_span)
                    else:
                        rakip['fotograf_sayisi'] = "N/A"
                    
                    # Sahiplenme Durumu
                    claim_span = row.find('span', string=lambda text: text and ('Claimed' in text or 'Un Claimed' in text))
                    rakip['sahiplenme_durumu'] = safe_extract_text(claim_span)
                    
                    # Bulunduğu Konum Sayısı
                    location_td = row.find('td', class_='text-center')
                    if location_td:
                        location_h5 = location_td.find('h5')
                        rakip['bulundugu_konum_sayisi'] = safe_extract_text(location_h5)
                    else:
                        rakip['bulundugu_konum_sayisi'] = "N/A"
                    
                    # Ortalama Sıralama (AR)
                    ar_span = row.find('span', class_='dotlg2')
                    rakip['ortalama_siralama_ar'] = safe_extract_text(ar_span)
                    
                    rakipler.append(rakip)
                    
    except Exception as e:
        print(f"Rakip bilgileri çekilirken hata oluştu: {e}")
    
    return rakipler


def scrape_sponsorlu_listeler(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Sponsorlu liste bilgilerini çeker.
    
    Args:
        soup (BeautifulSoup): Ayrıştırılmış HTML içeriği
        
    Returns:
        List[Dict[str, Any]]: Sponsorlu liste bilgilerini içeren liste
    """
    sponsorlu_listeler = []
    
    try:
        # Sponsorlu liste tablosunu bul
        ads_table = soup.find('table', id='tbl_ads_rank')
        if ads_table:
            tbody = ads_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    sponsorlu = {}
                    
                    # İsim
                    name_link = row.find('a', class_='ext')
                    sponsorlu['isim'] = safe_extract_text(name_link)
                    
                    # Puan/Yorum
                    rating_container = row.find('div', class_='rating-container')
                    if rating_container:
                        rating_span = rating_container.find_next_sibling('span')
                        sponsorlu['puan_yorum'] = safe_extract_text(rating_span)
                    else:
                        sponsorlu['puan_yorum'] = "N/A"
                    
                    # Görülme Sayısı (son td)
                    tds = row.find_all('td')
                    if tds:
                        last_td = tds[-1]
                        sponsorlu['gorulme_sayisi'] = safe_extract_text(last_td)
                    else:
                        sponsorlu['gorulme_sayisi'] = "N/A"
                    
                    sponsorlu_listeler.append(sponsorlu)
                    
    except Exception as e:
        print(f"Sponsorlu liste bilgileri çekilirken hata oluştu: {e}")
    
    return sponsorlu_listeler


def scrape_detayli_sonuclar(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Detaylı sonuç bilgilerini çeker.
    
    Args:
        soup (BeautifulSoup): Ayrıştırılmış HTML içeriği
        
    Returns:
        List[Dict[str, Any]]: Detaylı sonuç bilgilerini içeren liste
    """
    detayli_sonuclar = []
    
    try:
        # Result modal içindeki results_body alanını bul
        result_modal = soup.find('div', id='resultModal')
        if result_modal:
            results_body = result_modal.find('div', class_='results_body')
            if results_body:
                result_panels = results_body.find_all('div', class_='bg-light panel-body')
                for panel in result_panels:
                    sonuc = {}
                    
                    # Sıra
                    rank_span = panel.find('span', class_='dot')
                    sonuc['sira'] = safe_extract_text(rank_span)
                    
                    # İsim
                    name_h5 = panel.find('h5')
                    sonuc['isim'] = safe_extract_text(name_h5)
                    
                    # Puan/Yorum
                    rating_container = panel.find('div', class_='rating-container')
                    if rating_container:
                        rating_span = rating_container.find_next_sibling('span')
                        sonuc['puan_yorum'] = safe_extract_text(rating_span)
                    else:
                        sonuc['puan_yorum'] = "N/A"
                    
                    # Adres (Yorum sayısından sonraki div)
                    if rating_container:
                        address_div = rating_container.find_next_sibling('div')
                        if address_div:
                            sonuc['adres'] = safe_extract_text(address_div)
                        else:
                            sonuc['adres'] = "N/A"
                    else:
                        sonuc['adres'] = "N/A"
                    
                    detayli_sonuclar.append(sonuc)
                    
    except Exception as e:
        print(f"Detaylı sonuç bilgileri çekilirken hata oluştu: {e}")
    
    return detayli_sonuclar


def scrape_harita_verileri(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Harita verilerini script etiketlerinden çeker.
    
    Args:
        soup (BeautifulSoup): Ayrıştırılmış HTML içeriği
        
    Returns:
        List[Dict[str, Any]]: Harita verilerini içeren liste
    """
    harita_verileri = []
    
    try:
        # Tüm script etiketlerini bul
        scripts = soup.find_all('script')
        
        for script in scripts:
            script_text = script.string
            if script_text and 'var pinz = [' in script_text:
                # Regex ile pinz array'ini yakala
                match = re.search(r'var pinz = (\[.*?\]);', script_text, re.DOTALL)
                if match:
                    pinz_json = match.group(1)
                    try:
                        pinz_data = json.loads(pinz_json)
                        
                        # Her bir pin objesi için veri çıkar
                        for pin in pinz_data:
                            if isinstance(pin, dict):
                                harita_veri = {
                                    'lat': pin.get('lat', 'N/A'),
                                    'lon': pin.get('lon', 'N/A'),
                                    'label': pin.get('lable', 'N/A'),  # 'lable' yazım hatası olabilir
                                    'title': pin.get('title', 'N/A')
                                }
                                harita_verileri.append(harita_veri)
                    except json.JSONDecodeError as e:
                        print(f"JSON ayrıştırma hatası: {e}")
                        continue
                break
                    
    except Exception as e:
        print(f"Harita verileri çekilirken hata oluştu: {e}")
    
    return harita_verileri


def main():
    """
    Ana fonksiyon - tüm veri çekme işlemlerini yürütür.
    """
    url = 'https://www.local-rank.report/scan/97919fde-e478-4081-983f-7e0065b6b5bb'
    
    print("Web scraping başlatılıyor...")
    print(f"Hedef URL: {url}")
    
    # HTML içeriğini al
    soup = get_html_content(url)
    if not soup:
        print("HTML içeriği alınamadı. İşlem sonlandırılıyor.")
        return
    
    print("HTML içeriği başarıyla alındı. Veri çekme işlemleri başlatılıyor...")
    
    # Tüm veri çekme fonksiyonlarını çalıştır
    results = {}
    
    print("1. Özet bilgiler çekiliyor...")
    results['ozet_bilgiler'] = scrape_ozet_bilgiler(soup)
    
    print("2. Rakip bilgileri çekiliyor...")
    results['rakipler'] = scrape_rakipler(soup)
    
    print("3. Sponsorlu liste bilgileri çekiliyor...")
    results['sponsorlu_listeler'] = scrape_sponsorlu_listeler(soup)
    
    print("4. Detaylı sonuç bilgileri çekiliyor...")
    results['detayli_sonuclar'] = scrape_detayli_sonuclar(soup)
    
    print("5. Harita verileri çekiliyor...")
    results['harita_verileri'] = scrape_harita_verileri(soup)
    
    # Sonuçları JSON dosyasına kaydet
    try:
        with open('scraped_data.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("Veriler 'scraped_data.json' dosyasına kaydedildi.")
    except Exception as e:
        print(f"Veriler kaydedilirken hata oluştu: {e}")
    
    # Özet istatistikler
    print("\n=== ÖZET İSTATİSTİKLER ===")
    print(f"Özet bilgiler: {len(results['ozet_bilgiler'])} alan")
    print(f"Rakip sayısı: {len(results['rakipler'])}")
    print(f"Sponsorlu liste sayısı: {len(results['sponsorlu_listeler'])}")
    print(f"Detaylı sonuç sayısı: {len(results['detayli_sonuclar'])}")
    print(f"Harita veri sayısı: {len(results['harita_verileri'])}")
    
    return results


if __name__ == "__main__":
    main()