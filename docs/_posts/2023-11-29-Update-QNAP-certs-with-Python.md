---
layout: post
title: "Automating Certificate Updates on QNAP with Python"
date: 2023-11-29
categories: automation python
---

## QNAP and SSL... ugh, sorta.
I have a QNAP NAS. It's an older TS-1677X that I got a great deal on when it was new but is still getting QTS updates (currently QTS 5.1.2) and it's the primary disk store in my homelab.  A few years back I decided to HTTPS-all-the-things and actually created my own CA and used that for my certificate needs. Well, 24-November-2023 finally arrived and I had a choice: update the CA certs and all the certs issued OR use Let's Encrypt. I chose Let's Encrypt to make my life easier and its become the defacto cert provider for a number of homelabers that I folow. 

If you hae a QNAP NAS then you know that QTS is not the best way to manage *anything* and requires multiple steps to get a new cert and/or CA installed. One thing that you will also learn quickly is that 4096 bit or ECDSA certs aren't exactly supported requiring you to either jump through a conversion hoop or do it via command line. Since I didn't want to bother converting anything from Let's Encrypt I opted for command line and Python.

If you have SSH enabled on the QNAP you can connect, by default, as the 'admin' user. The directory you care about for certs is `/etc/stunnel` and the files of notes are:

```
backup.cert
backup.key
stunnel.pem
uca.cert
```
If you're here then I will assume you already have certs from Let's Encrypt, but if not you can look [here](https://scourgethetracker.github.io) for a post on how to get and renew Let's Encrypt Certs with AWS support or [here](https://scourgethetracker.github.io) for a more basic starter.

## What I wanted vs what I needed

I had a semi-clear set of goals in mind when starting this migration from my custom CA solution to Let's Encrypt:

- **Semi-Automated Certificate Upload**: whatever I write has to have enough logic to push certs where they need to be without too much hand holding so that I could run this from cron later.
- **SSH Key Authentication**: it also needs to be able to use SSH and ssh-keys to connect to the QNAP
- **Configurable Paths**: it also needs to know where source and destination data belong, as to be flexible
- **Dry Run Mode**: before making actual changes, it simulate the upload process, showing what files would be uploaded and where.
- **Restart Services**: there are three services that need restarting every time the certs change

I would learn later that I needed:

- **Delay Between Uploads**: The script waits for a specified time between each file upload to manage QNAP ssh connection annoyances when trying to use a for loop.

## Configs, the what and where
Before starting I knew I wanted a conf file called `~/.updatenas.conf` that contained everyting I needed so nothing was hardcoded in my Pythons script.  When planning out the configuration I learned that one of the files I would be updating, `stunnel.pem` was actualy the combiation of two pieces of data a private key and a certificate file so my conf needed to able to account for that.

I eventually settled on a [TOML](https://toml.io) conf file that looks like this; since I'm using things directly from the Let's Encrypt Certbot that are saved on disk those are the paths that made sense.

```ini
[general] # Destination and default dry run options
dry_run = true
upload_path = /etc/stunnel

[ssh_config] # How are we connecting to the QNAP
host = qnap.domain
port = 22
user = admin
key_path = .ssh/id_rsa

[stunnel_files] # What goes into the stunnel file
cert_file = /certbot/config/archive/domain/cert.pem
key_file = /certbot/config/archive/domain/privkey.pem

[certificate_files] # What other files go into /etc/stunnel
backup_cert = /certbot/config/archive/domain/cert.pem
backup_key = /certbot/config/archive/domain/privkey.pem
uca_pem = /certbot/config/archive/domain/fullchain.pem
```

## And so our story begins...

I knew I would need some basic things from Python: os, ssh, temp and conf file support for starters.

```python
import paramiko
import os
import tempfile
import configparser
import time
```

The first important task was reading the conf file I came up with and making use of the key+value pairs.
```python
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
```

Next I should get the business of `stunnel.pem` out of the way.
```python
def concatenate_files(file1, file2, output_file):
    with open(file1, 'r') as f1, open(file2, 'r') as f2, open(output_file, 'w') as out:
        out.write(f1.read())
        out.write('\n')
        out.write(f2.read())
```

Dry-run, before anything else because if it does not work it breaks the QTS UI.
```python
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
```

Now I started with this for uploading files to the QNAP with a slight delay to account for the write cache but aftter one or two uploads it would just fail to write files correctly.
```python
# Establish an SSH client
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_key = paramiko.RSAKey.from_private_key_file(os.path.expanduser(ssh_config['key_path']))
ssh.connect(ssh_config['host'], port=ssh_config['port'], username=ssh_config['user'], pkey=ssh_key)


sftp = ssh.open_sftp()
for local_file, remote_file in cert_files.items():
    sftp.put(local_file, os.path.join(remote_path, remote_file))
    print(f"Uploaded {local_file} to {os.path.join(remote_path, remote_file)}")
    time.sleep(5)
```
However, I ended up mupliple instances of this (each with a slight tweak) to account for the issue I was seeing. I'm still not sure if it's just my QNAP, paramiko, or even the firewall that exists between my desktop and the NAS in my homelab but whatever this cause this worked around the 'bug'.
```python
# Upload backup.cert
sftp.put(cert_files['backup_cert'], os.path.join(remote_path, 'backup.cert'))
print(f"Uploaded {cert_files['backup_cert']} to {os.path.join(remote_path, 'backup.cert')}")
time.sleep(1)
```

This worked for `stunnel.pem` so I went with what worked.
```python
# Concatenate stunnel files and upload
with tempfile.NamedTemporaryFile(delete=False) as tmp:
    concatenate_files(stunnel_files[0], stunnel_files[1], tmp.name)
    sftp.put(tmp.name, os.path.join(remote_path, 'stunnel.pem'))
    print(f"Created and uploaded stunnel.pem from {stunnel_files[0]} and {stunnel_files[1]} to {os.path.join(remote_path, 'stunnel.pem')}")
os.remove(tmp.name)
```

With all the files updated I needed to restart some services and hope I could log into the QTS gui after.
```python
# Execute restart scripts
restart_scripts = ["/etc/init.d/thttpd.sh restart", "/etc/init.d/stunnel.sh restart", "/etc/init.d/Qthttpd.sh restart"]
for script in restart_scripts:
    stdin, stdout, stderr = ssh.exec_command(script)
    print(f"Executed: {script}")
    time.sleep(5)
```
Each of the parts individually worked well during the many rounds of testing so it's time to glue them together and hope for the best, right?
```python
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
```
Well slap-ya-mama and call it done. I have to admit I was a bit surpised when it worked the first time round with the required bit to make is a cohesive script in place. Nonetheless, I was a happy camper and could cross that off my list.

Now I need to do the same for my OPNSense firewall... hmmmm.

If you want a complete script and example conf without having to copy and paste, check out my Github repo at [ScourgeTheTracker/devblog](https://github.com/scourgethetracker/devblog).