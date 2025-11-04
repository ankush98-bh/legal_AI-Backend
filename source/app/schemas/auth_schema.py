from pydantic import BaseModel, EmailStr

class SignupRequest(BaseModel):
    username: str
    mail_id: EmailStr
    password: str
    first_name: str
    last_name: str = None   # Optional last name

class LoginRequest(BaseModel):
    identifier: str  # Can be username or email
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"