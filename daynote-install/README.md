# DayNote

A command-line productivity dashboard that syncs your Obsidian daily notes with Apple Calendar and Gmail.

## Quick Start

```bash
cd /Users/jtsackton/daynote-install
pip3 install -e .
daynote init
```

## Setup

1. Edit `~/.daynote/config.yaml`:
```yaml
obsidian_vault: /Users/jtsackton/vault
daily_notes_folder: Daily Notes
gmail_accounts:
  - tsackton@gmail.com
  - jsackton@seafoodlink.com
```

2. Copy your Gmail credentials:
```bash
cp /path/to/credentials.json ~/.daynote/
```

3. Copy the calendar script:
```bash
cp /Users/jtsackton/daynote-install/scripts/refresh_calendar.scpt ~/.daynote/
```

## Commands

| Command | Description |
|---------|-------------|
| `daynote sync` | Refresh calendar/Gmail and show today |
| `daynote show today` | Show today's report |
| `daynote show tomorrow` | Preview tomorrow |
| `daynote week` | 7-day summary |
| `daynote add today` | Add items to today's note |
| `daynote status "name"` | Search Gmail for person |
| `daynote obsolete` | Show old tasks |
| `daynote clear-obsolete` | Mark old tasks cancelled |

Alias: `dn` works the same as `daynote`
