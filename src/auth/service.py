from datetime import timedelta, datetime, timezone
from typing import Annotated, List
from uuid import UUID, uuid4
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
import jwt
from jwt import PyJWTError
from sqlalchemy.orm import Session
from starlette.types import Message
from src.entities.user import User
from . import models
from fastapi. security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from ..exceptions import AuthenticationError
import logging
from ..entities import UserPreferences
from .models import UserPreferencesResponse
from ..exceptions import UserNotFoundError, UserPreferencesAlreadyExist

# You would want to store this in an environment variable or a secret manager
SECRET_KEY = '197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 43800

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return bcrypt_context.hash(password)


def authenticate_user(username: str, password: str, db: Session) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        logging.warning(f"Failed authentication attempt for user: {username}")
        return None
    return user


def create_access_token(username: str, user_id: UUID, expires_delta: timedelta) -> str:
    encode = {
        'sub': username,
        'id': str(user_id),
        'exp': datetime.now(timezone.utc) + expires_delta
    }
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> models.TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get('id')
        return models.TokenData(user_id=user_id)
    except PyJWTError as e:
        logging.warning(f"Token verification failed: {str(e)}")
        raise AuthenticationError()


def register_user(db: Session, register_user_request: models.RegisterUserRequest) -> models.Token:
    existing_user = db.query(User).filter(User.username == register_user_request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    new_user = User(
        id=uuid4(),
        username=register_user_request.username,
        birthdate=register_user_request.birthdate,
        password_hash=get_password_hash(register_user_request.password)
    )

    db.add(new_user)
    db.commit()

    access_token = create_access_token(
        username=new_user.username,
        user_id=new_user.id,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return models.Token(access_token=access_token, token_type="bearer")


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]) -> models.TokenData:
    return verify_token(token)

CurrentUser = Annotated [models.TokenData, Depends(get_current_user) ]


def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: Session) -> models.Token:
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise AuthenticationError(message="Nombre de usuario o contraseña incorrecta")
    token = create_access_token(user.username, user.id, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return models.Token(access_token=token, token_type='bearer')


def create_or_update_user_preferences_batch(db: Session, user_id: UUID, preferences: list[dict]):
    results = []

    for pref in preferences:
        question_id = pref["question_id"]
        selected_options = pref["selected_options"]

        existing = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id,
            UserPreferences.question_id == question_id
        ).first()

        if existing:
            existing.selected_options = selected_options
            existing.updated_at = datetime.now()
        else:
            existing = UserPreferences(
                user_id=user_id,
                question_id=question_id,
                selected_options=selected_options
            )
            db.add(existing)

        db.commit()
        db.refresh(existing)

        results.append({
            "question_id": existing.question_id,
            "selected_options": existing.selected_options
        })

    return results
