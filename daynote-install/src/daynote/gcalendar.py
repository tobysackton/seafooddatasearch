"""Google Calendar integration."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import get_config

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_gcal_cache_path() -> Path:
    """Get path to Google Calendar cache."""
    return Path.home() / ".daynote" / "cache" / "gcalendar.json"


def get_gcal_token_path() -> Path:
    """Get path to Google Calendar token file."""
    return Path.home() / ".daynote" / "token_gcalendar.pickle"


def get_gcal_credentials_path() -> Path:
    """Get path to Google Calendar credentials file."""
    config = get_config()
    creds_path = config.get("credentials_path", "~/.daynote")
    return Path(creds_path).expanduser() / "gcalendar_credentials.json"


def authenticate_gcal() -> Optional[Credentials]:
    """Authenticate with Google Calendar API."""
    import pickle
    token_path = get_gcal_token_path()
    creds_path = get_gcal_credentials_path()
    creds = None

    if token_path.exists():
        with open(token_path, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not creds_path.exists():
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            print("\nAuthenticating Google Calendar...")
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "wb") as f:
            pickle.dump(creds, f)

    return creds


def refresh_gcal_cache(days_ahead: int = 14) -> dict:
    """Refresh Google Calendar cache."""
    creds = authenticate_gcal()
    if not creds:
        return {"success": False, "message": "Google Calendar not configured. Place gcalendar_credentials.json in ~/.daynote/", "event_count": 0}

    try:
        service = build("calendar", "v3", credentials=creds)

        config = get_config()
        calendar_ids = config.get("google_calendars", ["primary"])

        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(days=days_ahead)).isoformat() + "Z"

        all_events = []
        for cal_id in calendar_ids:
            try:
                result = service.events().list(
                    calendarId=cal_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime"
                ).execute()

                for event in result.get("items", []):
                    start = event.get("start", {})
                    end = event.get("end", {})

                    all_events.append({
                        "title": event.get("summary", "Untitled"),
                        "start": start.get("dateTime", start.get("date", "")),
                        "end": end.get("dateTime", end.get("date", "")),
                        "calendar": cal_id,
                        "location": event.get("location", ""),
                        "notes": event.get("description", ""),
                        "all_day": "date" in start and "dateTime" not in start,
                        "source": "google"
                    })
            except Exception as e:
                print(f"Warning: Could not fetch calendar {cal_id}: {e}")

        cache_data = {
            "refreshed": datetime.now().isoformat(),
            "events": all_events
        }

        cache_path = get_gcal_cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(cache_data, f, indent=2)

        return {"success": True, "message": f"Google Calendar: {len(all_events)} events cached", "event_count": len(all_events)}

    except Exception as e:
        return {"success": False, "message": f"Google Calendar error: {e}", "event_count": 0}


def load_gcal_cache() -> Optional[dict]:
    """Load Google Calendar cache."""
    cache_path = get_gcal_cache_path()
    if not cache_path.exists():
        return None
    try:
        with open(cache_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def get_gcal_events_for_date(target_date: datetime) -> list[dict]:
    """Get Google Calendar events for a date."""
    cache = load_gcal_cache()
    if not cache or "events" not in cache:
        return []

    target_str = target_date.strftime("%Y-%m-%d")
    events = []

    for event in cache["events"]:
        try:
            start_str = event.get("start", "")
            if start_str.startswith(target_str):
                events.append(event)
            elif event.get("all_day") and start_str == target_str:
                events.append(event)
        except (ValueError, KeyError):
            continue

    events.sort(key=lambda e: e.get("start", ""))
    return events


def is_gcal_configured() -> bool:
    """Check if Google Calendar credentials exist."""
    return get_gcal_credentials_path().exists()


def get_gcal_cache_age_hours() -> Optional[float]:
    """Get age of Google Calendar cache in hours."""
    cache = load_gcal_cache()
    if not cache or "refreshed" not in cache:
        return None
    try:
        refreshed = datetime.fromisoformat(cache["refreshed"])
        age = datetime.now() - refreshed
        return age.total_seconds() / 3600
    except (ValueError, TypeError):
        return None


def is_gcal_cache_stale(max_age_hours: float = 24) -> bool:
    """Check if Google Calendar cache is stale."""
    age = get_gcal_cache_age_hours()
    if age is None:
        return True
    return age > max_age_hours
