from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from database.connection import get_db
from routes.middleware.auth import get_user_id
from logging_config import logger
from schemas.chatSchemas import ChatRequest, ChatTrialRequest, ChatResponse
from controllers.chatController import chat, chat_trial

router = APIRouter()

# ****** Chat Endpoints ******
@router.post("", status_code=200, response_model=ChatResponse)
def chat_endpoint(
    data: ChatRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Endpoint to perform chat for a user.
    
    :param data: Data for the chat request
    :param user_id: ID of the user making the request
    :param db: SQLAlchemy session object
    :return: Chat response
    """
    try:
        logger.info(f"User ID: {user_id} - Processing chat request")
        return chat(db, user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/trial", status_code=200, response_model=ChatResponse)
def chat_trial_endpoint(
    data: ChatTrialRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Endpoint to perform chat trial.
    
    :param data: Data for the chat trial request
    :param db: SQLAlchemy session object
    :return: Chat trial response
    """
    try:
        logger.info("Processing chat trial request")
        return chat_trial(db, data)
    except ProcessLookupError as e:
        raise HTTPException(status_code=406, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    