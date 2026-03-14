"""Obsidian vault integration."""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config import get_config


def get_vault_path() -> Path:
    """Get path to Obsidian vault."""
    config = get_config()
    return Path(config.get("obsidian_vault", "~/vault")).expanduser()


def get_daily_notes_path() -> Path:
    """Get path to daily notes folder."""
    config = get_config()
    folder = config.get("daily_notes_folder", "Daily Notes")
    return get_vault_path() / folder


def get_daily_note_filename(date: datetime) -> str:
    """
    Get the filename for a daily note.

    Format: MM-DD-Ddd-YYYY.md (e.g., 01-20-Tue-2026.md)
    """
    return date.strftime("%m-%d-%a-%Y").replace(
        date.strftime("%a"),
        date.strftime("%a").capitalize()[:3]
    ) + ".md"


def get_daily_note_path(date: datetime) -> Path:
    """Get full path to a daily note."""
    # Format: 01-20-Tue-2026.md (zero-padded day)
    day_abbrev = date.strftime("%a")[:3].capitalize()
    filename = date.strftime(f"%m-%d-{day_abbrev}-%Y.md")
    return get_daily_notes_path() / filename


def daily_note_exists(date: datetime) -> bool:
    """Check if a daily note exists for a date."""
    return get_daily_note_path(date).exists()


def read_daily_note(date: datetime) -> Optional[str]:
    """Read the contents of a daily note."""
    path = get_daily_note_path(date)
    if not path.exists():
        return None
    try:
        return path.read_text()
    except IOError:
        return None


def get_incomplete_tasks(content: str) -> list[str]:
    """Extract incomplete tasks from note content."""
    # Match lines starting with - [ ] (not - [x] or - [-])
    pattern = r"^- \[ \] .+$"
    return re.findall(pattern, content, re.MULTILINE)


def get_completed_tasks(content: str) -> list[str]:
    """Extract completed tasks from note content."""
    pattern = r"^- \[x\] .+$"
    return re.findall(pattern, content, re.MULTILINE)


def get_cancelled_tasks(content: str) -> list[str]:
    """Extract cancelled tasks from note content."""
    pattern = r"^- \[-\] .+$"
    return re.findall(pattern, content, re.MULTILINE)


def extract_calendar_items(content: str) -> list[dict]:
    """
    Extract calendar items from a daily note.

    Looks for items in the calendar sections with format:
    - TIME - TITLE or - All day - TITLE

    Returns:
        List of dicts with 'time', 'title', 'raw' keys
    """
    items = []

    # Pattern for calendar items: "- TIME - TITLE" or "- All day - TITLE"
    # Matches lines like:
    #   - 9 AM - Meeting name
    #   - 2:30 PM - Another meeting
    #   - All day - Event name
    pattern = r"^- ((?:\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))|All day) - (.+)$"

    for line in content.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            items.append({
                "time": match.group(1),
                "title": match.group(2).strip(),
                "raw": line.strip()
            })

    return items


def find_misnamed_notes() -> list[tuple[Path, Path]]:
    """
    Find daily notes with inconsistent naming format.

    Identifies notes where the day portion is single-digit when it should be
    zero-padded (e.g., 01-1-Thu-2026.md instead of 01-01-Thu-2026.md).

    Returns:
        List of (old_path, new_path) tuples for misnamed files
    """
    daily_notes_path = get_daily_notes_path()
    misnamed = []

    if not daily_notes_path.exists():
        return misnamed

    # Pattern to match MM-D-Ddd-YYYY.md or similar (single-digit day)
    # Valid format: MM-DD-Ddd-YYYY.md
    pattern = r"^(\d{2})-(\d{1,2})-([A-Za-z]{3})-(\d{4})\.md$"

    for note_file in daily_notes_path.glob("*.md"):
        match = re.match(pattern, note_file.name)
        if match:
            month_str = match.group(1)
            day_str = match.group(2)
            day_abbrev = match.group(3)
            year_str = match.group(4)

            # Check if day is single-digit (needs zero-padding)
            if len(day_str) == 1:
                # This is a misnamed file
                new_name = f"{month_str}-{int(day_str):02d}-{day_abbrev}-{year_str}.md"
                new_path = daily_notes_path / new_name
                misnamed.append((note_file, new_path))

    return misnamed


def rename_note(old_path: Path, new_path: Path) -> bool:
    """
    Rename a note file.

    Args:
        old_path: Current path to the file
        new_path: New path for the file

    Returns:
        True if successful
    """
    try:
        old_path.rename(new_path)
        return True
    except (IOError, OSError):
        return False


def fix_internal_links(content: str, old_name: str, new_name: str) -> str:
    """
    Update internal links in note content.

    Replaces [[old_name]] with [[new_name]].

    Args:
        content: Note content
        old_name: Old note stem/name (without .md)
        new_name: New note stem/name (without .md)

    Returns:
        Updated content
    """
    # Replace [[old_name]] with [[new_name]]
    return content.replace(f"[[{old_name}]]", f"[[{new_name}]]")


def find_obsolete_tasks(days_threshold: int = 14) -> list[dict]:
    """
    Find incomplete tasks older than threshold.

    Args:
        days_threshold: Number of days after which tasks are obsolete

    Returns:
        List of dicts with 'file', 'line_number', 'task', 'date' keys
    """
    daily_notes_path = get_daily_notes_path()
    cutoff_date = datetime.now() - timedelta(days=days_threshold)
    obsolete = []

    if not daily_notes_path.exists():
        return obsolete

    for note_file in daily_notes_path.glob("*.md"):
        # Parse date from filename (MM-DD-Ddd-YYYY.md)
        try:
            # Extract date parts from filename like 01-20-Tue-2026.md
            name = note_file.stem
            parts = name.split("-")
            if len(parts) >= 4:
                month = int(parts[0])
                day = int(parts[1])
                year = int(parts[3])
                note_date = datetime(year, month, day)

                if note_date < cutoff_date:
                    content = note_file.read_text()
                    lines = content.split("\n")

                    for i, line in enumerate(lines):
                        if re.match(r"^- \[ \] ", line):
                            obsolete.append({
                                "file": note_file,
                                "line_number": i + 1,
                                "task": line,
                                "date": note_date
                            })
        except (ValueError, IndexError):
            continue

    # Sort by date (oldest first)
    obsolete.sort(key=lambda x: x["date"])
    return obsolete


def mark_task_cancelled(file_path: Path, line_number: int, cancel_date: datetime = None) -> bool:
    """
    Mark a task as cancelled.

    Changes "- [ ]" to "- [-]" and adds cancellation date.

    Args:
        file_path: Path to the note file
        line_number: 1-indexed line number
        cancel_date: Date to record as cancellation (defaults to today)

    Returns:
        True if successful
    """
    if cancel_date is None:
        cancel_date = datetime.now()

    try:
        content = file_path.read_text()
        lines = content.split("\n")

        if 0 < line_number <= len(lines):
            line = lines[line_number - 1]
            if line.startswith("- [ ] "):
                # Replace checkbox and add cancellation date
                new_line = line.replace("- [ ] ", "- [-] ", 1)
                if "❌" not in new_line:
                    new_line += f" ❌ {cancel_date.strftime('%Y-%m-%d')}"
                lines[line_number - 1] = new_line

                file_path.write_text("\n".join(lines))
                return True

    except IOError:
        pass

    return False


def clear_obsolete_tasks(days_threshold: int = 14) -> dict:
    """
    Mark all obsolete tasks as cancelled.

    Returns:
        dict with 'cleared_count', 'files_modified', 'errors'
    """
    obsolete = find_obsolete_tasks(days_threshold)
    cancel_date = datetime.now()

    cleared = 0
    files_modified = set()
    errors = []

    for task in obsolete:
        if mark_task_cancelled(task["file"], task["line_number"], cancel_date):
            cleared += 1
            files_modified.add(task["file"])
        else:
            errors.append(f"Failed to clear: {task['file'].name}:{task['line_number']}")

    return {
        "cleared_count": cleared,
        "files_modified": len(files_modified),
        "errors": errors
    }


def insert_under_heading(date: datetime, heading: str, content: str,
                        placeholder: str = None) -> bool:
    """
    Insert content under an existing heading in a daily note.

    Finds the heading, optionally removes a placeholder line beneath it,
    and inserts the new content between the heading and the next section.

    Args:
        date: Date of the note
        heading: The heading to insert under (e.g., '## Added from Calendar')
        content: Content to insert (without the heading itself)
        placeholder: Optional placeholder text to remove (e.g., '*(Run `daynote add today` to populate)*')

    Returns:
        True if successful
    """
    path = get_daily_note_path(date)
    if not path.exists():
        return False

    try:
        existing = path.read_text()

        # Find the heading
        heading_pattern = re.escape(heading)
        match = re.search(f"^{heading_pattern}\\s*$", existing, re.MULTILINE)
        if not match:
            return False

        # Find the end of the heading line
        after_heading = match.end()

        # Find the next heading (any level) or end of file
        rest = existing[after_heading:]
        next_heading = re.search(r"^#{1,6} ", rest, re.MULTILINE)

        if next_heading:
            section_end = after_heading + next_heading.start()
        else:
            section_end = len(existing)

        # Get the content between heading and next section
        between = existing[after_heading:section_end]

        # Remove placeholder if specified
        if placeholder:
            between = between.replace(placeholder, "")

        # Remove any leftover blank lines from placeholder removal
        between = between.strip()

        # Build the new section content
        new_section = "\n" + content + "\n\n"

        # Reconstruct the file
        new_content = existing[:after_heading] + new_section + existing[section_end:]
        path.write_text(new_content)
        return True

    except IOError:
        return False


def append_to_daily_note(date: datetime, content: str, section: str = None) -> bool:
    """
    Append content to a daily note.

    Args:
        date: Date of the note
        content: Content to append
        section: Optional section header to append after (e.g., "# To do List")

    Returns:
        True if successful
    """
    path = get_daily_note_path(date)

    if not path.exists():
        return False

    try:
        existing = path.read_text()

        if section:
            # Find the section and append after it
            section_pattern = re.escape(section)
            match = re.search(f"^{section_pattern}.*$", existing, re.MULTILINE)

            if match:
                # Find the end of the section (next # heading or end of file)
                section_end = match.end()
                rest = existing[section_end:]

                # Find next heading
                next_heading = re.search(r"^\n#", rest)
                if next_heading:
                    insert_pos = section_end + next_heading.start()
                else:
                    insert_pos = len(existing)

                # Insert content
                new_content = existing[:insert_pos].rstrip() + "\n" + content + "\n" + existing[insert_pos:]
                path.write_text(new_content)
                return True

        # No section specified or not found - append at end
        path.write_text(existing.rstrip() + "\n\n" + content + "\n")
        return True

    except IOError:
        return False


def item_exists_in_note(date: datetime, item_title: str) -> bool:
    """
    Check if an item (calendar event or task) already exists in a note.

    Uses fuzzy matching - checks if the title appears in the note.

    Args:
        date: Date of the note to check
        item_title: Title to search for

    Returns:
        True if found
    """
    content = read_daily_note(date)
    if not content:
        return False

    # Normalize for comparison
    normalized_title = item_title.lower().strip()
    normalized_content = content.lower()

    return normalized_title in normalized_content


def get_all_daily_note_dates() -> list[datetime]:
    """Get dates of all existing daily notes."""
    daily_notes_path = get_daily_notes_path()
    dates = []

    if not daily_notes_path.exists():
        return dates

    for note_file in daily_notes_path.glob("*.md"):
        try:
            name = note_file.stem
            parts = name.split("-")
            if len(parts) >= 4:
                month = int(parts[0])
                day = int(parts[1])
                year = int(parts[3])
                dates.append(datetime(year, month, day))
        except (ValueError, IndexError):
            continue

    dates.sort()
    return dates
