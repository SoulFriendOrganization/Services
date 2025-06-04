from typing import Optional, List, TypedDict, Annotated, Dict, Literal
from uuid import UUID
from pydantic import BaseModel, EmailStr, AfterValidator, field_validator

class CreateUserRequest(BaseModel):
    full_name: str
    username: str
    password: str
    age: int
    @field_validator('age')
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Age must be a non-negative integer")
        return v
    class Config:
        orm_mode = True
    
class CreateUserResponse(BaseModel):
    id: UUID
    full_name: str
    username: str
    age: int

    class Config:
        orm_mode = True

class MonthlyMood(BaseModel):
    Happy: int = 0
    Surprise: int = 0
    Sad: int = 0
    Anger: int = 0
    Disgust: int = 0
    Fear: int = 0
    Neutral: int = 0


class FetchedInfoResponse(BaseModel):
    full_name: str
    age: int
    today_mood: Optional[Literal['happy', 'surprise', 'sad', 'anger', 'disgust', 'fear', 'neutral']]
    monthly_mood: MonthlyMood
    score: Optional[int] = 0
    point_earned: Optional[int] = 0

    class Config:
        orm_mode = True