"""Calendar integration via AppleScript."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import get_config


def get_calendar_cache_path() -> Path:
    """Get path to calendar cache file."""
    return Path.home() / ".daynote" / "calendar.json"


def get_applescript_path() -> Path:
    """Get path to the AppleScript file."""
    config = get_config()
    # Check user-configured path first, then default locations
    script_path = config.get("applescript_path")
    if script_path:
        return Path(script_path)

    # Default: same directory as the package was installed from
    # User should copy refresh_calendar.scpt to ~/.daynote/
    return Path.home() / ".daynote" / "refresh_calendar.scpt"


def refresh_calendar() -> dict:
    """
    Run AppleScript to refresh calendar data.

    Returns:
        dict with 'success', 'message', and 'event_count' keys
    """
    script_path = get_applescript_path()

    if not script_path.exists():
        return {
            "success": False,
            "message": f"AppleScript not found at {script_path}. Please copy refresh_calendar.scpt to ~/.daynote/",
            "event_count": 0
        }

    try:
        result = subprocess.run(
            ["bash", str(script_path)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # Parse the output message to get event count
            output = result.stdout.strip()
            return {
                "success": True,
                "message": output,
                "event_count": _parse_event_count(output)
            }
        else:
            return {
                "success": False,
                "message": f"AppleScript error: {result.stderr}",
                "event_count": 0
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "Calendar refresh timed out after 30 seconds",
            "event_count": 0
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error running AppleScript: {str(e)}",
            "event_count": 0
        }


def _parse_event_count(output: str) -> int:
    """Parse event count from AppleScript output."""
    try:
        # Output format: "Calendar refreshed: X events exported to /path"
        parts = output.split()
        for i, part in enumerate(parts):
            if part == "events":
                return int(parts[i - 1])
    except (ValueError, IndexError):
        pass
    return 0


def load_calendar_cache() -> Optional[dict]:
    """
    Load calendar data from cache file.

    Returns:
        dict with 'refreshed' timestamp and 'events' list, or None if no cache
    """
    cache_path = get_calendar_cache_path()

    if not cache_path.exists():
        return None

    try:
        with open(cache_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def get_cache_age_hours() -> Optional[float]:
    """
    Get the age of the calendar cache in hours.

    Returns:
        Age in hours, or None if no cache exists
    """
    cache = load_calendar_cache()
    if not cache or "refreshed" not in cache:
        return None

    try:
        refreshed = datetime.fromisoformat(cache["refreshed"])
        age = datetime.now() - refreshed
        return age.total_seconds() / 3600
    except (ValueError, TypeError):
        return None


def is_cache_stale(max_age_hours: float = 24) -> bool:
    """Check if cache is older than max_age_hours."""
    age = get_cache_age_hours()
    if age is None:
        return True
    return age > max_age_hours


def get_events_for_date(target_date: datetime) -> list[dict]:
    """
    Get calendar events for a specific date.

    Args:
        target_date: The date to get events for

    Returns:
        List of event dicts sorted by start time
    """
    cache = load_calendar_cache()
    if not cache or "events" not in cache:
        return []

    target_str = target_date.strftime("%Y-%m-%d")
    events = []

    for event in cache["events"]:
        # Parse start time and check if it matches target date
        try:
            start = datetime.fromisoformat(event["start"])
            if start.strftime("%Y-%m-%d") == target_str:
                events.append(event)
        except (ValueError, KeyError):
            continue

    # Sort by start time
    events.sort(key=lambda e: e.get("start", ""))
    return events


def get_events_for_range(start_date: datetime, end_date: datetime) -> list[dict]:
    """
    Get calendar events for a date range.

    Args:
        start_date: Start of range (inclusive)
        end_date: End of range (inclusive)

    Returns:
        List of event dicts sorted by start time
    """
    cache = load_calendar_cache()
    if not cache or "events" not in cache:
        return []

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    events = []

    for event in cache["events"]:
        try:
            event_start = datetime.fromisoformat(event["start"])
            event_date_str = event_start.strftime("%Y-%m-%d")
            if start_str <= event_date_str <= end_str:
                events.append(event)
        except (ValueError, KeyError):
            continue

    # Sort by start time
    events.sort(key=lambda e: e.get("start", ""))
    return events


def format_event_time(event: dict) -> str:
    """Format event time for display."""
    if event.get("all_day"):
        return "All day"

    try:
        start = datetime.fromisoformat(event["start"])
        return start.strftime("%-I:%M %p").replace(":00 ", " ").lower()
    except (ValueError, KeyError):
        return "?"


def format_event_for_display(event: dict) -> str:
    """Format a single event for terminal display."""
    time_str = format_event_time(event)
    title = event.get("title", "Untitled")
    location = event.get("location", "")

    if location:
        return f"{time_str} - {title} ({location})"
    return f"{time_str} - {title}"


def format_event_for_obsidian(event: dict) -> str:
    """Format a single event for Obsidian note as a checkbox task."""
    time_str = format_event_time(event)
    title = event.get("title", "Untitled")
    location = event.get("location", "")
    calendar = event.get("calendar", "")

    # Format calendar name as tag
    calendar_tag = ""
    if calendar:
        # Convert calendar ID to tag-friendly format
        # e.g., "personal" -> "#calendar/personal"
        calendar_tag = f" #calendar/{calendar.lower().replace(' ', '_')}"

    if event.get("all_day"):
        if location:
            return f"- [ ] All day - {title} ({location}) #meeting{calendar_tag}"
        return f"- [ ] All day - {title} #meeting{calendar_tag}"

    # Convert to simple format like "9 AM" or "2:30 PM"
    try:
        start = datetime.fromisoformat(event["start"])
        if start.minute == 0:
            time_display = start.strftime("%-I %p").upper()
        else:
            time_display = start.strftime("%-I:%M %p").upper()
    except:
        time_display = time_str.upper()

    if location:
        return f"- [ ] {time_display} - {title} ({location}) #meeting{calendar_tag}"
    return f"- [ ] {time_display} - {title} #meeting{calendar_tag}"
