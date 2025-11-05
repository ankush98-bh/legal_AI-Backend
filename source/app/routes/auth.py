from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from ..schemas.auth_schema import SignupRequest, LoginRequest, TokenResponse
from source.app.models.user_model import User
from ..services.auth_service import hash_password, create_access_token
from ..database import get_db

router = APIRouter()

@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest,  response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.mail_id == payload.mail_id).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=payload.username,
        mail_id=payload.mail_id,
        password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.user_id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,  # Set True if using HTTPS
        samesite="None",
        max_age=1800  # 1 hour
    )
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest,  response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.username == payload.identifier) | (User.mail_id == payload.identifier)
    ).first()
    # if not user or not verify_password(payload.password, user.password):
    #     raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": str(user.user_id)})
    # For Production
    # response.set_cookie(
    #     key="access_token",
    #     value=token,
    #     httponly=True,
    #     secure=True,
    #     samesite="Lax",
    #     max_age=1800
    # )
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="None",
        max_age=1800
    )
    return TokenResponse(access_token=token)

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}
