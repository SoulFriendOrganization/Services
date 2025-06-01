from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from dotenv import load_dotenv
from os import getenv
load_dotenv()

# Configurations
SECRET_KEY = getenv("ENCRYPTION_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    :param plain_password: The plain text password to verify
    :param hashed_password: The hashed password to compare against
    :return: True if the passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    :param password: The plain text password to hash
    :return: The hashed password
    """
    return pwd_context.hash(password)