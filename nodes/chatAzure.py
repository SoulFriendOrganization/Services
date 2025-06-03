from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import os
from dotenv import load_dotenv
from typing import TypedDict, Optional
from pydantic import BaseModel, Field
from logging_config import logger
load_dotenv()

class ChatAzureMentalCareResponse(BaseModel):
    response: str = Field(description="Response from the Azure mental care chat model")

class MessageHistoryItem(BaseModel):
    role: str = Field(description="Role of the message sender (e.g., 'user', 'assistant')")
    message: str = Field(description="Content of the message")

class ChatAzureMentalCareRequest(TypedDict):
    user_name: Optional[str]
    current_mood: str
    message_history: Optional[list[dict]]
    message: str


class ChatAzureMentalCare():
    def __init__(self):
        self.llm =  AzureChatOpenAI(
            deployment_name="gpt-4.1",
            model="gpt-4.1",
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            temperature=0.5,
            max_tokens=5000
        )

    def _formatted_history(self, message_history: MessageHistoryItem) -> str:
        """
        Formats the message history into a string for the prompt.
        """
        formatted_history = []
        for item in message_history:
            role = item.get("role", "user")
            message = item.get("message", "")
            if role and message:
                formatted_history.append(f"<im_start>{role.capitalize()}: {message}<im_end>")
        return "\n".join(formatted_history)

    def chat(self, data: ChatAzureMentalCareRequest) -> ChatAzureMentalCareResponse:
        """
        Sends a chat request to the Azure mental care model and returns the response.
        
        :param data: ChatAzureMentalCareRequest containing user_name, current_mood, message_history, and message
        :return: ChatAzureMentalCareResponse with the model's response
        """
        try:
            logger.info("Preparing to send chat request to Azure mental care model")
            formatted_history = self._formatted_history(data.get("message_history", [])) if data.get("message_history", None) else ""
            mental_care_prompt_template = """
            You are a mental care assistant. Your task is to provide empathetic and supportive responses to users based on their current mood and message history. 
            Make sure to consider the user's current mood and previous messages in your response. And make sure the response is in the same language as the user's message.
            make the user feel better and provide helpful suggestions.

            This is the user provided information:
            user_name: {user_name}
            current_mood: {current_mood}
            Here is the message history:
            {message_history}
            Here is the user's message:
            {message}

            NOTE: If the user asking for non-mental care related questions, please answer them in a concise manner that you are a mental care assistant and you can only answer mental care related questions.
            """
            mental_care_prompt = PromptTemplate(
                input_variables=["user_name", "current_mood", "message_history", "message"],
                template=mental_care_prompt_template
            )
            mental_care = mental_care_prompt | self.llm.with_structured_output(ChatAzureMentalCareResponse)
            logger.info("Sending chat request to Azure mental care model")
            response = mental_care.invoke({
                "user_name": data.get("user_name", "User"),
                "current_mood": data.get("current_mood", "neutral"),
                "message_history": formatted_history,
                "message": data.get("message", "")
            })
            logger.info("Received response from Azure mental care model")
            
            return response
        except Exception as e:
            logger.error(f"Error in chat method: {str(e)}")
            return None
        
    

chat_azure = ChatAzureMentalCare()