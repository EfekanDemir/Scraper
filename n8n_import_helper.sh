#!/bin/bash

# N8N JSON Import Helper Script
# Bu script JSON dosyalarını n8n'e import etmenize yardımcı olur

echo "🚀 N8N JSON Import Helper"
echo "=========================="

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonksiyonlar
check_n8n_running() {
    echo -e "${BLUE}N8N durumu kontrol ediliyor...${NC}"
    if curl -s http://localhost:5678 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ N8N çalışıyor (http://localhost:5678)${NC}"
        return 0
    else
        echo -e "${RED}❌ N8N çalışmıyor veya erişilemiyor${NC}"
        echo -e "${YELLOW}N8N'i başlatmak için: npx n8n start${NC}"
        return 1
    fi
}

validate_json() {
    local file=$1
    echo -e "${BLUE}JSON dosyası validasyonu: $file${NC}"
    
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Dosya bulunamadı: $file${NC}"
        return 1
    fi
    
    if command -v jq &> /dev/null; then
        if jq . "$file" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ JSON valid: $file${NC}"
            return 0
        else
            echo -e "${RED}❌ JSON invalid: $file${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  jq bulunamadı, JSON validasyonu atlanıyor${NC}"
        return 0
    fi
}

list_json_files() {
    echo -e "${BLUE}Mevcut JSON dosyaları:${NC}"
    echo "========================"
    
    local count=1
    for file in *.json; do
        if [ -f "$file" ]; then
            local size=$(ls -lh "$file" | awk '{print $5}')
            local lines=$(wc -l < "$file")
            
            if [[ "$file" == *"workflow"* ]]; then
                echo -e "${GREEN}$count. $file ${NC}(${size}, ${lines} lines) ${YELLOW}[WORKFLOW]${NC}"
            else
                echo -e "${BLUE}$count. $file ${NC}(${size}, ${lines} lines) ${YELLOW}[DATA]${NC}"
            fi
            
            ((count++))
        fi
    done
}

import_workflow() {
    local file=$1
    echo -e "${BLUE}Workflow import başlatılıyor: $file${NC}"
    
    # JSON'dan workflow adını çıkar
    if command -v jq &> /dev/null; then
        local workflow_name=$(jq -r '.name // "Unknown Workflow"' "$file")
        echo -e "${YELLOW}Workflow Adı: $workflow_name${NC}"
    fi
    
    echo -e "${YELLOW}Manuel Import Adımları:${NC}"
    echo "1. N8N arayüzünü açın: http://localhost:5678"
    echo "2. '+' butonuna tıklayın (yeni workflow)"
    echo "3. Sağ üst '⋯' menüsünden 'Import from file' seçin"
    echo "4. Dosyayı seçin: $file"
    echo "5. 'Activate' butonuna tıklayın"
    
    # Curl ile otomatik import dene (eğer API endpoint varsa)
    echo -e "\n${BLUE}Otomatik import deneniyor...${NC}"
    
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d @"$file" \
        http://localhost:5678/rest/workflows 2>/dev/null)
    
    if [ $? -eq 0 ] && [[ "$response" == *"id"* ]]; then
        echo -e "${GREEN}✅ Workflow başarıyla import edildi!${NC}"
    else
        echo -e "${YELLOW}⚠️  Otomatik import başarısız, manuel import kullanın${NC}"
    fi
}

process_data_file() {
    local file=$1
    echo -e "${BLUE}Veri dosyası işleniyor: $file${NC}"
    
    # Dosya türünü belirle
    if grep -q "ozet_bilgiler" "$file"; then
        echo -e "${GREEN}📊 Scraping data dosyası tespit edildi${NC}"
        
        # Özet bilgileri göster
        if command -v jq &> /dev/null; then
            echo -e "\n${YELLOW}Özet Bilgiler:${NC}"
            jq -r '.ozet_bilgiler | to_entries[] | "\(.key): \(.value)"' "$file" | head -5
            
            echo -e "\n${YELLOW}Rakip Sayısı:${NC}"
            local rakip_count=$(jq '.rakipler | length' "$file")
            echo "$rakip_count rakip"
        fi
        
        echo -e "\n${YELLOW}Bu veriyi N8N'de kullanmak için:${NC}"
        echo "1. N8N workflow'unuzda Code node ekleyin"
        echo "2. Şu kodu kullanın:"
        echo ""
        echo "const fs = require('fs');"
        echo "const data = JSON.parse(fs.readFileSync('$PWD/$file', 'utf8'));"
        echo "return { json: data };"
    else
        echo -e "${BLUE}📄 Genel JSON veri dosyası${NC}"
    fi
}

send_to_webhook() {
    local file=$1
    local webhook_url
    
    echo -e "${BLUE}Webhook URL'ini girin (örnek: http://localhost:5678/webhook/test):${NC}"
    read -r webhook_url
    
    if [[ -z "$webhook_url" ]]; then
        echo -e "${RED}❌ Webhook URL boş olamaz${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Veri webhook'a gönderiliyor...${NC}"
    
    local response=$(curl -s -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d @"$file" \
        "$webhook_url")
    
    local http_code="${response: -3}"
    local body="${response%???}"
    
    if [[ "$http_code" == "200" ]] || [[ "$http_code" == "201" ]]; then
        echo -e "${GREEN}✅ Veri başarıyla gönderildi! (HTTP $http_code)${NC}"
        if [[ -n "$body" ]] && [[ "$body" != *"html"* ]]; then
            echo -e "${YELLOW}Response: ${body:0:200}...${NC}"
        fi
    else
        echo -e "${RED}❌ Hata: HTTP $http_code${NC}"
        echo -e "${RED}Response: ${body:0:200}${NC}"
    fi
}

# Ana menü
show_menu() {
    echo -e "\n${BLUE}Ne yapmak istiyorsunuz?${NC}"
    echo "1. JSON dosyalarını listele"
    echo "2. Workflow dosyası import et"
    echo "3. Veri dosyasını analiz et"
    echo "4. Veri dosyasını webhook'a gönder"
    echo "5. N8N durumunu kontrol et"
    echo "6. Tüm JSON dosyalarını valide et"
    echo "0. Çıkış"
    echo -e "\n${YELLOW}Seçiminizi yapın [0-6]:${NC}"
}

# Ana döngü
main() {
    echo -e "${GREEN}Workspace: $PWD${NC}"
    
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1)
                list_json_files
                ;;
            2)
                echo -e "${BLUE}Workflow dosyasını seçin:${NC}"
                select file in *workflow*.json; do
                    if [[ -n "$file" ]]; then
                        if validate_json "$file"; then
                            import_workflow "$file"
                        fi
                        break
                    fi
                done
                ;;
            3)
                echo -e "${BLUE}Analiz edilecek veri dosyasını seçin:${NC}"
                select file in *.json; do
                    if [[ -n "$file" ]] && [[ "$file" != *"workflow"* ]]; then
                        if validate_json "$file"; then
                            process_data_file "$file"
                        fi
                        break
                    elif [[ "$file" == *"workflow"* ]]; then
                        echo -e "${YELLOW}Bu bir workflow dosyası. Veri dosyası seçin.${NC}"
                    fi
                done
                ;;
            4)
                echo -e "${BLUE}Webhook'a gönderilecek dosyayı seçin:${NC}"
                select file in *.json; do
                    if [[ -n "$file" ]] && [[ "$file" != *"workflow"* ]]; then
                        if validate_json "$file"; then
                            send_to_webhook "$file"
                        fi
                        break
                    fi
                done
                ;;
            5)
                check_n8n_running
                ;;
            6)
                echo -e "${BLUE}Tüm JSON dosyaları valide ediliyor...${NC}"
                for file in *.json; do
                    if [ -f "$file" ]; then
                        validate_json "$file"
                    fi
                done
                ;;
            0)
                echo -e "${GREEN}👋 Görüşürüz!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Geçersiz seçim. Lütfen 0-6 arası bir sayı girin.${NC}"
                ;;
        esac
        
        echo -e "\n${YELLOW}Devam etmek için Enter'a basın...${NC}"
        read -r
    done
}

# Script başlat
main