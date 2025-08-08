#!/usr/bin/env python3
"""
Data Exporter Module
Veri dışa aktarma işlemleri için yardımcı modül
"""

import json
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime


class DataExporter:
    """Veri dışa aktarma işlemleri için sınıf"""
    
    def __init__(self):
        """DataExporter sınıfını başlatır."""
        pass
    
    def save_to_json(self, data: Dict[str, Any], filename: str = "scraped_data.json") -> bool:
        """
        Verileri JSON dosyasına kaydeder.
        
        Args:
            data: Kaydedilecek veri
            filename: Dosya adı
            
        Returns:
            Başarı durumu
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Veriler '{filename}' dosyasına kaydedildi")
            return True
        except Exception as e:
            print(f"JSON kaydetme hatası: {e}")
            return False
    
    def save_to_excel(self, data: Dict[str, Any], filename: str = "scraped_data.xlsx") -> bool:
        """
        Verileri Excel dosyasına kaydeder.
        
        Args:
            data: Kaydedilecek veri
            filename: Dosya adı
            
        Returns:
            Başarı durumu
        """
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                
                # Her veri türü için ayrı sayfa
                for key, value in data.items():
                    if key == "metadata":
                        continue
                    
                    if isinstance(value, dict):
                        df = pd.DataFrame([value])
                    elif isinstance(value, list):
                        df = pd.DataFrame(value)
                    else:
                        continue
                    
                    # Sayfa adını 31 karakterle sınırla
                    sheet_name = key[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Sütun genişliklerini ayarla
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            print(f"Veriler '{filename}' dosyasına kaydedildi")
            return True
            
        except Exception as e:
            print(f"Excel kaydetme hatası: {e}")
            return False
    
    def save_to_csv(self, data: Dict[str, Any], base_filename: str = "scraped_data") -> bool:
        """
        Verileri CSV dosyalarına kaydeder.
        
        Args:
            data: Kaydedilecek veri
            base_filename: Temel dosya adı
            
        Returns:
            Başarı durumu
        """
        try:
            success_count = 0
            
            for key, value in data.items():
                if key == "metadata":
                    continue
                
                if isinstance(value, dict):
                    df = pd.DataFrame([value])
                elif isinstance(value, list):
                    df = pd.DataFrame(value)
                else:
                    continue
                
                # CSV dosya adı oluştur
                csv_filename = f"{base_filename}_{key}.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"'{key}' verisi '{csv_filename}' dosyasına kaydedildi")
                success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            print(f"CSV kaydetme hatası: {e}")
            return False
    
    def print_summary(self, data: Dict[str, Any]) -> None:
        """
        Çekilen verilerin özetini yazdırır.
        
        Args:
            data: Çekilen veriler
        """
        print("\n" + "=" * 60)
        print("VERİ ÇEKME ÖZET İSTATİSTİKLERİ")
        print("=" * 60)
        print(f"Özet bilgiler: {len(data.get('ozet_bilgiler', {}))} alan")
        print(f"Rakip sayısı: {len(data.get('rakipler', []))}")
        print(f"Sponsorlu liste sayısı: {len(data.get('sponsorlu_listeler', []))}")
        print(f"Detaylı sonuç sayısı: {len(data.get('detayli_sonuclar', []))}")
        print(f"Harita veri sayısı: {len(data.get('harita_verileri', []))}")
        print(f"JavaScript veri alanları: {len(data.get('javascript_verileri', {}))}")
        print(f"API veri alanları: {len(data.get('api_verileri', {}))}")
        
        if data.get('metadata'):
            print(f"Çekilme tarihi: {data['metadata'].get('scraped_at', 'N/A')}")
            print(f"Kullanılan yöntem: {data['metadata'].get('method', 'N/A')}")
            print(f"Selenium kullanıldı: {data['metadata'].get('selenium_used', 'N/A')}")
        print("=" * 60)
    
    def export_all_formats(self, data: Dict[str, Any], base_filename: str = "scraped_data") -> Dict[str, bool]:
        """
        Verileri tüm formatlarda dışa aktarır.
        
        Args:
            data: Kaydedilecek veri
            base_filename: Temel dosya adı
            
        Returns:
            Her format için başarı durumu
        """
        results = {}
        
        # JSON
        json_filename = f"{base_filename}.json"
        results["json"] = self.save_to_json(data, json_filename)
        
        # Excel
        excel_filename = f"{base_filename}.xlsx"
        results["excel"] = self.save_to_excel(data, excel_filename)
        
        # CSV
        results["csv"] = self.save_to_csv(data, base_filename)
        
        return results
    
    def create_timestamped_filename(self, base_name: str, extension: str = "") -> str:
        """
        Zaman damgalı dosya adı oluşturur.
        
        Args:
            base_name: Temel dosya adı
            extension: Dosya uzantısı
            
        Returns:
            Zaman damgalı dosya adı
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if extension:
            return f"{base_name}_{timestamp}.{extension}"
        else:
            return f"{base_name}_{timestamp}"

