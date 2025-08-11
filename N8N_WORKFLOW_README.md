# 🤖 **N8N MODÜLER WEB SCRAPER WORKFLOW**

## 📋 **Genel Bakış**

Bu n8n workflow dosyası, Python modüler web scraper projenizin tüm işlevselliğini n8n platformunda yeniden oluşturur. Local Rank Report sitesinden verileri otomatik olarak çeker ve çoklu formatlarda (JSON, Excel, CSV) dışa aktarır.

## 🎯 **Workflow Özellikleri**

### **✅ Python Modülleri → n8n Node'ları Eşleştirmesi:**

| Python Modülü | n8n Node'u | Açıklama |
|---------------|------------|----------|
| `web_client.py` | HTTP Request | HTML içeriğini alır |
| `js_extractor.py` | Function Node | JavaScript verilerini çıkarır |
| `html_parser.py` | HTML Extract + Function | HTML parsing işlemleri |
| `api_client.py` | HTTP Request (API) | API çağrıları yapar |
| `data_exporter.py` | Convert to File + Write Binary | Veri dışa aktarma |

### **🔄 İş Akışı (Workflow) Adımları:**

1. **Start** → Workflow'u başlatır
2. **HTTP Request - Get HTML** → Hedef URL'den HTML içeriğini alır
3. **Function - Extract JS Data** → JavaScript verilerini (pinz, scan_guid, place_id) çıkarır
4. **HTML Extract Nodes** → Scan info, competitors, sponsored listings çıkarır
5. **Function Nodes** → Çıkarılan HTML'i parse eder
6. **HTTP Request - API** → API endpoint'lerini çağırır
7. **Merge - All Data** → Tüm verileri birleştirir
8. **Function - Combine All Data** → Final veri yapısını oluşturur
9. **Export Nodes** → JSON, Excel, CSV formatlarında dışa aktarır

## 📥 **Kurulum ve Kullanım**

### **Adım 1: n8n Kurulumu**

```bash
# Docker ile n8n kurulumu
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n

# veya npm ile
npm install n8n -g
n8n start
```

### **Adım 2: Workflow Import**

1. n8n arayüzünde **"Import from File"** seçeneğini tıklayın
2. `n8n_modular_scraper_workflow.json` dosyasını seçin
3. **"Import"** butonuna tıklayın

### **Adım 3: Workflow Aktivasyonu**

1. Import edilen workflow'u açın
2. Sağ üst köşedeki **"Active"** switch'ini açın
3. **"Execute Workflow"** butonuna tıklayın

## ⚙️ **Konfigürasyon**

### **URL Değiştirme:**
Farklı bir Local Rank Report URL'i için:

```javascript
// "HTTP Request - Get HTML" node'unda URL'yi değiştirin
"url": "https://www.local-rank.report/scan/YOUR_SCAN_ID"
```

### **Rate Limiting Ayarı:**
```javascript
// "Function - Rate Limiting" node'unda
const rateLimit = 2000; // 2 saniye bekleme
```

### **Timeout Ayarları:**
```javascript
// HTTP Request node'larında
"options": {
  "timeout": 60000 // 60 saniye
}
```

## 📊 **Çıktı Formatları**

### **1. JSON Çıktısı:**
```json
{
  "ozet_bilgiler": {
    "İşletme Adı": "...",
    "Adres": "...",
    "Puan": "...",
    "Yorum Sayısı": "..."
  },
  "rakipler": [...],
  "sponsorlu_listeler": [...],
  "harita_verileri": [...],
  "metadata": {
    "scraped_at": "2025-01-08T10:00:00.000Z",
    "method": "n8n_modular_hybrid"
  }
}
```

### **2. Excel Çıktısı:**
- Çok sayfalı Excel dosyası
- Her veri türü için ayrı sayfa
- Otomatik formatlanmış tablolar

### **3. CSV Çıktıları:**
- `rakipler_YYYYMMDD_HHmmss.csv`
- Her veri türü için ayrı CSV dosyası

## 🔧 **Node Detayları**

### **HTTP Request Nodes:**
```javascript
// Headers konfigürasyonu
"headerParameters": {
  "parameters": [
    {
      "name": "User-Agent",
      "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
  ]
}
```

### **Function Nodes:**
Her Function node, orijinal Python modüllerinin işlevselliğini JavaScript'te implement eder:

- **Extract JS Data:** `js_extractor.py` mantığı
- **Parse Summary Info:** `html_parser.py` scan information
- **Parse Competitors:** `html_parser.py` competitors parsing
- **Parse Sponsored:** `html_parser.py` sponsored listings
- **Combine All Data:** `data_exporter.py` veri birleştirme

### **HTML Extract Nodes:**
CSS seçicileri kullanarak HTML'den veri çıkarır:

```javascript
"rules": {
  "rules": [
    {
      "extractor": "css",
      "cssSelector": ".competitor-row",
      "returnArray": true,
      "attribute": "outerHTML"
    }
  ]
}
```

## 🚀 **Gelişmiş Özellikler**

### **1. Paralel İşleme:**
Workflow, birden fazla veri kaynağını paralel olarak işler.

### **2. Hata Yönetimi:**
Her node'da try-catch bloklarıyla hata yönetimi yapılır.

### **3. Veri Doğrulama:**
Çıkarılan veriler doğrulanır ve varsayılan değerler atanır.

### **4. Dinamik Dosya Adları:**
Zaman damgalı dosya adları otomatik oluşturulur.

## 🔄 **Zamanlama (Scheduling)**

### **Cron Trigger Ekleme:**
```javascript
// Manuel Start node'u yerine Cron node kullanın
{
  "parameters": {
    "rule": {
      "intervalSize": 1,
      "intervalUnit": "hours"
    }
  },
  "name": "Cron Trigger",
  "type": "n8n-nodes-base.cron"
}
```

### **Webhook Trigger:**
```javascript
// Webhook ile tetikleme
{
  "parameters": {
    "path": "scrape-local-rank",
    "httpMethod": "POST"
  },
  "name": "Webhook",
  "type": "n8n-nodes-base.webhook"
}
```

## 📈 **Performans Optimizasyonu**

### **1. Memory Usage:**
- Node'lar arası veri transferini minimize edin
- Büyük HTML verilerini sadece gerekli node'lara gönderin

### **2. Execution Time:**
- Rate limiting'i ayarlayın
- Paralel işlemleri kullanın
- Timeout değerlerini optimize edin

### **3. Error Recovery:**
```javascript
// Retry mekanizması
"continueOnFail": true,
"retryOnFail": true,
"maxTries": 3
```

## 🛠️ **Troubleshooting**

### **Yaygın Problemler:**

**1. HTML Extract Başarısız:**
- CSS seçicilerini kontrol edin
- Hedef site yapısının değişip değişmediğini kontrol edin

**2. API Çağrıları Başarısız:**
- Rate limiting ayarlarını kontrol edin
- Headers'ı doğrulayın

**3. Function Node Hataları:**
- JavaScript syntax'ını kontrol edin
- Console.log ile debug yapın

### **Debug Modları:**
```javascript
// Function node'larında debug için
console.log('Debug data:', JSON.stringify(items, null, 2));
return items;
```

## 📞 **Destek ve Geliştirme**

### **Workflow Geliştirme:**
1. Yeni node'lar ekleyin
2. Mevcut function'ları genişletin
3. Ek veri kaynakları entegre edin

### **Community Resources:**
- [n8n Community](https://community.n8n.io/)
- [n8n Docs](https://docs.n8n.io/)
- [Workflow Templates](https://n8n.io/workflows/)

## 🎉 **Sonuç**

Bu n8n workflow, orijinal Python modüler scraper'ın tüm işlevselliğini görsel ve otomatik bir platformda sunar. Kodsuz/düşük kodlu çözüm arayan kullanıcılar için ideal bir alternatiftir.

**Avantajlar:**
- ✅ Görsel workflow editörü
- ✅ Otomatik zamanlama
- ✅ Webhook desteği
- ✅ Cloud hosting seçenekleri
- ✅ Entegrasyon kolaylığı
- ✅ Maintenance kolaylığı