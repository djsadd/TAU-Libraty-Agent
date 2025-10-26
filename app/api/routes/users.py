from fastapi import APIRouter, Depends
from app.core.security import oauth2_scheme, decode_access_token

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    return {"email": payload.get("sub")}
