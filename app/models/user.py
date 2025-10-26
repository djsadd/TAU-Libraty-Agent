from sqlalchemy import Column, String, Integer, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


# --- Перечисление ролей ---
class UserRole(enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


# --- Модель пользователя ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)

    full_name = Column(String, nullable=True)                       # Полное имя пользователя
    educational_program = Column(String, nullable=True)             # Образовательная программа
    language_of_study = Column(String, nullable=True)               # Язык обучения (например, "ru", "kz", "en")
    role = Column(Enum(UserRole), default=UserRole.student)         # Роль (студент / преподаватель / админ)

    university = Column(String, nullable=True)                      # Университет
    faculty = Column(String, nullable=True)                         # Факультет
    group_name = Column(String, nullable=True)                      # Группа (для студентов)
    phone_number = Column(String, nullable=True)                    # Контактный номер
    avatar_url = Column(String, nullable=True)                      # Фото профиля (если нужно)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Когда создан
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())       # Когда обновлён