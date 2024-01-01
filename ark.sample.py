import os
import sys
import boto3
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from base64 import urlsafe_b64encode, urlsafe_b64decode

def derive_key(password, salt):
    # Derive a key from the provided password and salt
    password = password.encode()
    salt = urlsafe_b64decode(salt)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        iterations=100000,
        salt=salt,
        length=32,
        backend=default_backend()
    )
    key = kdf.derive(password)
    return key

def encrypt_file(file_path, password, kms_key_id):
    # Encrypt a file using Fernet symmetric encryption
    salt = os.urandom(16)
    key = derive_key(password, urlsafe_b64encode(salt).decode())
    cipher = Cipher(algorithms.AES(key), modes.CFB, backend=default_backend())
    encryptor = cipher.encryptor()

    with open(file_path, 'rb') as file:
        plaintext = file.read()

    ciphertext = encryptor.update(plaintext) + encryptor.finalize()

    # Save the salt and ciphertext to a new file
    encrypted_file_path = file_path + '.enc'
    with open(encrypted_file_path, 'wb') as encrypted_file:
        encrypted_file.write(salt + ciphertext)

    # Use AWS KMS to encrypt the derived key
    kms = boto3.client('kms')
    encrypted_key = kms.encrypt(KeyId=kms_key_id, Plaintext=key)['CiphertextBlob']

    return encrypted_file_path, encrypted_key

def upload_to_s3_with_kms(file_path, bucket_name, object_name, aws_access_key_id, aws_secret_access_key, encrypted_key):
    # Upload a file to AWS S3 with AWS KMS encryption
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    s3.upload_file(file_path, bucket_name, object_name, ExtraArgs={'ServerSideEncryption': 'aws:kms', 'SSEKMSKeyId': aws_kms_key_id, 'SSEKMSContext': encrypted_key})

if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python ark.sample.py <file_path> <bucket_name> <object_name> <aws_access_key_id> <aws_secret_access_key> <kms_key_id>")
        sys.exit(1)

    file_path = sys.argv[1]
    bucket_name = sys.argv[2]
    object_name = sys.argv[3]
    aws_access_key_id = sys.argv[4]
    aws_secret_access_key = sys.argv[5]
    kms_key_id = sys.argv[6]

    password = input("Enter encryption password: ")

    encrypted_file_path, encrypted_key = encrypt_file(file_path, password, kms_key_id)
    upload_to_s3_with_kms(encrypted_file_path, bucket_name, object_name, aws_access_key_id, aws_secret_access_key, encrypted_key)

    print(f"File encrypted and uploaded to S3 with KMS: s3://{bucket_name}/{object_name}")

