"""Reconciliation logic - compare sources and find gaps."""

from datetime import datetime, timedelta
from typing import Optional

from .calendar import (
    get_events_for_date,
    get_events_for_range,
    format_event_for_display,
    format_event_for_obsidian,
    load_calendar_cache,
)
from .gmail import (
    get_cached_emails,
    get_meeting_emails_for_date,
    format_email_for_display,
    format_email_for_obsidian,
)
from .gcalendar import (
    get_gcal_events_for_date,
    is_gcal_configured,
)
from .obsidian import (
    daily_note_exists,
    read_daily_note,
    item_exists_in_note,
    extract_calendar_items,
)
from .config import get_config


class ReconciliationItem:
    """An item from calendar or email that may or may not be in Obsidian."""

    def __init__(
        self,
        title: str,
        source: str,  # "calendar" or "gmail"
        source_detail: str,  # calendar name or email account
        time: str,
        date: datetime,
        in_obsidian: bool,
        raw_data: dict,
    ):
        self.title = title
        self.source = source
        self.source_detail = source_detail
        self.time = time
        self.date = date
        self.in_obsidian = in_obsidian
        self.raw_data = raw_data

    def __repr__(self):
        status = "✓" if self.in_obsidian else "○"
        return f"{status} [{self.source}] {self.time} - {self.title}"

    def for_display(self) -> str:
        """Format for terminal display."""
        if self.source == "calendar":
            return format_event_for_display(self.raw_data)
        else:
            return format_email_for_display(self.raw_data)

    def for_obsidian(self) -> str:
        """Format for adding to Obsidian note."""
        if self.source == "calendar":
            return format_event_for_obsidian(self.raw_data)
        else:
            return format_email_for_obsidian(self.raw_data)


class DayReport:
    """Report for a single day."""

    def __init__(self, date: datetime):
        self.date = date
        self.note_exists = daily_note_exists(date)
        self.items_in_obsidian: list[ReconciliationItem] = []
        self.items_not_in_obsidian: list[ReconciliationItem] = []
        self.calendar_refreshed: Optional[str] = None
        self.gmail_accounts_checked: list[str] = []

    @property
    def total_items(self) -> int:
        return len(self.items_in_obsidian) + len(self.items_not_in_obsidian)

    @property
    def new_items_count(self) -> int:
        return len(self.items_not_in_obsidian)


def reconcile_day(target_date: datetime) -> DayReport:
    """
    Build a reconciliation report for a single day.

    Compares calendar and email items against what's in the Obsidian note.

    Args:
        target_date: Date to reconcile

    Returns:
        DayReport with items categorized by in_obsidian status
    """
    report = DayReport(target_date)
    config = get_config()

    # Get calendar refresh time
    cal_cache = load_calendar_cache()
    if cal_cache:
        report.calendar_refreshed = cal_cache.get("refreshed")

    # Check today's note for existing items (or yesterday's if we're looking at today)
    # For future dates, we check if items appear in ANY recent note
    note_content = ""
    if report.note_exists:
        note_content = read_daily_note(target_date) or ""

    # Also check today's note for calendar section items about this date
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if target_date.date() != today.date():
        today_content = read_daily_note(today) or ""
        note_content = note_content + "\n" + today_content

    # Get calendar events for this date
    events = get_events_for_date(target_date)
    for event in events:
        title = event.get("title", "")
        in_note = _item_in_content(title, note_content)

        item = ReconciliationItem(
            title=title,
            source="calendar",
            source_detail=event.get("calendar", ""),
            time=event.get("start", "")[:16],  # Just date and time
            date=target_date,
            in_obsidian=in_note,
            raw_data=event,
        )

        if in_note:
            report.items_in_obsidian.append(item)
        else:
            report.items_not_in_obsidian.append(item)

    # Get Google Calendar events if configured
    if is_gcal_configured():
        gcal_events = get_gcal_events_for_date(target_date)
        for event in gcal_events:
            title = event.get("title", "")
            in_note = _item_in_content(title, note_content)

            item = ReconciliationItem(
                title=title,
                source="calendar",
                source_detail=f"google:{event.get('calendar', '')}",
                time=event.get("start", "")[:16],
                date=target_date,
                in_obsidian=in_note,
                raw_data=event,
            )

            if in_note:
                report.items_in_obsidian.append(item)
            else:
                report.items_not_in_obsidian.append(item)

    # Get relevant emails
    gmail_accounts = config.get("gmail_accounts", [])
    report.gmail_accounts_checked = gmail_accounts

    emails = get_meeting_emails_for_date(target_date)
    for email in emails:
        subject = email.get("subject", "")
        # Check if this email subject appears in the note
        in_note = _item_in_content(subject, note_content)

        item = ReconciliationItem(
            title=subject,
            source="gmail",
            source_detail=email.get("account", ""),
            time=email.get("date", "")[:16],
            date=target_date,
            in_obsidian=in_note,
            raw_data=email,
        )

        if in_note:
            report.items_in_obsidian.append(item)
        else:
            report.items_not_in_obsidian.append(item)

    # Deduplicate by title+time before returning
    seen = set()
    deduped_in = []
    deduped_not_in = []

    for item in report.items_in_obsidian:
        key = (item.title.lower().strip(), item.time)
        if key not in seen:
            seen.add(key)
            deduped_in.append(item)

    for item in report.items_not_in_obsidian:
        key = (item.title.lower().strip(), item.time)
        if key not in seen:
            seen.add(key)
            deduped_not_in.append(item)

    report.items_in_obsidian = deduped_in
    report.items_not_in_obsidian = deduped_not_in

    # Sort items by time
    report.items_in_obsidian.sort(key=lambda x: x.time)
    report.items_not_in_obsidian.sort(key=lambda x: x.time)

    return report


def reconcile_week(start_date: datetime = None) -> list[DayReport]:
    """
    Build reconciliation reports for 7 days.

    Args:
        start_date: First day of range (defaults to today)

    Returns:
        List of 7 DayReports
    """
    if start_date is None:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    reports = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        reports.append(reconcile_day(day))

    return reports


def _item_in_content(title: str, content: str) -> bool:
    """Check if an item title appears in note content."""
    if not title or not content:
        return False

    # Normalize for comparison
    normalized_title = title.lower().strip()
    normalized_content = content.lower()

    # Check for exact match or partial match (title is at least 5 chars)
    if len(normalized_title) >= 5:
        return normalized_title in normalized_content

    # For short titles, require word boundary match
    import re
    pattern = r"\b" + re.escape(normalized_title) + r"\b"
    return bool(re.search(pattern, normalized_content))


def get_items_to_add(report: DayReport, indices: list[int] = None) -> list[ReconciliationItem]:
    """
    Get items to add to Obsidian from a report.

    Args:
        report: DayReport to get items from
        indices: List of indices (1-based) to add, or None for all

    Returns:
        List of ReconciliationItems to add
    """
    if indices is None:
        return report.items_not_in_obsidian.copy()

    items = []
    for i in indices:
        if 1 <= i <= len(report.items_not_in_obsidian):
            items.append(report.items_not_in_obsidian[i - 1])
    return items


def format_report_for_terminal(report: DayReport) -> str:
    """Format a DayReport for terminal output."""
    lines = []

    # Header
    date_str = report.date.strftime("%A, %B %d, %Y")
    lines.append(f"\n📅 {date_str}")
    lines.append("━" * 50)

    # Note status
    if report.note_exists:
        note_filename = report.date.strftime("%m-%d-%a-%Y").replace(
            report.date.strftime("%a"),
            report.date.strftime("%a").capitalize()[:3]
        ) + ".md"
        lines.append(f"📝 Daily Note: EXISTS ({note_filename})")
    else:
        lines.append("📝 Daily Note: NOT CREATED")

    lines.append("")

    # Items in Obsidian
    if report.items_in_obsidian:
        lines.append("✅ IN OBSIDIAN:")
        for item in report.items_in_obsidian:
            if item.source == "calendar":
                lines.append(f"   • {item.for_display()}")
            else:
                lines.append(f"   • 📧 {item.for_display()}")
        lines.append("")

    # Items not in Obsidian
    if report.items_not_in_obsidian:
        lines.append("📥 NOT IN OBSIDIAN:")
        for i, item in enumerate(report.items_not_in_obsidian, 1):
            icon = "📆" if item.source == "calendar" else "📧"
            lines.append(f"   [{i}] {icon} {item.for_display()}")
        lines.append("")
    else:
        lines.append("✨ All items are in Obsidian!")
        lines.append("")

    # Footer
    lines.append("━" * 50)

    if report.items_not_in_obsidian and report.note_exists:
        lines.append("Run 'daynote add' to add items to your note")
    elif report.items_not_in_obsidian and not report.note_exists:
        lines.append("Create the daily note first, then run 'daynote add'")

    return "\n".join(lines)


def format_week_summary(reports: list[DayReport]) -> str:
    """Format a week of reports as a summary."""
    lines = []
    lines.append("\n📅 7-Day Lookahead")
    lines.append("━" * 50)

    for report in reports:
        date_str = report.date.strftime("%a %b %d")
        note_icon = "📝" if report.note_exists else "  "
        event_count = len(report.items_in_obsidian) + len(report.items_not_in_obsidian)
        new_count = len(report.items_not_in_obsidian)

        if new_count > 0:
            lines.append(f"{note_icon} {date_str}: {event_count} items ({new_count} new)")
        else:
            lines.append(f"{note_icon} {date_str}: {event_count} items")

    lines.append("━" * 50)
    lines.append("Run 'daynote show <day>' for details")

    return "\n".join(lines)
