from pydantic import BaseModel

class FaceDetectionRequest(BaseModel):
    image: str  # Base64 encoded image string