from pydantic import BaseModel
from typing import Optional, List, Dict

class ChatRequest(BaseModel):
    user_id: str
    message: str
    message_history: Optional[List[Dict[str, str]]] = None
    user_name: Optional[str] = None
    current_mood: Optional[str] = None

class ChatTrialRequest(BaseModel):
    user_name: str
    message: str
    message_history: Optional[List[Dict[str, str]]] = None
    current_mood: str

class ChatResponse(BaseModel):
    response: str
