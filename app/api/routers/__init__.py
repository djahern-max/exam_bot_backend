
# Import routers to make them available through the package
from app.api.routers import auth, questions, payments

# Initialize router __all__ variable
__all__ = ["auth", "questions", "payments"]