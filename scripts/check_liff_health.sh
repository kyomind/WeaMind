#!/bin/bash

# LIFF Health Check Script
# 檢查 LIFF 頁面是否正常載入

LIFF_URL="https://api.kyomind.tw/static/liff/location/index.html"
LIFF_SDK_URL="https://static.line-scdn.net/liff/edge/2/sdk.js"

echo "🔍 Checking LIFF health..."

# Check if LIFF page is accessible
echo "Checking LIFF page accessibility..."
if curl -f -s -o /dev/null "$LIFF_URL"; then
    echo "✅ LIFF page is accessible"
else
    echo "❌ LIFF page is not accessible"
    exit 1
fi

# Check if LIFF SDK is accessible
echo "Checking LIFF SDK accessibility..."
if curl -f -s -o /dev/null "$LIFF_SDK_URL"; then
    echo "✅ LIFF SDK is accessible"
else
    echo "❌ LIFF SDK is not accessible"
    exit 1
fi

# Check if page contains expected content
echo "Checking LIFF page content..."
if curl -s "$LIFF_URL" | grep -q "地點設定"; then
    echo "✅ LIFF page contains expected content"
else
    echo "❌ LIFF page does not contain expected content"
    exit 1
fi

echo "🎉 All LIFF health checks passed!"
