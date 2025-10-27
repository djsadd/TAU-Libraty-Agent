from fastapi import APIRouter, Depends
from app.core.security import oauth2_scheme, decode_access_token

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    return {"email": payload.get("sub")}

#
# {
#   "full_name": "Иванов Иван",
#   "email": "ivanov@example.com",
#   "role": "student",
#   "educational_program": "6B061 – Информационные системы",
#   "language_of_study": "ru",
#   "university": "Туран-Астана",
#   "faculty": "Факультет ИТ",
#   "group_name": "ИС-21",
#   "phone_number": "+77010000000",
#   "avatar_url": "https://cdn.example.com/avatars/u123.jpg"
# }
