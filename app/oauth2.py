from jose import jwt, JWTError
from datetime import datetime, timedelta
from app import schemas, models
from app.database import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode["exp"] = expire

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    return encoded_jwt


def verify_access_token(token: str, credentials_exception=None):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

        id: str = payload.get("user_id")

        if id is None:
            if credentials_exception:
                raise credentials_exception

            return None

        token_data = schemas.TokenData(id=id)

        return token_data
    except JWTError:
        if credentials_exception:
            raise credentials_exception

        return None


def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
        credentials_exception=HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ),
):
    if token is None:
        raise credentials_exception

    token = verify_access_token(token, credentials_exception)

    user = db.query(models.User).filter(models.User.id == token.id).first()

    if user is None:
        raise credentials_exception

    return user
