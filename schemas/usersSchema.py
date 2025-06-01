from typing import Optional, List, TypedDict, Annotated
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