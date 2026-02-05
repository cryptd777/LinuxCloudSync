# Changelog - LinuxCloud Sync

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.2] - 2026-02-05 - PACKAGING & UX UPDATE

### ✨ Improvements
- App version now reads from `.build_version`
- About tab shows current version, release date, and credits
- Clickable GitHub link + download button added to About tab
- Force Resync can be stopped safely
- Stale bisync lock files can be cleared before runs
- New package name: `github.cryptd777.linuxcloudsync`
- New command: `lcs` (with `linuxcloudsync` symlink for compatibility)
- Added simple SVG app icon for packaging

---

## [2.0.0] - 2024-02-04 - MAJOR FEATURE RELEASE

### 🎉 Major Features Added

#### **New UI with Tabs**
- **Tabbed interface** with 4 tabs: Sync, Profiles, Advanced, About
- Modern, professional layout with better organization
- **Progress bar** showing sync status visually
- Enhanced status indicators with timestamps
- Larger window (900x700) for better usability

#### **Sync Profiles System** ✨
- **Save sync configurations** as reusable profiles
- **Load profiles** with one click
- **Delete profiles** you no longer need
- Profiles stored in `~/.config/linuxcloudsync/profiles.json`
- Auto-load last used profile on startup

#### **Advanced Sync Options** 🚀
- **3 Sync Modes:**
  1. Bidirectional (bisync) - Two-way sync
  2. Cloud to Local (copy) - Download only
  3. Local to Cloud (copy) - Upload only
- **Bandwidth limiting** - Control upload/download speed
- **Dry run mode** - Preview changes without syncing
- **Exclude patterns** - Skip specific files/folders
- **Custom rclone flags** - Power user options
- **Log level control** - ERROR, WARNING, INFO, DEBUG

#### **Force Resync Button** 🔄
- **ONE-CLICK FIX** for "bisync aborted" error
- Rebuilds baseline automatically
- No command-line needed
- Prevents data loss

### 🐛 Critical Bug Fixes

#### **Fixed: Bisync Baseline Error**
- **Issue:** `ERROR: Bisync critical error: cannot find prior Path1 or Path2 listings`
- **Solution:** Added "Force Resync" button to rebuild baseline
- **Impact:** Users can now recover from sync errors without terminal

#### **Fixed: Bisync Flag Compatibility**
- Removed `--compare` flag (not in rclone v1.65.2)
- Removed `--slow-hash-sync-only` (not needed)
- **Result:** Bisync now works reliably

### ✨ Enhancements

#### **Better User Guidance**
- Helpful tooltips and instructions
- Clear error messages with solutions
- About tab with quick start guide
- Integrated troubleshooting help

#### **Improved Logging**
- Timestamps on all log entries `[HH:MM:SS]`
- Color-coded status indicators
- Better error reporting
- Log level configuration

#### **File Management**
- "Open Log Folder" button
- "Open Config Folder" button
- Easy access to configuration files

### 🔒 Security (Preserved from v1.0.x)
- Input validation for remote names ✅
- Path restriction to safe directories ✅
- Secure config file permissions (0600) ✅
- Thread-safe UI updates ✅
- Proper process termination ✅

### 📊 Performance
- Efficient profile storage (JSON)
- Faster UI updates with progress tracking
- Better resource cleanup
- Optimized threading

### 🎨 UI/UX Improvements
- Professional tabbed layout
- Better button organization
- Visual progress indicator
- Larger, more readable interface
- Emoji icons for better navigation
- Consistent color scheme

### 📝 Documentation
- Comprehensive About tab
- Inline help text
- Quick start guide
- Troubleshooting section

### 🔧 Technical Changes
- Upgraded to CustomTkinter latest patterns
- Enhanced utils.py with profile management
- JSON-based configuration storage
- Modular tab creation system
- Improved error handling throughout

### 📦 New Files
```
~/.config/linuxcloudsync/
├── rclone.conf         # Cloud credentials
├── profiles.json       # Saved sync profiles (NEW)
├── last_profile.txt    # Last used profile (NEW)
└── logs/
    └── linuxcloudsync.log
```

### 🚀 Migration from v1.x

**Automatic migration** - No action needed!
- Existing `rclone.conf` preserved
- All cloud connections work as before
- Old sync configurations can be saved as profiles

**Recommended steps:**
1. Install v2.0.0
2. Your existing remote is already configured
3. Fill in remote and local folder
4. Click "Save Profile" to save for future use
5. Use "Force Resync" if you see bisync errors

### ⚠️ Breaking Changes
**NONE** - Fully backward compatible with v1.0.x

### 🎯 Upgrade Highlights

| Feature | v1.0.2 | v2.0.0 |
|---------|---------|---------|
| UI Layout | Single page | 4 tabs |
| Sync Profiles | ❌ No | ✅ Yes |
| Sync Modes | 1 (bisync) | 3 modes |
| Bandwidth Limit | ❌ No | ✅ Yes |
| Dry Run | ❌ No | ✅ Yes |
| Exclude Patterns | ❌ No | ✅ Yes |
| Force Resync | ❌ No | ✅ One-click |
| Progress Bar | ❌ No | ✅ Yes |
| About/Help | ❌ No | ✅ Built-in |
| Window Size | 800x600 | 900x700 |

### 📈 Statistics
- **Lines of Code:** ~1200 (was ~650)
- **New Features:** 12
- **Bug Fixes:** 2 critical
- **UI Improvements:** 15+
- **User-Facing Options:** 10+

---

## [1.0.2] - 2024-02-04 - Bisync Compatibility Hotfix

### 🐛 Fixed
- **Critical:** Removed `--compare` flag incompatible with rclone v1.65.2
- **Critical:** Removed `--slow-hash-sync-only` flag (not needed)
- Simplified bisync command to use only supported flags

### 📝 Changed
- Enhanced error messages for bisync initialization
- Improved first-time sync guidance

---

## [1.0.1] - 2024-02-04 - Security & Stability Release

### 🔒 Security
- **Critical:** Fixed command injection vulnerability (CWE-78)
- **Critical:** Fixed race condition in process termination (CWE-362)
- **Critical:** Fixed thread safety violations (CWE-662)
- Added input validation for remote names
- Added path validation to prevent directory traversal
- Implemented secure file permissions (0600/0700)

### 🐛 Fixed
- **Critical:** Changed from one-way sync to bidirectional (rclone bisync)
- **Critical:** Thread-safe UI updates using `self.after()`
- **Critical:** Proper process termination with wait/timeout
- Fixed file permission errors on read-only filesystems
- Fixed resource leaks (stdout cleanup)
- Fixed potential infinite loops

### ✨ Added
- Comprehensive logging system with rotation
- XDG Base Directory specification compliance
- Timeout protection (1 hour default)
- Network timeout for downloads (30s, 3 retries)
- Better error messages and guidance

### 📝 Documentation
- Added QUICKSTART.md
- Added INSTALL.md  
- Added comprehensive README.md
- Added CHANGELOG.md

---

## [1.0.0] - 2024-01-15 - Initial Release

### ✨ Initial Features
- Google Drive synchronization
- OneDrive synchronization
- Modern CustomTkinter GUI
- Zero-dependency installation (bundled rclone)
- Cross-architecture support (AMD64, ARM64, ARM, i386)
- DEB package for Debian/Ubuntu
- Desktop integration
- OAuth authentication

---

## Version Comparison

| Version | Release Date | Type | Key Changes |
|---------|--------------|------|-------------|
| 2.0.0 | 2024-02-04 | Major | Profiles, Advanced options, Force resync |
| 1.0.2 | 2024-02-04 | Hotfix | Bisync flag compatibility |
| 1.0.1 | 2024-02-04 | Security | Security fixes, bidirectional sync |
| 1.0.0 | 2024-01-15 | Initial | First public release |

---

## Roadmap

### v2.1.0 (Planned - Q2 2024)
- [ ] Scheduled sync (cron-like automation)
- [ ] System tray integration
- [ ] Desktop notifications
- [ ] Sync history viewer
- [ ] Real-time file watching

### v2.2.0 (Planned - Q3 2024)
- [ ] Dropbox support
- [ ] Cloud-to-cloud sync
- [ ] Encryption support (rclone crypt)
- [ ] Advanced conflict resolution
- [ ] Multiple simultaneous syncs

### v3.0.0 (Future)
- [ ] Plugin system
- [ ] Web interface
- [ ] Mobile companion app
- [ ] Team/Enterprise features
- [ ] S3/MinIO support

---

## Contributing

See commit messages and git log for detailed changes.

Report bugs: https://github.com/cryptd777/LinuxCloudSync/issues
Suggest features: https://github.com/cryptd777/LinuxCloudSync/discussions

---

**Last Updated:** February 5, 2026  
**Current Version:**   
**Status:** Production Ready ✅
