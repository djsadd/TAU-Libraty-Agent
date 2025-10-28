from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.db import get_db
from pydantic import BaseModel, EmailStr
from app.models.user import User, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# --- Pydantic-схема для регистрации ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    iin: str
    full_name: str | None = None
    educational_program: str | None = None
    language_of_study: str | None = None
    role: UserRole = UserRole.student
    university: str | None = None
    faculty: str | None = None
    group_name: str | None = None
    phone_number: str | None = None


# --- Регистрация ---
@router.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Проверяем email или ИИН на уникальность
    existing = db.query(User).filter(
        (User.email == user_data.email) | (User.iin == user_data.iin)
    ).first()

    if existing:
        if existing.email == user_data.email:
            raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
        if existing.iin == user_data.iin:
            raise HTTPException(status_code=400, detail="Пользователь с таким ИИН уже существует")
    print("Saving user with IIN:", user_data.iin)

    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        iin=user_data.iin,  # ← сохраняем ИИН
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

    return {
        "msg": "User created",
        "email": new_user.email,
        "iin": new_user.iin,
        "role": new_user.role.value,
    }


# --- Логин ---
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


# --- Получение текущего пользователя ---
@router.get("/me")
def get_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "university": user.university,
        "faculty": user.faculty,
        "group_name": user.group_name,
        "phone_number": user.phone_number,
        "educational_program": user.educational_program,
        "language_of_study": user.language_of_study,
    }
