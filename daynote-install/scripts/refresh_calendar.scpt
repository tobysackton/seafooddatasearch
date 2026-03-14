#!/bin/bash

# DayNote Calendar Refresh Script
# Uses icalBuddy for fast calendar access
# Only searches Personal, Meetings, and Social Events calendars

OUTPUT_PATH="$HOME/.daynote/calendar.json"
mkdir -p "$HOME/.daynote"

# Get events for next 14 days using icalBuddy
# Format: title | start | end | calendar | location | notes | allday
EVENTS=$(icalBuddy -ic "personal,Meetings,Social Events" -nf -ea -b "" -nc -nrd \
    -ps "| : |" -po "title,datetime,location,notes" \
    -df "%Y-%m-%dT%H:%M:00" -tf "" \
    eventsFrom:today to:today+14d 2>/dev/null)

# Get current timestamp
REFRESH_TIME=$(date +"%Y-%m-%dT%H:%M:%S")

# Convert to JSON using Python
python3 << PYTHON
import json
import re
from datetime import datetime, timedelta

events = []
raw_output = '''$EVENTS'''

# Parse icalBuddy output
current_cal = "Personal"
for line in raw_output.strip().split('\n'):
    if not line.strip():
        continue

    # Check if this is a calendar header
    if line.strip() in ['Personal', 'Meetings', 'Social Events']:
        current_cal = line.strip()
        continue

    # Try to parse event line
    # Format varies, but typically: title (location) datetime
    line = line.strip()
    if not line or line.startswith('•'):
        line = line.lstrip('• ').strip()

    if not line:
        continue

    # Extract datetime pattern
    dt_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
    if dt_match:
        start_str = dt_match.group(1)
        title = line[:dt_match.start()].strip().rstrip(' -:')

        # Check for location in parentheses
        loc_match = re.search(r'\(([^)]+)\)\s*$', title)
        location = ""
        if loc_match:
            location = loc_match.group(1)
            title = title[:loc_match.start()].strip()

        # Calculate end time (1 hour default)
        try:
            start_dt = datetime.fromisoformat(start_str)
            end_dt = start_dt + timedelta(hours=1)
            end_str = end_dt.strftime('%Y-%m-%dT%H:%M:%S')
        except:
            end_str = start_str

        events.append({
            'title': title,
            'start': start_str,
            'end': end_str,
            'calendar': current_cal,
            'location': location,
            'notes': '',
            'all_day': False
        })

output = {
    'refreshed': '$REFRESH_TIME',
    'events': events
}

with open('$OUTPUT_PATH', 'w') as f:
    json.dump(output, f, indent=2)

print(f"Calendar refreshed: {len(events)} events exported to $OUTPUT_PATH")
PYTHON
