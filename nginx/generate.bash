#!/bin/bash

# 현재 경로에 있는 .env 파일 로드
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ .env file not found in current directory."
    exit 1
fi

# DOMAIN 값 확인
if [ -z "$DOMAIN" ]; then
    echo "❌ DOMAIN variable not set in .env file."
    exit 1
fi

# EMAIL 값 확인
if [ -z "$EMAIL" ]; then
    echo "❌ EMAIL variable not set in .env file."
    exit 1
fi

# certbot 설치 여부 확인
if ! command -v certbot &> /dev/null; then
    echo "⚙️ certbot not found. Installing..."
    apt update
    apt install -y certbot python3-certbot-dns-cloudflare

    if [ $? -ne 0 ]; then
        echo "❌ Failed to install certbot. Exiting."
        exit 1
    fi
fi

# 인증서 발급 시도
echo "▶️ Issuing certificate for domain: $DOMAIN"
certbot certonly \
    --dns-cloudflare \
    --dns-cloudflare-credentials "cf-token.ini" \
    --register-unsafely-without-email \
    -d $DOMAIN

# 발급 성공 여부 확인
if [ $? -eq 0 ]; then
    mkdir -p "./certbot/conf/$DOMAIN"
    mkdir -p "./certbot/renewal"
    cp -L "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "./certbot/conf/$DOMAIN/fullchain.pem"
    cp -L "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "./certbot/conf/$DOMAIN/privkey.pem"
    cp "/etc/letsencrypt/renewal/$DOMAIN.conf" "./certbot/renewal/$DOMAIN.conf"

    echo "✅ Certificate issued for $DOMAIN."
else
    echo "⚠️ Failed to issue certificate for $DOMAIN."
fi

