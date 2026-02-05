#!/bin/bash
# build.sh - Automated Build Script for LinuxCloud Sync
# ======================================================
# This script downloads rclone, installs dependencies, and builds a standalone executable.
# Automatically detects CPU architecture (AMD64, ARM64, ARM, 386)
#
# Version: 1.0.1 (Enhanced)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Detect CPU architecture
detect_architecture() {
    local ARCH=$(uname -m)
    local RCLONE_ARCH=""
    local PKG_ARCH=""
    
    case "$ARCH" in
        x86_64|amd64)
            RCLONE_ARCH="amd64"
            PKG_ARCH="amd64"
            ;;
        aarch64|arm64)
            RCLONE_ARCH="arm64"
            PKG_ARCH="arm64"
            ;;
        armv7l|armv6l|arm)
            RCLONE_ARCH="arm"
            PKG_ARCH="armhf"
            ;;
        i386|i686)
            RCLONE_ARCH="386"
            PKG_ARCH="i386"
            ;;
        *)
            echo -e "${RED}❌ Unsupported architecture: $ARCH${NC}"
            echo -e "${YELLOW}Supported: x86_64, aarch64, armv7l, i386${NC}"
            exit 1
            ;;
    esac
    
    echo "$RCLONE_ARCH|$PKG_ARCH"
}

# Get architecture
ARCH_INFO=$(detect_architecture)
RCLONE_ARCH=$(echo $ARCH_INFO | cut -d'|' -f1)
PKG_ARCH=$(echo $ARCH_INFO | cut -d'|' -f2)

# Configuration
VERSION_FILE=".build_version"
DEFAULT_VERSION="1.0.1"
if [ -f "${VERSION_FILE}" ]; then
    DEFAULT_VERSION="$(cat "${VERSION_FILE}")"
fi

# Read from TTY if possible to avoid piping output into version input
if [ -r /dev/tty ]; then
    printf "Enter version [%s]: " "${DEFAULT_VERSION}" > /dev/tty
    if read -r APP_VERSION < /dev/tty; then
        APP_VERSION="${APP_VERSION:-$DEFAULT_VERSION}"
    else
        APP_VERSION="${DEFAULT_VERSION}"
    fi
else
    read -r -p "Enter version [${DEFAULT_VERSION}]: " APP_VERSION || true
    APP_VERSION="${APP_VERSION:-$DEFAULT_VERSION}"
fi
echo "${APP_VERSION}" > "${VERSION_FILE}"

# Update README/changelog versions if present
update_docs_version() {
    local version="$1"
    local major="${version%%.*}"

    if [ -f "README.md" ]; then
        # Badge
        sed -i -E "s/version-[0-9]+(\\.[0-9]+)*-blue/version-${version}-blue/" README.md || true
        # vX.x headings
        sed -i -E "s/v[0-9]+\\.x/v${major}.x/g" README.md || true
        # Highlights header
        sed -i -E "s/v[0-9]+\\.[0-9]+\\.[0-9]+ Highlights/v${version} Highlights/" README.md || true
        # Version comparison column header (keep v1.0.2)
        sed -i -E "s/\\| v1\\.0\\.2 \\| v[0-9]+\\.[0-9]+\\.[0-9]+ \\|/| v1.0.2 | v${version} |/" README.md || true
        # Footer version line
        sed -i -E "s/\\*\\*Version:\\*\\* [0-9]+\\.[0-9]+\\.[0-9]+ Professional Edition/\\*\\*Version:\\*\\* ${version} Professional Edition/" README.md || true
    fi

    if [ -f "changelog/CHANGELOG.md" ]; then
        sed -i -E "s/\\*\\*Current Version:\\*\\* [0-9]+\\.[0-9]+\\.[0-9]+/\\*\\*Current Version:\\*\\* ${version}/" changelog/CHANGELOG.md || true
    fi
}

update_docs_version "${APP_VERSION}"

RCLONE_VERSION="v1.65.2"
RCLONE_URL="https://downloads.rclone.org/${RCLONE_VERSION}/rclone-${RCLONE_VERSION}-linux-${RCLONE_ARCH}.zip"
RCLONE_ZIP="rclone-${RCLONE_VERSION}-linux-${RCLONE_ARCH}.zip"
APP_NAME="lcs"
BUILD_DIR="build"
DIST_DIR="dist"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  LinuxCloud Sync - Standalone Build System                ║${NC}"
echo -e "${BLUE}║  Building zero-dependency executable...                   ║${NC}"
echo -e "${BLUE}║  Version: ${APP_VERSION} (Enhanced)                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}System Information:${NC}"
echo -e "${CYAN}  • CPU Architecture: ${NC}$(uname -m)"
echo -e "${CYAN}  • Rclone Architecture: ${NC}${RCLONE_ARCH}"
echo -e "${CYAN}  • Package Architecture: ${NC}${PKG_ARCH}"
echo -e "${CYAN}  • Operating System: ${NC}$(uname -s)"
echo -e "${CYAN}  • Python Version: ${NC}$(python3 --version 2>/dev/null || echo 'Not found')"
echo ""

# Step 1: Clean previous builds
echo -e "${YELLOW}[1/6] Cleaning previous builds...${NC}"
rm -rf ${BUILD_DIR} ${DIST_DIR} bin/ *.spec __pycache__
mkdir -p bin
echo -e "${GREEN}✓ Clean complete${NC}"
echo ""

# Step 2: Download rclone binary
echo -e "${YELLOW}[2/6] Downloading rclone ${RCLONE_VERSION}...${NC}"
if [ ! -f "${RCLONE_ZIP}" ]; then
    wget -q --show-progress --timeout=30 --tries=3 "${RCLONE_URL}" || {
        echo -e "${RED}❌ Failed to download rclone after 3 attempts${NC}"
        echo -e "${YELLOW}Please check your internet connection and try again${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Download complete${NC}"
else
    echo -e "${GREEN}✓ Using cached rclone archive${NC}"
fi
echo ""

# Step 3: Extract rclone binary
echo -e "${YELLOW}[3/6] Extracting rclone binary...${NC}"
unzip -q -o "${RCLONE_ZIP}" "rclone-${RCLONE_VERSION}-linux-${RCLONE_ARCH}/rclone" -d . || {
    echo -e "${RED}❌ Failed to extract rclone${NC}"
    exit 1
}
mv "rclone-${RCLONE_VERSION}-linux-${RCLONE_ARCH}/rclone" bin/
rmdir "rclone-${RCLONE_VERSION}-linux-${RCLONE_ARCH}"
chmod +x bin/rclone
echo -e "${GREEN}✓ Extracted to bin/rclone${NC}"

# Verify rclone
RCLONE_VER=$(./bin/rclone version | head -n1)
echo -e "${GREEN}✓ ${RCLONE_VER}${NC}"
echo ""

# Step 4: Install Python dependencies
echo -e "${YELLOW}[4/6] Installing Python dependencies...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ Python $REQUIRED_VERSION or higher required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv || {
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        exit 1
    }
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null || {
    echo -e "${YELLOW}⚠ pip upgrade failed, continuing anyway...${NC}"
}

# Install required packages
echo -e "${BLUE}Installing required packages...${NC}"
pip install -q customtkinter pyinstaller pillow || {
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    echo -e "${YELLOW}Try: pip install customtkinter pyinstaller pillow${NC}"
    exit 1
}

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 5: Build executable with PyInstaller
echo -e "${YELLOW}[5/6] Building standalone executable...${NC}"
echo -e "${BLUE}This may take 2-3 minutes...${NC}"

pyinstaller \
    --name="${APP_NAME}" \
    --onefile \
    --windowed \
    --add-binary="bin/rclone:bin" \
    --add-data=".build_version:." \
    --hidden-import="PIL._tkinter_finder" \
    --collect-all=customtkinter \
    --icon=NONE \
    --clean \
    main.py > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful${NC}"
else
    echo -e "${RED}❌ Build failed${NC}"
    echo -e "${YELLOW}Check build.log for details${NC}"
    exit 1
fi
echo ""

# Step 6: Verify and finalize
echo -e "${YELLOW}[6/6] Finalizing build...${NC}"

if [ -f "dist/${APP_NAME}" ]; then
    chmod +x "dist/${APP_NAME}"
    FILE_SIZE=$(du -h "dist/${APP_NAME}" | cut -f1)
    
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  BUILD COMPLETED SUCCESSFULLY! 🎉                          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📦 Executable Location:${NC} dist/${APP_NAME}"
    echo -e "${BLUE}📊 File Size:${NC} ${FILE_SIZE}"
    echo -e "${BLUE}🏗️  Architecture:${NC} ${PKG_ARCH}"
    echo -e "${BLUE}🚀 To Run:${NC} ./dist/${APP_NAME}"
    echo ""
    echo -e "${YELLOW}📝 Next Steps:${NC}"
    echo -e "   1. Test: ${BLUE}./dist/${APP_NAME}${NC}"
    echo -e "   2. Build DEB: ${BLUE}./build_deb.sh${NC}"
    echo -e "   3. Install: ${BLUE}sudo dpkg -i github.cryptd777.linuxcloudsync_*.deb${NC}"
    echo ""
    echo -e "${CYAN}Troubleshooting:${NC}"
    echo -e "   • If sync doesn't work, ensure rclone is configured:"
    echo -e "     ${BLUE}./dist/${APP_NAME}${NC} then click 'Connect Google Drive'"
    echo -e "   • Check logs at: ${BLUE}~/.config/linuxcloudsync/logs/${NC}"
    echo ""
else
    echo -e "${RED}❌ Build failed - executable not found${NC}"
    exit 1
fi

deactivate
