"""Configuration management."""

import os
from pathlib import Path
from typing import Any, Optional

import yaml

# Default configuration
DEFAULT_CONFIG = {
    "obsidian_vault": "~/vault",
    "daily_notes_folder": "Daily Notes",
    "gmail_accounts": [],
    "google_calendars": [],
    "credentials_path": "~/.daynote",
    "obsolete_threshold_days": 14,
    "gmail_cache_hours": 48,
    "calendar_cache_hours": 24,
}

# Global config cache
_config_cache: Optional[dict] = None


def get_config_path() -> Path:
    """Get path to config file."""
    return Path.home() / ".daynote" / "config.yaml"


def load_config() -> dict:
    """
    Load configuration from file.

    Returns merged config with defaults.
    """
    global _config_cache

    if _config_cache is not None:
        return _config_cache

    config = DEFAULT_CONFIG.copy()
    config_path = get_config_path()

    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                user_config = yaml.safe_load(f) or {}
                config.update(user_config)
        except (yaml.YAMLError, IOError) as e:
            print(f"Warning: Could not load config: {e}")

    # Expand paths
    if "obsidian_vault" in config:
        config["obsidian_vault"] = os.path.expanduser(config["obsidian_vault"])
    if "credentials_path" in config:
        config["credentials_path"] = os.path.expanduser(config["credentials_path"])

    _config_cache = config
    return config


def get_config() -> dict:
    """Get configuration (loads if not cached)."""
    return load_config()


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific config value."""
    config = get_config()
    return config.get(key, default)


def reload_config() -> dict:
    """Force reload configuration from file."""
    global _config_cache
    _config_cache = None
    return load_config()


def save_config(config: dict) -> bool:
    """
    Save configuration to file.

    Args:
        config: Configuration dict to save

    Returns:
        True if successful
    """
    global _config_cache

    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        _config_cache = config
        return True
    except IOError as e:
        print(f"Error saving config: {e}")
        return False


def ensure_config_exists() -> bool:
    """
    Ensure config file exists with defaults.

    Returns:
        True if config exists or was created
    """
    config_path = get_config_path()

    if config_path.exists():
        return True

    # Create default config
    config_path.parent.mkdir(parents=True, exist_ok=True)

    default_with_comments = """# DayNote Configuration
# Edit this file to customize your setup

# Path to your Obsidian vault
obsidian_vault: ~/vault

# Folder within vault for daily notes
daily_notes_folder: Daily Notes

# Gmail accounts to check (add your email addresses)
gmail_accounts:
  # - your.email@gmail.com
  # - work.email@company.com

# Google Calendar IDs to sync (requires gcalendar_credentials.json)
# Use "primary" for your main calendar
google_calendars:
  # - primary
  # - family@group.calendar.google.com

# Path to Gmail and Google Calendar OAuth credentials
credentials_path: ~/.daynote

# Days after which incomplete tasks are considered obsolete
obsolete_threshold_days: 14

# Hours to cache Gmail data
gmail_cache_hours: 48

# Hours before calendar cache is considered stale
calendar_cache_hours: 24
"""

    try:
        with open(config_path, "w") as f:
            f.write(default_with_comments)
        return True
    except IOError:
        return False


def validate_config() -> list[str]:
    """
    Validate configuration and return list of issues.

    Returns:
        List of error messages (empty if valid)
    """
    config = get_config()
    issues = []

    # Check vault path
    vault_path = Path(config.get("obsidian_vault", "")).expanduser()
    if not vault_path.exists():
        issues.append(f"Obsidian vault not found: {vault_path}")
    else:
        daily_notes = vault_path / config.get("daily_notes_folder", "Daily Notes")
        if not daily_notes.exists():
            issues.append(f"Daily notes folder not found: {daily_notes}")

    # Check Gmail accounts configured
    gmail_accounts = config.get("gmail_accounts", [])
    if gmail_accounts:
        # Check credentials path
        creds_path = Path(config.get("credentials_path", "")).expanduser()
        if not (creds_path / "credentials.json").exists():
            issues.append(f"Gmail credentials not found: {creds_path}/credentials.json")

    # Check Google Calendar configured
    google_calendars = config.get("google_calendars", [])
    if google_calendars:
        creds_path = Path(config.get("credentials_path", "")).expanduser()
        if not (creds_path / "gcalendar_credentials.json").exists():
            issues.append(f"Google Calendar credentials not found: {creds_path}/gcalendar_credentials.json")

    # Check AppleScript
    script_path = Path.home() / ".daynote" / "refresh_calendar.scpt"
    if not script_path.exists():
        issues.append(f"Calendar script not found: {script_path}")

    return issues


def print_config_status():
    """Print configuration status for debugging."""
    config = get_config()
    issues = validate_config()

    print("\n📋 DayNote Configuration")
    print("━" * 40)
    print(f"Config file: {get_config_path()}")
    print(f"Obsidian vault: {config.get('obsidian_vault')}")
    print(f"Daily notes folder: {config.get('daily_notes_folder')}")
    print(f"Gmail accounts: {', '.join(config.get('gmail_accounts', [])) or '(none)'}")
    print(f"Google calendars: {', '.join(config.get('google_calendars', [])) or '(none)'}")
    print(f"Obsolete threshold: {config.get('obsolete_threshold_days')} days")
    print("━" * 40)

    if issues:
        print("\n⚠️  Configuration Issues:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("\n✅ Configuration valid")
