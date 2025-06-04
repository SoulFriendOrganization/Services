from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Dict
from uuid import UUID

class QuizGeneratedRequest(BaseModel):
    theme: Literal["mental_health", "judi_online"]
    difficulty: Literal["easy", "medium", "hard"] 
    
class QuizGeneratedResponse(BaseModel):
    quiz_id: UUID
    title: str
    description: str

class PossibleAnswers(BaseModel):
    A: str = Field(description="Option A")
    B: str = Field(description="Option B")
    C: str = Field(description="Option C")
    D: str = Field(description="Option D")

class QuestionAttemptResponse(BaseModel):
    question_id: UUID
    question_text: str
    possible_answers: PossibleAnswers
    question_type: Literal["multiple_choice", "multiple_answer"]

class QuizAttemptResponse(BaseModel):
    quiz_attempt_id: UUID
    quiz_id: UUID
    questions: list[QuestionAttemptResponse]

class UserAnswer(BaseModel):
    attempt_answer_id: Optional[UUID] = Field(description="ID of the attempt answer")
    user_answer: Optional[List[Literal["A", "B", "C", "D"]]] = Field(description="User's answer to the question")

class EvaluationQuestionDetail(BaseModel):
    question_id: UUID
    question_text: str
    user_answer: List[Optional[Literal["A", "B", "C", "D"]]]
    correct_answer: List[Optional[Literal["A", "B", "C", "D"]]]
    is_correct: bool
    possible_answers: Dict[str, str] = Field(description="Possible answers for the question")

class QuizEvaluationResponse(BaseModel):
    quiz_attempt_id: UUID
    score: int
    points_earned: int
    evaluation_details: List[EvaluationQuestionDetail]

class AttemptIdResponse(BaseModel):
    quiz_attempt_id: UUID

class AttemptQuizAnswerResponse(BaseModel):
    message: str
    attempt_answer_id: UUID

class AttemptQuizAnswerRequest(BaseModel):
    user_answers: List[Optional[Literal["A", "B", "C", "D"]]]