#!/usr/bin/env python3
"""
HTML Parser Module
HTML parsing işlemleri için yardımcı modül
"""

import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup


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
                    results["Yorum Sayısı"] = self._get_text(scan_table.select_one("div.rating-container + span"))
                    
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
                                if "Ranked Locations" in key:
                                    spans = value_cell.find_all("span")
                                    if len(spans) >= 2:
                                        ranked = self._get_text(spans[0])
                                        total = self._get_text(spans[1])
                                        results["Ranked Locations"] = f"{ranked}/{total}"
                                    else:
                                        results["Ranked Locations"] = value
                                elif "Un Ranked Locations" in key:
                                    results["Un Ranked Locations"] = value
                                elif "Average rank" in key:
                                    span = key_cell.find("span")
                                    if span and span.get("title"):
                                        results["Average rank (Ranked Locations)"] = value
                                    else:
                                        results["Average rank"] = value
                                elif "Avg total rank" in key:
                                    results["Avg total rank (All Locations)"] = value
                                elif "Best rank" in key:
                                    results["Best rank"] = value
                                elif "Max Distance" in key:
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
                comp = {
                    "İsim": self._get_text(row.select_one("a.ext")),
                    "Puan/Yorum": self._get_text(row.select_one("div.rating-container + span")),
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
                isim = self._get_text(row.select_one("a.ext"))
                rating = self._get_text(row.select_one("div.rating-container + span"))
                gorulme_sayisi = self._get_text(tds[-1] if tds else None)
                
                listings.append({
                    "İsim": isim,
                    "Puan/Yorum": rating,
                    "Görülme Sayısı": gorulme_sayisi,
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
                rating_span = panel.select_one("div.rating-container + span")
                rating = self._get_text(rating_span)
                
                address_div = rating_span.find_next("div") if rating_span else None
                address = self._get_text(address_div)
                
                detaylar.append({
                    "Sıra": rank,
                    "İsim": name,
                    "Puan/Yorum": rating,
                    "Adres": address,
                })
                
        except Exception as e:
            print(f"Detaylı sonuçlar parse hatası: {e}")
        
        return detaylar
