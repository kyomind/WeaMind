#!/bin/bash
# LIFF Version Update Script - Works with AI auto-update comments
# Usage: ./scripts/update_liff_version.sh

# Generate timestamp (YYYYMMDD-HHMM format)
VERSION=$(date +"%Y%m%d-%H%M")

# Path to files
HTML_FILE="static/liff/location/index.html"
JS_FILE="static/liff/location/app.js"

echo "🔄 Updating LIFF version to: $VERSION"

# Update CSS version in HTML
sed -i '' "s/style\.css?v=[^\"]*\"/style.css?v=$VERSION\"/g" "$HTML_FILE"

# Update JS version in HTML
sed -i '' "s/app\.js?v=[^\"]*\"/app.js?v=$VERSION\"/g" "$HTML_FILE"

# Update JS file AUTO_UPDATE_VERSION comment
sed -i '' "s/\/\/ AUTO_UPDATE_VERSION: [^(]*/\/\/ AUTO_UPDATE_VERSION: $VERSION /g" "$JS_FILE"

echo "✅ Updated version numbers in HTML and JS files"
echo "📝 New version: $VERSION"
echo "💡 Next: Run 'make dev-up' or 'make up' to restart Docker"

# Display the updated lines for verification
echo ""
echo "Updated lines in HTML:"
grep -n "\.css?v=\|\.js?v=" "$HTML_FILE"
echo ""
echo "Updated line in JS:"
grep -n "AUTO_UPDATE_VERSION:" "$JS_FILE"
