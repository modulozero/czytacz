from pydantic import BaseModel


class FeedBase(BaseModel):
    name: str
    source: str


class FeedCreate(FeedBase):
    pass


class Feed(FeedBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    feeds: list[Feed] = []

    class Config:
        from_attributes = True
