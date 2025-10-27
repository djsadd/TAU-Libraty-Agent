from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.db import get_db
from pydantic import BaseModel, EmailStr
from app.models.user import User, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


# --- Pydantic-схема для регистрации ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    educational_program: str | None = None
    language_of_study: str | None = None
    role: UserRole = UserRole.student
    university: str | None = None
    faculty: str | None = None
    group_name: str | None = None
    phone_number: str | None = None


@router.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        educational_program=user_data.educational_program,
        language_of_study=user_data.language_of_study,
        role=user_data.role,
        university=user_data.university,
        faculty=user_data.faculty,
        group_name=user_data.group_name,
        phone_number=user_data.phone_number,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"msg": "User created", "email": new_user.email, "role": new_user.role.value}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
