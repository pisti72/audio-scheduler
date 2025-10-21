from functools import wraps
from flask import session, redirect, url_for
import hashlib
import os

# File to store credentials
CREDENTIALS_FILE = 'credentials.json'

def init_credentials():
    """Initialize default credentials if they don't exist"""
    print("Checking for credentials file...") # Debug log
    if not os.path.exists(CREDENTIALS_FILE):
        print("Creating new credentials file with default admin/admin") # Debug log
        set_credentials('admin', 'admin')
    else:
        print("Credentials file already exists") # Debug log

def hash_password(password):
    """Hash password with salt"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return salt + key

def verify_password(stored_password, provided_password):
    """Verify password against stored hash"""
    salt = stored_password[:32]
    key = stored_password[32:]
    new_key = hashlib.pbkdf2_hmac(
        'sha256',
        provided_password.encode('utf-8'),
        salt,
        100000
    )
    return key == new_key

def set_credentials(username, password):
    """Save new credentials"""
    import json
    hashed = hash_password(password)
    credentials = {
        'username': username,
        'password': hashed.hex()  # Convert bytes to hex string for JSON storage
    }
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(credentials, f)
    print(f"Credentials saved: {credentials}")  # Debug log

def check_credentials(username, password):
    """Check if credentials are valid"""
    import json
    try:
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"Credentials file not found at {CREDENTIALS_FILE}") # Debug log
            init_credentials()
            
        with open(CREDENTIALS_FILE, 'rb') as f:
            content = f.read().decode('utf-8')
            print(f"Read credentials file: {content}") # Debug log
            credentials = json.loads(content)
            stored_username = credentials['username']
            stored_password = bytes.fromhex(credentials['password']) # Convert from hex string
            print(f"Stored username: {stored_username}") # Debug log
            return (username == stored_username and 
                    verify_password(stored_password, password))
    except:
        return False

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function