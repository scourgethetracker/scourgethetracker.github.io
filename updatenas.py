#!/usr/bin/env python3

import paramiko
import os
import tempfile
import configparser
import time

def read_config(config_file):
    config = configparser.ConfigParser()
    config.read(os.path.expanduser(config_file))
    general_config = {
        'dry_run': config.getboolean('general', 'dry_run', fallback=True),
        'upload_path': config.get('general', 'upload_path', fallback='/etc/stunnel')
    }
    ssh_config = {
        'host': config['ssh_config']['host'],
        'port': int(config['ssh_config']['port']),
        'user': config['ssh_config']['user'],
        'key_path': config['ssh_config']['key_path']
    }
    stunnel_files = (
        config['stunnel_files']['cert_file'],
        config['stunnel_files']['key_file']
    )
    cert_files = {
        'backup_cert': config['certificate_files']['backup_cert'],
        'backup_key': config['certificate_files']['backup_key'],
        'uca_pem': config['certificate_files']['uca_pem']
    }
    return general_config, ssh_config, stunnel_files, cert_files

def concatenate_files(file1, file2, output_file):
    with open(file1, 'r') as f1, open(file2, 'r') as f2, open(output_file, 'w') as out:
        out.write(f1.read())
        out.write('\n')
        out.write(f2.read())

def update_certificate(general_config, ssh_config, stunnel_files, cert_files):
    try:
        # Use the configured upload path
        remote_path = general_config['upload_path']

        # Dry run mode
        if general_config['dry_run']:
            print("Dry run mode: No changes will be made.")
            print(f"Would upload {cert_files['backup_cert']} to {ssh_config['host']}:{os.path.join(remote_path, 'backup.cert')}")
            print(f"Would upload {cert_files['backup_key']} to {ssh_config['host']}:{os.path.join(remote_path, 'backup.key')}")
            print(f"Would upload {cert_files['uca_pem']} to {ssh_config['host']}:{os.path.join(remote_path, 'uca.pem')}")
            print(f"Would create stunnel.pem from {stunnel_files[0]} and {stunnel_files[1]} at {ssh_config['host']}:{os.path.join(remote_path, 'stunnel.pem')}")
            return

        # Establish an SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_key = paramiko.RSAKey.from_private_key_file(os.path.expanduser(ssh_config['key_path']))
        ssh.connect(ssh_config['host'], port=ssh_config['port'], username=ssh_config['user'], pkey=ssh_key)

        sftp = ssh.open_sftp()

        # Upload backup.cert
        sftp.put(cert_files['backup_cert'], os.path.join(remote_path, 'backup.cert'))
        print(f"Uploaded {cert_files['backup_cert']} to {os.path.join(remote_path, 'backup.cert')}")
        time.sleep(1)

        # Upload backup.key
        sftp.put(cert_files['backup_key'], os.path.join(remote_path, 'backup.key'))
        print(f"Uploaded {cert_files['backup_key']} to {os.path.join(remote_path, 'backup.key')}")
        time.sleep(1)

        # Upload uca.pem
        sftp.put(cert_files['uca_pem'], os.path.join(remote_path, 'uca.pem'))
        print(f"Uploaded {cert_files['uca_pem']} to {os.path.join(remote_path, 'uca.pem')}")
        time.sleep(1)

        # Concatenate stunnel files and upload
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            concatenate_files(stunnel_files[0], stunnel_files[1], tmp.name)
            sftp.put(tmp.name, os.path.join(remote_path, 'stunnel.pem'))
            print(f"Created and uploaded stunnel.pem from {stunnel_files[0]} and {stunnel_files[1]} to {os.path.join(remote_path, 'stunnel.pem')}")
        os.remove(tmp.name)

        # Execute restart scripts
        restart_scripts = ["/etc/init.d/thttpd.sh restart", "/etc/init.d/stunnel.sh restart", "/etc/init.d/Qthttpd.sh restart"]
        for script in restart_scripts:
            stdin, stdout, stderr = ssh.exec_command(script)
            print(f"Executed: {script}")
            time.sleep(5)

        sftp.close()
        ssh.close()
        print("Certificate update completed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    general_config, ssh_config, stunnel_files, cert_files = read_config('./updatenas.conf')
    update_certificate(general_config, ssh_config, stunnel_files, cert_files)

if __name__ == "__main__":
    main()

