from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Float, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.session import Base


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    OPEN_ENDED = "open_ended"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    credits = Column(Integer, default=0)

    questions = relationship("Question", back_populates="user")
    payments = relationship("Payment", back_populates="user")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    image_path = Column(String)
    extracted_text = Column(Text)
    question_text = Column(Text)
    options = Column(JSON, nullable=True)  # For multiple choice questions
    question_type = Column(Enum(QuestionType))
    answer = Column(Text)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="questions")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    currency = Column(String, default="usd")
    status = Column(String)
    stripe_payment_id = Column(String, unique=True, index=True)
    credits_purchased = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="payments")