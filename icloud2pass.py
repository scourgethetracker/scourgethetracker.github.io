#!/usr/bin/env python3

import sys
import subprocess

def create_pass_entry(input_line):
    # Splitting the input line into components
    components = input_line.strip().split(',')
    
    # Ensure at least 4 components (Title, URL, Username, Password) are present
    if len(components) < 4:
        print("Input format error. Expected format: Title,URL,Username,Password[,Notes[,OTPAuth]]")
        return
    
    # Prepend 'imports/' to the title to place it in the imports folder
    title = "imports/" + components[0]
    
    # Unpack components with optional Notes and OTPAuth
    url, username, password, *optional = components[1:]
    notes = optional[0] if len(optional) > 0 else ""
    otpauth = optional[1] if len(optional) > 1 else ""
    
    # Formatting the entry content
    entry_content = f"{password}\nUsername: {username}\nURL: {url}\n"
    if notes:
        entry_content += f"Notes: {notes}\n"
    if otpauth:
        entry_content += f"{otpauth}"
    
    # Creating the entry in pass
    try:
        # Using subprocess to interact with the 'pass' command
        result = subprocess.run(['pass', 'insert', '--multiline', title], input=entry_content, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error creating entry in pass: {e}")
    except FileNotFoundError:
        print("Error: 'pass' command not found. Ensure pass is installed and configured.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    else:
        print(f"Entry for '{title}' created successfully.")

def main():
    # Read from stdin
    try:
        input_line = sys.stdin.readline()
        create_pass_entry(input_line)
    except Exception as e:
        print(f"An error occurred while reading input: {e}")

if __name__ == "__main__":
    main()