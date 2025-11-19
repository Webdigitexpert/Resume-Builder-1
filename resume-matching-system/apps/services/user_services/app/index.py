from fastapi import APIRouter
from .routes import auth_routes, profile_routes

router = APIRouter()
router.include_router(auth_routes.router)
router.include_router(profile_routes.router)
