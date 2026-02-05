"""
main.py - LinuxCloud Sync GUI Application
==========================================
A standalone Google Drive/OneDrive sync client for Linux with zero dependencies.

Version: dynamic (see .build_version)
Author: LinuxCloudSync Team
License: MIT
"""

import customtkinter as ctk
import subprocess
import threading
import os
import re
import time
import logging
import json
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional, Dict, List
from datetime import datetime
from utils import (
    get_rclone_path, 
    ensure_executable, 
    get_rclone_config_path, 
    setup_logging,
    get_config_dir,
    save_sync_profile,
    load_sync_profiles,
    delete_sync_profile,
    get_app_version
)


class LinuxCloudSync(ctk.CTk):
    """Main application window for LinuxCloud Sync."""
    
    # Constants
    WINDOW_WIDTH = 900
    WINDOW_HEIGHT = 700
    COMMAND_TIMEOUT = 10
    SYNC_TIMEOUT = 3600  # 1 hour
    VERSION = get_app_version()
    
    def __init__(self):
        super().__init__()
        
        # Setup logging
        self.logger = setup_logging()
        self.logger.info(f"LinuxCloudSync v{self.VERSION} starting...")
        
        # Window configuration
        self.title(f"LinuxCloud Sync v{self.VERSION} - Professional Edition")
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize rclone path
        self.rclone_path = get_rclone_path()
        self.rclone_config = get_rclone_config_path()
        self.bisync_workdir = str(get_config_dir() / "bisync")
        Path(self.bisync_workdir).mkdir(parents=True, exist_ok=True)
        
        # Ensure rclone is executable
        try:
            ensure_executable(self.rclone_path)
            self.logger.info(f"Using bundled rclone engine at: {self.rclone_path}")
        except FileNotFoundError as e:
            self.logger.error(f"Critical error: {e}")
            messagebox.showerror("Critical Error", str(e))
            self.quit()
            return
        
        # State variables
        self.sync_process: Optional[subprocess.Popen] = None
        self.is_syncing: bool = False
        self.sync_start_time: float = 0
        self.sync_profiles: Dict = {}
        self.current_profile: Optional[str] = None
        
        # Advanced options
        self.bandwidth_limit: str = ""
        self.exclude_patterns: List[str] = []
        self.dry_run: bool = False
        
        # Load saved profiles
        self.sync_profiles = load_sync_profiles()
        
        # Build UI
        self.create_widgets()
        
        # Check rclone version on startup
        self.check_rclone_version()
        
        # Load last used profile if exists
        self.load_last_profile()

    def _get_bisync_lock_files(self) -> List[Path]:
        """Return any bisync lock files in the workdir."""
        try:
            workdir = Path(self.bisync_workdir)
            if not workdir.exists():
                return []
            return sorted(workdir.glob("*.lck"))
        except Exception:
            return []

    def _maybe_clear_bisync_locks(self) -> None:
        """Offer to clear stale bisync lock files."""
        lock_files = self._get_bisync_lock_files()
        if not lock_files:
            return
        if self.is_syncing:
            return

        lock_list = "\n".join(str(p) for p in lock_files)
        confirm = messagebox.askyesno(
            "Stale Bisync Lock Detected",
            "One or more bisync lock files were found. This can happen if a prior\n"
            "sync was interrupted and may block new bisync runs.\n\n"
            f"Lock files:\n{lock_list}\n\n"
            "Remove these lock files now?"
        )

        if not confirm:
            return

        removed = 0
        for lock_file in lock_files:
            try:
                lock_file.unlink()
                removed += 1
            except Exception:
                pass

        if removed:
            self.log(f"🧹 Removed {removed} stale bisync lock file(s)")
    
    def create_widgets(self):
        """Create and layout all UI widgets."""
        
        # Header Frame
        header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"☁️ LinuxCloud Sync v{self.VERSION}",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        self.status_indicator = ctk.CTkLabel(
            header_frame,
            text="● Ready",
            font=ctk.CTkFont(size=14),
            text_color="#4ade80"
        )
        self.status_indicator.pack(side="right")
        
        # Main Content Frame with Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create tabs
        self.tabview.add("Sync")
        self.tabview.add("Profiles")
        self.tabview.add("Advanced")
        self.tabview.add("About")
        
        # Build each tab
        self.create_sync_tab()
        self.create_profiles_tab()
        self.create_advanced_tab()
        self.create_about_tab()
    
    def create_sync_tab(self):
        """Create the main sync configuration tab."""
        sync_tab = self.tabview.tab("Sync")
        
        # Connection Section
        connection_frame = ctk.CTkFrame(sync_tab)
        connection_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            connection_frame,
            text="Cloud Storage Connection",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        button_frame = ctk.CTkFrame(connection_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(5, 10))
        
        self.connect_gdrive_btn = ctk.CTkButton(
            button_frame,
            text="🔗 Connect Google Drive",
            command=self.connect_google_drive,
            width=180
        )
        self.connect_gdrive_btn.pack(side="left", padx=(0, 10))
        
        self.connect_onedrive_btn = ctk.CTkButton(
            button_frame,
            text="🔗 Connect OneDrive",
            command=self.connect_onedrive,
            width=180
        )
        self.connect_onedrive_btn.pack(side="left", padx=(0, 10))
        
        self.list_remotes_btn = ctk.CTkButton(
            button_frame,
            text="📋 List Remotes",
            command=self.list_remotes,
            width=140,
            fg_color="#6366f1"
        )
        self.list_remotes_btn.pack(side="left", padx=(0, 10))
        
        self.resync_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Force Resync",
            command=self.force_resync,
            width=140,
            fg_color="#f59e0b"
        )
        self.resync_btn.pack(side="left")
        
        # Sync Configuration
        sync_frame = ctk.CTkFrame(sync_tab)
        sync_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(
            sync_frame,
            text="Sync Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        # Remote selector
        remote_frame = ctk.CTkFrame(sync_frame, fg_color="transparent")
        remote_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(remote_frame, text="Remote:", width=100).pack(side="left", padx=(0, 10))
        self.remote_entry = ctk.CTkEntry(remote_frame, placeholder_text="e.g., gdrive:")
        self.remote_entry.pack(side="left", fill="x", expand=True)
        
        # Local folder selector
        local_frame = ctk.CTkFrame(sync_frame, fg_color="transparent")
        local_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(local_frame, text="Local Folder:", width=100).pack(side="left", padx=(0, 10))
        self.local_path_entry = ctk.CTkEntry(local_frame, placeholder_text="Select local folder...")
        self.local_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            local_frame,
            text="Browse",
            command=self.browse_folder,
            width=100
        )
        browse_btn.pack(side="left")
        
        # Sync mode selector
        mode_frame = ctk.CTkFrame(sync_frame, fg_color="transparent")
        mode_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(mode_frame, text="Sync Mode:", width=100).pack(side="left", padx=(0, 10))
        self.sync_mode = ctk.CTkOptionMenu(
            mode_frame,
            values=["Bidirectional (bisync)", "Cloud to Local (copy)", "Local to Cloud (copy)"],
            width=300
        )
        self.sync_mode.set("Bidirectional (bisync)")
        self.sync_mode.pack(side="left")
        
        # Sync controls
        control_frame = ctk.CTkFrame(sync_frame, fg_color="transparent")
        control_frame.pack(fill="x", padx=20, pady=(10, 10))
        
        self.sync_btn = ctk.CTkButton(
            control_frame,
            text="▶ Start Sync",
            command=self.start_sync,
            width=150,
            height=40,
            fg_color="#10b981"
        )
        self.sync_btn.pack(side="left", padx=(0, 10))
        
        self.stop_btn = ctk.CTkButton(
            control_frame,
            text="⬛ Stop Sync",
            command=self.stop_sync,
            width=150,
            height=40,
            fg_color="#ef4444",
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=(0, 10))
        
        self.save_profile_btn = ctk.CTkButton(
            control_frame,
            text="💾 Save Profile",
            command=self.save_current_profile,
            width=150,
            height=40,
            fg_color="#8b5cf6"
        )
        self.save_profile_btn.pack(side="left")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(sync_frame)
        self.progress_bar.pack(fill="x", padx=20, pady=(10, 5))
        self.progress_bar.set(0)
        
        # Log Output
        log_label = ctk.CTkLabel(
            sync_frame,
            text="Output Log:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        log_label.pack(anchor="w", padx=20, pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(sync_frame, height=200, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 10))
    
    def create_profiles_tab(self):
        """Create the profiles management tab."""
        profiles_tab = self.tabview.tab("Profiles")
        
        ctk.CTkLabel(
            profiles_tab,
            text="Sync Profiles",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Profiles list
        self.profiles_frame = ctk.CTkScrollableFrame(profiles_tab, height=400)
        self.profiles_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.refresh_profiles_list()
        
        # Buttons
        btn_frame = ctk.CTkFrame(profiles_tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 Refresh",
            command=self.refresh_profiles_list,
            width=150
        ).pack(side="left", padx=(0, 10))
    
    def create_advanced_tab(self):
        """Create the advanced options tab."""
        advanced_tab = self.tabview.tab("Advanced")
        
        ctk.CTkLabel(
            advanced_tab,
            text="Advanced Options",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        options_frame = ctk.CTkFrame(advanced_tab)
        options_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Bandwidth limit
        bw_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        bw_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(bw_frame, text="Bandwidth Limit:").pack(side="left", padx=(0, 10))
        self.bw_entry = ctk.CTkEntry(bw_frame, placeholder_text="e.g., 10M (10 MB/s)")
        self.bw_entry.pack(side="left", fill="x", expand=True)
        
        # Dry run
        dry_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        dry_frame.pack(fill="x", padx=20, pady=10)
        
        self.dry_run_switch = ctk.CTkSwitch(
            dry_frame,
            text="Dry Run (preview changes without syncing)",
            command=self.toggle_dry_run
        )
        self.dry_run_switch.pack(side="left")
        
        # Exclude patterns
        exclude_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        exclude_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            exclude_frame,
            text="Exclude Patterns (one per line):"
        ).pack(anchor="w", pady=(0, 5))
        
        self.exclude_text = ctk.CTkTextbox(exclude_frame, height=100)
        self.exclude_text.pack(fill="both", expand=True)
        self.exclude_text.insert("1.0", "*.tmp\n*.log\n.git/\nnode_modules/")
        
        # Log level
        log_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        log_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(log_frame, text="Log Level:").pack(side="left", padx=(0, 10))
        self.log_level = ctk.CTkOptionMenu(
            log_frame,
            values=["ERROR", "WARNING", "INFO", "DEBUG"],
            width=150
        )
        self.log_level.set("INFO")
        self.log_level.pack(side="left")
        
        # Additional options
        ctk.CTkLabel(
            options_frame,
            text="Additional rclone flags:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.additional_flags_entry = ctk.CTkEntry(
            options_frame,
            placeholder_text="e.g., --transfers=4 --checkers=8"
        )
        self.additional_flags_entry.pack(fill="x", padx=20, pady=5)
    
    def create_about_tab(self):
        """Create the about/help tab."""
        about_tab = self.tabview.tab("About")
        
        about_frame = ctk.CTkScrollableFrame(about_tab)
        about_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(
            about_frame,
            text=f"LinuxCloud Sync v{self.VERSION}",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=10)
        
        # Description
        about_text = f"""
        Professional Cloud Sync Client for Linux

        Version: v{self.VERSION}
        Release Date: 2026-02-05
        
        Features:
        • Bidirectional sync with Google Drive & OneDrive
        • Multiple sync profiles
        • Bandwidth limiting
        • Advanced filtering
        • Dry run mode
        • Secure credential storage
        • Zero external dependencies
        
        Quick Start:
        1. Connect your cloud storage (Sync tab)
        2. Select remote and local folder
        3. Click "Start Sync" TWICE for first-time setup
        4. Save as profile for easy reuse
        
        Troubleshooting:
        • "Bisync aborted" error: Click "Force Resync" button
        • "Remote not found": Connect cloud storage first
        • Logs located at: ~/.config/linuxcloudsync/logs/
        
        License: MIT

        Made with love by cryptd
        """
        
        ctk.CTkLabel(
            about_frame,
            text=about_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        ).pack(pady=10, padx=20)

        # Clickable GitHub link
        github_url = "https://github.com/cryptd777/LinuxCloudSync"
        github_label = ctk.CTkLabel(
            about_frame,
            text=github_url,
            font=ctk.CTkFont(size=12, underline=True),
            text_color="#38bdf8",
            cursor="hand2"
        )
        github_label.pack(pady=(0, 10))
        github_label.bind("<Button-1>", lambda _e: webbrowser.open(github_url))
        
        # Buttons
        btn_frame = ctk.CTkFrame(about_frame, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="⬇ Download Latest .deb",
            command=lambda: webbrowser.open("https://github.com/cryptd777/LinuxCloudSync/releases/latest"),
            width=200,
            fg_color="#22c55e"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="📂 Open Log Folder",
            command=self.open_log_folder,
            width=180
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="📂 Open Config Folder",
            command=self.open_config_folder,
            width=180
        ).pack(side="left", padx=10)
    
    def log(self, message: str, level: str = "INFO"):
        """Add a message to the log output."""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_msg = f"[{timestamp}] {message}"
            
            self.log_text.configure(state="normal")
            self.log_text.insert("end", f"{formatted_msg}\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        except Exception as e:
            self.logger.error(f"Error writing to log widget: {e}")
        
        # Also log to file
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    def check_rclone_version(self):
        """Verify rclone is working and display version."""
        try:
            result = subprocess.run(
                [self.rclone_path, "version"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=self.COMMAND_TIMEOUT
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                self.log(f"✓ {version_line}")
            else:
                self.log("⚠ Warning: Could not verify rclone version", "WARNING")
        except subprocess.TimeoutExpired:
            self.log("⚠ Timeout checking rclone version", "WARNING")
        except Exception as e:
            self.log(f"⚠ Error checking rclone: {str(e)}", "WARNING")
    
    def validate_remote_name(self, remote: str) -> bool:
        """Validate remote name format for security."""
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_-]*:[/a-zA-Z0-9_.-]*$'
        return bool(re.match(pattern, remote))
    
    def validate_local_path(self, path: str) -> tuple[bool, str]:
        """Validate local path for security."""
        try:
            abs_path = os.path.abspath(path)
            
            if not Path(abs_path).exists():
                return False, "Path does not exist"
            
            safe_bases = [str(Path.home()), '/mnt', '/media', '/tmp/linuxcloudsync']
            is_safe = any(abs_path.startswith(base) for base in safe_bases)
            
            if not is_safe:
                return False, "Path must be within home directory, /mnt, or /media"
            
            if not Path(abs_path).is_dir():
                return False, "Path must be a directory"
            
            return True, abs_path
            
        except Exception as e:
            return False, f"Path validation error: {str(e)}"
    
    def connect_google_drive(self):
        """Launch rclone config for Google Drive setup."""
        self.log("🔧 Launching Google Drive configuration wizard...")
        self.log("Follow the prompts in the terminal window that opens.")
        
        def run_config():
            try:
                env = os.environ.copy()
                env['RCLONE_CONFIG'] = self.rclone_config
                
                result = subprocess.run(
                    [self.rclone_path, "config", "create", "gdrive", "drive"],
                    env=env,
                    timeout=300
                )
                
                if result.returncode == 0:
                    self.after(0, lambda: self.log("✓ Google Drive configuration completed"))
                    self.after(0, lambda: self.list_remotes())
                else:
                    self.after(0, lambda: self.log("❌ Configuration failed or cancelled", "WARNING"))
                    
            except subprocess.TimeoutExpired:
                self.after(0, lambda: self.log("❌ Configuration timeout (5 minutes)", "ERROR"))
            except Exception as e:
                self.after(0, lambda: self.log(f"❌ Configuration error: {str(e)}", "ERROR"))
        
        threading.Thread(target=run_config, daemon=True).start()
    
    def connect_onedrive(self):
        """Launch rclone config for OneDrive setup."""
        self.log("🔧 Launching OneDrive configuration wizard...")
        self.log("Follow the prompts in the terminal window that opens.")
        
        def run_config():
            try:
                env = os.environ.copy()
                env['RCLONE_CONFIG'] = self.rclone_config
                
                result = subprocess.run(
                    [self.rclone_path, "config", "create", "onedrive", "onedrive"],
                    env=env,
                    timeout=300
                )
                
                if result.returncode == 0:
                    self.after(0, lambda: self.log("✓ OneDrive configuration completed"))
                    self.after(0, lambda: self.list_remotes())
                else:
                    self.after(0, lambda: self.log("❌ Configuration failed or cancelled", "WARNING"))
                    
            except subprocess.TimeoutExpired:
                self.after(0, lambda: self.log("❌ Configuration timeout (5 minutes)", "ERROR"))
            except Exception as e:
                self.after(0, lambda: self.log(f"❌ Configuration error: {str(e)}", "ERROR"))
        
        threading.Thread(target=run_config, daemon=True).start()
    
    def list_remotes(self):
        """List all configured remotes."""
        try:
            env = os.environ.copy()
            env['RCLONE_CONFIG'] = self.rclone_config
            
            result = subprocess.run(
                [self.rclone_path, "listremotes"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                timeout=self.COMMAND_TIMEOUT
            )
            
            if result.returncode == 0:
                remotes = result.stdout.strip()
                if remotes:
                    self.log("📋 Configured remotes:")
                    for remote in remotes.split('\n'):
                        self.log(f"  • {remote}")
                else:
                    self.log("ℹ No remotes configured yet")
                    self.log("  Use 'Connect Google Drive' or 'Connect OneDrive' buttons")
            else:
                self.log(f"❌ Error: {result.stderr}", "ERROR")
        except subprocess.TimeoutExpired:
            self.log("❌ Timeout listing remotes", "ERROR")
        except Exception as e:
            self.log(f"❌ Error listing remotes: {str(e)}", "ERROR")
    
    def force_resync(self):
        """Force bisync resync to fix baseline errors."""
        remote = self.remote_entry.get().strip()
        local_path = self.local_path_entry.get().strip()
        
        if not remote or not local_path:
            messagebox.showwarning("Input Required", "Please enter remote and local folder first")
            return
        
        is_valid, result = self.validate_local_path(local_path)
        if not is_valid:
            messagebox.showerror("Invalid Path", result)
            return
        
        local_path = result
        
        confirm = messagebox.askyesno(
            "Force Resync",
            f"This will rebuild the sync baseline for:\n\n"
            f"Remote: {remote}\n"
            f"Local: {local_path}\n\n"
            f"Continue?"
        )
        
        if not confirm:
            return
        
        self._maybe_clear_bisync_locks()
        self.log("🔄 Force resync initiated...")

        self.is_syncing = True
        self.sync_start_time = time.time()
        self.sync_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_indicator.configure(text="● Resyncing", text_color="#f59e0b")
        self.progress_bar.set(0.1)

        def run_resync():
            process_stdout = None
            proc = None
            try:
                env = os.environ.copy()
                env['RCLONE_CONFIG'] = self.rclone_config

                cmd = [
                    self.rclone_path,
                    "bisync",
                    remote,
                    local_path,
                    "--workdir",
                    self.bisync_workdir,
                    "--resync",
                    "--create-empty-src-dirs",
                    "--resilient",
                    "-v"
                ]

                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env,
                    bufsize=1
                )
                self.sync_process = proc

                if not self.is_syncing:
                    self.after(0, lambda: self.log("⏹ Resync stopped by user"))
                    self._terminate_sync_process()
                    return

                process_stdout = proc.stdout
                timeout_time = time.time() + 300
                for line in iter(proc.stdout.readline, ''):
                    if not self.is_syncing:
                        self.after(0, lambda: self.log("⏹ Resync stopped by user"))
                        self._terminate_sync_process()
                        break
                    if time.time() > timeout_time:
                        self.after(0, lambda: self.log("⏱️ Resync timeout (5 min)", "WARNING"))
                        self.is_syncing = False
                        break
                    line_clean = line.rstrip()
                    if line_clean:
                        self.after(0, lambda msg=line_clean: self.log(msg))

                proc.wait(timeout=10)

                if self.is_syncing:
                    if proc.returncode == 0:
                        self.after(0, lambda: self.log("✓ Resync completed successfully"))
                        self.after(0, lambda: self.log("   You can now run normal sync"))
                    else:
                        self.after(0, lambda: self.log(f"⚠ Resync exit code: {proc.returncode}", "WARNING"))

            except subprocess.TimeoutExpired:
                self.after(0, lambda: self.log("❌ Resync timeout", "ERROR"))
            except Exception as e:
                self.after(0, lambda err=str(e): self.log(f"❌ Resync error: {err}", "ERROR"))
            finally:
                if process_stdout:
                    try:
                        process_stdout.close()
                    except Exception:
                        pass
                self.sync_process = None

                def reset_ui():
                    self.is_syncing = False
                    self.sync_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
                    self.status_indicator.configure(text="● Ready", text_color="#4ade80")
                    self.progress_bar.set(0)

                self.after(0, reset_ui)

        threading.Thread(target=run_resync, daemon=True).start()
    
    def browse_folder(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory(
            title="Select Local Sync Folder",
            initialdir=str(Path.home())
        )
        
        if folder:
            is_valid, result = self.validate_local_path(folder)
            
            if is_valid:
                self.local_path_entry.delete(0, "end")
                self.local_path_entry.insert(0, result)
            else:
                messagebox.showwarning(
                    "Invalid Directory",
                    f"Cannot use this directory:\n{result}\n\n"
                    "Please select a directory in your home folder, /mnt, or /media"
                )
    
    def toggle_dry_run(self):
        """Toggle dry run mode."""
        self.dry_run = self.dry_run_switch.get()
        if self.dry_run:
            self.log("ℹ Dry run mode enabled (preview only)")
            if "Bidirectional" in self.sync_mode.get():
                self.log("   ⚠ Bisync dry run cannot initialize baseline")
                self.log("   If you see listing errors, disable Dry Run and click Force Resync")
        else:
            self.log("ℹ Dry run mode disabled")

    def _terminate_sync_process(self):
        """Terminate the running rclone process if it exists."""
        if not self.sync_process:
            return
        try:
            self.sync_process.terminate()
            try:
                self.sync_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.sync_process.kill()
                self.sync_process.wait()
        except Exception:
            pass
    
    def start_sync(self):
        """Start the sync process with enhanced features."""
        remote = self.remote_entry.get().strip()
        local_path = self.local_path_entry.get().strip()
        
        # Validate inputs
        if not remote:
            messagebox.showwarning("Input Error", "Please enter a remote name (e.g., gdrive:)")
            return
        
        if not self.validate_remote_name(remote):
            messagebox.showerror(
                "Invalid Remote Format",
                "Remote name must:\n"
                "• Start with a letter or number\n"
                "• Contain only letters, numbers, underscore, hyphen\n"
                "• Include a colon (:)\n"
                "• Example: gdrive: or gdrive:/folder"
            )
            return
        
        if not local_path:
            messagebox.showwarning("Input Error", "Please select a local folder")
            return
        
        is_valid, result = self.validate_local_path(local_path)
        if not is_valid:
            messagebox.showerror("Invalid Path", result)
            return
        
        local_path = result
        
        # Update UI state
        self.is_syncing = True
        self.sync_start_time = time.time()
        self.sync_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_indicator.configure(text="● Syncing", text_color="#f59e0b")
        self.progress_bar.set(0.1)
        
        sync_mode = self.sync_mode.get()
        self.log(f"🔄 Starting sync ({sync_mode})")
        self.log(f"   Remote: {remote}")
        self.log(f"   Local: {local_path}")
        
        if self.dry_run:
            self.log("   ⚠ DRY RUN MODE - No changes will be made")
        
        def run_sync():
            process_stdout = None
            proc = None
            try:
                env = os.environ.copy()
                env['RCLONE_CONFIG'] = self.rclone_config
                
                # Build command based on sync mode
                if "Bidirectional" in sync_mode:
                    self._maybe_clear_bisync_locks()
                    cmd = [
                        self.rclone_path,
                        "bisync",
                        remote,
                        local_path,
                        "--workdir",
                        self.bisync_workdir,
                        "--create-empty-src-dirs",
                        "--resilient",
                        "-v"
                    ]
                elif "Cloud to Local" in sync_mode:
                    cmd = [
                        self.rclone_path,
                        "copy",
                        remote,
                        local_path,
                        "-v"
                    ]
                else:  # Local to Cloud
                    cmd = [
                        self.rclone_path,
                        "copy",
                        local_path,
                        remote,
                        "-v"
                    ]
                
                # Add bandwidth limit if specified
                bandwidth = self.bw_entry.get().strip()
                if bandwidth:
                    cmd.extend(["--bwlimit", bandwidth])
                    self.after(0, lambda: self.log(f"   Bandwidth limit: {bandwidth}"))
                
                # Add dry run flag
                if self.dry_run:
                    cmd.append("--dry-run")
                
                # Add exclude patterns
                exclude_text = self.exclude_text.get("1.0", "end").strip()
                if exclude_text:
                    for pattern in exclude_text.split('\n'):
                        pattern = pattern.strip()
                        if pattern and not pattern.startswith('#'):
                            cmd.extend(["--exclude", pattern])
                
                # Add additional flags
                additional_flags = self.additional_flags_entry.get().strip()
                if additional_flags:
                    flag_parts = additional_flags.split()
                    if "Bidirectional" in sync_mode:
                        filtered = []
                        for flag in flag_parts:
                            if flag in ("--compare", "--slow-hash-sync-only"):
                                self.after(0, lambda f=flag: self.log(f"⚠ Removed unsupported flag for bisync: {f}", "WARNING"))
                                continue
                            filtered.append(flag)
                        flag_parts = filtered
                    cmd.extend(flag_parts)
                
                self.after(0, lambda: self.log(f"   Command: {' '.join(cmd[2:])}"))
                self.after(0, lambda: self.log(""))
                
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env,
                    bufsize=1
                )
                self.sync_process = proc

                if not self.is_syncing:
                    self.after(0, lambda: self.log("⏹ Sync stopped by user"))
                    self._terminate_sync_process()
                    return
                
                process_stdout = proc.stdout
                
                # Read output with timeout check
                timeout_time = time.time() + self.SYNC_TIMEOUT
                for line in iter(proc.stdout.readline, ''):
                    if not self.is_syncing:
                        self.after(0, lambda: self.log("⏹ Sync stopped by user"))
                        self._terminate_sync_process()
                        break
                    
                    if time.time() > timeout_time:
                        self.after(0, lambda: self.log(f"⏱️ Sync timeout ({self.SYNC_TIMEOUT // 60} min)", "WARNING"))
                        self.is_syncing = False
                        break
                    
                    line_clean = line.rstrip()
                    if line_clean:
                        self.after(0, lambda msg=line_clean: self.log(msg))
                        
                        # Update progress bar based on output
                        if "Transferred:" in line_clean:
                            self.after(0, lambda: self.progress_bar.set(0.7))
                
                proc.wait(timeout=10)
                
                if self.is_syncing:
                    elapsed = int(time.time() - self.sync_start_time)
                    self.after(0, lambda: self.progress_bar.set(1.0))
                    
                    if proc.returncode == 0:
                        self.after(0, lambda: self.log(f"✓ Sync completed in {elapsed}s"))
                    elif proc.returncode == 2:
                        self.after(0, lambda: self.log(""))
                        self.after(0, lambda: self.log("⚠ Bisync requires initialization", "WARNING"))
                        self.after(0, lambda: self.log("   Click 'Force Resync' button to fix"))
                    else:
                        self.after(0, lambda: self.log(f"⚠ Exit code: {proc.returncode}", "WARNING"))
                
            except subprocess.TimeoutExpired:
                self.after(0, lambda: self.log("❌ Sync timeout", "ERROR"))
            except Exception as e:
                self.after(0, lambda err=str(e): self.log(f"❌ Error: {err}", "ERROR"))
            finally:
                if process_stdout:
                    try:
                        process_stdout.close()
                    except:
                        pass
                self.sync_process = None
                
                def reset_ui():
                    self.is_syncing = False
                    self.sync_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
                    self.status_indicator.configure(text="● Ready", text_color="#4ade80")
                    self.progress_bar.set(0)
                
                self.after(0, reset_ui)
        
        threading.Thread(target=run_sync, daemon=True).start()
    
    def stop_sync(self):
        """Stop the running sync process."""
        if self.sync_process and self.is_syncing:
            self.log("⏹ Stopping sync...")
            self.is_syncing = False
            try:
                self._terminate_sync_process()
                self.log("✓ Sync stopped")
            except Exception as e:
                self.log(f"❌ Error stopping: {str(e)}", "ERROR")
    
    def save_current_profile(self):
        """Save current sync configuration as a profile."""
        profile_name = ctk.CTkInputDialog(
            text="Enter profile name:",
            title="Save Profile"
        ).get_input()
        
        if not profile_name:
            return
        
        profile = {
            "remote": self.remote_entry.get().strip(),
            "local_path": self.local_path_entry.get().strip(),
            "sync_mode": self.sync_mode.get(),
            "bandwidth": self.bw_entry.get().strip(),
            "exclude_patterns": self.exclude_text.get("1.0", "end").strip(),
            "dry_run": self.dry_run,
            "additional_flags": self.additional_flags_entry.get().strip()
        }
        
        if save_sync_profile(profile_name, profile):
            self.log(f"✓ Profile '{profile_name}' saved")
            self.sync_profiles = load_sync_profiles()
            self.refresh_profiles_list()
        else:
            self.log(f"❌ Failed to save profile", "ERROR")
    
    def load_profile(self, profile_name: str):
        """Load a saved sync profile."""
        if profile_name not in self.sync_profiles:
            return
        
        profile = self.sync_profiles[profile_name]
        
        self.remote_entry.delete(0, "end")
        self.remote_entry.insert(0, profile.get("remote", ""))
        
        self.local_path_entry.delete(0, "end")
        self.local_path_entry.insert(0, profile.get("local_path", ""))
        
        self.sync_mode.set(profile.get("sync_mode", "Bidirectional (bisync)"))
        
        self.bw_entry.delete(0, "end")
        self.bw_entry.insert(0, profile.get("bandwidth", ""))
        
        self.exclude_text.delete("1.0", "end")
        self.exclude_text.insert("1.0", profile.get("exclude_patterns", ""))
        
        self.dry_run = profile.get("dry_run", False)
        if self.dry_run:
            self.dry_run_switch.select()
        else:
            self.dry_run_switch.deselect()
        
        self.additional_flags_entry.delete(0, "end")
        self.additional_flags_entry.insert(0, profile.get("additional_flags", ""))
        
        self.current_profile = profile_name
        self.log(f"✓ Loaded profile: {profile_name}")
        
        # Switch to Sync tab
        self.tabview.set("Sync")
    
    def delete_profile(self, profile_name: str):
        """Delete a saved profile."""
        confirm = messagebox.askyesno(
            "Delete Profile",
            f"Delete profile '{profile_name}'?"
        )
        
        if confirm and delete_sync_profile(profile_name):
            self.log(f"✓ Profile '{profile_name}' deleted")
            self.sync_profiles = load_sync_profiles()
            self.refresh_profiles_list()
    
    def refresh_profiles_list(self):
        """Refresh the profiles list display."""
        # Clear existing widgets
        for widget in self.profiles_frame.winfo_children():
            widget.destroy()
        
        if not self.sync_profiles:
            ctk.CTkLabel(
                self.profiles_frame,
                text="No saved profiles yet.\nCreate one from the Sync tab!",
                font=ctk.CTkFont(size=14)
            ).pack(pady=20)
            return
        
        for profile_name, profile in self.sync_profiles.items():
            profile_frame = ctk.CTkFrame(self.profiles_frame)
            profile_frame.pack(fill="x", padx=10, pady=5)
            
            info_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            ctk.CTkLabel(
                info_frame,
                text=profile_name,
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_frame,
                text=f"Remote: {profile.get('remote', 'N/A')}",
                font=ctk.CTkFont(size=11)
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_frame,
                text=f"Local: {profile.get('local_path', 'N/A')}",
                font=ctk.CTkFont(size=11)
            ).pack(anchor="w")
            
            btn_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)
            
            ctk.CTkButton(
                btn_frame,
                text="Load",
                command=lambda p=profile_name: self.load_profile(p),
                width=80
            ).pack(side="left", padx=5)
            
            ctk.CTkButton(
                btn_frame,
                text="Delete",
                command=lambda p=profile_name: self.delete_profile(p),
                width=80,
                fg_color="#ef4444"
            ).pack(side="left", padx=5)
    
    def load_last_profile(self):
        """Load the last used profile if exists."""
        config_file = get_config_dir() / "last_profile.txt"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    last_profile = f.read().strip()
                    if last_profile in self.sync_profiles:
                        self.load_profile(last_profile)
            except Exception as e:
                self.logger.error(f"Error loading last profile: {e}")
    
    def open_log_folder(self):
        """Open the log folder in file manager."""
        log_dir = get_config_dir() / "logs"
        subprocess.Popen(["xdg-open", str(log_dir)])
    
    def open_config_folder(self):
        """Open the config folder in file manager."""
        config_dir = get_config_dir()
        subprocess.Popen(["xdg-open", str(config_dir)])


def main():
    """Application entry point."""
    app = LinuxCloudSync()
    app.mainloop()


if __name__ == "__main__":
    main()
