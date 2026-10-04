from pydantic import BaseModel, ConfigDict, Field

#pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'

    model_config = ConfigDict(from_attributes=True)

class RegisterRequest(BaseModel):
    username: str
    password: str = Field(min_length=6, max_length=20)
    email: str
