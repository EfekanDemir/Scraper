#!/usr/bin/env python3
"""
JavaScript Extractor Module
JavaScript verilerini çıkarma işlemleri için yardımcı modül
"""

import re
import json
import ast
from typing import Dict, Any, List
from bs4 import BeautifulSoup


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
    
    def extract_pinz_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        var pinz array'ini çıkarır.
        
        Args:
            soup: BeautifulSoup objesi
            
        Returns:
            pinz array verisi
        """
        pinz_data = []
        
        try:
            for script in soup.find_all("script"):
                script_text = script.string or ""
                if "var pinz" in script_text:
                    match = re.search(r"var\s+pinz\s*=\s*(\[.*?\]);", script_text, re.DOTALL)
                    if match:
                        raw_json = match.group(1)
                        pinz_data = self._safe_json_loads(raw_json)
                        break
                        
        except Exception as e:
            print(f"pinz veri çıkarma hatası: {e}")
        
        return pinz_data
    
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
            for script in soup.find_all("script"):
                script_text = script.string or ""
                scan_match = re.search(r"scan_guid['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]", script_text)
                if scan_match:
                    scan_guid = scan_match.group(1)
                    break
                    
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
            for script in soup.find_all("script"):
                script_text = script.string or ""
                place_match = re.search(r"place_id['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]", script_text)
                if place_match:
                    place_id = place_match.group(1)
                    break
                    
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
        js_data = {}
        
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
        pins = []
        
        try:
            if "pinz" in js_data:
                for obj in js_data["pinz"]:
                    if isinstance(obj, dict):
                        pins.append({
                            "lat": obj.get("location", {}).get("lat") or obj.get("lat"),
                            "lon": obj.get("location", {}).get("lon") or obj.get("lng") or obj.get("longitude"),
                            "label": obj.get("lable") or obj.get("label"),
                            "title": obj.get("title"),
                            "url": obj.get("url"),
                            "color": obj.get("color"),
                        })
                        
        except Exception as e:
            print(f"Harita veri çıkarma hatası: {e}")
        
        return pins


