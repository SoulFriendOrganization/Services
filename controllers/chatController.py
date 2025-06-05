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
        logger.info(f"Sending chat trial request with message: {data.get('message')}...")
        if len(data.get('message_history')) > 7:
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
        
        current_mood = db.query(DailyMood, Moods.name.label("mood_name")).join(
            Moods, DailyMood.mood_level == Moods.id
        ).filter(
            DailyMood.user_id == user_id,
            DailyMood.date == func.current_date()
        ).first()._asdict()

        if not current_mood:
            logger.error(f"Current mood not found for user ID: {user_id}")
            raise ValueError("Current mood not found for the user")
        
        user_collection = db.query(UserCollection).filter(
            UserCollection.user_id == user_id
        ).first()

        data['user_name'] = user.full_name if user else None
        data['current_mood'] = current_mood.get('mood_name')
        data['notes'] = current_mood.get('notes') if current_mood.get('notes') else None
        data['user_condition_summary'] = user_collection.user_condition_summary if user_collection else None
        
        logger.info(f"Sending chat request for user: {user_id} with mood: {data.get('current_mood')}")
        response = chat_azure.chat(data)

        if not response:
            logger.error(f"Chat failed to get a response for user ID: {user_id}")
            raise ValueError("Chat failed to get a response")
        
        db.query(DailyMood).filter(
            DailyMood.user_id == user_id,
            DailyMood.date == func.current_date()
        ).update(
            {DailyMood.notes: response.summary},
            synchronize_session=False
        )
        db.commit()
        
        db.query(UserCollection).filter(
            UserCollection.user_id == user_id
        ).update(
            {UserCollection.user_condition_summary: response.summary},
            synchronize_session=False
        )
        db.commit()

        logger.info(f"Chat successful for user ID: {user_id}")
        return response
    except Exception as e:
        logger.exception(f"Error in chat function: {str(e)}")
        raise ValueError("Chat failed due to an error") from e