from uuid import UUID
from typing import List, Optional
from database.models import Quiz, QuizAttempt, AttemptAnswer, UserCollection, Question, func
from sqlalchemy.orm import Session
from logging_config import logger
from schemas.quizSchemas import *
from nodes.quizAiAgent import quiz_agent
from os import getenv

def generate_quiz(db: Session, quiz_data: QuizGeneratedRequest, user_id: UUID):
    """
    Generate a quiz based on the provided data and save it to the database.
    
    :param db: SQLAlchemy session object
    :param quiz_data: Data for the quiz generation
    :param user_id: ID of the user for whom the quiz is being generated
    :return: Generated Quiz object
    """
    try:
        quiz_data = quiz_data.model_dump()
        logger.info(f"Generating quiz with data: {quiz_data} for user {user_id}")
        if quiz_data.get("theme") == "mental_health":
            user_condition_summary = db.query(UserCollection).filter(
                UserCollection.user_id == user_id,
                UserCollection.user_condition_summary.isnot(None)
            ).first()
        else:
            user_condition_summary = None
        quiz_generated = quiz_agent.generate_quiz(quiz_data.get("theme"),
                                                   quiz_data.get("difficulty"),
                                                    user_condition_summary,
                                                    total_questions= 5 if getenv("PRODUCTION") == "True" 
                                                                    else 2)
        if not quiz_generated:
            logger.error("Quiz generation failed, no data returned from AI agent")
            raise ValueError("Quiz generation failed, no data returned from AI agent")
        quiz = Quiz(
            generated_by_user_id= user_id,
            title=quiz_generated.get("quiz_title"),
            description=quiz_generated.get("quiz_description"),   
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        logger.info(f"Quiz {quiz.id} generated successfully for user {user_id}")
        for question_data in quiz_generated.get("questions", []):
            question = Question(
                quiz_id=quiz.id,
                question_text=question_data.get("question"),
                possible_answers=question_data.get("possible_answers"),
                question_type=question_data.get("question_type"),
                correct_answer=question_data.get("correct_answer")
            )
            db.add(question)
        db.commit()
        response = QuizGeneratedResponse(
            quiz_id=quiz.id,
            title=quiz.title,
            description=quiz.description
        )
        logger.info(f"Quiz {quiz.id} generated and saved successfully")
        return response
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise ValueError("Failed to generate quiz") from e
    
def attempt_quiz(db: Session, quiz_id: UUID, user_id: UUID) -> QuizAttemptResponse:
    """
    Create a quiz attempt for a given quiz and user.
    
    :param db: SQLAlchemy session object
    :param quiz_id: ID of the quiz
    :param user_id: ID of the user
    """
    try:
        logger.info(f"Creating quiz attempt for quiz {quiz_id} and user {user_id}")
        questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
        if not questions:
            logger.error(f"No questions found for quiz {quiz_id}")
            raise ValueError("No questions found for the quiz")
        
        quiz_attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id
        )
        db.add(quiz_attempt)
        db.commit()
        db.refresh(quiz_attempt)
        logger.info(f"Quiz attempt {quiz_attempt.id} created successfully for user {user_id}")
        response = QuizAttemptResponse(
            quiz_attempt_id=quiz_attempt.id,
            quiz_id=quiz_id,
            questions=[{
                "question_id": question.id,
                "question_text": question.question_text,
                "possible_answers": question.possible_answers,
                "question_type": question.question_type
            } for question in questions],
            expired_at=quiz_attempt.expired_at.strftime("%Y-%m-%d %H:%M:%S")
        )
        return response
    except Exception as e:
        logger.error(f"Error creating quiz attempt: {e}")
        raise ValueError("Failed to create quiz attempt") from e
    
def get_quiz_attempt_id(db: Session, user_id: UUID) -> AttemptIdResponse:
    """
    Retrieve the latest quiz attempt ID for a user.
    
    :param db: SQLAlchemy session object
    :param user_id: ID of the user
    :return: QuizAttempt ID if found, else None
    """
    try:
        logger.info(f"Retrieving latest quiz attempt for user {user_id}")
        quiz_attempt = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.expired_at > func.now()
        ).order_by(QuizAttempt.attempted_at.desc()).first()
        
        if not quiz_attempt:
            logger.warning(f"No active quiz attempt found for user {user_id}")
            return None
        
        logger.info(f"Latest quiz attempt ID {quiz_attempt.id} retrieved for user {user_id}")
        response = {
            "quiz_attempt_id": quiz_attempt.id
        }
        return response
    except Exception as e:
        logger.error(f"Error retrieving quiz attempt ID: {e}")
        raise ValueError("Failed to retrieve quiz attempt ID") from e
    
def get_quiz_questions(db: Session, quiz_attempt_id: UUID, user_id: UUID) -> CheckQuizAttemptQuestion:
    """
    Retrieve questions for a quiz attempt.
    
    :param db: SQLAlchemy session object
    :param quiz_attempt_id: ID of the quiz attempt
    :param user_id: ID of the user
    :return: List of questions for the quiz attempt
    """
    try:
        logger.info(f"Retrieving questions for quiz attempt {quiz_attempt_id} by user {user_id}")
        quiz_attempt = db.query(QuizAttempt).filter(QuizAttempt.id == quiz_attempt_id, QuizAttempt.user_id == user_id, QuizAttempt.expired_at > func.now()).first()
        if not quiz_attempt:
            logger.error(f"Quiz attempt {quiz_attempt_id} not found for user {user_id}")
            raise ValueError("Quiz attempt not found for the user or has expired")
        
        questions = db.query(Question).filter(Question.quiz_id == quiz_attempt.quiz_id).all()
        if not questions:
            logger.error(f"No questions found for quiz attempt {quiz_attempt_id}")
            raise ValueError("No questions found for the quiz attempt")
        
        response = CheckQuizAttemptQuestion(
            questions=[{
                "question_id": question.id,
                "question_text": question.question_text,
                "possible_answers": question.possible_answers,
                "question_type": question.question_type
            } for question in questions],
            expired_at=quiz_attempt.expired_at.strftime("%Y-%m-%d %H:%M:%S")
        )
        print(response)
        logger.info(f"Questions retrieved successfully for quiz attempt {quiz_attempt_id} by user {user_id}")
        return response
    except Exception as e:
        logger.error(f"Error retrieving quiz questions: {e}")
        raise ValueError("Failed to retrieve quiz questions") from e

    
def attempt_quiz_answer(db: Session, quiz_attempt_id: UUID, user_id: UUID, question_id:UUID, answers: AttemptQuizAnswerRequest) -> AttemptQuizAnswerResponse:
    """
    Submit answers for a quiz attempt by one question.
    
    :param db: SQLAlchemy session object
    :param quiz_attempt_id: ID of the quiz attempt
    :param user_id: ID of the user
    :param answers: List of answers for the quiz attempt
    """
    try:
        logger.info(f"Submitting answers for quiz attempt {quiz_attempt_id} by user {user_id}")
        quiz_attempt = db.query(QuizAttempt).filter(
            QuizAttempt.id == quiz_attempt_id,
            QuizAttempt.user_id == user_id,
            QuizAttempt.expired_at > func.now(),
            QuizAttempt.is_completed == False
        ).first()
        if not quiz_attempt:
            logger.error(f"Quiz attempt {quiz_attempt_id} not found or has expired for user {user_id}")
            raise ValueError("Quiz attempt not found or has expired")
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            logger.error(f"Question {question_id} not found for quiz attempt {quiz_attempt_id}")
            raise ValueError("Question not found for the quiz attempt")
        if question.question_type == "multiple_choice" and len(answers.user_answers) > 1:
            logger.error(f"Invalid number of answers for question {question_id} in quiz attempt {quiz_attempt_id}")
            raise ValueError("Invalid number of answers for the question")
        check_answer = db.query(AttemptAnswer).filter(
            AttemptAnswer.attempt_id == quiz_attempt_id,
            AttemptAnswer.question_id == question_id
        ).first()
        if check_answer:
            db.query(AttemptAnswer).filter(
            AttemptAnswer.id == check_answer.id
            ).update(
                {AttemptAnswer.user_answer: answers.model_dump().get("user_answers", [])},
                synchronize_session=False
            )
        else:
            logger.info(f"Creating new answer record for question {question_id} in quiz attempt {quiz_attempt_id}")
            answer = AttemptAnswer(
                attempt_id=quiz_attempt_id,
                question_id=question_id,
                user_answer=answers.model_dump().get("user_answers", []),
            )
            db.add(answer)
        db.commit()
        db.refresh(answer)
        logger.info(f"Answers submitted successfully for quiz attempt {quiz_attempt_id} by user {user_id}")
        response = AttemptQuizAnswerResponse(
            message="Answers submitted successfully",
            attempt_answer_id=check_answer.id if check_answer else answer.id
        )
        return response
    except Exception as e:
        logger.error(f"Error submitting answers for quiz attempt: {e}")
        raise ValueError("Failed to submit answers for quiz attempt") from e
    
def get_answer_by_quiz_attempt_question_id(db: Session, quiz_attempt_id: UUID, question_id:UUID, user_id: UUID) -> UserAnswer:
    """
    Retrieve answers for a specific question in a quiz attempt.
    :param db: SQLAlchemy session object
    :param quiz_attempt_id: ID of the quiz attempt
    :param question_id: ID of the question
    :param user_id: ID of the user
    :return: List of answers for the specified question in the quiz attempt
    """
    try:
        logger.info(f"Retrieving answers for question {question_id} in quiz attempt {quiz_attempt_id} by user {user_id}")
        answers = db.query(AttemptAnswer).filter(
            AttemptAnswer.attempt_id == quiz_attempt_id,
            AttemptAnswer.question_id == question_id
        ).first()
        
        if not answers:
            logger.error(f"No answers found for question {question_id} in quiz attempt {quiz_attempt_id}")
            raise ValueError("No answers found for the specified question in the quiz attempt")
        response = {"attempt_answer_id": answers.id ,"user_answer": answers.user_answer}
        logger.info(f"Answers retrieved successfully for question {question_id} in quiz attempt {quiz_attempt_id} by user {user_id}")
        return response
    except Exception as e:
        logger.error(f"Error retrieving question answers: {e}")
        raise ValueError("Failed to retrieve question answers") from e
    
def get_answer_by_answer_id(db: Session, answer_id: UUID, user_id: UUID) -> UserAnswer:
    """
    Retrieve an answer by its ID for a specific user.
    
    :param db: SQLAlchemy session object
    :param answer_id: ID of the answer
    :param user_id: ID of the user
    :return: AttemptAnswer object if found, else None
    """
    try:
        logger.info(f"Retrieving answer with ID {answer_id} for user {user_id}")
        answer = db.query(AttemptAnswer).filter(
            AttemptAnswer.id == answer_id
        ).first()
        
        if not answer:
            logger.error(f"Answer with ID {answer_id} not found for user {user_id}")
            raise ValueError("Answer not found for the specified ID")
        response = {
            "attempt_answer_id": answer_id,
            "user_answer": answer.user_answer
        }
        logger.info(f"Answer retrieved successfully for user {user_id}")
        return response
    except Exception as e:
        logger.error(f"Error retrieving answer by ID: {e}")
        raise ValueError("Failed to retrieve answer by ID") from e
    
def evaluate_quiz(db: Session, quiz_attempt_id: UUID, user_id: UUID) -> QuizEvaluationResponse:
    """
    Evaluate a quiz attempt and return the score.
    
    :param db: SQLAlchemy session object
    :param quiz_attempt_id: ID of the quiz attempt
    :param user_id: ID of the user
    :return: QuizEvaluationResponse containing the score and evaluation details
    """
    try:
        logger.info(f"Evaluating quiz attempt {quiz_attempt_id} for user {user_id}")
        quiz_attempt = db.query(QuizAttempt).filter(
            QuizAttempt.id == quiz_attempt_id,
            QuizAttempt.is_completed == False
        ).first()
        
        if not quiz_attempt:
            logger.error(f"Quiz attempt {quiz_attempt_id} not found or has expired for user {user_id}")
            raise ValueError("Quiz attempt not found or has expired")
        
        answers = db.query(AttemptAnswer).filter(AttemptAnswer.attempt_id == quiz_attempt_id).all()
        if not answers:
            logger.error(f"No answers found for quiz attempt {quiz_attempt_id}")
            raise ValueError("No answers found for the quiz attempt")
        
        score = 0
        point = 0
        evaluation_details = []

        questions = db.query(Question).filter(
            Question.quiz_id == quiz_attempt.quiz_id
        ).all()

        for question in questions:
            answer = next((a for a in answers if a.question_id == question.id), [])
            is_correct = False
            if answer:
                is_correct = set(answer.user_answer) == set(question.correct_answer)
            # Update the answer record
            db.query(AttemptAnswer).filter(
                AttemptAnswer.id == answer.id
            ).update(
                {AttemptAnswer.is_correct: is_correct},
                synchronize_session=False
            )
            
            # Add points if correct
            if is_correct:
                score += 1
                point += 1
            
            # Add to evaluation details regardless of whether answer exists
            evaluation_details.append({
            "question_id": question.id,
            "question_text": question.question_text,
            "possible_answers": question.possible_answers,
            "user_answer": answer.user_answer if answer else [],
            "correct_answer": question.correct_answer,
            "is_correct": is_correct
            })
        score_in_percentage = (score / len(questions)) * 100
        db.query(QuizAttempt).filter(
            QuizAttempt.id == quiz_attempt_id
        ).update(
            {QuizAttempt.is_completed: True, QuizAttempt.score: score_in_percentage, QuizAttempt.points_earned: point},
            synchronize_session=False
        )
        user_collection = db.query(UserCollection).filter(
            UserCollection.user_id == user_id
        ).first()
        if user_collection:
            user_collection.score = int((user_collection.score + score_in_percentage) / (user_collection.num_quiz_attempt + 1))
            user_collection.point_earned += point
            user_collection.num_quiz_attempt += 1
            db.commit()
        else:
            user_collection = UserCollection(
                user_id=user_id,
                score=(score_in_percentage / 1),
                point_earned=point,
                num_quiz_attempt=1
            )
            db.add(user_collection)
            db.commit()
        
        
        evaluation_response = QuizEvaluationResponse(
            quiz_attempt_id=quiz_attempt.id,
            score=score_in_percentage,
            points_earned=point,
            evaluation_details=evaluation_details
        )
        
        logger.info(f"Quiz attempt {quiz_attempt_id} evaluated successfully with score {evaluation_response.score}")
        return evaluation_response
    except Exception as e:
        logger.error(f"Error evaluating quiz attempt: {e}")
        raise ValueError("Failed to evaluate quiz attempt") from e



def update_quiz_abandoned(db: Session, user_id: UUID) -> None:
    """
    Update the quiz attempt that abandoned from user for a given quiz and user.
    
    :param db: SQLAlchemy session object
    :param quiz_id: ID of the quiz
    :param user_id: ID of the user
    """
    try:
        check_abandoned_quiz = db\
            .query(QuizAttempt)\
                .filter(QuizAttempt.user_id == user_id, 
                        QuizAttempt.is_completed == False,
                        QuizAttempt.expired_at < func.now())\
                            .all()
        
        for quiz_attempt in check_abandoned_quiz:
            logger.info(f"Updating quiz {quiz_attempt.id} for user {user_id} to abandoned status")
            questions = db.query(Question).filter(Question.quiz_id == quiz_attempt.quiz_id).all()
            answers = db.query(AttemptAnswer).filter(
                AttemptAnswer.attempt_id == quiz_attempt.id
            ).all()

            score = 0
            point = 0

            for question in questions:
                answer = next((a for a in answers if a.question_id == question.id), [])
                is_correct = False
                if answer:
                    is_correct = set(answer.user_answer) == set(question.correct_answer)
                # Update the answer record
                db.query(AttemptAnswer).filter(
                    AttemptAnswer.id == answer.id
                ).update(
                    {AttemptAnswer.is_correct: is_correct},
                    synchronize_session=False
                )
                
                # Add points if correct
                if is_correct:
                    score += 1
                    point += 1
            score_in_percentage = (score / len(questions)) * 100 if questions else 0
            db.query(QuizAttempt).filter(
                QuizAttempt.id == quiz_attempt.id
            ).update(
                {QuizAttempt.is_completed: True, QuizAttempt.score: score_in_percentage, QuizAttempt.points_earned: point},
                synchronize_session=False
            )
            db.commit()
            user_collection = db.query(UserCollection).filter(
            UserCollection.user_id == user_id
            ).first()
            if user_collection:
                user_collection.score = int((user_collection.score + score_in_percentage) / (user_collection.num_quiz_attempt + 1))
                user_collection.point_earned += point
                user_collection.num_quiz_attempt += 1
                db.commit()
            else:
                user_collection = UserCollection(
                    user_id=user_id,
                    score=(score_in_percentage / 1),
                    point_earned=point,
                    num_quiz_attempt=1
                )
                db.add(user_collection)
                db.commit()
            logger.info(f"Quiz {quiz_attempt.id} for user {user_id} updated to abandoned status successfully")
            return
    except Exception as e:
        logger.error(f"Error updating quiz attempt: {e}")
        raise ValueError("Failed to update quiz attempt") from e