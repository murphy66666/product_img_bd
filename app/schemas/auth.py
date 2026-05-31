from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    phone: str = Field(min_length=1)
    password: str = Field(min_length=1)
    remember_me: bool = Field(default=False, alias="rememberMe")


class UserProfile(BaseModel):
    id: str
    name: str
    avatar: str
    balance: int
    role: str


class LoginData(BaseModel):
    token: str
    user: UserProfile
