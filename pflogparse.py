#!/usr/bin/env python3

import re
import socket
import paramiko
import os

file_path = 'latest.log'  # Specify the path to the file you want to remove

try:
    # Check if the file exists before attempting to remove it
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File '{file_path}' has been successfully removed.")
    else:
        print(f"File '{file_path}' does not exist.")

except Exception as e:
    print(f"An error occurred: {e}")

# Replace these variables with your specific values
remote_host = '192.168.10.1'
remote_user = 'root'
remote_private_key = '/Users/3c3c1d/.ssh/id_rsa'
remote_file_path = '/var/log/filter/latest.log'
local_file_path = 'latest.log'  # The local path where you want to save the file

# Create an SSH client
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # Connect to the remote host using the SSH key
    ssh_key = paramiko.RSAKey.from_private_key_file(remote_private_key)
    ssh_client.connect(remote_host, username=remote_user, pkey=ssh_key)

    # SCP the remote file to the local machine
    scp_client = ssh_client.open_sftp()
    scp_client.get(remote_file_path, local_file_path)
    scp_client.close()

    print(f"File {remote_file_path} copied to {local_file_path} successfully.")

except paramiko.AuthenticationException:
    print("Authentication failed. Please check your SSH key or credentials.")
except paramiko.SSHException as e:
    print(f"SSH connection error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    ssh_client.close()

# Specify the path to your log file
log_file_path = 'latest.log'

# Open the log file for reading
with open(log_file_path, 'r') as log_file:
    # Iterate through each line in the file
    for log_line in log_file:
        # Process each log line here
        # For example, you can print the line or perform other operations
        #print(log_line.strip())  # .strip() removes leading and trailing whitespace

        # Regular expression pattern to extract IP addresses and port numbers
        pattern = r'(\d+\.\d+\.\d+\.\d+),(\d+\.\d+\.\d+\.\d+),(\d+),(\d+)'

        # Search for the pattern in the log line
        match = re.search(pattern, log_line)

        # Check if a match was found
        if match:
            # Extract the matched values
            source_ip = match.group(1)
            dest_ip = match.group(2)
            source_port = int(match.group(3))
            dest_port = int(match.group(4))
            
            # Print the extracted values
            print("Source IP:", source_ip)
            print("Destination IP:", dest_ip)
            print("Source Port:", source_port)
            print("Destination Port:", dest_port)
            try:
                dns_name, _, _ = socket.gethostbyaddr(dest_ip)
                print(f"DNS Name: {dns_name}")
            except socket.herror:
                print(f"Could not resolve IP address {dest_ip} to a hostname.")

            print("------")
        else:
            print("No match found in the log line.")
            print("------")
