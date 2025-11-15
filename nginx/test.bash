#!/bin/bash

CERT_DIR="./certbot/localhost"
DOMAIN="localhost"

# 인증서가 이미 존재하면 패스
if [ -f "$CERT_DIR/fullchain.crt" ] && [ -f "$CERT_DIR/privkey.key" ]; then
    echo "✅ Certificate for $DOMAIN already exists. Skipping generation."
    exit 0
fi

# openssl 설치 여부 확인
if ! command -v openssl &> /dev/null; then
    echo "⚙️ openssl not found. Installing..."
    sudo apt update
    sudo apt install -y openssl

    if [ $? -ne 0 ]; then
        echo "❌ Failed to install openssl. Exiting."
        exit 1
    fi
fi

# certs 디렉토리 없으면 생성
mkdir -p "$CERT_DIR"

# self-signed 인증서 발급
echo "▶️ Generating self-signed certificate for $DOMAIN..."

openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$CERT_DIR/privkey.key" \
    -out "$CERT_DIR/fullchain.crt" \
    -subj "/CN=$DOMAIN"

# 성공 여부 확인
if [ $? -eq 0 ]; then
    echo "✅ Self-signed certificate generated at $CERT_DIR"
else
    echo "❌ Failed to generate self-signed certificate."
fi

