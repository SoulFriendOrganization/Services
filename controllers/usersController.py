from uuid import UUID
from typing import List, Optional
from database.models import User, UserAuth, func
from sqlalchemy.orm import Session
from schemas.usersSchema import CreateUserRequest, CreateUserResponse
from utils.auth import get_password_hash, verify_password, create_access_token
from logging_config import logger

def create_users(db:Session, user_data:CreateUserRequest) -> User:
    """
    Create a new user in the database.
    
    :param db: SQLAlchemy session object
    :param user_data: User data to be created
    :return: Created User object
    """
    try:
        # Check if the username already exists
        logger.info(f"Attempting to create user with username: {user_data.username}")
        existing_user = db.query(UserAuth).filter(UserAuth.username == user_data.username).first()
        if existing_user:
            raise ValueError("Username already exists")
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            full_name=user_data.full_name,
            age=user_data.age
        )
        db.add(db_user)
        db.commit()
        db_user_auth = UserAuth(
            user_id=db_user.id,
            username=user_data.username,
            password=hashed_password
        )
        db.add(db_user_auth)
        db.commit()
        db.refresh(db_user)
        db.refresh(db_user_auth)
        response = CreateUserResponse(
            id=db_user.id,
            full_name=db_user.full_name,
            username=db_user_auth.username,
            age=db_user.age
        )
        return response
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise ValueError("Failed to create user") from e

def login_users(db: Session, username: str, password: str) -> str:
    """
    Log in a user by verifying the username and password.
    
    :param db: SQLAlchemy session object
    :param username: Username of the user
    :param password: Password of the user
    :return: UserAuth object if login is successful
    """
    try:
        logger.info(f"User login attempt with username: {username}")
        user_auth = db.query(UserAuth).filter(UserAuth.username == username).first()
        user_hashed_password = user_auth.password if user_auth else None
        if not user_auth or not verify_password(password, user_hashed_password):
            raise ValueError("Invalid username or password")
        access_token = create_access_token(data={"user_id": str(user_auth.user_id), "username": user_auth.username})
        return access_token
    except Exception as e:
        logger.error(f"Error during user login: {e}")
        raise ValueError("Login failed") from e
    
