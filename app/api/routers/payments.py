import stripe
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlalchemy.orm import Session

from app.api.routers.auth import get_current_active_user
from app.core.config import settings
from app.db.session import get_db
from app.models.models import User, Payment
from app.schemas.schemas import Payment as PaymentSchema, StripePaymentIntent

router = APIRouter(tags=["payments"])

# Configure Stripe
stripe.api_key = settings.STRIPE_API_KEY

# Define credit packages
CREDIT_PACKAGES = {
    "small": {"credits": 10, "amount": 499},  # $4.99
    "medium": {"credits": 50, "amount": 1999},  # $19.99
    "large": {"credits": 200, "amount": 5999},  # $59.99
}


@router.post("/payments/create-payment-intent", response_model=Dict[str, Any])
def create_payment_intent(
    payment_data: StripePaymentIntent,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create a Stripe payment intent
    """
    # Validate credit package
    if payment_data.credit_package not in CREDIT_PACKAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid credit package. Available packages: {', '.join(CREDIT_PACKAGES.keys())}",
        )
    
    # Get package details
    package = CREDIT_PACKAGES[payment_data.credit_package]
    amount = package["amount"]
    
    try:
        # Create payment intent with Stripe
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            metadata={
                "user_id": current_user.id,
                "credit_package": payment_data.credit_package,
                "credits": package["credits"],
            },
        )
        
        return {"client_secret": intent.client_secret}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment intent: {str(e)}",
        )


@router.post("/payments/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request, db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Handle Stripe webhook events
    """
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        # Handle successful payment
        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            metadata = payment_intent.get("metadata", {})
            
            # Get user and credit package info
            user_id = int(metadata.get("user_id"))
            credit_package = metadata.get("credit_package")
            credits = int(metadata.get("credits"))
            
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"status": "error", "message": "User not found"}
            
            # Create payment record
            payment = Payment(
                user_id=user_id,
                amount=payment_intent["amount"] / 100,  # Convert cents to dollars
                status="completed",
                stripe_payment_id=payment_intent["id"],
                credits_purchased=credits,
            )
            db.add(payment)
            
            # Add credits to user
            user.credits += credits
            
            db.commit()
            
        return {"status": "success"}
        
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook error: {str(e)}",
        )


@router.get("/payments/history", response_model=list[PaymentSchema])
def get_payment_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get payment history for the current user
    """
    payments = (
        db.query(Payment)
        .filter(Payment.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return payments