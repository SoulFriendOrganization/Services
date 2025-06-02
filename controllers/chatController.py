from nodes.chatAzure import chat_azure
from uuid import UUID
from typing import List, Optional
from database.models import User, DailyMood, Moods, func
from schemas.chatSchemas import ChatRequest, ChatTrialRequest, ChatResponse
from sqlalchemy.orm import Session
from logging_config import logger

def chat_trial(db: Session, data: ChatTrialRequest) -> str:
    """
    Perform chat trial for a user based on the provided data.
    
    :param db: SQLAlchemy session object
    :param user_id: ID of the user for whom chat trial is to be performed
    :param data: Data to be sent for chat trial
    :return: Chat trial result as a string
    """
    try:
        logger.info(f"Sending chat trial request with message: {data.message[:50]}...")
        if len(data.message_history) > 3:
            logger.warning("Chat trial message history exceeds 3 messages, truncating to last 3")
            raise ValueError("Chat trial message history exceeds 3 messages")
        response = chat_azure.chat(data)
        
        if not response:
            logger.error("Chat trial failed to get a response")
            raise ValueError("Chat trial failed to get a response")
        
        logger.info("Chat trial successful")
        return response
    except Exception as e:
        logger.exception(f"Error in chat_trial function: {str(e)}")
        raise ValueError("Chat trial failed due to an error") from e

def chat(db: Session, user_id: UUID, data: ChatRequest) -> str:
    """
    Perform chat for a user based on the provided data.
    
    :param db: SQLAlchemy session object
    :param user_id: ID of the user for whom chat is to be performed
    :param data: Data to be sent for chat
    :return: Chat result as a string
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found with ID: {user_id}")
            raise ValueError("User not found")
        
        current_mood = db.query(DailyMood).filter(
            DailyMood.user_id == user_id,
            DailyMood.date == func.current_date()
        ).first()
        if not current_mood:
            logger.error(f"Current mood not found for user ID: {user_id}")
            raise ValueError("Current mood not found for the user")
        
        data.user_name = user.full_name
        data.current_mood = current_mood.mood_level.name
        
        logger.info(f"Sending chat request for user: {user_id} with mood: {data.current_mood}")
        response = chat_azure.chat(data)

        if not response:
            logger.error(f"Chat failed to get a response for user ID: {user_id}")
            raise ValueError("Chat failed to get a response")
        
        logger.info(f"Chat successful for user ID: {user_id}")
        return response
    except Exception as e:
        logger.exception(f"Error in chat function: {str(e)}")
        raise ValueError("Chat failed due to an error") from e