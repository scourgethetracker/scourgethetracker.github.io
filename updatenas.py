#!/usr/bin/env python3

import paramiko
import os
import tempfile
import configparser
import time
import logging
from logging.handlers import RotatingFileHandler

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('update_certificate.log', maxBytes=5000000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def read_config(config_file):
    config = configparser.ConfigParser()
    try:
        config.read(os.path.expanduser(config_file))
    except configparser.Error as e:
        logger.error(f"Failed to read configuration file: {e}")
        raise

    sections_needed = ['general', 'ssh_config', 'stunnel_files', 'certificate_files']
    for section in sections_needed:
        if section not in config:
            logger.error(f"Configuration file is missing required section: {section}")
            raise ValueError(f"Missing section: {section}")

    general_config = {'dry_run': config.getboolean('general', 'dry_run', fallback=True),
                      'upload_path': config.get('general', 'upload_path', fallback='/etc/stunnel')}

    ssh_config = {'host': config.get('ssh_config', 'host'),
                  'port': config.getint('ssh_config', 'port'),
                  'user': config.get('ssh_config', 'user'),
                  'key_path': config.get('ssh_config', 'key_path')}

    stunnel_files = (config.get('stunnel_files', 'cert_file'),
                     config.get('stunnel_files', 'key_file'))

    cert_files = {'backup_cert': config.get('certificate_files', 'backup_cert'),
                  'backup_key': config.get('certificate_files', 'backup_key'),
                  'uca_pem': config.get('certificate_files', 'uca_pem')}

    return general_config, ssh_config, stunnel_files, cert_files

def concatenate_files(file1, file2, output_file):
    try:
        with open(file1, 'r') as f1, open(file2, 'r') as f2, open(output_file, 'w') as out:
            out.write(f1.read() + '\n' + f2.read())
    except IOError as e:
        logger.error(f"Error concatenating files: {e}")
        raise

def update_certificate(general_config, ssh_config, stunnel_files, cert_files):
    try:
        remote_path = general_config['upload_path']
        if general_config['dry_run']:
            logger.info("Dry run mode: No changes will be made.")
            return

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_key = paramiko.RSAKey.from_private_key_file(os.path.expanduser(ssh_config['key_path']))
        ssh.connect(ssh_config['host'], port=ssh_config['port'], username=ssh_config['user'], pkey=ssh_key)

        with ssh.open_sftp() as sftp:
            for name, local_path in cert_files.items():
                remote_file_path = os.path.join(remote_path, f"{name}.pem")
                sftp.put(local_path, remote_file_path)
                logger.info(f"Uploaded {local_path} to {remote_file_path}")

            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                concatenate_files(*stunnel_files, tmp.name)
                sftp.put(tmp.name, os.path.join(remote_path, 'stunnel.pem'))
                logger.info(f"Created and uploaded stunnel.pem from {stunnel_files} to {os.path.join(remote_path, 'stunnel.pem')}")
                os.remove(tmp.name)

        for script in ["/etc/init.d/thttpd restart", "/etc/init.d/stunnel restart", "/etc/init.d/Qthttpd restart"]:
            ssh.exec_command(script)
            logger.info(f"Executed: {script}")
            time.sleep(5)

    except Exception as e:
        logger.error(f"An error occurred during certificate update: {e}")
        raise
    finally:
        ssh.close()
        logger.info("Certificate update process completed.")

def main():
    try:
        general_config, ssh_config, stunnel_files, cert_files = read_config('./updatenas.conf')
        update_certificate(general_config, ssh_config, stunnel_files, cert_files)
    except Exception as e:
        logger.error(f"Failed to update certificates: {e}")

if __name__ == "__main__":
    main()
