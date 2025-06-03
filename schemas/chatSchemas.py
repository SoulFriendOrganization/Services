from pydantic import BaseModel
from typing import Optional, List, Dict

class MessageHistoryItem(BaseModel):
    role: str
    message: str

class ChatRequest(BaseModel):
    user_id: str
    message: str
    message_history: Optional[List[MessageHistoryItem]]
    user_name: Optional[str] = None
    current_mood: Optional[str] = None

class ChatTrialRequest(BaseModel):
    user_name: str
    message: str
    message_history: Optional[List[MessageHistoryItem]] = None
    current_mood: str

class ChatResponse(BaseModel):
    response: str
