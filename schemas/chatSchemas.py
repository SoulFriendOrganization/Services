from pydantic import BaseModel
from typing import Optional, List, Dict

class MessageHistoryItem(BaseModel):
    role: str
    message: str

class ChatRequest(BaseModel):
    message: str
    message_history: Optional[List[MessageHistoryItem]]

class ChatTrialRequest(BaseModel):
    user_name: str
    message: str
    message_history: Optional[List[MessageHistoryItem]] = None
    current_mood: str

class ChatResponse(BaseModel):
    response: str
