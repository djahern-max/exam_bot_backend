from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi.responses import PlainTextResponse
from app.api.routers import questions, auth, payments
from app.core.config import settings
from app.db.session import engine
from app.models import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for analyzing exam questions from screenshots using Google Vision and OpenAI",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(payments.router, prefix="/api")


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/routes-simple", response_class=PlainTextResponse)
async def get_routes_simple():
    """
    Returns a concise list of all routes with their paths and methods.
    """
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = ", ".join(route.methods)
            routes.append(f"{methods}: {route.path}")

    return "\n".join(routes)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)