# In app/api/routers/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.models import User, Question, Transaction
from app.core.security import get_current_user

router = APIRouter()


@router.get("")
async def get_dashboard_data(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    # Get question count
    question_count = (
        db.query(Question).filter(Question.user_id == current_user.id).count()
    )

    # Get recent questions
    recent_questions = (
        db.query(Question)
        .filter(Question.user_id == current_user.id)
        .order_by(Question.created_at.desc())
        .limit(5)
        .all()
    )

    # Calculate question type breakdown
    question_types = (
        db.query(Question.question_type, func.count(Question.id))
        .filter(Question.user_id == current_user.id)
        .group_by(Question.question_type)
        .all()
    )

    # Format data for frontend
    question_type_breakdown = [
        {"name": q_type, "value": count} for q_type, count in question_types
    ]

    # Get usage over time (last 7 days)
    today = datetime.now().date()
    usage_over_time = []

    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        date_str = date.strftime("%m/%d")

        # Count questions for this day
        count = (
            db.query(Question)
            .filter(
                Question.user_id == current_user.id,
                func.date(Question.created_at) == date,
            )
            .count()
        )

        usage_over_time.append({"date": date_str, "questions": count})

    # Get credit transaction history
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )

    credit_history = []
    for tx in transactions:
        date_str = tx.created_at.strftime("%m/%d")
        action = "Purchase" if tx.amount > 0 else "Usage"
        credit_history.append({"date": date_str, "action": action, "amount": tx.amount})

    # Get subject areas (if you track this in your database)
    # This is a placeholder - you'll need to adapt this to your schema
    subject_areas = [
        {"subject": "Mathematics", "count": 0},
        {"subject": "Science", "count": 0},
        {"subject": "Business", "count": 0},
        {"subject": "Computer Science", "count": 0},
    ]

    # Check system status
    # This would be replaced with actual checks in a production environment
    system_status = {
        "apiStatus": "operational",
        "processingQueueStatus": "normal",
        "maintenanceAnnouncements": [],
    }

    return {
        "questionCount": question_count,
        "recentQuestions": [q.to_dict() for q in recent_questions],
        "questionTypeBreakdown": question_type_breakdown,
        "usageOverTime": usage_over_time,
        "creditHistory": credit_history,
        "subjectAreas": subject_areas,
        "systemStatus": system_status,
    }
