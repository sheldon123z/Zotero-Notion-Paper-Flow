#!/bin/bash
# Unified build script for Zotero-Notion-Paper-Flow
# Builds both Python package and Desktop app for all platforms

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Paper Flow Build System${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Read version from VERSION file
VERSION=$(cat "$PROJECT_ROOT/VERSION" | tr -d '[:space:]')
echo -e "${YELLOW}Building version: ${VERSION}${NC}"
echo ""

# Create dist directory
DIST_DIR="$PROJECT_ROOT/dist"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# ===================================
# 1. Build Python Package
# ===================================
echo -e "${GREEN}[1/3] Building Python package...${NC}"
cd "$PROJECT_ROOT"

# Clean previous builds
rm -rf build/ src/*.egg-info

# Build wheel and source distribution
python -m pip install --upgrade build
python -m build --outdir "$DIST_DIR/python"

echo -e "${GREEN}✓ Python package built successfully${NC}"
echo ""

# ===================================
# 2. Build Desktop App (macOS)
# ===================================
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${GREEN}[2/3] Building Desktop app for macOS...${NC}"
    cd "$PROJECT_ROOT/desktop-app"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing npm dependencies..."
        npm install
    fi
    
    # Build for macOS
    npm run build:mac
    
    # Move builds to unified dist directory
    mkdir -p "$DIST_DIR/desktop"
    if [ -d "dist" ]; then
        cp -r dist/* "$DIST_DIR/desktop/"
    fi
    
    echo -e "${GREEN}✓ macOS Desktop app built successfully${NC}"
else
    echo -e "${YELLOW}⚠ Skipping macOS build (not on macOS)${NC}"
fi
echo ""

# ===================================
# 3. Generate Checksums
# ===================================
echo -e "${GREEN}[3/3] Generating checksums...${NC}"
cd "$DIST_DIR"

CHECKSUM_FILE="checksums.txt"
rm -f "$CHECKSUM_FILE"

echo "SHA256 Checksums for Paper Flow v${VERSION}" > "$CHECKSUM_FILE"
echo "Generated: $(date)" >> "$CHECKSUM_FILE"
echo "========================================" >> "$CHECKSUM_FILE"
echo "" >> "$CHECKSUM_FILE"

# Generate checksums for all files
find . -type f \( -name "*.whl" -o -name "*.tar.gz" -o -name "*.dmg" -o -name "*.zip" -o -name "*.exe" -o -name "*.AppImage" -o -name "*.deb" \) -exec sh -c '
    for file; do
        if [ -f "$file" ]; then
            sha256sum "$file" >> checksums.txt
        fi
    done
' sh {} +

echo -e "${GREEN}✓ Checksums generated${NC}"
echo ""

# ===================================
# Summary
# ===================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Build artifacts:"
echo "  Python packages: $DIST_DIR/python/"
echo "  Desktop apps:    $DIST_DIR/desktop/"
echo "  Checksums:       $DIST_DIR/checksums.txt"
echo ""
echo "Contents:"
find "$DIST_DIR" -type f \( -name "*.whl" -o -name "*.tar.gz" -o -name "*.dmg" -o -name "*.zip" \) -exec basename {} \;
echo ""
echo -e "${GREEN}Ready for release! 🚀${NC}"
