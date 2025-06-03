from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.quizSchemas import *
from controllers.quizController import *
from routes.middleware.auth import get_user_id

router = APIRouter()

# ****** Quiz Endpoints ******
@router.post("/generate", status_code=201, response_model=QuizGeneratedResponse)
def generate_quiz_endpoint(
    quiz_data: QuizGeneratedRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
) -> QuizGeneratedResponse:
    """
    Endpoint to generate a quiz for a user.
    
    :param quiz_data: Data for the quiz generation
    :param user_id: ID of the user making the request
    :param db: SQLAlchemy session object
    :return: Generated Quiz object
    """
    try:
        return generate_quiz(db, quiz_data, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    
@router.post("/attempt/{quiz_id}", status_code=200, response_model=QuizAttemptResponse)
def attempt_quiz_endpoint(
    quiz_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
) -> dict:
    """
    Endpoint to attempt a quiz for a user.
    
    :param quiz_id: ID of the quiz to be attempted
    :param user_id: ID of the user making the request
    :param db: SQLAlchemy session object
    :return: Response with quiz attempt result
    """
    try:
        return attempt_quiz(db, quiz_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    
@router.get("/attempt", status_code=200, response_model=AttemptIdResponse)
def get_quiz_attempts_endpoint(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
) -> list:
    """
    Endpoint to get all quiz attempts for a user.
    
    :param user_id: ID of the user making the request
    :param db: SQLAlchemy session object
    :return: List of quiz attempts
    """
    try:
        return get_quiz_attempt_id(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    
@router.get("/attempt/{quiz_attempt_id}", status_code=200, response_model=List[QuestionAttemptResponse])
def get_quiz_attempt_details_endpoint(
    quiz_attempt_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
) -> List[QuestionAttemptResponse]:
    """
    Endpoint to get details of a specific quiz attempt.
    
    :param quiz_attempt_id: ID of the quiz attempt
    :param user_id: ID of the user making the request
    :param db: SQLAlchemy session object
    :return: Details of the quiz attempt
    """
    try:
        return get_quiz_questions(db, quiz_attempt_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    
@router.post("/submit/{quiz_attempt_id}", status_code=200, response_model=QuizEvaluationResponse)
def submit_quiz_attempt_endpoint(
    quiz_attempt_id: str,
    user_answers: List[UserAnswer],
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
) -> QuizEvaluationResponse:
    """
    Endpoint to submit a quiz attempt and evaluate the answers.
    
    :param quiz_attempt_id: ID of the quiz attempt
    :param user_answers: User's answers to the quiz questions
    :param user_id: ID of the user making the request
    :param db: SQLAlchemy session object
    :return: Evaluation response of the quiz attempt
    """
    try:
        return attempt_quiz_answer(db, quiz_attempt_id, user_id, user_answers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    
@router.get("/answer/{quiz_attempt_id}/{question_id}", status_code=200, response_model=UserAnswer)
def get_quiz_answer_details_endpoint(
    quiz_attempt_id: str,
    question_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
) -> List[EvaluationQuestionDetail]:
    """
    Endpoint to get details of a specific question in a quiz attempt.
    
    :param quiz_attempt_id: ID of the quiz attempt
    :param question_id: ID of the question in the quiz attempt
    :param user_id: ID of the user making the request
    :param db: SQLAlchemy session object
    :return: Details of the question in the quiz attempt
    """
    try:
        return get_answer_by_quiz_attempt_question_id(db, quiz_attempt_id, question_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    
@router.get("/answer/{answer_id}", status_code=200, response_model=UserAnswer)
def get_possible_answers_endpoint(
    answer_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
) -> PossibleAnswers:
    """
    Endpoint to get possible answers for a specific question in a quiz attempt.
    
    :param answer_id: ID of the answer
    :param user_id: ID of the user making the request
    :param db: SQLAlchemy session object
    :return: Possible answers for the question
    """
    try:
        return get_answer_by_answer_id(db, answer_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    
@router.post("/submit/{quiz_attempt_id}", status_code=200, response_model=QuizEvaluationResponse)
def submit_quiz_attempt_endpoint(
    quiz_attempt_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
) -> QuizEvaluationResponse:
    """
    Endpoint to submit a quiz attempt and evaluate the answers.
    
    :param quiz_attempt_id: ID of the quiz attempt
    :param user_answers: User's answers to the quiz questions
    :param user_id: ID of the user making the request
    :param db: SQLAlchemy session object
    :return: Evaluation response of the quiz attempt
    """
    try:
        return evaluate_quiz(db, quiz_attempt_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
