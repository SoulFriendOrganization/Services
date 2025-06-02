from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.moodDetectionSchemas import FaceDetectionRequest, MoodInferenceResponse
from controllers.moodDetectionController import mood_inference, mood_inference_trial
from routes.middleware.auth import get_user_id
from logging_config import logger

router = APIRouter()

# ****** Face Detection Endpoints ******
@router.post("/face-detection", status_code=200, response_model=MoodInferenceResponse)
def face_detection_endpoint(
    data: FaceDetectionRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
) -> dict:
    """
    Endpoint to perform face detection and mood inference.
    
    :param data: Data for face detection
    :param db: SQLAlchemy session object
    :param user_id: ID of the user making the request
    :return: Inference result
    """
    try:
        logger.info(f"User ID: {user_id} - Processing face detection request")
        return mood_inference(db, user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/face-detection/trial", status_code=200, response_model=MoodInferenceResponse)
def face_detection_trial_endpoint(
    data: FaceDetectionRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Endpoint to perform face detection and mood inference for trial purposes.
    
    :param data: Data for face detection
    :param db: SQLAlchemy session object
    :return: Inference result
    """
    try:
        logger.info("Processing face detection trial request")
        return mood_inference_trial(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))