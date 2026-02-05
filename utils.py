"""
utils.py - Enhanced utilities for LinuxCloud Sync
"""

import sys
import os
import logging
import json
from pathlib import Path
from typing import Optional, Dict


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource."""
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(__file__).parent.absolute()
    return str(base_path / relative_path)


def get_rclone_path() -> str:
    """Get the bundled rclone binary path."""
    return resource_path('bin/rclone')


def ensure_executable(path: str) -> None:
    """Ensure a file has executable permissions."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Binary not found: {path}")
    
    try:
        os.chmod(path, 0o755)
        print(f"✓ Set executable permissions: {path}")
    except (PermissionError, OSError) as e:
        if not os.access(path, os.X_OK):
            raise PermissionError(f"Cannot execute {path}: {e}")


def get_config_dir() -> Path:
    """Get the user's config directory."""
    xdg_config = os.environ.get('XDG_CONFIG_HOME')
    
    if xdg_config:
        config_dir = Path(xdg_config) / 'linuxcloudsync'
    else:
        config_dir = Path.home() / '.config' / 'linuxcloudsync'
    
    config_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        config_dir.chmod(0o700)
    except (PermissionError, OSError):
        pass
    
    return config_dir


def get_rclone_config_path() -> str:
    """Get the path where rclone config should be stored."""
    return str(get_config_dir() / 'rclone.conf')


def setup_logging() -> logging.Logger:
    """Setup application logging."""
    log_dir = get_config_dir() / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / 'linuxcloudsync.log'
    
    logger = logging.getLogger('LinuxCloudSync')
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    try:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,
            backupCount=3
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"⚠ Warning: Could not setup file logging: {e}")
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def save_sync_profile(name: str, profile: Dict) -> bool:
    """Save a sync profile."""
    try:
        profiles_file = get_config_dir() / 'profiles.json'
        
        profiles = {}
        if profiles_file.exists():
            with open(profiles_file, 'r') as f:
                profiles = json.load(f)
        
        profiles[name] = profile
        
        with open(profiles_file, 'w') as f:
            json.dump(profiles, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving profile: {e}")
        return False


def load_sync_profiles() -> Dict:
    """Load all sync profiles."""
    try:
        profiles_file = get_config_dir() / 'profiles.json'
        
        if profiles_file.exists():
            with open(profiles_file, 'r') as f:
                return json.load(f)
        
        return {}
    except Exception as e:
        print(f"Error loading profiles: {e}")
        return {}


def delete_sync_profile(name: str) -> bool:
    """Delete a sync profile."""
    try:
        profiles_file = get_config_dir() / 'profiles.json'
        
        if not profiles_file.exists():
            return False
        
        with open(profiles_file, 'r') as f:
            profiles = json.load(f)
        
        if name in profiles:
            del profiles[name]
            
            with open(profiles_file, 'w') as f:
                json.dump(profiles, f, indent=2)
            
            return True
        
        return False
    except Exception as e:
        print(f"Error deleting profile: {e}")
        return False


def get_app_version() -> str:
    """Get the application version from .build_version if present."""
    try:
        version_file = Path(__file__).parent / ".build_version"
        if version_file.exists():
            version = version_file.read_text(encoding="utf-8").strip()
            if version:
                return version
    except Exception:
        pass
    return "3.0.2"
