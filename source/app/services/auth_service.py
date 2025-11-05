from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Request
from functools import wraps
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user_model import User
from ..config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return password

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("✅ Token Decoded:", decoded)
        return decoded
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
def authorize():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract `request` from args or kwargs
            request: Request = kwargs.get('request') or next((arg for arg in args if isinstance(arg, Request)), None)
            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")

            token = request.cookies.get("access_token")
            print("token-->",token,type(token))
            # if not token:
            #     raise HTTPException(status_code=401, detail="Not authenticated")
            # try:
            #     payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            #     print("payload-->",payload)
            #     user_id = payload.get("sub")
            #     print("sub: ", user_id)
            #     if not user_id:
            #         raise HTTPException(status_code=400, detail="Invalid token payload")
            # except Exception as e:
            #     raise HTTPException(status_code=400, detail="Invalid or expired token")

            # db: Session = next(get_db())
            # user = db.query(User).filter(User.user_id == user_id).first()
            # if not user:
                # raise HTTPException(status_code=400, detail="User not found")

            # kwargs["current_user"] = user
            kwargs["current_user"] = None
            return await func(*args, **kwargs)
        return wrapper
    return decorator