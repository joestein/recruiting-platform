from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...core.database import Base, engine
from ...core.security import create_access_token, get_password_hash, verify_password
from ...models.organization import Organization
from ...models.user import User
from ...schemas.auth import Token, RegisterRequest, UserOut
from ..deps import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

# Dev-only: auto-create tables
Base.metadata.create_all(bind=engine)


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(subject=user.id, expires_delta=access_token_expires)
    return Token(access_token=token)


@router.post("/register", response_model=UserOut)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    org_name = payload.org_name or "My Organization"
    org = Organization(name=org_name, slug=org_name.lower().replace(" ", "-"))
    db.add(org)
    db.flush()

    user = User(
        org_id=org.id,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        full_name=payload.email.split("@")[0],
        role="org_admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
