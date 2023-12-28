#!/usr/bin/env python3
import configparser
import paramiko

def load_config(config_file='remote-memmon.conf'):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def get_ram_usage(ssh):
    try:
        stdin, stdout, stderr = ssh.exec_command("free -m")
        for line in stdout:
            if "Mem:" in line:
                total_ram, used_ram, *_ = line.split()[1:]
                return int(total_ram), int(used_ram)
    except Exception as e:
        print(f"Error executing command: {e}")
        return None, None

def main():
    config = load_config()

    # SSH configuration
    hostname = config.get('ssh_config', 'host')
    username = config.get('ssh_config', 'user')
    private_key_path = config.get('ssh_config', 'private_key_path')

    # Threshold configuration
    ram_usage_threshold = config.getint('thresholds', 'ram_usage_percentage', fallback=85)

    try:
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
            ssh.connect(hostname, username=username, pkey=private_key)

            total_ram, used_ram = get_ram_usage(ssh)
            if total_ram and used_ram:
                ram_usage_percentage = (used_ram / total_ram) * 100

                if ram_usage_percentage > ram_usage_threshold:
                    print(f"RAM usage is above {ram_usage_threshold}%!")
                else:
                    print("RAM usage is normal.")
    except Exception as e:
        print(f"Error connecting to SSH: {e}")

if __name__ == "__main__":
    main()
