from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import appliances, auth, bills, health, reminders
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Vault - Connected Personal Finance and Asset-Protection Platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(auth.router)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(bills.router)
app.include_router(bills.router, prefix=settings.API_V1_STR)
app.include_router(appliances.router)
app.include_router(appliances.router, prefix=settings.API_V1_STR)
app.include_router(reminders.router)
app.include_router(reminders.router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }
