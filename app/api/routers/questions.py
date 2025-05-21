import os
import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api.routers.auth import get_current_active_user
from app.db.session import get_db
from app.models.models import User, Question, QuestionType
from app.schemas.schemas import Question as QuestionSchema, QuestionImageUpload
from app.services.google_vision import GoogleVisionService
from app.services.openai_service import OpenAIService
from app.utils.image_processing import save_uploaded_image

router = APIRouter(tags=["questions"])

# Initialize services
vision_service = GoogleVisionService()
openai_service = OpenAIService()

# Define upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/questions/upload", response_model=QuestionSchema)
async def upload_question_image(
    file: UploadFile = File(...),
    question_type: QuestionType = Form(...),
    show_explanation: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Upload an image of a question, extract text, and analyze it
    """
    # Check if user has enough credits
    if current_user.credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Not enough credits. Please purchase more credits.",
        )

    try:
        # Save the uploaded image, handling HEIC conversion if needed
        file_path = save_uploaded_image(file.file, file.filename)

        # Process the screenshot with Google Vision
        vision_result = vision_service.process_screenshot(file_path, question_type)

        # Analyze the extracted text with OpenAI
        analysis_result = openai_service.analyze_question(
            vision_result["extracted_text"], question_type, show_explanation
        )

        # Create a new Question record
        question = Question(
            user_id=current_user.id,
            image_path=file_path,
            extracted_text=vision_result["extracted_text"],
            question_text=analysis_result["question_text"],
            options=analysis_result["options"],
            question_type=question_type,
            answer=analysis_result["answer"],
            explanation=analysis_result["explanation"],
        )

        # Save to database
        db.add(question)

        # Deduct a credit from the user
        current_user.credits -= 1

        db.commit()
        db.refresh(question)

        return question

    except Exception as e:
        # Delete the uploaded file if there's an error
        if "file_path" in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}",
        )


@router.get("/questions", response_model=List[QuestionSchema])
def get_user_questions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get all questions belonging to the current user
    """
    questions = (
        db.query(Question)
        .filter(Question.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return questions


@router.get("/questions/{question_id}", response_model=QuestionSchema)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific question by ID
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    # Ensure the question belongs to the current user
    if question.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this question",
        )

    return question


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Delete a question
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    # Ensure the question belongs to the current user
    if question.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this question",
        )

    # Delete the image file
    if os.path.exists(question.image_path):
        os.remove(question.image_path)

    # Delete from database
    db.delete(question)
    db.commit()
