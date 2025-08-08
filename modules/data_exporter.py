#!/usr/bin/env python3
"""
Data Exporter Module
Veri dışa aktarma işlemleri için yardımcı modül
"""

import json
import os
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    # Supabase Python SDK
    from supabase import create_client, Client
except Exception:
    create_client = None
    Client = None


class DataExporter:
    """Veri dışa aktarma işlemleri için sınıf"""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """DataExporter sınıfını başlatır ve Supabase istemcisini hazırlar.
        
        Args:
            supabase_url: Supabase proje URL'si (örn: https://<ref>.supabase.co)
            supabase_key: Supabase anon/public API anahtarı
        """
        self.supabase: Optional[Client] = None
        # Önce parametre, sonra env'den al
        resolved_url = supabase_url or os.getenv("SUPABASE_URL")
        resolved_key = supabase_key or os.getenv("SUPABASE_ANON_KEY")
        # create_client kullanılabilir ve kimlikler mevcutsa başlat
        if create_client and resolved_url and resolved_key:
            try:
                self.supabase = create_client(resolved_url, resolved_key)
            except Exception as exc:
                print(f"Supabase istemcisi oluşturulamadı: {exc}")
                self.supabase = None
        else:
            if not create_client:
                print("Supabase kütüphanesi yüklü değil. requirements.txt dosyasına 'supabase>=2.4.0' ekleyin ve kurun.")
            if not (resolved_url and resolved_key):
                print("SUPABASE_URL ve/veya SUPABASE_ANON_KEY eksik. Ortam değişkeni olarak ayarlayın veya kurucuya parametre geçin.")
    
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
    
    def save_to_supabase(self, data: Dict[str, Any]) -> bool:
        """Verileri dosya oluşturmadan doğrudan Supabase tablolarına yazar.
        
        Varsayılan olarak aşağıdaki anahtarlar aynı isimli tablolara yazılır:
        - ozet_bilgiler, rakipler, sponsorlu_listeler, detayli_sonuclar,
          harita_verileri, javascript_verileri, api_verileri
        
        Not: Tabloların Supabase Postgres tarafında önceden oluşturulmuş olması gerekir.
        Önerilen minimum sütunlar: id (uuid default), scraped_at (timestamptz), url (text), payload (jsonb)
        Veya alan-alan eşleşecek kolonlar.
        """
        if not self.supabase:
            print("Supabase istemcisi hazır değil. Lütfen kimlik bilgilerini sağlayın ve supabase paketini kurun.")
            return False
        
        metadata = data.get("metadata", {}) or {}
        scraped_at = metadata.get("scraped_at") or datetime.utcnow().isoformat()
        source_url = metadata.get("url") or None
        
        def to_rows(value: Any) -> List[Dict[str, Any]]:
            if isinstance(value, list):
                rows: List[Dict[str, Any]] = []
                for it in value:
                    if isinstance(it, dict):
                        rows.append(it)
                    else:
                        rows.append({"value": it})
                return rows
            elif isinstance(value, dict):
                return [value]
            else:
                return [{"value": value}]
        
        def add_meta(row: Dict[str, Any]) -> Dict[str, Any]:
            # Eğer tabloda birebir kolonlar tanımlı değilse, 'payload' sütunu kullanılabilir.
            # Burada iki yaklaşımı aynı anda destekliyoruz: birebir kolon eşleşmesi + payload jsonb
            enriched = dict(row)
            enriched.setdefault("scraped_at", scraped_at)
            if source_url:
                enriched.setdefault("url", source_url)
            # payload alanı yoksa ham satırı payload olarak da geçelim (şema esnekliği için)
            if "payload" not in enriched:
                try:
                    enriched_payload = row if isinstance(row, dict) else {"value": row}
                    enriched["payload"] = enriched_payload
                except Exception:
                    pass
            return enriched
        
        tables = [
            "ozet_bilgiler",
            "rakipler",
            "sponsorlu_listeler",
            "detayli_sonuclar",
            "harita_verileri",
            "javascript_verileri",
            "api_verileri",
        ]
        
        overall_success = True
        for key, value in data.items():
            if key == "metadata":
                continue
            if key not in tables:
                # Yine de yazmayı dene; kullanıcı farklı bir tablo kurmuş olabilir
                pass
            try:
                rows = [add_meta(r) for r in to_rows(value)]
                if not rows:
                    continue
                # Büyük listeleri parçala
                chunk_size = 500
                for i in range(0, len(rows), chunk_size):
                    chunk = rows[i:i+chunk_size]
                    self.supabase.table(key).insert(chunk).execute()
                print(f"Supabase tablosuna yazıldı: {key} ({len(rows)} satır)")
            except Exception as exc:
                overall_success = False
                error_msg = str(exc)
                
                # RLS ve yetki hatalarını daha açık hale getir
                if "42501" in error_msg:
                    print(f"❌ Supabase yazma hatası [{key}]: YETKİ SORUNU (42501)")
                    print(f"   Çözüm önerileri:")
                    print(f"   1. '{key}' tablosunun RLS politikalarını kontrol edin")
                    print(f"   2. Tablo mevcut değilse schema.sql'i çalıştırın")
                    print(f"   3. Geliştirme için Service Key kullanmayı deneyin")
                elif "42P01" in error_msg:
                    print(f"❌ Supabase yazma hatası [{key}]: TABLO MEVCUT DEĞİL (42P01)")
                    print(f"   Çözüm: schema.sql dosyasını Supabase SQL Editor'da çalıştırın")
                elif "23505" in error_msg:
                    print(f"⚠️  Supabase yazma hatası [{key}]: DUPLICATE KEY - Bazı kayıtlar zaten mevcut")
                else:
                    print(f"❌ Supabase yazma hatası [{key}]: {exc}")
                print(f"   Tam hata mesajı: {error_msg}")
        return overall_success
    
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
        Verileri Supabase'e dışa aktarır (dosya oluşturulmaz).
        
        Args:
            data: Kaydedilecek veri
            base_filename: (artık kullanılmıyor) Eski dosya adı uyumluluğu için tutuldu
            
        Returns:
            İşlem sonuçları
        """
        results = {}
        
        # Sadece Supabase'e gönder
        results["supabase"] = self.save_to_supabase(data)
        
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


