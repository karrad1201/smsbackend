from pydantic import BaseModel


class UserBase(BaseModel):
    id: int
    name: str


class UserCreate(UserBase):
    password: str


class UserPublic(UserBase):
    class Config:
        from_attributes = True


class UserPrivate(UserBase):
    password_hash: str
