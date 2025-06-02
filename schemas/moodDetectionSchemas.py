from pydantic import BaseModel
from typing import Literal, Dict

class FaceDetectionRequest(BaseModel):
    image: str  # Base64 encoded image string

class MoodInferenceResponse(BaseModel):
    time: str
    prediction: str
    scores: Dict[Literal['happy', 'surprise', 'sad', 'anger', 'disgust', 'fear', 'neutral'], str]