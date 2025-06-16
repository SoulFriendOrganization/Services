from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.usersSchema import CreateUserRequest, CreateUserResponse, FetchedInfoResponse, MonthlyMood
from controllers.usersController import create_users, login_users
from controllers.quizController import update_quiz_abandoned
from fastapi.security import OAuth2PasswordRequestForm
from logging_config import logger
from routes.middleware.auth import get_user_id
from database.models import User, func, DailyMood, UserCollection, Moods, QuizAttempt
import threading

router = APIRouter()

# ****** Users Endpoints ******
@router.post("/register", status_code=201, response_model=CreateUserResponse)
def create_user_endpoint(
    user_data: CreateUserRequest,
    db: Session = Depends(get_db)
) -> CreateUserResponse:
    """
    Endpoint to create a new user.
    
    :param user_data: User data to be created
    :param db: SQLAlchemy session object
    :return: Created User object
    """
    try:
        logger.info(f"Creating user with username: {user_data.username}")
        return create_users(db, user_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/login", status_code=200)
def login_endpoint(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    response: Response = None
):
    """
    Endpoint to log in a user.

    :param form_data: Form data containing username and password
    :param db: SQLAlchemy session object
    :return: Response with access token
    """
    try:
        logger.info(f"User login attempt with username: {form_data.username}")
        access_token = login_users(db, form_data.username, form_data.password)
        if response is None:
            raise HTTPException(status_code=500, detail="Response object is required")
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=False,
            secure=True,  
            samesite="Lax"  
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/logout", status_code=200)
def logout_endpoint(response: Response):
    """
    Endpoint to log out a user by clearing the access token cookie.

    :param response: Response object to clear the cookie
    :return: Success message
    """
    try:
        logger.info("User logged out successfully")
        response.delete_cookie(key="token")
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/fetch_stat", status_code=200, response_model=FetchedInfoResponse)
def fetch_user_info_endpoint(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    Request: Request = None,
    response: Response = None
):
    """
    Endpoint to fetch user information and update quiz abandonment status.
    :param user_id: ID of the user making the request
    :param db: SQLAlchemy session object
    :return: User information including full name, age, and mood statistics
    """
    try:
        logger.info(f"Fetching user info for user ID: {user_id}")
        user_info = db.query(User).filter(User.id == user_id).first()
        thread = threading.Thread(
            target=update_quiz_abandoned, 
            args=(db, user_id)
        )
        thread.start()
        # Cek if the user still has active quiz attempts
        quiz_attempt = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.expired_at > func.now(),
            QuizAttempt.is_completed == False
        ).first()
        if quiz_attempt:
            logger.warning(f"User has an active quiz attempt that is not completed.")
            origin_url = Request.headers.get("Origin") if Request else ""
            raise HTTPException(
            status_code=307,
            detail={
                "message": "You have an active quiz attempt that is not completed.",
                "redirect_url": f"/quiz/{quiz_attempt.id}"
            }
            )
        today_mood = db.query(
            Moods.name
        ).join(
            DailyMood, 
            Moods.id == DailyMood.mood_level
        ).filter(
            DailyMood.user_id == user_id,
            DailyMood.date == func.current_date()
        ).first()
        monthly_mood = db.query(
            Moods.name,
            func.count(DailyMood.mood_level).label('mood_count')
        ).join(
            DailyMood, 
            Moods.id == DailyMood.mood_level
        ).filter(
            DailyMood.user_id == user_id,
            DailyMood.date >= func.date_trunc('month', func.current_date())
        ).group_by(Moods.name).all()
        monthly_mood_dict = {mood.name: mood.mood_count for mood in monthly_mood}
        score_and_points = db.query(
            UserCollection.score, 
            UserCollection.point_earned
        ).filter(UserCollection.user_id == user_id).first()
        return FetchedInfoResponse(
            full_name=user_info.full_name,
            age=user_info.age,
            today_mood=today_mood[0] if today_mood else None,
            monthly_mood=MonthlyMood(**monthly_mood_dict),
            score=score_and_points.score if score_and_points else 0,
            point_earned=score_and_points.point_earned if score_and_points else 0
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        