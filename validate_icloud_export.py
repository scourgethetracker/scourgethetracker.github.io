#!/usr/bin/env python3

import sys
import re

def validate_line(line):
    """
    Validate the line with the format: Title,URL,Username,Password,Notes,OTPAuth
    Notes and OTPAuth are optional.
    """
    # Regular expression pattern for validation
    pattern = r'^[^,]+,[^,]+,[^,]+,[^,]+(,[^,]*)?(,[^,]*)?$'
    return re.match(pattern, line.strip()) is not None

def validate_file(file_path):
    """
    Validate each line of the file and print the validated lines.
    """
    with open(file_path, 'r') as file:
        for line_number, line in enumerate(file, start=1):
            if validate_line(line):
                print(line.strip())
            else:
                return f"{line_number}  -- NOTOK"
    return "OK"

def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_icloud_export.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    result = validate_file(file_path)
    print(result)

if __name__ == "__main__":
    main()

