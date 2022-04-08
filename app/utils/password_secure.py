from fastapi import HTTPException
from zxcvbn import zxcvbn


def check_password_secure(password):
    score = zxcvbn(password)["score"]

    if score < 3:
        raise HTTPException(status_code=400, detail="Password is too weak")
