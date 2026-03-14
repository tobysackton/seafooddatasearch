"""Gmail integration with caching."""

import json
import pickle
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import get_config

# Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_cache_path(account: str) -> Path:
    """Get path to Gmail cache file for an account."""
    # Sanitize account name for filename
    safe_name = account.replace("@", "_at_").replace(".", "_")
    return Path.home() / ".daynote" / "cache" / f"gmail_{safe_name}.json"


def get_token_path(account: str) -> Path:
    """Get path to token file for an account."""
    safe_name = account.replace("@", "_at_").replace(".", "_")
    return Path.home() / ".daynote" / f"token_{safe_name}.pickle"


def get_credentials_path() -> Path:
    """Get path to OAuth credentials file."""
    config = get_config()
    creds_path = config.get("credentials_path")
    if creds_path:
        return Path(creds_path) / "credentials.json"
    return Path.home() / ".daynote" / "credentials.json"


def authenticate_gmail(account: str) -> Optional[Credentials]:
    """
    Authenticate with Gmail API.

    Args:
        account: Email address (used to identify token file)

    Returns:
        Credentials object or None if authentication fails
    """
    token_path = get_token_path(account)
    creds_path = get_credentials_path()
    creds = None

    # Load existing token
    if token_path.exists():
        with open(token_path, "rb") as token:
            creds = pickle.load(token)

    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not creds_path.exists():
                print(f"Credentials file not found: {creds_path}")
                print("Please download OAuth credentials from Google Cloud Console")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            print(f"\nAuthenticating Gmail account: {account}")
            creds = flow.run_local_server(port=0)

        # Save token
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)

    return creds


def get_gmail_service(account: str):
    """Get Gmail API service object."""
    creds = authenticate_gmail(account)
    if not creds:
        return None
    return build("gmail", "v1", credentials=creds)


def search_emails(account: str, query: str, max_results: int = 50) -> list[dict]:
    """
    Search emails using Gmail query syntax.

    Args:
        account: Email account to search
        query: Gmail search query
        max_results: Maximum number of results

    Returns:
        List of email dicts with id, threadId, subject, from, date, snippet
    """
    service = get_gmail_service(account)
    if not service:
        return []

    try:
        results = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            # Get full message details
            msg_data = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"]
            ).execute()

            headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}

            emails.append({
                "id": msg["id"],
                "thread_id": msg["threadId"],
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "snippet": msg_data.get("snippet", ""),
                "account": account
            })

        return emails

    except Exception as e:
        print(f"Error searching Gmail: {e}")
        return []


def get_thread_conversation(account: str, thread_id: str) -> list[dict]:
    """
    Get all messages in a thread.

    Args:
        account: Email account
        thread_id: Thread ID to retrieve

    Returns:
        List of message dicts in chronological order
    """
    service = get_gmail_service(account)
    if not service:
        return []

    try:
        thread = service.users().threads().get(
            userId="me",
            id=thread_id,
            format="metadata",
            metadataHeaders=["Subject", "From", "To", "Date"]
        ).execute()

        messages = []
        for msg in thread.get("messages", []):
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            messages.append({
                "id": msg["id"],
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "date": headers.get("Date", ""),
                "snippet": msg.get("snippet", "")
            })

        return messages

    except Exception as e:
        print(f"Error getting thread: {e}")
        return []


def refresh_gmail_cache(account: str, cache_hours: int = 48) -> dict:
    """
    Refresh Gmail cache for an account.

    Fetches meeting-related emails from the last cache_hours.

    Args:
        account: Email account to refresh
        cache_hours: How many hours of emails to cache

    Returns:
        dict with 'success', 'message', 'email_count'
    """
    # Meeting-related search query
    query = f"newer_than:{cache_hours}h (subject:(meeting OR invite OR zoom OR teams OR call OR schedule OR calendar) OR from:(calendar OR invite))"

    emails = search_emails(account, query, max_results=100)

    if emails:
        cache_path = get_gmail_cache_path(account)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        cache_data = {
            "refreshed": datetime.now().isoformat(),
            "account": account,
            "cache_hours": cache_hours,
            "emails": emails
        }

        with open(cache_path, "w") as f:
            json.dump(cache_data, f, indent=2)

        return {
            "success": True,
            "message": f"Cached {len(emails)} emails from {account}",
            "email_count": len(emails)
        }
    else:
        # Still create cache file even if empty
        cache_path = get_gmail_cache_path(account)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        cache_data = {
            "refreshed": datetime.now().isoformat(),
            "account": account,
            "cache_hours": cache_hours,
            "emails": []
        }

        with open(cache_path, "w") as f:
            json.dump(cache_data, f, indent=2)

        return {
            "success": True,
            "message": f"No meeting emails found in {account} (cache updated)",
            "email_count": 0
        }


def load_gmail_cache(account: str) -> Optional[dict]:
    """Load Gmail cache for an account."""
    cache_path = get_gmail_cache_path(account)

    if not cache_path.exists():
        return None

    try:
        with open(cache_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def get_gmail_cache_age_hours(account: str) -> Optional[float]:
    """Get age of Gmail cache in hours."""
    cache = load_gmail_cache(account)
    if not cache or "refreshed" not in cache:
        return None

    try:
        refreshed = datetime.fromisoformat(cache["refreshed"])
        age = datetime.now() - refreshed
        return age.total_seconds() / 3600
    except (ValueError, TypeError):
        return None


def is_gmail_cache_stale(account: str, max_age_hours: float = 48) -> bool:
    """Check if Gmail cache is stale."""
    age = get_gmail_cache_age_hours(account)
    if age is None:
        return True
    return age > max_age_hours


def get_cached_emails(account: str) -> list[dict]:
    """Get emails from cache."""
    cache = load_gmail_cache(account)
    if not cache:
        return []
    return cache.get("emails", [])


def search_person(person_name: str) -> list[dict]:
    """
    Live search for emails from/to a specific person across all accounts.

    Args:
        person_name: Name or email to search for

    Returns:
        List of email dicts from all accounts
    """
    config = get_config()
    accounts = config.get("gmail_accounts", [])

    all_emails = []
    query = f"from:{person_name} OR to:{person_name}"

    for account in accounts:
        emails = search_emails(account, query, max_results=20)
        all_emails.extend(emails)

    # Sort by date (newest first)
    all_emails.sort(key=lambda e: e.get("date", ""), reverse=True)
    return all_emails


def get_meeting_emails_for_date(target_date: datetime) -> list[dict]:
    """
    Get meeting-related emails that mention a specific date.

    Searches cached emails for date mentions.

    Args:
        target_date: Date to search for

    Returns:
        List of relevant emails
    """
    config = get_config()
    accounts = config.get("gmail_accounts", [])

    # Date patterns to look for
    date_patterns = [
        target_date.strftime("%B %d"),  # January 20
        target_date.strftime("%b %d"),  # Jan 20
        target_date.strftime("%m/%d"),  # 01/20
        target_date.strftime("%Y-%m-%d"),  # 2026-01-20
        target_date.strftime("%A"),  # Tuesday
    ]

    relevant_emails = []

    for account in accounts:
        emails = get_cached_emails(account)
        for email in emails:
            # Check if any date pattern appears in subject or snippet
            text = f"{email.get('subject', '')} {email.get('snippet', '')}".lower()
            for pattern in date_patterns:
                if pattern.lower() in text:
                    relevant_emails.append(email)
                    break

    return relevant_emails


def format_email_for_display(email: dict) -> str:
    """Format email for terminal display."""
    subject = email.get("subject", "(no subject)")
    sender = email.get("from", "")
    # Extract just the name or email from "Name <email>" format
    if "<" in sender:
        sender = sender.split("<")[0].strip().strip('"')

    account = email.get("account", "")
    account_short = account.split("@")[0] if account else ""

    return f"[{account_short}] {sender}: {subject}"


def format_email_for_obsidian(email: dict) -> str:
    """Format email as Obsidian task with follow-up tag."""
    subject = email.get("subject", "(no subject)")
    sender = email.get("from", "")
    if "<" in sender:
        sender = sender.split("<")[0].strip().strip('"')

    return f"- [ ] Follow up: {subject} (from {sender}) #email"
