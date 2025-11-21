from fastapi import APIRouter, Depends
from resources.auth.dependencies import get_current_user
from apps.services.user_services.app.schemas.user_schemas import UserResponse
from ..models.user_model import User

router = APIRouter(prefix="/users", tags=["Users"])

# @router.get("/me", response_model=UserResponse)
# def get_me(current_user: User = Depends(get_current_user)):
#     return current_user
