import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID, uuid4

import jwt
from fastapi import Depends, HTTPException, status
from fastapi. security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import PyJWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.entities.user import User
from src.user_timezone import to_user_timezone

from ..entities import UserPreferences
from ..exceptions import AuthenticationError
from . import models
import os
import json
from src.fsrs.fsrs import State
from src.entities.card import Card as CardDB


KANJI_FILE = os.path.join(os.path.dirname(__file__), "../kanjis_convertidos_normalizado.json")

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
    # 1) comprobación de username existente
    existing_user = db.query(User).filter(User.username == register_user_request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # 2) crear usuario (id con uuid4(), así podemos usarlo sin hacer commit ahora)
    new_user = User(
        id=uuid4(),
        username=register_user_request.username,
        birthdate=register_user_request.birthdate,
        password_hash=get_password_hash(register_user_request.password),
        timezone=register_user_request.timezone,
        rol="user",
    )

    # No hacemos commit todavía — lo haremos al final en una sola transacción.
    db.add(new_user)

    # 3) cargar kanjis desde JSON y seleccionar hasta 200 (aquí: primeros 200 por position)
    try:
        with open(KANJI_FILE, "r", encoding="utf-8") as f:
            kanji_list = json.load(f)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error reading kanji file: {e}")

    # Ordenamos por 'position' si existe, y extraemos 'character'
    def _position_key(item):
        try:
            return int(item.get("position", 10**9))
        except Exception:
            return 10**9

    sorted_kanjis = sorted(kanji_list, key=_position_key)
    kanji_chars = [item.get("character") for item in sorted_kanjis if item.get("character")]

    # Tomamos hasta 200 — sin usar random.sample para evitar avisos de tipos
    selected_chars = kanji_chars[:50]

    # 4) crear cards en memoria asociadas al new_user.id
    now_local = to_user_timezone(datetime.now(), register_user_request.timezone or new_user.timezone)

    cards_to_add = []
    for ch in selected_chars:
        card = CardDB(
            user_id=new_user.id,
            kanji_char=ch,
            state=int(State.Learning),
            step=0,
            stability=None,
            difficulty=None,
            due=None,
            last_review=None,
            created_at=now_local,
        )
        cards_to_add.append(card)
        db.add(card)

    # 5) commit único (usuario + cards)
    try:
        db.commit()
        # optional: refresh if necesitas los ids generados
        # db.refresh(new_user)
        # for c in cards_to_add:
        #     db.refresh(c)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user/cards: {e}")

    # 6) crear token y devolverlo
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
