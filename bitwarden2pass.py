#!/usr/bin/env python3
import csv
import argparse
import sys
import subprocess

def create_password_store_entry(entry_name, login_uri, login_username, login_password, login_totp, dry_run):
    """
    Create or simulate creation of an entry in the Password-Store with conditional TOTP field.
    """
    entry_path = f"imports/{entry_name.replace(' ', '_')}"
    entry_content = [f"{login_password}", f"Username: {login_username}", f"URL: {login_uri}"]
    # Include TOTP only if it's not empty, without the prefix "TOTP: "
    if login_totp:
        entry_content.append(f"{login_totp}")
    entry_data = '\n'.join(entry_content)
    if dry_run:
        # Print the full entry that would have been created
        print(f"--- DRY RUN ---\nEntry Path: {entry_path}\nEntry Content:\n{entry_data}")
    else:
        # Use 'pass insert' command to create the entry
        process = subprocess.Popen(['pass', 'insert', '--multiline', entry_path], stdin=subprocess.PIPE, text=True)
        process.communicate(entry_data)
        process.stdin.close()
        if process.returncode != 0:
            print(f"Failed to create entry for {entry_name}", file=sys.stderr)

def process_csv_file(file_path, dry_run):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header row
        for row in reader:
            name, uri, username, password, totp = row[3], row[7], row[8], row[9], row[10]
            create_password_store_entry(name, uri, username, password, totp, dry_run)

def main():
    parser = argparse.ArgumentParser(description='Process a CSV file for Password-Store entries using the "pass" command.')
    parser.add_argument('csv_file', type=str, help='Path to the CSV file')
    parser.add_argument('--dry_run', action='store_true', help='Print entries without creating them')

    args = parser.parse_args()

    try:
        process_csv_file(args.csv_file, args.dry_run)
    except Exception as e:
        print(f"Error processing file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()