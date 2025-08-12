# N8N Otomatik İş Akışları

Bu proje, [awesome-n8n-templates](https://github.com/enescingoz/awesome-n8n-templates) deposundan esinlenerek oluşturulmuş, Türkçe dil desteği ile geliştirilmiş n8n iş akışlarını içermektedir.

## 🚀 Oluşturulan İş Akışları

### 1. **Basit Telegram AI Bot** (`simple-telegram-ai-bot.json`)

**Açıklama:** Telegram üzerinden çalışan Türkçe destekli AI asistanı.

**Özellikler:**
- Türkçe konuşma desteği
- Chat hafızası (son 10 mesaj)
- OpenAI GPT-4o-mini entegrasyonu
- Emoji kullanımı
- Markdown desteği

**Gerekli Bağlantılar:**
- Telegram Bot API
- OpenAI API

**Kullanım:**
1. Telegram'da yeni bir bot oluşturun (@BotFather)
2. Bot token'ınızı n8n'de yapılandırın
3. OpenAI API anahtarınızı ekleyin
4. Workflow'u aktifleştirin

### 2. **Gmail AI Otomatik E-posta Sınıflandırıcı** (`gmail-ai-classifier.json`)

**Açıklama:** Gelen e-postaları AI ile otomatik olarak kategorize eden sistem.

**Özellikler:**
- 6 farklı kategori (İş, Kişisel, Promosyon, Haber, Spam, Destek)
- Otomatik etiket ekleme
- Dakikada bir kontrol
- Türkçe dil desteği

**Gerekli Bağlantılar:**
- Gmail OAuth2
- OpenAI API

**Kurulum:**
1. Gmail API'yi etkinleştirin
2. OAuth2 kimlik bilgilerini yapılandırın
3. Gmail'de etiketleri oluşturun
4. Label ID'lerini workflow'da güncelleyin

### 3. **AI İçerik Üretici** (`ai-content-generator.json`)

**Açıklama:** Blog yazıları, sosyal medya içeriği ve pazarlama materyalleri üreten kapsamlı sistem.

**Özellikler:**
- 3 farklı içerik türü (Blog, Sosyal Medya, Pazarlama)
- Otomatik görsel oluşturma
- Google Sheets entegrasyonu
- Telegram bildirimleri
- SEO dostu içerik

**API Kullanımı:**
```bash
# Blog içeriği oluşturma
curl -X POST https://your-n8n-domain.com/webhook/content-generator \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "blog",
    "topic": "Yapay Zeka ve Gelecek",
    "audience": "Teknoloji meraklıları",
    "tone": "Bilgilendirici ve eğlenceli"
  }'

# Sosyal medya içeriği
curl -X POST https://your-n8n-domain.com/webhook/content-generator \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "social",
    "topic": "Dijital pazarlama ipuçları",
    "platform": "Instagram",
    "tone": "Enerjik ve eğlenceli"
  }'
```

### 4. **Akıllı Belge İşleyici** (`smart-document-processor.json`)

**Açıklama:** PDF belgelerini analiz eden, içerik çıkaran ve hassas veri tespiti yapan sistem.

**Özellikler:**
- PDF metin çıkarma
- Belge türü otomatik tespiti
- Hassas veri analizi (KVKK/GDPR uyumlu)
- Supabase & Google Sheets entegrasyonu
- Risk seviyesi değerlendirmesi

**Desteklenen Belge Türleri:**
- Faturalar
- Sözleşmeler
- CV'ler
- Raporlar
- Resmi mektuplar
- Sertifikalar

## 🛠️ Kurulum Rehberi

### Gerekli Hesaplar ve API'lar

1. **n8n Kurulumu**
   ```bash
   npm install n8n -g
   n8n start
   ```

2. **OpenAI API**
   - https://platform.openai.com/ adresinden hesap oluşturun
   - API anahtarı alın

3. **Telegram Bot**
   - @BotFather ile konuşun
   - `/newbot` komutu ile bot oluşturun
   - Token'ı kaydedin

4. **Gmail API**
   - Google Cloud Console'da proje oluşturun
   - Gmail API'yi etkinleştirin
   - OAuth2 kimlik bilgileri oluşturun

5. **Supabase (Opsiyonel)**
   - https://supabase.com/ adresinden hesap oluşturun
   - Veritabanı oluşturun
   - API anahtarlarını alın

### Workflow İçe Aktarma

1. n8n arayüzünde "Import from File" seçeneğini kullanın
2. JSON dosyalarını tek tek içe aktarın
3. Credential'ları yapılandırın
4. Gerekli ID'leri güncelleyin (Google Sheet ID, Telegram Chat ID vb.)

### Veritabanı Tabloları

**Supabase için processed_documents tablosu:**
```sql
CREATE TABLE processed_documents (
  id SERIAL PRIMARY KEY,
  filename TEXT NOT NULL,
  document_type TEXT,
  summary TEXT,
  key_information JSONB,
  language TEXT,
  confidence_score INTEGER,
  has_sensitive_data BOOLEAN,
  risk_level TEXT,
  priority TEXT,
  processed_at TIMESTAMP DEFAULT NOW(),
  extracted_text TEXT
);
```

## 📋 Yapılandırma Listesi

### 1. Telegram Bot
- [ ] Bot token alındı
- [ ] Chat ID belirlendi
- [ ] n8n'de credential oluşturuldu

### 2. Gmail Entegrasyonu
- [ ] Gmail API etkinleştirildi
- [ ] OAuth2 yapılandırıldı
- [ ] Etiketler oluşturuldu
- [ ] Label ID'leri güncellendi

### 3. OpenAI
- [ ] API anahtarı alındı
- [ ] n8n'de credential oluşturuldu
- [ ] Model tercihleri ayarlandı

### 4. Google Services
- [ ] Google Sheets ID'si güncellendi
- [ ] Google Drive folder ID'si güncellendi
- [ ] OAuth2 yetkilendirmesi tamamlandı

## 🎯 Kullanım Senaryoları

### İş Otomasyonu
- E-posta sınıflandırma ve önceliklendirme
- Belge işleme ve arşivleme
- Müşteri hizmetleri otomasyonu

### İçerik Üretimi
- Blog yazıları oluşturma
- Sosyal medya içerik planlaması
- Pazarlama materyali üretimi

### Veri İşleme
- PDF'lerden bilgi çıkarma
- Hassas veri tespiti
- Otomatik raporlama

## 🔧 Özelleştirme

### Dil Değiştirme
AI promptlarında Türkçe yerine istediğiniz dili kullanabilirsiniz:

```javascript
// Örnek prompt değişikliği
"Sen profesyonel bir içerik yazarısın..." 
// yerine
"You are a professional content writer..."
```

### Yeni Kategoriler Ekleme
E-posta sınıflandırıcıya yeni kategoriler eklemek için:

1. Prompt'ta yeni kategoriyi tanımlayın
2. Switch node'da yeni condition ekleyin
3. Gmail'de yeni etiketi oluşturun
4. Yeni Gmail node ekleyin

### Webhook Güvenliği
Production ortamında webhook'lara güvenlik ekleyin:

```javascript
// Basic Auth örneği
if ($json.headers.authorization !== 'Bearer YOUR_SECRET_TOKEN') {
  throw new Error('Unauthorized');
}
```

## 📊 Performans Optimizasyonu

### Token Kullanımını Azaltma
```javascript
// Daha kısa promptlar kullanın
"Kategori belirle: İş/Kişisel/Promosyon"
// uzun açıklamalar yerine
```

### Batch İşleme
Birden fazla dosya için batch processing ekleyin:

```javascript
// Birden fazla PDF'i aynı anda işleme
for (const file of files) {
  // işlem
}
```

## 🐛 Sorun Giderme

### Yaygın Hatalar

1. **Credential Hatası**
   - Tüm API anahtarlarını kontrol edin
   - Yetkilendirme sürelerini kontrol edin

2. **Webhook Çalışmıyor**
   - URL'lerin doğruluğunu kontrol edin
   - Firewall ayarlarını kontrol edin

3. **AI Yanıt Vermiyor**
   - OpenAI quota'nızı kontrol edin
   - Model availability'sini kontrol edin

4. **Gmail Etiketleri Eklenmiyor**
   - Label ID'lerinin doğruluğunu kontrol edin
   - Gmail API yetkilendirmesini yenileyin

## 📚 Ek Kaynaklar

- [n8n Dokumentasyonu](https://docs.n8n.io/)
- [OpenAI API Rehberi](https://platform.openai.com/docs/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Original Awesome n8n Templates](https://github.com/enescingoz/awesome-n8n-templates)

## 🤝 Katkıda Bulunma

Bu projeyi geliştirmek için:

1. Repository'yi fork edin
2. Yeni özellikler ekleyin
3. Pull request gönderin
4. Issues bölümünde geri bildirim verin

## 📄 Lisans

Bu proje MIT lisansı altında dağıtılmaktadır. Detaylar için LICENSE dosyasına bakın.

---

**Not:** Bu workflow'lar eğitim ve örnek amaçlı oluşturulmuştur. Production ortamında kullanmadan önce güvenlik ve performans testlerini yapmayı unutmayın.