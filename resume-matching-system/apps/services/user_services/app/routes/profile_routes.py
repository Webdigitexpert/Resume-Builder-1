from fastapi import APIRouter, Depends
from resources.auth.dependencies import get_current_user
from apps.services.user_services.app.schemas.user_schemas import UserResponse
from ..models.user_model import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "phone": current_user.phone,
        "role": current_user.role
    }

