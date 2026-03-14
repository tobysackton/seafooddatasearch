#!/usr/bin/env python3
"""
WPForms Direct Database Export
==============================
Lexington Alarm - Simple Form Data Export

Connects directly to WordPress MySQL database and exports
WPForms entries to CSV files in Proton Drive folder.

No PHP, no REST API, no deletion - just reliable CSV export.
"""

import os
import csv
import json
import mysql.connector
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURATION - Edit these values as needed
# ============================================================

# Database connection (Bluehost Remote MySQL)
DB_CONFIG = {
    'host': '50.6.2.226',
    'database': 'ozpxkamy_WPJYZ',
    'user': 'ozpxkamy_WPJYZ',
    'password': '#P]%q{UdhplXiK@fR',
    'charset': 'utf8',
    'connection_timeout': 30
}

# WordPress table prefix
TABLE_PREFIX = 'vcS_'

# Massport campaign forms to combine into single CSV
MASSPORT_FORMS = [
    {'id': 1510, 'name': 'massport-governor'},
    {'id': 1478, 'name': 'massport-email'},
    {'id': 1401, 'name': 'massport-board-letters'},
]

# Output folder (Proton Drive) — uses home directory so works on both Gadus and Sardinia
OUTPUT_FOLDER = str(Path.home() / 'Library/CloudStorage/ProtonDrive-info@lexingtonalarm.org-folder/LexingtonAlarm Executive/WP_Form_Data_Files')

# ============================================================
# MAIN SCRIPT - No need to edit below this line
# ============================================================

def get_existing_entry_keys(csv_path):
    """Read existing entry keys (form_id-entry_id) from CSV to avoid duplicates."""
    existing_keys = set()
    if csv_path.exists():
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'entry_id' in row and 'form_id' in row:
                        key = f"{row['form_id']}-{row['entry_id']}"
                        existing_keys.add(key)
        except Exception as e:
            print(f"  Warning: Could not read existing CSV: {e}")
    return existing_keys


def format_zip_code(value):
    """Format ZIP code to preserve leading zeros.
    
    Handles:
    - 5-digit ZIPs: "2421" -> "02421"
    - 9-digit ZIPs: "024211234" or "02421-1234" -> "02421-1234"
    - Empty/None values
    """
    if not value:
        return value
    
    # Remove any existing dashes and spaces
    clean_zip = str(value).replace('-', '').replace(' ', '').strip()
    
    # Skip if not numeric (might be non-US or invalid)
    if not clean_zip.isdigit():
        return value
    
    # 5-digit ZIP: pad with leading zeros
    if len(clean_zip) <= 5:
        return clean_zip.zfill(5)
    
    # 9-digit ZIP: format as XXXXX-XXXX
    if len(clean_zip) == 9:
        return f"{clean_zip[:5].zfill(5)}-{clean_zip[5:]}"
    
    # Other lengths: return as-is
    return value


def parse_fields(fields_json):
    """Parse WPForms fields JSON into flat dictionary."""
    fields = {}
    hidden_fields = {}
    if not fields_json:
        return fields, hidden_fields
    
    try:
        data = json.loads(fields_json)
        if isinstance(data, dict):
            for field_id, field_data in data.items():
                if isinstance(field_data, dict):
                    name = field_data.get('name', f'field_{field_id}')
                    value = field_data.get('value', '')
                    field_type = field_data.get('type', '')
                    
                    # Clean field name for CSV header
                    clean_name = name.lower().replace(' ', '_').replace('-', '_')
                    clean_name = ''.join(c for c in clean_name if c.isalnum() or c == '_')
                    
                    # Format ZIP codes to preserve leading zeros
                    if 'zip' in clean_name.lower():
                        value = format_zip_code(value)
                    
                    # Track hidden fields separately
                    if field_type == 'hidden':
                        hidden_fields[f"hidden_{clean_name}"] = value
                    
                    fields[clean_name] = value
                else:
                    fields[f'field_{field_id}'] = str(field_data)
    except json.JSONDecodeError:
        pass
    
    return fields, hidden_fields


def export_combined_massport(cursor, forms, output_folder):
    """Export entries from multiple forms into a single combined CSV."""
    print(f"\nProcessing combined Massport forms...")
    
    # Generate CSV filename with current month
    now = datetime.now()
    csv_filename = f"massport_all-{now.year}-{str(now.month).zfill(2)}.csv"
    csv_path = Path(output_folder) / csv_filename
    
    # Get existing entry keys to avoid duplicates
    existing_keys = get_existing_entry_keys(csv_path)
    print(f"  Existing entries in CSV: {len(existing_keys)}")
    
    # Build form ID to name mapping
    form_id_to_name = {form['id']: form['name'] for form in forms}
    form_ids = [form['id'] for form in forms]
    
    # Query database for entries from all forms
    table_name = f"{TABLE_PREFIX}wpforms_entries"
    placeholders = ', '.join(['%s'] * len(form_ids))
    query = f"""
        SELECT DISTINCT entry_id, form_id, user_id, status, 
               fields, date, date_modified, ip_address, user_agent
        FROM {table_name}
        WHERE form_id IN ({placeholders})
        ORDER BY date ASC, entry_id ASC
    """
    
    cursor.execute(query, form_ids)
    entries = cursor.fetchall()
    print(f"  Total entries in database across {len(forms)} forms: {len(entries)}")
    
    # Show per-form counts
    for form in forms:
        form_count = sum(1 for e in entries if e['form_id'] == form['id'])
        print(f"    - {form['name']} (ID {form['id']}): {form_count} entries")
    
    if not entries:
        print(f"  No entries found")
        return 0
    
    # Filter to only new entries
    new_entries = []
    for entry in entries:
        key = f"{entry['form_id']}-{entry['entry_id']}"
        if key not in existing_keys:
            new_entries.append(entry)
    
    print(f"  New entries to add: {len(new_entries)}")
    
    if not new_entries:
        print(f"  No new entries to export")
        return 0
    
    # Parse all entries and collect all field names
    parsed_entries = []
    all_field_names = set()
    all_hidden_names = set()
    
    for entry in new_entries:
        form_name = form_id_to_name.get(entry['form_id'], f"form_{entry['form_id']}")
        
        parsed = {
            'entry_id': entry['entry_id'],
            'form_id': entry['form_id'],
            'form_name': form_name,
            'date_created': entry['date'].isoformat() if entry['date'] else '',
            'date_modified': entry['date_modified'].isoformat() if entry.get('date_modified') else '',
            'status': entry.get('status', ''),
            'user_id': entry.get('user_id', ''),
            'ip_address': entry.get('ip_address', ''),
            'export_timestamp': now.isoformat()
        }
        
        # Parse form fields (including hidden fields)
        fields, hidden_fields = parse_fields(entry.get('fields', ''))
        parsed.update(fields)
        parsed.update(hidden_fields)
        all_field_names.update(fields.keys())
        all_hidden_names.update(hidden_fields.keys())
        
        parsed_entries.append(parsed)
    
    # Determine CSV headers - put form_name early, hidden fields at end
    standard_headers = ['entry_id', 'form_id', 'form_name', 'date_created', 'date_modified', 
                       'status', 'user_id', 'ip_address', 'export_timestamp']
    field_headers = sorted([f for f in all_field_names if not f.startswith('hidden_')])
    hidden_headers = sorted(list(all_hidden_names))
    
    # If file exists, read existing headers
    if csv_path.exists():
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            existing_headers = next(reader, [])
            # Merge headers (keep existing order, add new ones at end)
            for header in standard_headers + field_headers + hidden_headers:
                if header not in existing_headers:
                    existing_headers.append(header)
            all_headers = existing_headers
    else:
        all_headers = standard_headers + field_headers + hidden_headers
    
    # Write to CSV
    file_exists = csv_path.exists()
    mode = 'a' if file_exists else 'w'
    
    with open(csv_path, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=all_headers, extrasaction='ignore')
        
        if not file_exists:
            writer.writeheader()
        
        for entry in parsed_entries:
            writer.writerow(entry)
    
    print(f"  ✓ Added {len(parsed_entries)} entries to {csv_filename}")
    return len(parsed_entries)


def main():
    """Main entry point."""
    print("=" * 60)
    print("WPForms Direct Database Export")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Ensure output folder exists
    output_path = Path(OUTPUT_FOLDER)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    print(f"\nConnecting to database at {DB_CONFIG['host']}...")
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        print("✓ Connected successfully")
    except mysql.connector.Error as e:
        print(f"✗ Database connection failed: {e}")
        return 1
    
    # Export combined Massport forms
    total_exported = 0
    
    try:
        count = export_combined_massport(cursor, MASSPORT_FORMS, OUTPUT_FOLDER)
        total_exported += count
    except Exception as e:
        print(f"\n✗ Error during export: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        cursor.close()
        connection.close()
        print("\n✓ Database connection closed")
    
    # Summary
    print("\n" + "=" * 60)
    print("Export Complete!")
    print(f"  Total new entries exported: {total_exported}")
    print(f"  Output folder: {OUTPUT_FOLDER}")
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())
