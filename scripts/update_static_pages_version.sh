#!/bin/bash
# Static Pages Version Update Script - Solves browser cache issues
# Usage: ./scripts/update_static_pages_version.sh

# Generate timestamp (YYYYMMDD-HHMM format)
VERSION=$(date +"%Y%m%d-%H%M")

# Path to static pages
ANNOUNCEMENTS_FILE="static/announcements/index.html"
HELP_FILE="static/help/index.html"
ABOUT_FILE="static/about/index.html"

echo "🔄 Updating static pages version to: $VERSION"

# Function to add/update version in file
update_file_version() {
    local file=$1
    local file_name=$(basename "$file")

    if [ ! -f "$file" ]; then
        echo "⚠️  Warning: $file not found, skipping..."
        return
    fi

    echo "📝 Processing $file_name..."

    # Update or add cache-version meta tag
    if grep -q "cache-version" "$file"; then
        sed -i '' "s/<meta name=\"cache-version\" content=\"[^\"]*\">/<meta name=\"cache-version\" content=\"$VERSION\">/g" "$file"
        echo "   ✅ Updated cache-version meta tag"
    else
        sed -i '' "s/<meta charset=\"UTF-8\">/<meta charset=\"UTF-8\">\
    <meta name=\"cache-version\" content=\"$VERSION\">/g" "$file"
        echo "   ✅ Added cache-version meta tag"
    fi
}

# Update all static pages
echo ""
update_file_version "$ANNOUNCEMENTS_FILE"
echo ""
update_file_version "$HELP_FILE"
echo ""
update_file_version "$ABOUT_FILE"

echo ""
echo "✅ All static pages updated to version: $VERSION"
echo "📝 Updated files:"
echo "   - $ANNOUNCEMENTS_FILE"
echo "   - $HELP_FILE"
echo "   - $ABOUT_FILE"
echo ""
echo "💡 Browser cache will be busted on next deployment"
echo "🚀 Changes ready for commit and deploy"

# Display verification
echo ""
echo "=== Version Verification ==="
for file in "$ANNOUNCEMENTS_FILE" "$HELP_FILE" "$ABOUT_FILE"; do
    if [ -f "$file" ]; then
        echo ""
        echo "$(basename "$file"):"
        grep -n "cache-version" "$file" | head -1
    fi
done
echo "   - $ABOUT_FILE"
echo ""
echo "💡 Browser cache will be busted on next deployment"
echo "🚀 Changes ready for commit and deploy"

# Display verification
echo ""
echo "=== Version Verification ==="
for file in "$ANNOUNCEMENTS_FILE" "$HELP_FILE" "$ABOUT_FILE"; do
    if [ -f "$file" ]; then
        echo ""
        echo "$(basename "$file"):"
        grep -n "cache-version" "$file" | head -1
    fi
done
