# LinuxCloud Sync - Professional Edition

![Version](https://img.shields.io/badge/version-0.0.3-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)

**Professional cloud storage sync client for Linux with advanced features**
Release date: 2026-02-05
First public release: v0.0.3

## 🎉 What's New in v0.x

### Major Features
- ✨ **Sync Profiles** - Save and load sync configurations
- 🎨 **Tabbed Interface** - Clean, organized 4-tab layout
- 🚀 **3 Sync Modes** - Bidirectional, Cloud→Local, Local→Cloud
- 🔄 **Force Resync Button** - One-click fix for bisync errors
- 📊 **Progress Bar** - Visual sync feedback
- ⚙️ **Advanced Options** - Bandwidth, dry-run, exclude patterns

### The Fix You Needed
**One-click solution for:** `ERROR: Bisync critical error: cannot find prior listings`

Just click the **"Force Resync"** button! No command-line needed.

## 📦 Download & Install (Recommended)

### Debian/Ubuntu (.deb)
1. Download the latest `.deb` from GitHub Releases.
2. Install:
```bash
sudo dpkg -i github.cryptd777.linuxcloudsync_*.deb
sudo apt-get install -f  # If dependencies are missing
```

### Build From Source
```bash
chmod +x build.sh && ./build.sh
./dist/lcs
```

```bash
# Download and install (example)
wget https://github.com/cryptd777/LinuxCloudSync/releases/latest/download/github.cryptd777.linuxcloudsync_amd64.deb
sudo dpkg -i github.cryptd777.linuxcloudsync_amd64.deb
```

## 🚀 Quick Start

1. **Launch:** `lcs`
2. **Connect:** Click "Connect Google Drive" or "Connect OneDrive"
3. **Setup:**
   - Remote: `gdrive:`
   - Local: Select folder
4. **Fix Baseline:** Click "Force Resync" (first time)
5. **Sync:** Click "Start Sync"
6. **Save:** Click "Save Profile" for easy reuse

## ✨ Features

### Core Features
- ✅ Bidirectional sync with Google Drive & OneDrive
- ✅ Zero dependencies (bundles rclone v1.65.2)
- ✅ Secure credential storage (0600 permissions)
- ✅ Cross-architecture (AMD64, ARM64, ARMHF, i386)
- ✅ One-click DEB installation

### New in v0.x
- ✅ **Sync Profiles** - Save configurations, load instantly
- ✅ **Multiple Sync Modes** - Choose your workflow
- ✅ **Bandwidth Control** - Limit upload/download speed
- ✅ **Dry Run Mode** - Preview changes first
- ✅ **File Exclusion** - Skip patterns like `*.tmp`, `.git/`
- ✅ **Force Resync** - Fix bisync errors with one click
- ✅ **Progress Tracking** - Visual progress bar
- ✅ **Enhanced Logging** - Timestamps, better messages
- ✅ **Built-in Help** - About tab with quick start
- ✅ **Updated Packaging** - New package name + `lcs` command

## 🎯 Solving Your Error

### The Bisync Error You're Seeing

```
2026/02/04 22:49:14 NOTICE: bisync is EXPERIMENTAL
2026/02/04 22:49:14 ERROR: Bisync critical error: cannot find prior Path1 or Path2 listings
2026/02/04 22:49:14 ERROR: Bisync aborted. Error is retryable without --resync
```

### Solution (3 Ways)

**Method 1: Force Resync Button** (Easiest!)
1. In the app, click **"Force Resync"** button
2. Confirm the prompt
3. Wait ~10-30 seconds
4. Click "Start Sync" normally
5. ✅ Done!

**Method 2: Profiles Tab**
1. Save your current setup as a profile
2. It remembers everything
3. Load profile anytime
4. First time? Use Force Resync

**Method 3: Command Line** (if app not working)
```bash
~/.local/bin/lcs  # Or wherever installed
# Then use Force Resync button in GUI
```

## ✅ Do & Don’t

### Do
- ✅ Use **Force Resync** the first time you run bisync
- ✅ Let Force Resync finish to create the baseline
- ✅ Start with a **test folder** before syncing large directories
- ✅ Keep your system time accurate (NTP enabled)
- ✅ Save a profile once everything works

### Don’t
- ❌ Don’t stop Force Resync before it completes
- ❌ Don’t edit files on both sides during the first sync
- ❌ Don’t use bisync on production data without a backup
- ❌ Don’t place local sync folders outside your home, `/mnt`, or `/media`

## 📖 Documentation
### Tabs Explained

**1. Sync Tab**
- Main sync configuration
- Connect cloud storage
- Start/Stop sync
- Force Resync button
- Save profiles

**2. Profiles Tab**
- View saved profiles
- Load with one click
- Delete old profiles
- Manage configurations

**3. Advanced Tab**
- Bandwidth limiting
- Dry run mode
- Exclude patterns
- Log level control
- Custom rclone flags

**4. About Tab**
- Quick start guide
- Troubleshooting help
- Open log folder
- Open config folder
- Version info

### Sync Modes

**Bidirectional (bisync)** - Default
- Changes sync both ways
- Cloud → Local ✅
- Local → Cloud ✅
- Best for: Active work folders

**Cloud to Local (copy)**
- Download only
- Cloud → Local ✅
- Local → Cloud ❌
- Best for: Backups, archives

**Local to Cloud (copy)**
- Upload only
- Cloud → Local ❌
- Local → Cloud ✅
- Best for: Backup to cloud

## 🔧 Advanced Features

### Bandwidth Limiting
Control sync speed to prevent network saturation:
- `1M` = 1 MB/s
- `500K` = 500 KB/s
- `10M` = 10 MB/s

### Dry Run Mode
Preview changes without actual syncing:
1. Enable in Advanced tab
2. Run sync
3. Check log for what would happen
4. Disable to actually sync

### Exclude Patterns
Skip files/folders you don't want synced:
```
*.tmp         # Temporary files
*.log         # Log files
.git/         # Git repositories  
node_modules/ # Node.js packages
__pycache__/  # Python cache
```

## 📁 File Locations

```
~/.config/linuxcloudsync/
├── rclone.conf       # Cloud credentials (KEEP SAFE!)
├── profiles.json     # Saved sync profiles
├── last_profile.txt  # Auto-load last used
└── logs/
    └── linuxcloudsync.log  # Detailed logs
```

## 🐛 Troubleshooting

### Bisync Error?
→ Click "Force Resync" button

### Remote Not Found?
→ Click "Connect Google Drive/OneDrive" first

### Permission Denied?
→ Select folder in /home, /mnt, or /media

### Too Fast/Slow?
→ Set bandwidth limit in Advanced tab

### Want to Test First?
→ Enable "Dry Run" in Advanced tab

## 📌 Notes for Releases
- Always download the **latest** `.deb` from GitHub Releases.
- If you build from source, the app version follows `.build_version`.

## ❤️ Credits
Made with love by cryptd.

### Need Logs?
→ Click "Open Log Folder" in About tab

## 🔒 Security

- ✅ Input validation (prevents command injection)
- ✅ Path restrictions (safe directories only)
- ✅ Secure permissions (0600 on credentials)
- ✅ Thread-safe operations
- ✅ Proper cleanup on exit

## 🏗️ Building

```bash
# Prerequisites
sudo apt install python3 python3-venv python3-pip wget unzip

# Build
chmod +x build.sh
./build.sh

# Run
./dist/lcs

# Create DEB (optional)
chmod +x build_deb.sh
./build_deb.sh
sudo dpkg -i github.cryptd777.linuxcloudsync_*.deb
```

## 🧾 Version History

- **v0.0.3** — First public release (2026-02-05)

See [changelog/CHANGELOG.md](changelog/CHANGELOG.md) for detailed history and internal pre-release notes.

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- [rclone](https://rclone.org/) - Sync engine
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI
- [PyInstaller](https://pyinstaller.org/) - Bundling

## 📞 Support

- **Docs:** This file + About tab in app
- **Logs:** Click "Open Log Folder" in app
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions

---

**Made with ❤️ for the Linux community**

**Version:** 0.0.3 Professional Edition  
**Released:** February 5, 2026  
**Status:** Production Ready ✅
