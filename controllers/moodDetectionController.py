from uuid import UUID
from typing import List, Optional
from database.models import User, DailyMood, Moods, func
from schemas.moodDetectionSchemas import FaceDetectionRequest
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from os import getenv
import requests
import json
from logging_config import logger
load_dotenv()


def mood_inference(db: Session, user_id: UUID, data:FaceDetectionRequest) -> str:
    """
    Perform mood inference for a user based on the provided data.
    :param db: SQLAlchemy session object
    :param user_id: ID of the user for whom mood inference is to be performed
    :param data: Data to be sent for mood inference
    :return: Mood inference result as a string
    """

    logger.info(f"User ID: {user_id} - Processing mood inference request")
    logger.info("Checking if mood for today has already been recorded")
    check_mood_current_date = db.query(DailyMood).filter(
        DailyMood.user_id == user_id,
        DailyMood.date == func.current_date()
    ).first()
    if check_mood_current_date:
        logger.warning(f"Mood for user {user_id} on current date already exists")
        raise ValueError("Mood for today has already been recorded")
    inference_url = "https://moodclassifier.eastasia.inference.ml.azure.com/score"
    api_key = getenv("MOOD_CLASSIFIER_API_KEY")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        logger.info(f"Sending data for mood inference for user {user_id}")
        response = requests.post(inference_url, json=data.model_dump(), headers=headers)
        response.raise_for_status()
        result = response.json()
        
        if result.get("prediction") is not None:
            mood_level = result["prediction"]
            mood = db.query(Moods).filter(Moods.name == mood_level.capitalize()).first()
            if mood is None:
                raise ValueError("Mood level not found in the database")
            daily_mood = DailyMood(
                user_id=user_id,
                date=func.current_date(),
                mood_level=mood.id,
                notes=None
            )
            db.add(daily_mood)
            db.commit()
            return result
        else:
            logger.error("Invalid response from mood inference service")
            raise ValueError("Invalid response from mood inference service")
    except Exception as e:
        logger.error(f"Failed to perform mood inference: {str(e)}")
        raise ValueError(f"Failed to perform mood inference")


def mood_inference_trial(db: Session, data: FaceDetectionRequest) -> str:
    """
    Perform mood inference for a user based on the provided data.
    :param db: SQLAlchemy session object
    :param data: Data to be sent for mood inference
    :return: Mood inference result as a string
    """
    inference_url = "https://moodclassifier.eastasia.inference.ml.azure.com/score"
    api_key = getenv("MOOD_CLASSIFIER_API_KEY")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        logger.info(f"Sending data for mood inference trial")
        response = requests.post(inference_url, json=data.model_dump(), headers=headers)
        response.raise_for_status()
        result = response.json()
        if result.get("prediction") is not None:
            return result
        else:
            logger.error("Invalid response from mood inference service")
            raise ValueError("Invalid response from mood inference service")
    except Exception as e:
        logger.error(f"Failed to perform mood inference trial: {str(e)}")
        raise ValueError("Failed to perform mood inference") from e
