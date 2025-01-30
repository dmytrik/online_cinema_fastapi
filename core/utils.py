import re
import uuid
import secrets
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import List, Optional
from fastapi import HTTPException
from collections import defaultdict

# initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# validate email format
def validate_email(email: str) -> Optional[str]:
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(email_regex, email):
        return None
    return "Invalid email address format"

# hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# if file exists or not
def file_exists(file_path: str) -> bool:
    return os.path.isfile(file_path)

# handle HTTP errors
def handle_http_error(detail: str, status_code: int = 400):
    raise HTTPException(status_code=status_code, detail=detail)

# user permissions
def has_permission(user_roles: List[str], required_roles: List[str]) -> bool:
    return any(role in user_roles for role in required_roles)

# requests per time window
class Throttle:
    def __init__(self, window_size: timedelta):
        self.window_size = window_size
        self.timestamps = defaultdict(list)

    def is_throttled(self, user_id: str) -> bool:
        now = datetime.now()
        self.timestamps[user_id] = [timestamp for timestamp in self.timestamps[user_id] if timestamp > now - self.window_size]
        if len(self.timestamps[user_id]) >= 5:  # Example: 5 requests per 1 minute
            return True
        self.timestamps[user_id].append(now)
        return False

# validate URL format
def validate_url(url: str) -> bool:
    url_regex = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
    return bool(re.match(url_regex, url))

# Caching example
cache = {}

def get_from_cache(key: str):
    return cache.get(key)

def set_cache(key: str, value: any):
    cache[key] = value

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.

    Returns:
        str: Securely generated token.
    """
    return secrets.token_urlsafe(length)