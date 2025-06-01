from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.usersSchema import CreateUserRequest, CreateUserResponse
from controllers.usersController import create_user, login_user
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(tags=["users"])

# ****** Users Endpoints ******
@router.post("/register", status_code=201, response_model=CreateUserResponse)
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
    
@router.post("/login", status_code=200)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    Response: Response = None
):
    """
    Endpoint to log in a user.
    
    :param form_data: Form data containing username and password
    :param db: SQLAlchemy session object
    :return: Response with access token
    """
    try:
        access_token = login_user(db, form_data.username, form_data.password)
        Response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            secure=True,  # Set to True if using HTTPS
            samesite="Lax"  # Adjust as needed
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))