#!/usr/bin/env python3
import os
import subprocess
import datetime
import json
import time

# Define directories and test period
user_home = os.path.expanduser("~")
documents_dir = os.path.join(user_home, "Documents")
ignored_directories = [
    os.path.join(documents_dir, "text_current"),
    os.path.join(documents_dir, "text_archive"),
    os.path.join(documents_dir, "Library"),
]

# File extensions to process
text_extensions = ['.doc', '.docx', '.txt', '.rtf', '.xls', '.xlsx', '.pdf', '.pages', '.numbers', '.key']

# Test period: Jan 20-27, 2025
TEST_START_DATE = datetime.datetime(2025, 1, 20)
TEST_END_DATE = datetime.datetime(2025, 1, 27, 23, 59, 59)

def is_ignored_directory(path):
    for ignored_dir in ignored_directories:
        if os.path.normpath(path).startswith(os.path.normpath(ignored_dir)):
            return True
    return False

def get_file_date(file_path):
    return datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

def is_in_test_period(file_path):
    file_date = get_file_date(file_path)
    return TEST_START_DATE <= file_date <= TEST_END_DATE

def is_icloud_downloaded(file_path):
    """Check if file is downloaded from iCloud with better error handling."""
    try:
        # Basic check - if file doesn't exist or has zero size, it's not downloaded
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return False
            
        # Use mdls to check if it's an iCloud file
        result = subprocess.run(
            ['mdls', '-name', 'kMDItemCloudDocumentRelativePathKey', file_path], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        
        # If mdls shows a null value, it's not an iCloud file (or is already downloaded)
        if "(null)" in result.stdout:
            return True
            
        # If there's a cloud path but no eviction attribute, it's downloaded
        if "kMDItemCloudDocumentRelativePathKey" in result.stdout:
            attr_result = subprocess.run(
                ['xattr', '-l', file_path], 
                capture_output=True,
                text=True,
                timeout=5
            )
            return "com.apple.metadata:com_apple_backup_excludeItem" not in attr_result.stdout
            
        # Default to True if we can't determine
        return True
            
    except Exception as e:
        print(f"Warning: Could not check iCloud status for {file_path}: {e}")
        return False  # Assume not downloaded if there's an error

def download_icloud_file(file_path):
    """Force download an iCloud file."""
    if is_icloud_downloaded(file_path):
        return True
        
    print(f"Downloading: {os.path.basename(file_path)}")
    try:
        # Use brctl to start the download
        subprocess.run(['brctl', 'download', file_path], check=False)
        return True  # Return success immediately - we're not waiting in this script
    except Exception as e:
        print(f"Error downloading {file_path}: {e}")
        return False

def main():
    print(f"Starting iCloud downloads at {datetime.datetime.now()}")
    print(f"Looking for files from {TEST_START_DATE.strftime('%Y-%m-%d')} to {TEST_END_DATE.strftime('%Y-%m-%d')}")
    
    files_to_download = []
    downloaded_count = 0
    already_local_count = 0
    
    # First pass: Find all relevant files
    print("Scanning for files within test period...")
    for root, dirs, files in os.walk(documents_dir):
        if is_ignored_directory(root):
            dirs[:] = []  # Skip subdirectories
            continue
            
        for filename in files:
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in text_extensions:
                file_path = os.path.join(root, filename)
                
                try:
                    if is_in_test_period(file_path):
                        files_to_download.append(file_path)
                except Exception as e:
                    print(f"Error checking date for {file_path}: {e}")
    
    print(f"Found {len(files_to_download)} files in test period")
    
    # Second pass: Download all files
    for file_path in files_to_download:
        if not is_icloud_downloaded(file_path):
            if download_icloud_file(file_path):
                downloaded_count += 1
        else:
            already_local_count += 1
    
    print("\nDownload Summary:")
    print(f"  Files already local: {already_local_count}")
    print(f"  Downloads initiated: {downloaded_count}")
    print(f"  Total files: {len(files_to_download)}")
    print("\nDownload requests have been initiated. You may need to wait")
    print("for downloads to complete before running the copy script.")
    print("Check Finder to see download progress.")

if __name__ == "__main__":
    main()
