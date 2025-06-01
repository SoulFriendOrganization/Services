from uuid import UUID
from typing import List, Optional
from database.models import User, UserAuth
from sqlalchemy.orm import Session
from schemas.usersSchema import CreateUserRequest, CreateUserResponse

def create_user(db:Session, user_data:CreateUserRequest) -> User:
    """
    Create a new user in the database.
    
    :param db: SQLAlchemy session object
    :param user_data: User data to be created
    :return: Created User object
    """
    db_user = User(
        full_name=user_data.full_name,
        age=user_data.age
    )
    db_user_auth = UserAuth(
        user_id=db_user.id,
        username=user_data.username,
        password=user_data.password
    )
    db.add(db_user)
    db.add(db_user_auth)
    db.commit()
    db.refresh(db_user)
    db.refresh(db_user_auth)
    response = CreateUserResponse(
        id=db_user.id,
        full_name=db_user.full_name,
        username=db_user_auth.username,
        email=user_data.email,
        age=db_user.age
    )
    return response