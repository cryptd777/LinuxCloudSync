#!/bin/bash
# build_deb.sh - DEB Package Builder for LinuxCloud Sync
# =======================================================
# Creates a production-ready .deb package for Debian/Ubuntu systems
# Automatically detects CPU architecture (AMD64, ARM64, ARMHF, i386)
#
# Version: 1.0.1 (Enhanced)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Detect CPU architecture for DEB package
detect_deb_architecture() {
    local ARCH=$(uname -m)
    local DEB_ARCH=""
    
    case "$ARCH" in
        x86_64|amd64)
            DEB_ARCH="amd64"
            ;;
        aarch64|arm64)
            DEB_ARCH="arm64"
            ;;
        armv7l|armv6l|arm)
            DEB_ARCH="armhf"
            ;;
        i386|i686)
            DEB_ARCH="i386"
            ;;
        *)
            echo -e "${RED}❌ Unsupported architecture: $ARCH${NC}"
            echo -e "${YELLOW}Supported: x86_64, aarch64, armv7l, i386${NC}"
            exit 1
            ;;
    esac
    
    echo "$DEB_ARCH"
}

# Get architecture
PKG_ARCH=$(detect_deb_architecture)

# Package information
VERSION_FILE=".build_version"
DEFAULT_VERSION="1.0.1"
if [ -f "${VERSION_FILE}" ]; then
    DEFAULT_VERSION="$(cat "${VERSION_FILE}")"
fi

# Read from TTY if possible to avoid piping output into version input
if [ -r /dev/tty ]; then
    printf "Enter package version [%s]: " "${DEFAULT_VERSION}" > /dev/tty
    if read -r PKG_VERSION < /dev/tty; then
        PKG_VERSION="${PKG_VERSION:-$DEFAULT_VERSION}"
    else
        PKG_VERSION="${DEFAULT_VERSION}"
    fi
else
    read -r -p "Enter package version [${DEFAULT_VERSION}]: " PKG_VERSION || true
    PKG_VERSION="${PKG_VERSION:-$DEFAULT_VERSION}"
fi
echo "${PKG_VERSION}" > "${VERSION_FILE}"

PKG_NAME="github.cryptd777.linuxcloudsync"
PKG_MAINTAINER="LinuxCloudSync Team <support@linuxcloudsync.org>"
PKG_DESCRIPTION="Zero-dependency cloud storage sync client for Linux"
PKG_HOMEPAGE="https://github.com/cryptd777/LinuxCloudSync"

# Directories
DEB_DIR="deb_build"
PKG_DIR="${DEB_DIR}/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  LinuxCloud Sync - DEB Package Builder                    ║${NC}"
echo -e "${BLUE}║  Creating installable Debian package...                   ║${NC}"
echo -e "${BLUE}║  Version: ${PKG_VERSION} (Enhanced)                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Package Information:${NC}"
echo -e "${CYAN}  • CPU Architecture: ${NC}$(uname -m)"
echo -e "${CYAN}  • DEB Architecture: ${NC}${PKG_ARCH}"
echo -e "${CYAN}  • Package Version: ${NC}${PKG_VERSION}"
echo ""

# Step 1: Check if executable exists
echo -e "${YELLOW}[1/7] Checking for executable...${NC}"
if [ ! -f "dist/lcs" ]; then
    echo -e "${RED}❌ Executable not found!${NC}"
    echo -e "${YELLOW}Please run ./build.sh first${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Executable found${NC}"
echo ""

# Step 2: Clean previous DEB builds
echo -e "${YELLOW}[2/7] Cleaning previous DEB builds...${NC}"
rm -rf ${DEB_DIR} ${PKG_NAME}_*.deb
echo -e "${GREEN}✓ Clean complete${NC}"
echo ""

# Step 3: Create DEB directory structure
echo -e "${YELLOW}[3/7] Creating DEB directory structure...${NC}"
mkdir -p ${PKG_DIR}/DEBIAN
chmod 755 ${PKG_DIR}/DEBIAN
mkdir -p ${PKG_DIR}/usr/bin
mkdir -p ${PKG_DIR}/usr/share/applications
mkdir -p ${PKG_DIR}/usr/share/pixmaps
mkdir -p ${PKG_DIR}/usr/share/doc/${PKG_NAME}
mkdir -p ${PKG_DIR}/usr/share/man/man1
echo -e "${GREEN}✓ Directory structure created${NC}"
echo ""

# Step 4: Copy executable
echo -e "${YELLOW}[4/7] Copying executable...${NC}"
cp dist/lcs ${PKG_DIR}/usr/bin/lcs
chmod 755 ${PKG_DIR}/usr/bin/lcs
ln -sf lcs ${PKG_DIR}/usr/bin/linuxcloudsync
echo -e "${GREEN}✓ Executable copied${NC}"
echo ""

# Step 5: Create control file
echo -e "${YELLOW}[5/7] Creating package metadata...${NC}"
cat > ${PKG_DIR}/DEBIAN/control << EOF
Package: ${PKG_NAME}
Version: ${PKG_VERSION}
Section: net
Priority: optional
Architecture: ${PKG_ARCH}
Maintainer: ${PKG_MAINTAINER}
Homepage: ${PKG_HOMEPAGE}
Depends: libgtk-3-0, libglib2.0-0
Installed-Size: $(du -sk ${PKG_DIR}/usr/bin/lcs | cut -f1)
Description: ${PKG_DESCRIPTION}
 LinuxCloud Sync is a standalone GUI application for syncing files
 with Google Drive and OneDrive on Linux systems. It requires no
 external dependencies or configuration - just install and run.
 .
 Features:
  * Zero-dependency installation
  * Bidirectional sync support (using rclone bisync)
  * Google Drive sync support
  * OneDrive sync support
  * Modern GTK-based interface
  * Embedded rclone engine
  * Secure credential storage
EOF

echo -e "${GREEN}✓ Control file created${NC}"
echo ""

# Step 6: Create desktop entry
echo -e "${YELLOW}[6/7] Creating desktop integration...${NC}"
cat > ${PKG_DIR}/usr/share/applications/linuxcloudsync.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=LinuxCloud Sync
GenericName=Cloud Storage Sync
Comment=Sync files with Google Drive and OneDrive
Exec=/usr/bin/lcs
Icon=linuxcloudsync
Terminal=false
Categories=Network;FileTransfer;Utility;
Keywords=cloud;sync;gdrive;onedrive;rclone;backup;
StartupNotify=true
EOF

# Install icon (SVG preferred, fallback to simple XPM)
if [ -f "assets/linuxcloudsync.svg" ]; then
    cp assets/linuxcloudsync.svg ${PKG_DIR}/usr/share/pixmaps/linuxcloudsync.svg
else
    cat > ${PKG_DIR}/usr/share/pixmaps/linuxcloudsync.xpm << 'EOF'
/* XPM */
static char * linuxcloudsync_xpm[] = {
"32 32 3 1",
" 	c None",
".	c #0284C7",
"+	c #FFFFFF",
"                                ",
"                                ",
"          ........              ",
"        ..+++++++...            ",
"       .+++++++++++.            ",
"      .++++....++++.            ",
"     .++++.    .+++.            ",
"     .+++.      .++.            ",
"     .+++.       ..             ",
"     .+++.                      ",
"     .++++.                     ",
"      .++++....                 ",
"       .++++++++..              ",
"        ..+++++++..             ",
"          ........              ",
"                                ",
"       ................         ",
"      .++++++++++++++++.        ",
"     .++++++++++++++++++.       ",
"    .+++++..........+++++.      ",
"    .++++.          .++++.      ",
"    .++++.          .++++.      ",
"    .++++.          .++++.      ",
"    .+++++..........+++++.      ",
"     .++++++++++++++++++.       ",
"      .++++++++++++++++.        ",
"       ................         ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                "};
EOF
fi

# Create README
cat > ${PKG_DIR}/usr/share/doc/${PKG_NAME}/README << EOF
LinuxCloud Sync - Cloud Storage Sync Client
============================================

VERSION: ${PKG_VERSION}

DESCRIPTION:
LinuxCloud Sync is a standalone application for syncing files with
Google Drive and OneDrive on Linux systems using bidirectional sync.

USAGE:
  Launch from application menu: Applications → Internet → LinuxCloud Sync
  Or run from terminal: lcs

CONFIGURATION:
  On first run, use the "Connect Google Drive" or "Connect OneDrive"
  buttons to set up your cloud storage accounts. Follow the on-screen
  instructions to authorize access via your web browser.

  Configuration is stored in: ~/.config/linuxcloudsync/
  Logs are stored in: ~/.config/linuxcloudsync/logs/

SYNCING:
  1. Click "Connect Google Drive" or "Connect OneDrive" to set up your account
  2. After configuration, click "List Configured Remotes" to see your remotes
  3. Enter the remote name (e.g., "gdrive:") in the Remote field
  4. Select a local folder to sync
  5. Click "Start Sync" to begin bidirectional synchronization

  Note: The first sync may take longer as it establishes the sync baseline.
  Subsequent syncs will be faster, only transferring changed files.

TROUBLESHOOTING:
  • If sync fails, check the logs at ~/.config/linuxcloudsync/logs/
  • Ensure you have internet connectivity
  • Verify your remote is configured: click "List Configured Remotes"
  • For first-time sync, you may need to initialize: the app will prompt you

SUPPORT:
  Website: ${PKG_HOMEPAGE}
  Issues: ${PKG_HOMEPAGE}/issues

LICENSE:
  This software is provided as-is without warranty.
  See /usr/share/doc/${PKG_NAME}/copyright for details.
EOF

# Create changelog
cat > ${PKG_DIR}/usr/share/doc/${PKG_NAME}/changelog << EOF
${PKG_NAME} (${PKG_VERSION}) stable; urgency=medium

  * Security enhancements (fixed command injection vulnerability)
  * Improved error handling and logging
  * Added bidirectional sync support (rclone bisync)
  * Fixed sync initialization issues
  * Added input validation for paths and remotes
  * Improved thread safety for UI updates
  * Enhanced build scripts with better error checking
  * Added comprehensive logging to ~/.config/linuxcloudsync/logs/

 -- ${PKG_MAINTAINER}  $(date -R)

${PKG_NAME} (1.0.0) stable; urgency=low

  * Initial release
  * Google Drive sync support
  * OneDrive sync support
  * Zero-dependency installation
  * Modern GTK interface

 -- ${PKG_MAINTAINER}  $(date -R)
EOF

gzip -9 ${PKG_DIR}/usr/share/doc/${PKG_NAME}/changelog

# Create man page
cat > ${PKG_DIR}/usr/share/man/man1/lcs.1 << EOF
.TH LCS 1 "$(date +%Y-%m-%d)" "LinuxCloud Sync ${PKG_VERSION}" "User Commands"
.SH NAME
lcs \- Cloud storage sync client for Linux
.SH SYNOPSIS
.B lcs
.SH DESCRIPTION
LinuxCloud Sync is a standalone GUI application for syncing files with Google Drive and OneDrive on Linux systems. It provides a modern interface with zero external dependencies and uses bidirectional synchronization to keep your files in sync.
.SH FEATURES
.IP \[bu] 2
Bidirectional sync (using rclone bisync)
.IP \[bu]
Google Drive and OneDrive support
.IP \[bu]
Zero external dependencies
.IP \[bu]
Secure credential storage
.IP \[bu]
Automatic conflict resolution
.IP \[bu]
Progress monitoring and logging
.SH FILES
.I ~/.config/linuxcloudsync/
.RS
User configuration directory
.RE
.I ~/.config/linuxcloudsync/rclone.conf
.RS
Cloud storage credentials and settings
.RE
.I ~/.config/linuxcloudsync/logs/
.RS
Application logs
.RE
.SH EXAMPLES
.TP
  Launch the application:
.B lcs
.TP
View logs:
.B tail -f ~/.config/linuxcloudsync/logs/linuxcloudsync.log
.SH AUTHOR
${PKG_MAINTAINER}
.SH SEE ALSO
rclone(1)
EOF

gzip -9 ${PKG_DIR}/usr/share/man/man1/lcs.1

# Create copyright file
cat > ${PKG_DIR}/usr/share/doc/${PKG_NAME}/copyright << EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: github.cryptd777.linuxcloudsync
Source: ${PKG_HOMEPAGE}

Files: *
Copyright: $(date +%Y) LinuxCloudSync Team
License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.

Files: bin/rclone
Copyright: 2012-2024 Nick Craig-Wood and contributors
License: MIT
 Rclone is licensed under the MIT License.
 See https://github.com/rclone/rclone/blob/master/COPYING for details.
EOF

# Create postinst script (runs after installation)
cat > ${PKG_DIR}/DEBIAN/postinst << 'EOF'
#!/bin/bash
set -e

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q
fi

# Update icon cache
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/pixmaps 2>/dev/null || true
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  LinuxCloud Sync installed successfully!                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Launch from: Applications → Internet → LinuxCloud Sync"
echo "Or run: lcs"
echo ""
echo "First time setup:"
echo "  1. Launch the application"
echo "  2. Click 'Connect Google Drive' or 'Connect OneDrive'"
echo "  3. Follow the authorization prompts in your browser"
echo "  4. Select folders to sync"
echo ""
echo "Logs: ~/.config/linuxcloudsync/logs/linuxcloudsync.log"
echo ""

exit 0
EOF

chmod 755 ${PKG_DIR}/DEBIAN/postinst

# Create postrm script (runs after uninstallation)
cat > ${PKG_DIR}/DEBIAN/postrm << 'EOF'
#!/bin/bash
set -e

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q
fi

# Note: We don't remove ~/.config/linuxcloudsync to preserve user data
echo ""
echo "LinuxCloud Sync has been removed."
echo "User configuration preserved at: ~/.config/linuxcloudsync/"
echo "To completely remove: rm -rf ~/.config/linuxcloudsync"
echo ""

exit 0
EOF

chmod 755 ${PKG_DIR}/DEBIAN/postrm

echo -e "${GREEN}✓ Desktop integration created${NC}"
echo ""

# Step 7: Build DEB package
echo -e "${YELLOW}[7/7] Building DEB package...${NC}"
dpkg-deb --build --root-owner-group ${PKG_DIR} 2>&1 | grep -v "warning: ignoring"

# Move to current directory
DEB_FILE="${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"
mv ${DEB_DIR}/${DEB_FILE} .

FILE_SIZE=$(du -h ${DEB_FILE} | cut -f1)

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  DEB PACKAGE CREATED SUCCESSFULLY! 📦                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📦 Package:${NC} ${DEB_FILE}"
echo -e "${BLUE}📊 Size:${NC} ${FILE_SIZE}"
echo -e "${BLUE}🏗️  Architecture:${NC} ${PKG_ARCH}"
echo -e "${BLUE}📋 Version:${NC} ${PKG_VERSION}"
echo ""
echo -e "${YELLOW}Installation Instructions:${NC}"
echo -e "  ${BLUE}sudo dpkg -i ${DEB_FILE}${NC}"
echo -e "  ${BLUE}sudo apt-get install -f${NC}  ${YELLOW}# If dependencies are missing${NC}"
echo ""
echo -e "${YELLOW}Verification:${NC}"
echo -e "  ${BLUE}dpkg -c ${DEB_FILE}${NC}  ${YELLOW}# List contents${NC}"
echo -e "  ${BLUE}dpkg -I ${DEB_FILE}${NC}  ${YELLOW}# Show info${NC}"
echo ""
echo -e "${YELLOW}Uninstallation:${NC}"
echo -e "  ${BLUE}sudo apt remove ${PKG_NAME}${NC}"
echo ""

# Cleanup build directory
rm -rf ${DEB_DIR}
echo -e "${GREEN}✓ Cleanup complete${NC}"
