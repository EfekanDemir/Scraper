# 🚀 n8n Local Rank Report Scraper - İmport ve Kullanım Kılavuzu

## 📋 İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Ön Gereksinimler](#ön-gereksinimler)
3. [Workflow Dosyalarının İmport Edilmesi](#workflow-dosyalarının-import-edilmesi)
4. [Kurulum ve Yapılandırma](#kurulum-ve-yapılandırma)
5. [Kullanım Talimatları](#kullanım-talimatları)
6. [Sorun Giderme](#sorun-giderme)
7. [İleri Düzey Yapılandırma](#i̇leri-düzey-yapılandırma)

---

## 📊 Genel Bakış

Bu proje, Local Rank Report sitesinden veri çekmek için 3 farklı n8n workflow'u içerir:

### 🔧 Workflow Tipleri:

1. **`n8n_basic_scraper_workflow.json`** - Temel Scraper
   - ✅ HTML parsing
   - ✅ JavaScript veri çıkarma
   - ✅ JSON çıktı
   - ❌ API çağrıları yok
   - 🎯 **Kullanım:** Hızlı veri çekme, test amaçlı

2. **`n8n_advanced_scraper_workflow.json`** - Gelişmiş Scraper
   - ✅ HTML parsing
   - ✅ JavaScript veri çıkarma
   - ✅ API çağrıları
   - ✅ JSON + CSV çıktı
   - ✅ Çoklu veri kaynağı
   - 🎯 **Kullanım:** Kapsamlı veri toplama

3. **`n8n_production_scraper_workflow.json`** - Production Ready
   - ✅ Tüm gelişmiş özellikler
   - ✅ Hata yönetimi ve retry logic
   - ✅ Rate limiting
   - ✅ Validation ve monitoring
   - ✅ Detaylı logging
   - 🎯 **Kullanım:** Canlı ortam, otomatik çalışma

---

## 🛠 Ön Gereksinimler

### n8n Kurulumu:
```bash
# Docker ile (önerilen)
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n

# NPM ile
npm install n8n -g
n8n start
```

### Gerekli Node.js Paketleri:
- **cheerio**: HTML parsing için (n8n'de built-in)
- **URL**: URL işlemleri için (n8n'de built-in)

### Sistem Gereksinimleri:
- Node.js 16+
- 2GB RAM (minimum)
- İnternet bağlantısı

---

## 📥 Workflow Dosyalarının İmport Edilmesi

### Adım 1: n8n Arayüzüne Erişim
1. Tarayıcınızda `http://localhost:5678` açın
2. n8n hesabınıza giriş yapın

### Adım 2: Workflow İmport
1. **Sol menüden "Workflows"** seçin
2. **"Import from file"** butonuna tıklayın
3. **JSON dosyasını seçin** (örn: `n8n_basic_scraper_workflow.json`)
4. **"Import"** butonuna tıklayın

### Adım 3: İmport Doğrulama
```javascript
// Console'da çalıştırın (F12)
console.log('Workflow imported successfully');
```

---

## ⚙️ Kurulum ve Yapılandırma

### 1. URL Yapılandırması

**Basic/Advanced Workflow için:**
```json
{
  "name": "url",
  "value": "YOUR_LOCAL_RANK_REPORT_URL_HERE"
}
```

**Production Workflow için:**
```json
{
  "name": "url", 
  "value": "YOUR_URL_HERE"
},
{
  "name": "user_agent",
  "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
},
{
  "name": "max_retries",
  "value": 3
},
{
  "name": "rate_limit_seconds", 
  "value": 2
}
```

### 2. Header Yapılandırması (İsteğe Bağlı)

Production workflow'da ekstra güvenlik için:
```json
{
  "name": "Accept-Language",
  "value": "tr-TR,tr;q=0.9,en;q=0.8"
}
```

### 3. Dosya Çıktı Yolu

n8n ayarlarında dosya yazma iznini kontrol edin:
```bash
# Docker kullanıyorsanız
docker run -it --rm --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n
```

---

## 🚀 Kullanım Talimatları

### Temel Kullanım:

1. **Workflow'u seçin**
2. **"Execute Workflow" butonuna tıklayın**
3. **Sonuçları bekleyin** (30-60 saniye)
4. **Çıktı dosyalarını kontrol edin**

### Manuel Execution:

```bash
# n8n CLI ile
n8n execute --id=WORKFLOW_ID

# Belirli parametrelerle
n8n execute --id=WORKFLOW_ID --data='{"url":"YOUR_URL"}'
```

### Otomatik Çalışma (Cron):

```json
{
  "name": "Cron Trigger",
  "type": "n8n-nodes-base.cron",
  "parameters": {
    "rule": {
      "interval": [
        {
          "field": "cronExpression",
          "expression": "0 9 * * 1-5"
        }
      ]
    }
  }
}
```

---

## 🔧 Sorun Giderme

### Yaygın Hatalar ve Çözümleri:

#### 1. "HTML content not found" Hatası
```javascript
// Çözüm: CSS selector'ları güncelleyin
"cssSelector": "div.card-body table"  // Eski
"cssSelector": "div.content table"    // Yeni (site değişirse)
```

#### 2. "JavaScript data extraction failed" Hatası
```javascript
// Çözüm: Regex pattern'leri kontrol edin
const pinzMatch = scriptText.match(/var\s+pinz\s*=\s*(\[.*?\]);/s);
```

#### 3. API Timeout Hatası
```json
{
  "timeout": 30000,  // 15000'den 30000'e çıkar
  "retry": {
    "retryCount": 5  // 3'ten 5'e çıkar
  }
}
```

#### 4. Rate Limiting
```javascript
// Wait node'un süresini artırın
"amount": 5,  // 2'den 5'e
"unit": "seconds"
```

### Debug İpuçları:

```javascript
// Function node'larda debug için
console.log('Debug data:', JSON.stringify(data, null, 2));

// Hata yakalama
try {
  // risky operation
} catch (error) {
  console.error('Error:', error.message);
  throw new Error('Custom error message');
}
```

---

## 🎯 İleri Düzey Yapılandırma

### 1. Proxy Kullanımı

```json
{
  "options": {
    "proxy": "http://proxy-server:port",
    "timeout": 30000
  }
}
```

### 2. Cookie Yönetimi

```json
{
  "sendHeaders": true,
  "headerParameters": {
    "parameters": [
      {
        "name": "Cookie",
        "value": "session_id=YOUR_SESSION_ID"
      }
    ]
  }
}
```

### 3. Paralel API Çağrıları

```javascript
// Function node'da
const requests = pinzArray.map((pin, index) => ({
  json: {
    url: `${baseUrl}${pin.url}`,
    pin_index: index
  }
}));

return requests; // n8n otomatik olarak paralel çalıştırır
```

### 4. Veri Validation

```javascript
// Gelişmiş validation
function validateScrapedData(data) {
  const required = ['ozet_bilgiler', 'rakipler'];
  const missing = required.filter(key => !data[key] || Object.keys(data[key]).length === 0);
  
  if (missing.length > 0) {
    throw new Error(`Missing required data: ${missing.join(', ')}`);
  }
  
  return true;
}
```

### 5. Monitoring ve Alerting

```javascript
// Webhook ile Slack/Discord notification
const webhookUrl = 'YOUR_WEBHOOK_URL';
const message = {
  text: `Scraping completed: ${data.metadata.data_quality.rakipler_count} competitors found`
};

// HTTP Request node ile gönder
```

---

## 📁 Çıktı Dosyaları

### Dosya Formatları:

1. **JSON**: `scraped_data_YYYY-MM-DD_HH-mm-ss.json`
2. **CSV**: `scraped_data_YYYY-MM-DD_HH-mm-ss.csv`
3. **Log**: `execution_log_YYYY-MM-DD_HH-mm-ss.json`

### Örnek Çıktı Yapısı:

```json
{
  "ozet_bilgiler": {
    "Business Name": "Example Business",
    "Address": "123 Example St",
    "Average Position": "3.2"
  },
  "rakipler": [
    {
      "rank": "1",
      "business_name": "Competitor 1",
      "address": "456 Competitor Ave"
    }
  ],
  "harita_verileri": [
    {
      "lat": 40.7128,
      "lng": -74.0060,
      "title": "Location 1"
    }
  ],
  "metadata": {
    "scraped_at": "2024-01-20T12:00:00.000Z",
    "scraper_version": "3.0-n8n-production",
    "success": true
  }
}
```

---

## 🔄 Güncellemeler ve Bakım

### Site Değişikliklerinde:

1. **CSS Selector'ları güncelleyin**
2. **JavaScript regex pattern'lerini kontrol edin**
3. **API endpoint'lerini doğrulayın**

### Performance Optimizasyonu:

1. **Rate limiting değerlerini ayarlayın**
2. **Timeout değerlerini optimize edin**
3. **Paralel işlem sayısını kontrol edin**

---

## 📞 Destek

Herhangi bir sorun yaşadığınızda:

1. **n8n execution log'larını kontrol edin**
2. **Browser developer tools'u kullanın**
3. **Site yapısını manuel olarak kontrol edin**

---

**🎉 Başarılı scraping!**