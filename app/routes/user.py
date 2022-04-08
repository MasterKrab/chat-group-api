from fastapi import APIRouter, status, HTTPException, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.utils.bcrypt import hash, verify
from app.utils.password_secure import check_password_secure
from app.oauth2 import create_access_token
from app.oauth2 import get_current_user
from app.config import settings
from typing import List, Optional
import cloudinary
import cloudinary.uploader

cloudinary.config(cloud_name=settings.cloudinary_cloud_name, api_key=settings.cloudinary_api_key, api_secret=settings.cloudinary_api_secret)

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=schemas.Token,
)
def register(
        user_credentials: schemas.UserCreate,
        db: Session = Depends(get_db),
):
    user_credentials.username = user_credentials.username.strip()

    if not 0 < len(user_credentials.username) <= 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be between 1 and 15 characters",
        )

    if db.query(models.User).filter(models.User.username == user_credentials.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    check_password_secure(user_credentials.password)

    user = models.User(
        username=user_credentials.username,
        hash=hash(user_credentials.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/user", response_model=schemas.UserOutput)
def get_user(
        current_user=Depends(get_current_user),
):
    return current_user


@router.put("/user", response_model=schemas.UserOutput)
def update_user(
        avatar: bytes = File(None),
        username: Optional[str] = Form(None),
        current_password: Optional[str] = Form(None),
        password: Optional[str] = Form(None),
        user=Depends(get_current_user),
        db: Session = Depends(get_db),
):
    if username and username != user.username:
        user_with_username = db.query(models.User).filter(
            models.User.username == username
        ).first()

        if user_with_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        user.username = username

    if password:
        check_password_secure(password)

        if not current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required",
            )

        if not current_password or not verify(current_password, user.hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password",
            )

        user.hash = hash(password)

    if avatar is not None:
        if len(avatar) > settings.max_avatar_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image is too big",
            )

        try:
            uploaded_avatar = cloudinary.uploader.upload(
                avatar,
                folder=settings.cloudinary_avatars_folder,
                public_id=user.id,
                overwrite=True,
                resource_type="image",
            )

            user.avatar = uploaded_avatar.get("url")
        except cloudinary.exceptions.Error as error:
            if error.message == " Invalid image file":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid image file",
                )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    db.commit()
    db.refresh(user)
    return user


@router.delete("/user", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
        user=Depends(get_current_user),
        db: Session = Depends(get_db),
):
    if user.avatar:
        cloudinary.uploader.destroy(
            f"{settings.cloudinary_avatars_folder}/{user.id}",
            resource_type="image",
            invalidate=True
        )

    db.delete(user)
    db.commit()


@router.get("/users", response_model=List[schemas.UserOutput])
def get_users(
        db: Session = Depends(get_db),
):
    return db.query(models.User).order_by(models.User.username).all()
