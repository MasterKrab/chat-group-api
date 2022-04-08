from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.utils.bcrypt import verify
from app.oauth2 import create_access_token

router = APIRouter(tags=["Authentication"])


@router.post(
    "/login",
    response_model=schemas.Token,
)
def login(
        user_credentials: schemas.UserLogin,
        db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
            .filter(models.User.username == user_credentials.username)
            .first()
    )

    if not user or not verify(user_credentials.password, user.hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}
