#!/usr/bin/env python3
"""
HTML Parser Module
HTML parsing işlemleri için yardımcı modül
"""

import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


class HTMLParser:
    """HTML parsing işlemleri için sınıf"""
    
    def __init__(self):
        """HTMLParser sınıfını başlatır."""
        pass
    
    def _get_text(self, elem, default: str = "N/A") -> str:
        """
        Güvenli bir şekilde element metnini çıkarır.
        
        Args:
            elem: BeautifulSoup elementi
            default: Varsayılan değer
            
        Returns:
            Çıkarılan metin veya varsayılan değer
        """
        try:
            if elem is None:
                return default
            return elem.get_text(strip=True)
        except Exception:
            return default
    
    def _extract_rating_and_reviews(self, container) -> Dict[str, str]:
        """Yıldız puanı ve yorum sayısını çıkarır.
        
        Bu fonksiyon, aynı satır/panel içerisinde bulunan
        `div.rating-container` ve onu takip eden `span` içinden
        puan (yıldız) ve yorum sayısını ayrıştırır.
        """
        rating_value: Optional[str] = None
        reviews_count: Optional[str] = None

        try:
            # 1) Puan: rating-stars title="4.9 out of 5" üzerinden
            rating_stars = container.select_one("div.rating-container div.rating-stars")
            if rating_stars:
                title_text = rating_stars.get("title", "")
                m = re.search(r"([0-9]+(?:[\.,][0-9]+)?)\s*out\s*of\s*5", title_text, re.I)
                if m:
                    rating_value = m.group(1).replace(",", ".")
            # 2) Alternatif: style width: 98% -> 4.9
            if rating_value is None and rating_stars and rating_stars.has_attr("style"):
                m2 = re.search(r"width:\s*([0-9]+)%", rating_stars["style"])  # type: ignore[index]
                if m2:
                    pct = int(m2.group(1))
                    rating_value = f"{round(pct * 5 / 100, 1)}"

            # 3) Yorum sayısı: rating-container + span -> "(35)" veya "(35 Reviews)"
            reviews_span = container.select_one("div.rating-container + span")
            if reviews_span:
                text = self._get_text(reviews_span, default="")
                m3 = re.search(r"\(?\s*([0-9]+)\s*(?:Reviews?|Yorum(?:lar)?|Değerlendirme)?\s*\)?", text, re.I)
                if m3:
                    reviews_count = m3.group(1)
        except Exception:
            pass

        # Normalleştir
        if rating_value is None:
            rating_value = "N/A"
        if reviews_count is None:
            reviews_count = "0"

        combined = rating_value if rating_value != "N/A" else ""
        if reviews_count and reviews_count != "0":
            combined = f"{combined} ({reviews_count})".strip()
        if not combined:
            combined = "N/A"

        return {
            "Puan": rating_value,
            "Yorum Sayısı": reviews_count,
            "Puan/Yorum": combined,
        }
    
    def _extract_cid_from_url(self, url: Optional[str]) -> str:
        """Verilen Google Maps URL içinden CID değerini çıkarır.
        Çeşitli parametre adlarını (cid, ludocid) ve URL biçimlerini dener.
        """
        if not url:
            return "N/A"
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            # Yaygın parametre adları
            for key in ("cid", "ludocid"):
                if key in qs and qs[key]:
                    return qs[key][0]
            # Bazı linklerde cid parametresi path veya fragmente gömülü olabilir
            # Örn: .../maps?hl=tr&gl=tr#cid=1234567890
            if parsed.fragment and "cid=" in parsed.fragment:
                frag_qs = parse_qs(parsed.fragment)
                if "cid" in frag_qs and frag_qs["cid"]:
                    return frag_qs["cid"][0]
            # Son çare: doğrudan cid= desenini ara
            m = re.search(r"[?&#]cid=([0-9]+)", url)
            if m:
                return m.group(1)
        except Exception:
            pass
        return "N/A"
    
    def parse_scan_information(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Scan Information tablosunu parse eder.
        
        Args:
            soup: BeautifulSoup objesi
            
        Returns:
            Scan Information verileri
        """
        results = {}
        
        try:
            scan_header = soup.find("h4", string=re.compile(r"^\s*Scan Information\s*$", re.I))
            if scan_header:
                scan_table = scan_header.find_next("table")
                if scan_table:
                    results["İşletme Adı"] = self._get_text(scan_table.select_one("span.bizname"))
                    results["Adres"] = self._get_text(scan_table.select_one("span.center-block"))
                    # Yorum sayısı ve puanı birlikte al
                    rating_info = self._extract_rating_and_reviews(scan_table)
                    results.update({
                        "Puan": rating_info.get("Puan", "N/A"),
                        "Yorum Sayısı": rating_info.get("Yorum Sayısı", "0"),
                    })
                    
                    # Anahtar Kelime ve Dil
                    kw_td = scan_table.find("td", string=re.compile(r"Keyword", re.I))
                    kw_val_td = kw_td.find_next_sibling("td") if kw_td else None
                    results["Anahtar Kelime ve Dil"] = self._get_text(kw_val_td)
                    
                    # Tarih
                    date_td = scan_table.find("td", class_=re.compile(r"cnv_dt_lcl", re.I))
                    results["Tarih"] = self._get_text(date_td)
                    
        except Exception as e:
            print(f"Scan Information parse hatası: {e}")
        
        return results
    
    def parse_rank_summary(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Rank Summary tablosunu parse eder.
        
        Args:
            soup: BeautifulSoup objesi
            
        Returns:
        	    Rank Summary verileri
        """
        results = {}
        
        try:
            rank_header = soup.find("h4", string=re.compile(r"^\s*Rank Summary\s*$", re.I))
            if rank_header:
                rank_table = rank_header.find_next("table")
                if rank_table:
                    for tr in rank_table.select("tr"):
                        tds = tr.find_all("td")
                        if len(tds) >= 2:
                            key_cell = tds[0]
                            # Icon'ları kaldır
                            for icon in key_cell.find_all("icon"):
                                icon.decompose()
                            key = self._get_text(key_cell, default="")
                            
                            value_cell = tds[1]
                            value = self._get_text(value_cell)
                            
                            if key:
                                # Anahtar metni normalize et ve regex ile eşleştir (alt string çakışmalarını önlemek için)
                                key_norm = re.sub(r"\s+", " ", key).strip()
                                
                                # Önce 'Un Ranked Locations' kontrol et ("Ranked Locations" ile çakışmayı önlemek için)
                                if re.search(r"^Un\s*Ranked\s+Locations$", key_norm, re.I):
                                    results["Un Ranked Locations"] = value
                                elif re.search(r"^Ranked\s+Locations$", key_norm, re.I):
                                    spans = value_cell.find_all("span")
                                    if len(spans) >= 2:
                                        ranked = self._get_text(spans[0])
                                        total = self._get_text(spans[1])
                                        results["Ranked Locations"] = f"{ranked}/{total}"
                                    else:
                                        results["Ranked Locations"] = value
                                elif re.search(r"^Average\s+rank$", key_norm, re.I):
                                    span = key_cell.find("span")
                                    if span and span.get("title"):
                                        results["Average rank (Ranked Locations)"] = value
                                    else:
                                        results["Average rank"] = value
                                elif re.search(r"^Avg\s+total\s+rank$", key_norm, re.I):
                                    results["Avg total rank (All Locations)"] = value
                                elif re.search(r"^Best\s+rank$", key_norm, re.I):
                                    results["Best rank"] = value
                                elif re.search(r"^Max\s+Distance$", key_norm, re.I):
                                    results["Max Distance"] = value
                                else:
                                    results[key] = value
                                    
        except Exception as e:
            print(f"Rank Summary parse hatası: {e}")
        
        return results
    
    def parse_competitors(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Rakip bilgilerini parse eder.
        
        Args:
            soup: BeautifulSoup objesi
            
        Returns:
            Rakip bilgileri listesi
        """
        competitors = []
        
        try:
            rows = soup.select("table#tbl_comp_rank tbody tr")
            
            for row in rows:
                rating_info = self._extract_rating_and_reviews(row)
                name_link = row.select_one("a.ext[href]")
                name_text = self._get_text(name_link)
                maps_url = name_link.get("href") if name_link else None
                cid_value = self._extract_cid_from_url(maps_url)

                comp = {
                    "İsim": name_text,
                    "Puan": rating_info.get("Puan", "N/A"),
                    "Yorum Sayısı": rating_info.get("Yorum Sayısı", "0"),
                    "Puan/Yorum": rating_info.get("Puan/Yorum", "N/A"),
                    "Maps URL": maps_url or "N/A",
                    "CID": cid_value,
                }
                
                # Adres
                addr_span = None
                map_icon = row.select_one("i.fa-map-marker")
                if map_icon:
                    addr_span = map_icon.find_parent("span")
                comp["Adres"] = self._get_text(addr_span)
                
                # Kategoriler
                cat_p = row.find("p", string=re.compile(r"Categories:", re.I))
                comp["Kategoriler"] = self._get_text(cat_p)
                
                # Web Sitesi
                website_link = None
                globe_icon = row.select_one("i.fa-globe")
                if globe_icon:
                    parent_span = globe_icon.find_parent("span")
                    if parent_span:
                        a_tag = parent_span.find("a", href=True)
                        if a_tag:
                            website_link = a_tag["href"]
                comp["Web Sitesi"] = website_link or "N/A"
                
                # Fotoğraf Sayısı
                photo_span = None
                photo_icon = row.select_one("i.fa-photo")
                if photo_icon:
                    photo_span = photo_icon.find_parent("span")
                comp["Fotoğraf Sayısı"] = self._get_text(photo_span)
                
                # Sahiplenme Durumu
                claim_span = row.find("span", string=re.compile(r"(Claimed|Un\s*Claimed)", re.I))
                comp["Sahiplenme Durumu"] = self._get_text(claim_span)
                
                # Bulunduğu Konum Sayısı
                comp["Bulunduğu Konum Sayısı"] = self._get_text(row.select_one("td.text-center > h5"))
                
                # Ortalama Sıralama
                comp["Ortalama Sıralama"] = self._get_text(row.select_one("span.dotlg2"))
                
                competitors.append(comp)
                
        except Exception as e:
            print(f"Rakip bilgileri parse hatası: {e}")
        
        return competitors
    
    def parse_sponsorlu_listeler(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Sponsorlu liste bilgilerini parse eder.
        
        Args:
            soup: BeautifulSoup objesi
            
        Returns:
            Sponsorlu liste bilgileri
        """
        listings = []
        
        try:
            rows = soup.select("table#tbl_ads_rank tbody tr")
            
            for row in rows:
                tds = row.find_all("td")
                name_link = row.select_one("a.ext[href]")
                isim = self._get_text(name_link)
                rating_info = self._extract_rating_and_reviews(row)
                gorulme_sayisi = self._get_text(tds[-1] if tds else None)

                maps_url = name_link.get("href") if name_link else None
                cid_value = self._extract_cid_from_url(maps_url)
                
                listings.append({
                    "İsim": isim,
                    "Puan": rating_info.get("Puan", "N/A"),
                    "Yorum Sayısı": rating_info.get("Yorum Sayısı", "0"),
                    "Puan/Yorum": rating_info.get("Puan/Yorum", "N/A"),
                    "Görülme Sayısı": gorulme_sayisi,
                    "Maps URL": maps_url or "N/A",
                    "CID": cid_value,
                })
                
        except Exception as e:
            print(f"Sponsorlu liste parse hatası: {e}")
        
        return listings
    
    def parse_detayli_sonuclar(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Detaylı sonuç bilgilerini parse eder.
        
        Args:
            soup: BeautifulSoup objesi
            
        Returns:
            Detaylı sonuç bilgileri
        """
        detaylar = []
        
        try:
            container = soup.select_one("div#resultModal div.results_body")
            if not container:
                return detaylar
            
            panels = container.select("div.bg-light.panel-body")
            for panel in panels:
                rank = self._get_text(panel.select_one("span.dot"))
                name = self._get_text(panel.select_one("h5"))
                rating_info = self._extract_rating_and_reviews(panel)
                
                address_div = None
                rating_span = panel.select_one("div.rating-container + span")
                if rating_span:
                    address_div = rating_span.find_next("div")
                address = self._get_text(address_div)
                
                # Detay panelinde bazen isim linki yer alabilir
                name_link = panel.select_one("h5 a[href]")
                maps_url = name_link.get("href") if name_link else None
                cid_value = self._extract_cid_from_url(maps_url)
                
                detaylar.append({
                    "Sıra": rank,
                    "İsim": name,
                    "Puan": rating_info.get("Puan", "N/A"),
                    "Yorum Sayısı": rating_info.get("Yorum Sayısı", "0"),
                    "Puan/Yorum": rating_info.get("Puan/Yorum", "N/A"),
                    "Adres": address,
                    "Maps URL": maps_url or "N/A",
                    "CID": cid_value,
                })
                
        except Exception as e:
            print(f"Detaylı sonuçlar parse hatası: {e}")
        
        return detaylar


