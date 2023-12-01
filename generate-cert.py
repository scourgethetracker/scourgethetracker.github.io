#!/usr/bin/env python3

import os
import stat
import subprocess

def check_and_set_permissions(path, expected_perms):
    """
    Check and set the permissions of a file or directory.
    :param path: Path to the file or directory.
    :param expected_perms: Expected permission mode (e.g., 0o700 for directories, 0o600 for files).
    """
    try:
        current_perms = stat.S_IMODE(os.lstat(path).st_mode)
    except FileNotFoundError:
        raise FileNotFoundError(f"Path {path} does not exist.")
    except Exception as e:
        raise Exception(f"Error accessing {path}: {e}")

    if current_perms != expected_perms:
        try:
            print(f"Updating permissions for {path} to {oct(expected_perms)}")
            os.chmod(path, expected_perms)
        except PermissionError:
            raise PermissionError(f"Insufficient permissions to change {path}.")
        except Exception as e:
            raise Exception(f"Error setting permissions for {path}: {e}")
    else:
        print(f"Permissions for {path} are already set correctly.")

def generate_wildcard_cert(domain, email):
    """
    Generate a wildcard certificate for the given domain using Let's Encrypt and certbot with the DNS Route53 plugin.
    """
    aws_cred_path = os.path.expanduser("~/.aws/credentials")
    aws_dir_path = os.path.dirname(aws_cred_path)

    # Check and set permissions for AWS credentials and directory
    try:
        check_and_set_permissions(aws_dir_path, 0o700)  # Permissions set to drwx------
        check_and_set_permissions(aws_cred_path, 0o600)  # Permissions set to -rw-------
    except Exception as e:
        print(f"Error setting permissions: {e}")
        return

    try:
        # Run certbot command with Route53 plugin
        subprocess.run([
            "certbot", "certonly", 
            "--dns-route53", 
            "-d", f"*.{domain}", 
            "-d", domain, 
            "--non-interactive", 
            "--agree-tos", 
            "--email", email,
            "--server https://acme-v02.api.letsencrypt.org/directory" # Use an ACME server that allwos wildcard certs
        ], check=True)
        print(f"Wildcard certificate for {domain} generated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Certbot error: {e}")
    except FileNotFoundError:
        print("Certbot executable not found. Ensure it is installed and in the PATH.")
    except Exception as e:
        print(f"Unexpected error during certificate generation: {e}")

if __name__ == "__main__":
    try:
        domain = os.environ['CERTBOT_DOMAIN']
        email = os.environ['CERTBOT_EMAIL']
        generate_wildcard_cert(domain, email)
    except KeyError as e:
        print(f"Environment variable {e} not set. Please set CERTBOT_DOMAIN and CERTBOT_EMAIL.")
    except Exception as e:
        print(f"Failed to generate wildcard certificate: {e}")
