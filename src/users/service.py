from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from .models import UserListResponse, UserResponse, UserEditRequest
from src.entities.user import User
from src.exceptions import UserNotFoundError
import logging

def get_user_by_id(db: Session, user_id: UUID) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logging.warning(f"User not found with ID: {user_id}")
        raise UserNotFoundError(user_id)
    logging.info(f"Successfully retrieved user with ID: {user_id}")
    return user

def put_edit_user(db: Session, user_id: UUID, newUser: UserEditRequest) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logging.warning(f"User not found with ID: {user_id}")
        raise UserNotFoundError(user_id)

    if newUser.username is not None:
        existing_user = db.query(User).filter(
            User.username == newUser.username,
            User.id != user_id  # excluir el usuario actual
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        user.username = newUser.username

    if newUser.birthdate is not None:
        user.birthdate = newUser.birthdate

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        rol=user.rol,
        username=user.username,
        birthdate=user.birthdate,
        created_at=user.created_at,
    )


def get_all_normal_users(db: Session, user_id: UUID) -> UserListResponse:
    current_user = db.query(User).filter(User.id == user_id).first()

    if not current_user:
        logging.warning(f"User not found with ID: {user_id}")
        return UserListResponse(users=[])

    # Verificar que tenga rol admin
    if current_user.rol != "admin":
        logging.warning(f"User '{current_user.username}' is not admin. Access denied.")
        return UserListResponse(users=[])

    users = db.query(User).filter(User.rol == "user").all()
    logging.info(f"Retrieved {len(users)} normal users (requested by admin: {current_user.username})")

    return UserListResponse(
        users=[
            UserResponse(
                id=u.id,
                username=u.username,
                birthdate=u.birthdate,
                created_at=u.created_at,
                rol=u.rol,
            )
            for u in users
        ]
    )
