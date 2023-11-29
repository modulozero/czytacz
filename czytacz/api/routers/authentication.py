from fastapi import APIRouter, HTTPException, status

from czytacz import dependencies, schemas
from czytacz.api import authentication

router = APIRouter()


@router.post("/users/", response_model=schemas.User)
def create_user(
    db: dependencies.DatabaseSession,
    password_hasher: dependencies.PasswordHasher,
    user: schemas.UserCreate,
):
    try:
        return authentication.create_user(
            db=db, password_hasher=password_hasher, user=user
        )
    except authentication.EmailAlreadyUsedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User email already registered",
        )
