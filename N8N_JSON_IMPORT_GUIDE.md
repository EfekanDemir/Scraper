# N8N JSON Dosyalarını İçe Aktarma Rehberi

Bu rehber, 2 farklı türdeki JSON dosyasını n8n'e nasıl içe aktaracağınızı açıklar.

## 📋 Dosya Türleri

Workspace'inizde 2 ana JSON dosya türü var:

### 1. **N8N Workflow Dosyaları** 
- `n8n_modular_scraper_workflow.json` (24KB)
- `n8n_modular_scraper_workflow_backup.json` (28KB)

### 2. **Scraping Veri Dosyaları**
- `modular_scraped_data_20250807_193801.json` (8.5KB)
- `modular_scraped_data_20250808_100814.json` (9.8KB)

---

## 🔄 1. N8N Workflow Dosyalarını İçe Aktarma

### Adım 1: N8N Arayüzüne Giriş
1. N8N web arayüzünüzü açın (genellikle `http://localhost:5678`)
2. Ana sayfada **"Import from File"** veya **"Workflows"** sekmesine gidin

### Adım 2: Workflow İçe Aktarma
```bash
# Dosyayı n8n'e yüklemek için:
1. "+" butonuna tıklayın (yeni workflow oluştur)
2. Sağ üst köşede "⋯" (3 nokta) menüsüne tıklayın
3. "Import from file" seçeneğini seçin
4. JSON dosyasını seçin: n8n_modular_scraper_workflow.json
```

### Adım 3: Workflow Aktifleştirme
- Workflow yüklendikten sonra **"Activate"** butonuna tıklayın
- Webhook URL'ini not alın (webhook node'unda görünür)

---

## 📊 2. Veri Dosyalarını N8N'de Kullanma

### Yöntem A: HTTP Request ile Dosya Okuma

```json
// Code node örneği - JSON dosyasını okuma
const fs = require('fs');
const path = require('path');

// JSON dosyasını oku
const jsonFile = '/workspace/modular_scraped_data_20250807_193801.json';
const data = JSON.parse(fs.readFileSync(jsonFile, 'utf8'));

return {
  json: data
};
```

### Yöntem B: Webhook ile Veri Gönderme

```bash
# JSON dosyasını webhook'a POST etme
curl -X POST \
  http://your-n8n-instance:5678/webhook/scraper-webhook \
  -H "Content-Type: application/json" \
  -d @modular_scraped_data_20250807_193801.json
```

### Yöntem C: Manual Trigger ile

1. **Manual Trigger** node ekleyin
2. **Code** node ekleyin ve şu kodu kullanın:

```javascript
// Veri dosyasını manual olarak yükle
const data = {
  "ozet_bilgiler": {
    "İşletme Adı": "Kanal-Immobilien GmbH",
    "Adres": "Torstraße 18",
    "Yorum Sayısı": "(35 Reviews)",
    // ... diğer veriler
  },
  "rakipler": [
    // rakip verileri
  ]
};

return {
  json: data
};
```

---

## 🛠️ 3. Pratik Örnekler

### Örnek 1: JSON Dosyasını İşleme
```javascript
// Code node - JSON verisini işleme
const inputData = $input.all();

// Özet bilgileri çıkar
const ozetBilgiler = inputData[0].json.ozet_bilgiler;

// Rakip sayısını hesapla
const rakipSayisi = inputData[0].json.rakipler.length;

return {
  json: {
    isletme_adi: ozetBilgiler["İşletme Adı"],
    adres: ozetBilgiler["Adres"],
    rakip_sayisi: rakipSayisi,
    tarih: ozetBilgiler["Tarih"]
  }
};
```

### Örnek 2: Verileri Filtreleme
```javascript
// Sadece belirli puanın üzerindeki rakipleri al
const rakipler = $json.rakipler;
const yuksekPuanliRakipler = rakipler.filter(rakip => {
  const puan = parseInt(rakip["Puan/Yorum"].replace(/[()]/g, ''));
  return puan > 50;
});

return {
  json: yuksekPuanliRakipler
};
```

---

## 🚀 4. Otomatik İçe Aktarma Script'i

Dosyaları otomatik olarak n8n'e yüklemek için:

```bash
#!/bin/bash
# n8n_import.sh

# Workflow dosyalarını import et
echo "Workflow dosyaları import ediliyor..."

# JSON dosyalarını n8n data klasörüne kopyala
cp n8n_modular_scraper_workflow.json ~/.n8n/workflows/
cp n8n_modular_scraper_workflow_backup.json ~/.n8n/workflows/

echo "İşlem tamamlandı!"
```

---

## ⚠️ Önemli Notlar

1. **Dosya Boyutu**: Büyük JSON dosyaları için n8n'in memory limitlerini kontrol edin
2. **Encoding**: JSON dosyalarının UTF-8 encoding'de olduğundan emin olun
3. **Webhook URL**: Workflow import ettikten sonra webhook URL'lerini güncelleyin
4. **Credentials**: API anahtarları gibi hassas bilgileri n8n Credentials'da saklayın

---

## 🔧 Sorun Giderme

### Import Hatası Alıyorsanız:
```bash
# JSON syntax'ını kontrol edin
cat n8n_modular_scraper_workflow.json | jq '.'

# Dosya izinlerini kontrol edin
ls -la *.json
```

### Veri Formatı Hataları:
- JSON'un valid olduğundan emin olun
- Türkçe karakterlerde encoding problemi olabilir
- Büyük dosyalar için pagination kullanın

---

## 📞 Özet

✅ **Workflow Import**: N8N arayüzünden "Import from file" ile  
✅ **Veri Import**: Code node, webhook veya manual trigger ile  
✅ **Otomatik Process**: Script'ler ile batch import  

**Hangi dosyaları import etmek istiyorsunuz?**
- Workflow dosyaları → N8N arayüzünden import
- Veri dosyaları → Workflow içinde işleyin