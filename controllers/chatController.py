from nodes.chatAzure import chat_azure, ChatAzureMentalCareResponse
from uuid import UUID
from typing import List, Optional
from database.models import User, DailyMood, Moods, func, UserCollection
from schemas.chatSchemas import ChatRequest, ChatTrialRequest
from sqlalchemy.orm import Session
from logging_config import logger

def chat_trial(db: Session, data: ChatTrialRequest) -> ChatAzureMentalCareResponse:
    """
    Perform chat trial for a user based on the provided data.
    
    :param db: SQLAlchemy session object
    :param user_id: ID of the user for whom chat trial is to be performed
    :param data: Data to be sent for chat trial
    :return: Chat trial result as a string
    """
    try:
        data = data.model_dump()
        logger.info(f"Sending chat trial request with message: {data.message[:50]}...")
        if len(data.message_history) > 7:
            logger.warning("Chat trial message history exceeds 3 messages, truncating to last 3")
            raise ProcessLookupError("Chat trial message history exceeds 3 messages")
        response = chat_azure.chat(data)
        
        if not response:
            logger.error("Chat trial failed to get a response")
            raise ValueError("Chat trial failed to get a response")
        
        logger.info("Chat trial successful")
        return response
    except Exception as e:
        logger.exception(f"Error in chat_trial function: {str(e)}")
        raise ValueError("Chat trial failed due to an error") from e

def chat(db: Session, user_id: UUID, data: ChatRequest) -> ChatAzureMentalCareResponse:
    """
    Perform chat for a user based on the provided data.
    
    :param db: SQLAlchemy session object
    :param user_id: ID of the user for whom chat is to be performed
    :param data: Data to be sent for chat
    :return: Chat result as a string
    """
    try:
        data = data.model_dump()
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
        
        user_collection = db.query(UserCollection).filter(
            UserCollection.user_id == user_id
        ).first()

        data['user_name'] = user.full_name
        data['current_mood'] = current_mood.mood_level.name
        data['notes'] = current_mood.notes if current_mood.notes else None
        data['user_condition_summary'] = user_collection.user_condition_summary if user_collection else None
        
        logger.info(f"Sending chat request for user: {user_id} with mood: {data.get('current_mood')}")
        response = chat_azure.chat(data)

        if not response:
            logger.error(f"Chat failed to get a response for user ID: {user_id}")
            raise ValueError("Chat failed to get a response")
        
        db.query(DailyMood).update(
            {DailyMood.notes: data.get('notes')},
            synchronize_session=False
        ).filter(
            DailyMood.user_id == user_id,
            DailyMood.date == func.current_date()
        )
        db.commit()
        
        db.query(UserCollection).update(
            {UserCollection.user_condition_summary: response.summary},
            synchronize_session=False
        ).filter(
            UserCollection.user_id == user_id
        )

        logger.info(f"Chat successful for user ID: {user_id}")
        return response
    except Exception as e:
        logger.exception(f"Error in chat function: {str(e)}")
        raise ValueError("Chat failed due to an error") from e