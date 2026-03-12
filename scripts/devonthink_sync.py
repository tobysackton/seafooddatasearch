#!/usr/bin/env python3
import os
import shutil
import datetime
import subprocess
import json
import time
from pathlib import Path

# Define the directories
user_home = os.path.expanduser("~")
documents_dir = os.path.join(user_home, "Documents")
current_dir = os.path.join(documents_dir, "text_current")
archive_dir = os.path.join(documents_dir, "text_archive")

# File extensions to process
text_extensions = ['.doc', '.docx', '.txt', '.rtf', '.xls', '.xlsx', '.pdf', '.pages', '.numbers', '.key']

# Directories to ignore 
ignored_directories = [
    current_dir,
    archive_dir,
    os.path.join(documents_dir, "Library"),
    # Add more directories to ignore as needed
]

# Test period: Jan 20-27, 2025
TEST_START_DATE = datetime.datetime(2025, 1, 20)
TEST_END_DATE = datetime.datetime(2025, 1, 27, 23, 59, 59)

def is_ignored_directory(path):
    """Check if the directory should be ignored."""
    for ignored_dir in ignored_directories:
        if os.path.normpath(path).startswith(os.path.normpath(ignored_dir)):
            return True
    return False

def get_file_date(file_path):
    """Get the modification date of a file."""
    return datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

def is_in_test_period(file_path):
    """Check if file's modification date is within our test period."""
    file_date = get_file_date(file_path)
    return TEST_START_DATE <= file_date <= TEST_END_DATE

def is_icloud_downloaded(file_path):
    """
    Check if an iCloud file is fully downloaded to local storage.
    """
    try:
        # Try a simpler approach first - check if file exists and has size
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return False
            
        # Try to run mdls command
        try:
            result = subprocess.run(
                ['mdls', '-name', 'kMDItemCloudDocumentRelativePathKey', '-json', file_path], 
                capture_output=True, 
                text=True,
                timeout=5  # Add timeout to prevent hanging
            )
            
            # If command successful, try to parse the JSON
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    has_cloud_path = data.get('kMDItemCloudDocumentRelativePathKey') is not None
                    
                    if has_cloud_path:
                        # It's an iCloud file, check if downloaded
                        try:
                            attr_result = subprocess.run(
                                ['xattr', '-p', 'com.apple.metadata:com_apple_backup_excludeItem', file_path], 
                                capture_output=True,
                                timeout=5
                            )
                            # If this attribute exists, file is not fully downloaded
                            return attr_result.returncode != 0
                        except Exception:
                            # If xattr fails, assume it's downloaded
                            return True
                    
                    # Not an iCloud file
                    return True
                except json.JSONDecodeError:
                    # If JSON parsing fails, try a different approach
                    # Check if the output contains "null" for the cloud path
                    if "(null)" in result.stdout:
                        return True  # Not an iCloud file
                    elif "kMDItemCloudDocumentRelativePathKey" in result.stdout:
                        # It's an iCloud file, check with xattr as a backup
                        try:
                            attr_result = subprocess.run(
                                ['xattr', '-l', file_path], 
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            # If the output contains backup exclude flag, it's not downloaded
                            return "com.apple.metadata:com_apple_backup_excludeItem" not in attr_result.stdout
                        except Exception:
                            return True
                    else:
                        return True  # Assume downloaded if we can't determine
            else:
                # mdls command failed, assume the file is local
                return True
                
        except subprocess.TimeoutExpired:
            print(f"Command timed out for {file_path}")
            return True  # Assume downloaded
            
    except Exception as e:
        print(f"Warning: Could not determine iCloud status for {file_path}: {e}")
        # Assume it's downloaded rather than skipping
        return True

def download_icloud_file(file_path):
    """
    Force download of an iCloud file.
    """
    if is_icloud_downloaded(file_path):
        return True
        
    try:
        subprocess.run(['brctl', 'download', file_path], check=True)
        
        for _ in range(60):
            if is_icloud_downloaded(file_path):
                return True
            time.sleep(1)
            
        return False
    except Exception as e:
        print(f"Error downloading {file_path}: {e}")
        return False

def file_needs_update(source_path, dest_path):
    """Check if the destination file needs to be updated (different or newer source)."""
    # If destination doesn't exist, it definitely needs an update
    if not os.path.exists(dest_path):
        return True
        
    # Check if source is newer than destination
    source_mtime = os.path.getmtime(source_path)
    dest_mtime = os.path.getmtime(dest_path)
    
    # If modification times differ by more than 1 second, update
    return abs(source_mtime - dest_mtime) > 1

def process_icloud_files():
    """Find and process all text files in iCloud Documents within test period."""
    print(f"Starting iCloud files processing at {datetime.datetime.now()}")
    print(f"Test period: {TEST_START_DATE.strftime('%Y-%m-%d')} to {TEST_END_DATE.strftime('%Y-%m-%d')}")
    
    # Track all files that should be in text_current
    current_files = set()
    files_processed = 0
    files_in_test_period = 0
    
    # Find all text files in Documents and subdirectories
    for root, dirs, files in os.walk(documents_dir):
        # Skip ignored directories
        if is_ignored_directory(root):
            dirs[:] = []  # Clear the dirs list to prevent os.walk from traversing subdirectories
            continue
            
        for filename in files:
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in text_extensions:
                files_processed += 1
                source_path = os.path.join(root, filename)
                
                # Skip if the file is just an iCloud placeholder and we can't download it
                if not is_icloud_downloaded(source_path):
                    print(f"Attempting to download: {filename}")
                    if not download_icloud_file(source_path):
                        print(f"Skipping placeholder file (not downloaded): {filename}")
                        continue
                
                # Check if file is in our test period
                try:
                    if is_in_test_period(source_path):
                        files_in_test_period += 1
                        # Calculate the relative path from documents_dir
                        rel_path = os.path.relpath(root, documents_dir)
                        
                        # Create the same directory structure in text_current
                        if rel_path != '.':  # If not in the root of documents_dir
                            target_dir = os.path.join(current_dir, rel_path)
                            os.makedirs(target_dir, exist_ok=True)
                            dest_path = os.path.join(target_dir, filename)
                        else:
                            dest_path = os.path.join(current_dir, filename)
                        
                        # Add to set of files that should be in current
                        current_files.add(os.path.normpath(dest_path))
                        
                        # Check if file needs to be updated
                        if file_needs_update(source_path, dest_path):
                            print(f"Copying to current: {os.path.relpath(dest_path, current_dir)}")
                            shutil.copy2(source_path, dest_path)
                            
                            # Ensure the file is downloaded locally
                            subprocess.run(['brctl', 'download', dest_path], check=False)
                except Exception as e:
                    print(f"Error processing {source_path}: {e}")
    
    # Clean up files in current that shouldn't be there anymore
    # (files that are outside our test period)
    files_removed = 0
    for root, dirs, files in os.walk(current_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            if os.path.normpath(file_path) not in current_files:
                # This file should no longer be in text_current
                print(f"Removing file outside test period: {os.path.relpath(file_path, current_dir)}")
                files_removed += 1
                os.remove(file_path)
    
    # Clean up empty directories in text_current
    dirs_removed = 0
    for root, dirs, files in os.walk(current_dir, topdown=False):
        for dirname in dirs:
            dir_path = os.path.join(root, dirname)
            if not os.listdir(dir_path):  # Check if directory is empty
                os.rmdir(dir_path)
                dirs_removed += 1
                print(f"Removed empty directory: {os.path.relpath(dir_path, current_dir)}")
                
    print(f"Test run summary:")
    print(f"  Total files processed: {files_processed}")
    print(f"  Files within test period: {files_in_test_period}")
    print(f"  Files removed from text_current: {files_removed}")
    print(f"  Empty directories removed: {dirs_removed}")

def main():
    # Create directories if they don't exist
    os.makedirs(current_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)
    
    process_icloud_files()
    print("Processing complete. DEVONthink should now be able to index the text_current folder.")
    print(f"Files from {TEST_START_DATE.strftime('%Y-%m-%d')} to {TEST_END_DATE.strftime('%Y-%m-%d')} have been copied to {current_dir}")

if __name__ == "__main__":
    main()