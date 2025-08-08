#!/usr/bin/env python3
"""
JavaScript Extractor Module
JavaScript verilerini çıkarma işlemleri için yardımcı modül
"""

import re
import json
import ast
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


class JSExtractor:
    """JavaScript veri çıkarma işlemleri için sınıf"""
    
    def __init__(self):
        """JSExtractor sınıfını başlatır."""
        pass
    
    def _safe_json_loads(self, text: str) -> List[Any]:
        """
        JSON'ı güvenli bir şekilde parse eder.
        
        Args:
            text: Parse edilecek JSON string
            
        Returns:
            Parse edilmiş veri
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                # JavaScript boolean / null değerlerini Python eşdeğerleriyle değiştir
                text = re.sub(r"\btrue\b", "True", text, flags=re.I)
                text = re.sub(r"\bfalse\b", "False", text, flags=re.I)
                text = re.sub(r"\bnull\b", "None", text, flags=re.I)
                return ast.literal_eval(text)
            except Exception:
                return []
    
    def _extract_cid_from_url(self, url: Optional[str]) -> str:
        """Verilen Google Maps URL içinden CID değerini çıkarır."""
        if not url:
            return "N/A"
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            for key in ("cid", "ludocid"):
                if key in qs and qs[key]:
                    return qs[key][0]
            if parsed.fragment and "cid=" in parsed.fragment:
                frag_qs = parse_qs(parsed.fragment)
                if "cid" in frag_qs and frag_qs["cid"]:
                    return frag_qs["cid"][0]
            m = re.search(r"[?&#]cid=([0-9]+)", url)
            if m:
                return m.group(1)
        except Exception:
            pass
        return "N/A"

    def _page_text(self, soup: BeautifulSoup) -> str:
        """Sayfanın tüm metnini döndürür (script içerikleri dahil)."""
        try:
            return str(soup)
        except Exception:
            return ""
    
    def extract_pinz_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        var pinz array'ini çıkarır.
        
        Args:
            soup: BeautifulSoup objesi
            
        Returns:
            pinz array verisi
        """
        pinz_data: List[Dict[str, Any]] = []
        
        try:
            # 1) Script tag'ları içinde ara (string veya get_text ile)
            for script in soup.find_all("script"):
                script_text = (script.string or "") or script.get_text() or ""
                if "pinz" not in script_text:
                    continue
                # Doğrudan dizi ataması: var|let|const pinz = [...];
                match = re.search(r"(?:var|let|const)\s+pinz\s*=\s*(\[[\s\S]*?\]);", script_text)
                if match:
                    raw_json = match.group(1)
                    arr = self._safe_json_loads(raw_json)
                    if arr:
                        pinz_data = arr
                        break
                # JSON.parse fallback: pinz = JSON.parse('...')
                match2 = re.search(r"pinz\s*=\s*JSON\.parse\(\s*(['\"])(.*?)\1\s*\)\s*;", script_text)
                if not pinz_data and match2:
                    raw_str = match2.group(2)
                    try:
                        arr = json.loads(raw_str)
                        if arr:
                            pinz_data = arr
                            break
                    except Exception:
                        pass
            # 2) Tüm sayfa metninde ara
            if not pinz_data:
                page_txt = self._page_text(soup)
                match = re.search(r"(?:var|let|const)\s+pinz\s*=\s*(\[[\s\S]*?\]);", page_txt)
                if match:
                    raw_json = match.group(1)
                    pinz_data = self._safe_json_loads(raw_json)
                else:
                    match2 = re.search(r"pinz\s*=\s*JSON\.parse\(\s*(['\"])(.*?)\1\s*\)\s*;", page_txt)
                    if match2:
                        raw_str = match2.group(2)
                        try:
                            pinz_data = json.loads(raw_str)
                        except Exception:
                            pinz_data = []
                # 3) push kalıpları: pinz.push({...}); biriktir
                if not pinz_data:
                    objs = re.findall(r"pinz\.push\(\s*(\{[\s\S]*?\})\s*\)\s*;", page_txt)
                    collected: List[Dict[str, Any]] = []
                    for o in objs:
                        try:
                            parsed = self._safe_json_loads(o)
                            if isinstance(parsed, dict):
                                collected.append(parsed)
                        except Exception:
                            continue
                    if collected:
                        pinz_data = collected
        
        except Exception as e:
            print(f"pinz veri çıkarma hatası: {e}")
        
        # pinz dizisinde beklenen anahtarları normalize et
        normalized: List[Dict[str, Any]] = []
        for obj in pinz_data:
            if isinstance(obj, dict):
                normalized.append(obj)
        return normalized
    
    def extract_scan_guid(self, soup: BeautifulSoup) -> str:
        """
        scan_guid parametresini çıkarır.
        
        Args:
            soup: BeautifulSoup objesi
            
        Returns:
            scan_guid değeri
        """
        scan_guid = ""
        
        try:
            # Scriptlerde doğrudan atama
            for script in soup.find_all("script"):
                script_text = (script.string or "") or script.get_text() or ""
                scan_match = re.search(r"scan_guid['\"]?\s*[:=]\s*['\"]([0-9a-fA-F-]{36})['\"]", script_text)
                if scan_match:
                    scan_guid = scan_match.group(1)
                    break
            # Sayfa genelinde endpoint içinde (fallback)
            if not scan_guid:
                page_txt = self._page_text(soup)
                m2 = re.search(r"/scans/get-competitors-list\?scan_guid=([0-9a-fA-F-]{36})", page_txt)
                if m2:
                    scan_guid = m2.group(1)
                else:
                    m3 = re.search(r"/scans/compare\?scan=([0-9a-fA-F-]{36})", page_txt)
                    if m3:
                        scan_guid = m3.group(1)
                    
        except Exception as e:
            print(f"scan_guid çıkarma hatası: {e}")
        
        return scan_guid
    
    def extract_place_id(self, soup: BeautifulSoup) -> str:
        """
        place_id parametresini çıkarır.
        
        Args:
            soup: BeautifulSoup objesi
            
        Returns:
            place_id değeri
        """
        place_id = ""
        
        try:
            # Scriptlerde atama
            for script in soup.find_all("script"):
                script_text = (script.string or "") or script.get_text() or ""
                place_match = re.search(r"place_id['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]", script_text)
                if place_match:
                    place_id = place_match.group(1)
                    break
            # Analytics URL'lerinden pid parametresi (fallback)
            if not place_id:
                page_txt = self._page_text(soup)
                m2 = re.search(r"/analytics/GetResults\?[^\n\r\"']*\bpid=([^&\"'\s]+)", page_txt)
                if m2:
                    place_id = m2.group(1)
                else:
                    # compare endpoint'inden biz1/biz2 pid olabilir
                    m3 = re.search(r"/scans/compare\?[^\n\r\"']*\bbiz1=([^&\"'\s]+)", page_txt)
                    if m3:
                        place_id = m3.group(1)
                    else:
                        m4 = re.search(r"/scans/compare\?[^\n\r\"']*\bbiz2=([^&\"'\s]+)", page_txt)
                        if m4:
                            place_id = m4.group(1)
        
        except Exception as e:
            print(f"place_id çıkarma hatası: {e}")
        
        return place_id
    
    def extract_all_js_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Tüm JavaScript verilerini çıkarır.
        
        Args:
            soup: BeautifulSoup objesi
            
        Returns:
            Tüm JavaScript verileri
        """
        js_data: Dict[str, Any] = {}
        
        try:
            # pinz array'ini çıkar
            js_data["pinz"] = self.extract_pinz_data(soup)
            
            # scan_guid çıkar
            js_data["scan_guid"] = self.extract_scan_guid(soup)
            
            # place_id çıkar
            js_data["place_id"] = self.extract_place_id(soup)
            
        except Exception as e:
            print(f"JavaScript veri çıkarma hatası: {e}")
        
        return js_data
    
    def extract_map_data(self, js_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Harita verilerini JavaScript verilerinden çıkarır.
        
        Args:
            js_data: JavaScript verileri
            
        Returns:
            Harita verileri listesi
        """
        pins: List[Dict[str, Any]] = []
        
        try:
            if "pinz" in js_data:
                for obj in js_data["pinz"]:
                    if isinstance(obj, dict):
                        maps_url = obj.get("url")
                        cid_value = self._extract_cid_from_url(maps_url)
                        pins.append({
                            "lat": obj.get("location", {}).get("lat") or obj.get("lat"),
                            "lon": obj.get("location", {}).get("lon") or obj.get("lng") or obj.get("longitude"),
                            "label": obj.get("lable") or obj.get("label"),
                            "title": obj.get("title"),
                            "url": maps_url,
                            "color": obj.get("color"),
                            "cid": cid_value,
                        })
                        
        except Exception as e:
            print(f"Harita veri çıkarma hatası: {e}")
        
        return pins


