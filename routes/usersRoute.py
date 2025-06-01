from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.usersSchema import CreateUserRequest, CreateUserResponse
from controllers.usersController import create_user

router = APIRouter(tags=["users"])

# ****** Users Endpoints ******
@router.post("/users", status_code=201, response_model=CreateUserResponse)
def create_user_endpoint(
    user_data: CreateUserRequest,
    db: Session = Depends(get_db)
) -> CreateUserResponse:
    """
    Endpoint to create a new user.
    
    :param user_data: User data to be created
    :param db: SQLAlchemy session object
    :return: Created User object
    """
    try:
        return create_user(db, user_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))