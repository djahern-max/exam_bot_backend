from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.models import QuestionType


# User schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    credits: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class User(UserInDBBase):
    pass


# Question schemas
class QuestionBase(BaseModel):
    question_type: QuestionType


class QuestionCreate(QuestionBase):
    pass


class QuestionImageUpload(BaseModel):
    question_type: QuestionType
    show_explanation: bool = False


class QuestionInDBBase(QuestionBase):
    id: int
    user_id: int
    image_path: str
    extracted_text: str
    question_text: str
    options: Optional[Dict[str, str]] = None
    answer: str
    explanation: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True


class Question(QuestionInDBBase):
    pass


# Payment schemas
class PaymentBase(BaseModel):
    amount: float
    currency: str = "usd"
    credits_purchased: int


class PaymentCreate(PaymentBase):
    pass


class PaymentInDBBase(PaymentBase):
    id: int
    user_id: int
    status: str
    stripe_payment_id: str
    created_at: datetime

    class Config:
        orm_mode = True


class Payment(PaymentInDBBase):
    pass


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[int] = None


# Stripe payment intent
class StripePaymentIntent(BaseModel):
    amount: int  # Amount in cents
    credit_package: str  # e.g., "small", "medium", "large"


# OpenAI analysis response
class OpenAIAnalysisResponse(BaseModel):
    question_text: str
    options: Optional[Dict[str, str]] = None
    answer: str
    explanation: Optional[str] = None