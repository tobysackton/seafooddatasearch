"""Command-line interface for DayNote."""

import sys
import re
from datetime import datetime, timedelta
from pathlib import Path

import click

from . import __version__
from .config import (
    get_config,
    ensure_config_exists,
    validate_config,
    print_config_status,
    get_config_value,
)
from .calendar import (
    refresh_calendar,
    is_cache_stale as is_calendar_stale,
    get_cache_age_hours as get_calendar_age,
    load_calendar_cache,
    get_events_for_date,
    get_events_for_range,
    format_event_for_obsidian,
    format_event_time,
)
from .gmail import (
    refresh_gmail_cache,
    is_gmail_cache_stale,
    get_gmail_cache_age_hours,
    search_person,
    get_thread_conversation,
)
from .obsidian import (
    daily_note_exists,
    find_obsolete_tasks,
    clear_obsolete_tasks,
    append_to_daily_note,
    insert_under_heading,
    get_daily_note_path,
    find_misnamed_notes,
    get_vault_path,
    get_daily_notes_path,
    read_daily_note,
    get_incomplete_tasks,
    get_completed_tasks,
    get_cancelled_tasks,
)
from .reconcile import (
    reconcile_day,
    reconcile_week,
    format_report_for_terminal,
    format_week_summary,
    get_items_to_add,
)
from .gcalendar import (
    refresh_gcal_cache,
    is_gcal_configured,
    get_gcal_cache_age_hours,
    is_gcal_cache_stale,
)


@click.group()
@click.version_option(version=__version__)
def cli():
    """DayNote - Daily productivity dashboard for Obsidian, Gmail, and Calendar."""
    pass


@cli.command()
def init():
    """Initialize DayNote configuration."""
    click.echo("Starting DayNote initialization...")

    # Create config
    if ensure_config_exists():
        click.echo(f"Configuration created: ~/.daynote/config.yaml")
    else:
        click.echo("Failed to create config file")
        return

    # Check for AppleScript
    script_src = Path(__file__).parent.parent.parent / "scripts" / "refresh_calendar.scpt"
    script_dst = Path.home() / ".daynote" / "refresh_calendar.scpt"

    if script_src.exists() and not script_dst.exists():
        import shutil
        shutil.copy(script_src, script_dst)
        click.echo(f"Calendar script installed: {script_dst}")
    elif not script_dst.exists():
        click.echo(f"Please copy refresh_calendar.scpt to {script_dst}")

    click.echo("\nNext steps:")
    click.echo("1. Edit ~/.daynote/config.yaml with your settings")
    click.echo("2. Add your Gmail OAuth credentials.json to ~/.daynote/")
    click.echo("3. Run 'daynote config' to verify setup")
    click.echo("4. Run 'daynote sync' to start using!")


@cli.command()
def config():
    """Show configuration status."""
    print_config_status()


@cli.command()
@click.option("--force", is_flag=True, help="Force refresh even if cache is fresh")
def sync(force):
    """Refresh calendar and Gmail, then show today's report."""
    config = get_config()

    click.echo("Syncing...")

    # Refresh Apple Calendar
    cal_age = get_calendar_age()
    cal_stale = is_calendar_stale(get_config_value("calendar_cache_hours", 24))

    if force or cal_stale:
        click.echo("   Refreshing Apple Calendar...")
        result = refresh_calendar()
        if result["success"]:
            click.echo(f"   {result['message']}")
        else:
            click.echo(f"   {result['message']}")
    else:
        click.echo(f"   Apple Calendar cache is fresh ({cal_age:.1f}h old)")

    # Refresh Google Calendar if configured
    if is_gcal_configured():
        gcal_age = get_gcal_cache_age_hours()
        gcal_stale = is_gcal_cache_stale(get_config_value("calendar_cache_hours", 24))

        if force or gcal_stale:
            click.echo("   Refreshing Google Calendar...")
            result = refresh_gcal_cache()
            if result["success"]:
                click.echo(f"   {result['message']}")
            else:
                click.echo(f"   {result['message']}")
        else:
            if gcal_age:
                click.echo(f"   Google Calendar cache is fresh ({gcal_age:.1f}h old)")

    # Refresh Gmail
    gmail_accounts = config.get("gmail_accounts", [])
    cache_hours = get_config_value("gmail_cache_hours", 48)

    for account in gmail_accounts:
        age = get_gmail_cache_age_hours(account)
        stale = is_gmail_cache_stale(account, cache_hours)

        if force or stale:
            click.echo(f"   Refreshing {account}...")
            result = refresh_gmail_cache(account, cache_hours)
            if result["success"]:
                click.echo(f"   {result['message']}")
            else:
                click.echo(f"   Failed to refresh {account}")
        else:
            click.echo(f"   {account} cache is fresh ({age:.1f}h old)")

    # Show today's report
    click.echo("")
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    report = reconcile_day(today)
    click.echo(format_report_for_terminal(report))


@cli.command()
@click.argument("day", default="today")
def show(day):
    """
    Show reconciliation report for a day.

    DAY can be: today, tomorrow, monday, tuesday, etc., or a date like 2026-01-20
    """
    target_date = _parse_day(day)
    if target_date is None:
        click.echo(f"Could not parse date: {day}")
        return

    report = reconcile_day(target_date)
    click.echo(format_report_for_terminal(report))


@cli.command()
def week():
    """Show 7-day lookahead summary."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    reports = reconcile_week(today)
    click.echo(format_week_summary(reports))

    # Ask if user wants details for any day
    click.echo("\nEnter a day name for details (or press Enter to exit):")


@cli.command()
@click.argument("day", default="today")
@click.option("--all", "add_all", is_flag=True, help="Add all items without prompting")
def add(day, add_all):
    """
    Add items to a daily note.

    DAY can be: today, tomorrow, or a date.
    """
    target_date = _parse_day(day)
    if target_date is None:
        click.echo(f"Could not parse date: {day}")
        return

    # Check if note exists
    if not daily_note_exists(target_date):
        note_path = get_daily_note_path(target_date)
        click.echo(f"Daily note does not exist: {note_path.name}")
        click.echo("   Create the note in Obsidian first, then run this command again.")
        return

    # Get report
    report = reconcile_day(target_date)

    if not report.items_not_in_obsidian:
        click.echo("All items are already in Obsidian!")
        return

    # Show items
    click.echo(f"\nItems to add to {target_date.strftime('%B %d, %Y')}:")
    for i, item in enumerate(report.items_not_in_obsidian, 1):
        icon = "📆" if item.source == "calendar" else "📧"
        click.echo(f"   [{i}] {icon} {item.for_display()}")

    if add_all:
        items_to_add = report.items_not_in_obsidian
    else:
        # Prompt for selection
        click.echo("\nEnter numbers to add (comma-separated), 'all', or 'none':")
        selection = click.prompt("Selection", default="all")

        if selection.lower() == "none":
            click.echo("No items added.")
            return
        elif selection.lower() == "all":
            items_to_add = report.items_not_in_obsidian
        else:
            try:
                # Remove trailing commas and empty strings
                parts = [x.strip() for x in selection.split(",") if x.strip()]
                indices = [int(x) for x in parts]
                items_to_add = get_items_to_add(report, indices)
            except ValueError:
                click.echo("Invalid selection. Use numbers like: 1,3,5")
                return

    if not items_to_add:
        click.echo("No items to add.")
        return

    # Build content to add
    calendar_items = [item for item in items_to_add if item.source == "calendar"]
    email_items = [item for item in items_to_add if item.source == "gmail"]

    added_count = 0

    # Insert calendar items under existing heading
    if calendar_items:
        cal_content = "\n".join(item.for_obsidian() for item in calendar_items)

        # Try inserting under existing headings (v4, v3, v1 templates)
        inserted = insert_under_heading(
            target_date,
            "## Today's Meetings",
            cal_content,
            placeholder="*(Populated by `daynote add today`)*"
        )
        if not inserted:
            inserted = insert_under_heading(
                target_date,
                "## Added from Calendar",
                cal_content,
                placeholder="*(Run `daynote add today` to populate)*"
            )
        if not inserted:
            inserted = insert_under_heading(
                target_date,
                "## Schedule & Meetings",
                cal_content,
                placeholder="*(Run `daynote add today` to populate, or add manually)*"
            )
        if not inserted:
            # Fallback: append with heading
            fallback = "## Added from Calendar\n" + cal_content
            inserted = append_to_daily_note(target_date, fallback)

        if inserted:
            added_count += len(calendar_items)
            click.echo(f"   Inserted {len(calendar_items)} calendar item(s) under heading")
        else:
            click.echo("   Failed to add calendar items")

    # Insert email items under existing heading or append
    if email_items:
        email_content = "\n".join(item.for_obsidian() for item in email_items)

        inserted = insert_under_heading(
            target_date,
            "## Follow-up from Email",
            email_content
        )
        if not inserted:
            # No existing heading — append with heading
            fallback = "\n## Follow-up from Email\n" + email_content
            inserted = append_to_daily_note(target_date, fallback)

        if inserted:
            added_count += len(email_items)
            click.echo(f"   Inserted {len(email_items)} email item(s)")
        else:
            click.echo("   Failed to add email items")

    if added_count > 0:
        click.echo(f"\nAdded {added_count} item(s) to daily note")
    else:
        click.echo("Failed to update daily note")


@cli.command()
@click.argument("person")
def status(person):
    """
    Search for email threads with a person.

    PERSON can be a name or email address.
    """
    click.echo(f"Searching for emails with '{person}'...")

    emails = search_person(person)

    if not emails:
        click.echo(f"   No emails found for '{person}'")
        return

    click.echo(f"\nFound {len(emails)} email(s):\n")

    for i, email in enumerate(emails[:10], 1):  # Show top 10
        account = email.get("account", "").split("@")[0]
        sender = email.get("from", "")
        if "<" in sender:
            sender = sender.split("<")[0].strip().strip('"')
        subject = email.get("subject", "(no subject)")
        date = email.get("date", "")[:16]

        click.echo(f"[{i}] [{account}] {date}")
        click.echo(f"    From: {sender}")
        click.echo(f"    Subject: {subject}")
        click.echo(f"    {email.get('snippet', '')[:100]}...")
        click.echo()

    if len(emails) > 10:
        click.echo(f"   ... and {len(emails) - 10} more")


@cli.command()
def obsolete():
    """Show obsolete tasks (>14 days old)."""
    threshold = get_config_value("obsolete_threshold_days", 14)
    tasks = find_obsolete_tasks(threshold)

    if not tasks:
        click.echo(f"No obsolete tasks (older than {threshold} days)")
        return

    click.echo(f"\nFound {len(tasks)} obsolete task(s):\n")

    current_file = None
    for task in tasks:
        if task["file"] != current_file:
            current_file = task["file"]
            click.echo(f"📄 {current_file.name}")

        click.echo(f"   {task['task']}")

    click.echo(f"\nRun 'daynote clear-obsolete' to mark these as cancelled")


@cli.command("clear-obsolete")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def clear_obsolete_cmd(yes):
    """Mark obsolete tasks as cancelled."""
    threshold = get_config_value("obsolete_threshold_days", 14)
    tasks = find_obsolete_tasks(threshold)

    if not tasks:
        click.echo(f"No obsolete tasks to clear")
        return

    click.echo(f"Found {len(tasks)} obsolete task(s) to clear")

    if not yes:
        if not click.confirm("Mark these tasks as cancelled?"):
            click.echo("Cancelled.")
            return

    result = clear_obsolete_tasks(threshold)

    click.echo(f"\nCleared {result['cleared_count']} tasks in {result['files_modified']} files")

    if result["errors"]:
        click.echo("\nErrors:")
        for error in result["errors"]:
            click.echo(f"   {error}")


@cli.command("refresh")
@click.argument("source", type=click.Choice(["calendar", "gmail", "all"]), default="all")
def refresh_cmd(source):
    """Force refresh calendar or Gmail cache."""
    config = get_config()

    if source in ("calendar", "all"):
        click.echo("Refreshing Apple Calendar...")
        result = refresh_calendar()
        if result["success"]:
            click.echo(f"{result['message']}")
        else:
            click.echo(f"{result['message']}")

        if is_gcal_configured():
            click.echo("Refreshing Google Calendar...")
            result = refresh_gcal_cache()
            if result["success"]:
                click.echo(f"{result['message']}")
            else:
                click.echo(f"{result['message']}")

    if source in ("gmail", "all"):
        gmail_accounts = config.get("gmail_accounts", [])
        cache_hours = get_config_value("gmail_cache_hours", 48)

        for account in gmail_accounts:
            click.echo(f"Refreshing {account}...")
            result = refresh_gmail_cache(account, cache_hours)
            if result["success"]:
                click.echo(f"{result['message']}")
            else:
                click.echo(f"Failed to refresh {account}")


@cli.group()
def fix():
    """Fix vault issues."""
    pass


@fix.command("dates")
@click.option("--dry-run", is_flag=True, help="Show what would change without renaming")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def fix_dates(dry_run, yes):
    """Rename daily notes to consistent MM-DD-Ddd-YYYY format."""
    misnamed = find_misnamed_notes()

    if not misnamed:
        click.echo("All daily notes have consistent names.")
        return

    click.echo(f"Found {len(misnamed)} notes to rename:\n")
    for old_path, new_path in misnamed:
        click.echo(f"  {old_path.name} -> {new_path.name}")

    if dry_run:
        click.echo("\n(dry run - no changes made)")
        return

    if not yes:
        if not click.confirm("\nRename these files?"):
            return

    # Do the renames and fix internal links
    vault = get_vault_path()

    renamed = 0
    for old_path, new_path in misnamed:
        if new_path.exists():
            click.echo(f"  SKIP {old_path.name} - target already exists")
            continue
        old_path.rename(new_path)
        renamed += 1

    # Fix links in all markdown files
    click.echo(f"\nRenamed {renamed} files. Fixing internal links...")
    link_fixes = 0
    for md_file in vault.rglob("*.md"):
        try:
            content = md_file.read_text()
            new_content = content
            for old_path, new_path in misnamed:
                old_stem = old_path.stem
                new_stem = new_path.stem
                new_content = new_content.replace(f"[[{old_stem}]]", f"[[{new_stem}]]")
            if new_content != content:
                md_file.write_text(new_content)
                link_fixes += 1
        except Exception:
            pass

    click.echo(f"Fixed links in {link_fixes} files.")


@fix.command("template")
def fix_template():
    """Fix template to use zero-padded date format."""
    vault = get_vault_path()
    template_path = vault / "Templates" / "Daily_list.md"

    if not template_path.exists():
        click.echo(f"Template not found: {template_path}")
        return

    content = template_path.read_text()
    # Fix MM-D-ddd-YYYY to MM-DD-ddd-YYYY in Templater syntax
    old = 'tp.date.now("MM-D-ddd-YYYY"'
    new = 'tp.date.now("MM-DD-ddd-YYYY"'

    if old in content:
        content = content.replace(old, new)
        template_path.write_text(content)
        click.echo("Fixed template Previous link date format.")
    else:
        click.echo("Template already uses correct format (or format not found).")


@cli.command()
@click.argument("day", default="today")
def review(day):
    """Show end-of-day review for a daily note."""
    target_date = _parse_day(day)
    if target_date is None:
        click.echo(f"Could not parse date: {day}")
        return

    content = read_daily_note(target_date)
    if not content:
        click.echo(f"No daily note found for {target_date.strftime('%B %d, %Y')}")
        return

    completed = get_completed_tasks(content)
    incomplete = get_incomplete_tasks(content)
    cancelled = get_cancelled_tasks(content)

    date_str = target_date.strftime("%A, %B %d, %Y")
    click.echo(f"\nDay Review: {date_str}")
    click.echo("=" * 50)

    if completed:
        click.echo(f"\nCompleted ({len(completed)}):")
        for task in completed:
            click.echo(f"   {task}")

    if incomplete:
        click.echo(f"\nIncomplete ({len(incomplete)}):")
        for task in incomplete:
            # Skip empty placeholder tasks
            stripped = task.replace("- [ ] ", "").strip()
            if stripped:
                click.echo(f"   {task}")

    if cancelled:
        click.echo(f"\nCancelled ({len(cancelled)}):")
        for task in cancelled:
            click.echo(f"   {task}")

    # Check consulting time log
    if "| **TOTAL**" in content:
        # Try to find if hours were logged
        total_match = re.search(r'\| \*\*TOTAL\*\* \|([^|]*)\|', content)
        if total_match:
            hours = total_match.group(1).strip()
            if hours and hours != "":
                click.echo(f"\nConsulting time logged: {hours} hours")
            else:
                click.echo(f"\nNo consulting time logged today")

    click.echo("\n" + "=" * 50)
    total = len(completed) + len(incomplete) + len(cancelled)
    if total > 0:
        pct = len(completed) / total * 100 if total > 0 else 0
        click.echo(f"Completion rate: {len(completed)}/{total} ({pct:.0f}%)")


@cli.command()
@click.option("--add", "add_to_note", is_flag=True, help="Add upcoming section to today's daily note")
def upcoming(add_to_note):
    """Show upcoming meetings/appointments for the next 7 days and optionally add to today's note."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    end_near = today + timedelta(days=3)  # next 3 days
    end_far = today + timedelta(days=7)   # 4-7 days out

    # Gather events from Apple Calendar
    near_events = get_events_for_range(tomorrow, end_near)
    far_events = get_events_for_range(end_near + timedelta(days=1), end_far)

    # Gather events from Google Calendar if configured
    if is_gcal_configured():
        from .gcalendar import get_gcal_events_for_date
        for day_offset in range(1, 4):
            d = today + timedelta(days=day_offset)
            for ev in get_gcal_events_for_date(d):
                # Deduplicate by title
                if not any(e.get("title", "").lower() == ev.get("title", "").lower() for e in near_events):
                    near_events.append(ev)
        for day_offset in range(4, 8):
            d = today + timedelta(days=day_offset)
            for ev in get_gcal_events_for_date(d):
                if not any(e.get("title", "").lower() == ev.get("title", "").lower() for e in far_events):
                    far_events.append(ev)

    # Sort by start time
    near_events.sort(key=lambda e: e.get("start", ""))
    far_events.sort(key=lambda e: e.get("start", ""))

    if not near_events and not far_events:
        click.echo("No upcoming events in the next 7 days.")
        return

    # Terminal display
    click.echo(f"\n{'=' * 50}")
    click.echo("UPCOMING")
    click.echo(f"{'=' * 50}")

    if near_events:
        click.echo(f"\nNext 3 Days:")
        current_date = None
        for event in near_events:
            try:
                event_date = datetime.fromisoformat(event["start"]).strftime("%A %b %d")
            except (ValueError, KeyError):
                event_date = "?"
            if event_date != current_date:
                current_date = event_date
                click.echo(f"\n  {event_date}:")
            time_str = format_event_time(event)
            title = event.get("title", "Untitled")
            click.echo(f"    {time_str} - {title}")

    if far_events:
        click.echo(f"\nLater This Week (4-7 days):")
        current_date = None
        for event in far_events:
            try:
                event_date = datetime.fromisoformat(event["start"]).strftime("%A %b %d")
            except (ValueError, KeyError):
                event_date = "?"
            if event_date != current_date:
                current_date = event_date
                click.echo(f"\n  {event_date}:")
            time_str = format_event_time(event)
            title = event.get("title", "Untitled")
            click.echo(f"    {time_str} - {title}")

    click.echo(f"\n{'=' * 50}")

    # Optionally add to today's note
    if add_to_note:
        if not daily_note_exists(today):
            click.echo("Today's daily note doesn't exist yet. Create it in Obsidian first.")
            return

        # Check if upcoming section already exists
        note_content = read_daily_note(today) or ""
        if "## Upcoming (Next 3 Days)" in note_content:
            click.echo("Upcoming section already in today's note. Remove it first to refresh.")
            return

        lines = []
        lines.append("\n## Upcoming (Next 3 Days)")
        if near_events:
            current_date = None
            for event in near_events:
                try:
                    event_date = datetime.fromisoformat(event["start"]).strftime("%A %b %d")
                except (ValueError, KeyError):
                    event_date = ""
                if event_date != current_date:
                    current_date = event_date
                    lines.append(f"**{event_date}:**")
                lines.append(format_event_for_obsidian(event))
        else:
            lines.append("*(nothing scheduled)*")

        lines.append("\n## Upcoming (4-7 Days)")
        if far_events:
            current_date = None
            for event in far_events:
                try:
                    event_date = datetime.fromisoformat(event["start"]).strftime("%A %b %d")
                except (ValueError, KeyError):
                    event_date = ""
                if event_date != current_date:
                    current_date = event_date
                    lines.append(f"**{event_date}:**")
                lines.append(format_event_for_obsidian(event))
        else:
            lines.append("*(nothing scheduled)*")

        content = "\n".join(lines)
        if append_to_daily_note(today, content, section="# Today"):
            click.echo(f"\nAdded upcoming section to today's note ({len(near_events) + len(far_events)} events)")
        else:
            # Try appending without section targeting
            if append_to_daily_note(today, content):
                click.echo(f"\nAdded upcoming section to today's note ({len(near_events) + len(far_events)} events)")
            else:
                click.echo("Failed to update daily note")


@cli.command()
@click.option("--days", default=7, help="Keep notes from the last N days (default: 7)")
@click.option("--dry-run", is_flag=True, help="Show what would be moved without moving")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def archive(days, dry_run, yes):
    """Move daily notes older than N days to Archive/YYYY-MM subfolders."""
    daily_notes_path = get_daily_notes_path()
    archive_base = daily_notes_path / "Archive"
    cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)

    to_move = []
    for note_file in daily_notes_path.glob("*.md"):
        try:
            name = note_file.stem
            parts = name.split("-")
            if len(parts) >= 4:
                month = int(parts[0])
                day_num = int(parts[1])
                year = int(parts[3])
                note_date = datetime(year, month, day_num)
                if note_date < cutoff:
                    subfolder = note_date.strftime("%Y-%m")
                    dest_dir = archive_base / subfolder
                    to_move.append((note_file, dest_dir / note_file.name, note_date))
        except (ValueError, IndexError):
            continue

    to_move.sort(key=lambda x: x[2])

    if not to_move:
        click.echo(f"Nothing to archive (all notes are within {days} days).")
        return

    click.echo(f"Found {len(to_move)} notes to archive (older than {days} days):\n")
    for src, dest, date in to_move:
        click.echo(f"  {src.name} -> Archive/{dest.parent.name}/")

    if dry_run:
        click.echo("\n(dry run - no files moved)")
        return

    if not yes:
        if not click.confirm(f"\nMove {len(to_move)} notes to Archive?"):
            return

    moved = 0
    for src, dest, date in to_move:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            click.echo(f"  SKIP {src.name} - already exists in archive")
            continue
        src.rename(dest)
        moved += 1

    click.echo(f"\nArchived {moved} notes.")


def _parse_day(day_str: str) -> datetime:
    """Parse a day string into a datetime."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    day_lower = day_str.lower()

    if day_lower == "today":
        return today

    if day_lower == "tomorrow":
        return today + timedelta(days=1)

    if day_lower == "yesterday":
        return today - timedelta(days=1)

    # Day of week
    days = {
        "monday": 0, "mon": 0,
        "tuesday": 1, "tue": 1,
        "wednesday": 2, "wed": 2,
        "thursday": 3, "thu": 3,
        "friday": 4, "fri": 4,
        "saturday": 5, "sat": 5,
        "sunday": 6, "sun": 6,
    }

    if day_lower in days:
        target_weekday = days[day_lower]
        current_weekday = today.weekday()
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    # Try parsing as date
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d", "%m-%d-%Y", "%m-%d", "%B %d", "%b %d"):
        try:
            parsed = datetime.strptime(day_str, fmt)
            # If no year in format, use current year
            if parsed.year == 1900:
                parsed = parsed.replace(year=today.year)
            return parsed.replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            continue

    return None


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
