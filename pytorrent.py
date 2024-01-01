#!/usr/bin/env python3

import subprocess
import sys
import os
import configparser

def read_config():
    config = configparser.ConfigParser()
    config_path = os.path.expanduser('./.pytorrent.conf')

    if not os.path.exists(config_path):
        return 50  # Default max peers value if config file doesn't exist

    config.read(config_path)
    max_peers = config.getint('settings', 'max_peers', fallback=50)
    download_dir = config('settings', 'download_dir', falback='~/Downloads')
    method = config('settings', 'method', fallback=prealloc)

    return max_peers

def download_torrent(magnet_link, max_peers):
    # Construct the command to use Aria2
    aria2_command = [
        'aria2c',
        '--bt-max-peers={}'.format(max_peers),
        '--dir={}'.format(download_dir),
        '--file-allocation={}'.format(method),
        magnet_link
    ]

    # Start the download
    print("Starting download with Aria2...")
    subprocess.run(aria2_command)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pytorrent.py magnet_link")
        sys.exit(1)

    magnet_link = sys.argv[1]
    max_peers = read_config()
    download_torrent(magnet_link, max_peers)

