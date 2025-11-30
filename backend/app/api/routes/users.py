from fastapi import APIRouter, Depends

from ...models.user import User
from ...schemas.auth import UserOut
from ..deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user
