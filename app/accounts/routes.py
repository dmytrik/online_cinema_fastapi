from datetime import datetime, timezone
from typing import cast

from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.dependencies import (
    get_jwt_auth_manager, get_current_user_id,
)
from app.accounts.models import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
)
from app.accounts.email_service import send_email
from core.database import get_db
from core.config import settings
from exceptions import BaseSecurityError
from app.accounts.schemas import (
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
    MessageResponseSchema,
    PasswordResetRequestSchema,
    PasswordResetCompleteRequestSchema,
    UserLoginResponseSchema,
    UserLoginRequestSchema,
    TokenRefreshRequestSchema,
    TokenRefreshResponseSchema,
)

from security.interfaces import JWTAuthManagerInterface

router = APIRouter()


@router.post(
    "/register/",
    response_model=UserRegistrationResponseSchema,
    summary="User Registration",
    description="Register a new user with an email and password.",
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "Conflict - User with this email already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "A user with this email test@example.com already exists."
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error - An error occurred during user creation.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred during user creation."
                    }
                }
            },
        },
    },
)
def register_user(
        user_data: UserRegistrationRequestSchema,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
) -> UserRegistrationResponseSchema:
    """
    Endpoint for user registration.

    Registers a new user, hashes their password, and assigns them to the default user group.
    If a user with the same email already exists, an HTTP 409 error is raised.
    In case of any unexpected issues during the creation process, an HTTP 500 error is returned.
    """
    db_user = (
        db.query(UserModel).filter(UserModel.email == user_data.email).first()
    )

    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with this email {user_data.email} already exists.",
        )

    try:
        group = (
            db.query(UserGroupModel)
            .filter(UserGroupModel.name == UserGroupEnum.USER)
            .first()
        )

        if not group:
            group = UserGroupModel(name=UserGroupEnum.USER)
            db.add(group)
            db.flush()
            db.refresh(group)

        new_user = UserModel(
            email=user_data.email,
            password=user_data.password,
            group_id=group.id,
            group=group,
        )
        db.add(new_user)
        db.flush()
        db.refresh(new_user)

        activation_token = ActivationTokenModel(
            user_id=new_user.id, user=new_user
        )
        db.add(activation_token)
        db.flush()
        db.refresh(activation_token)

        new_user.activation_token = activation_token

        db.commit()

        body = (f"Please click the link to activate your account: "
                f"{settings.ACTIVATION_URL}/{activation_token.token}/")

        subject = "Activate Your Account"

        background_tasks.add_task(
            send_email,
            new_user.email,
            body,
            subject,
        )
        return new_user
    except SQLAlchemyError as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(err))


@router.get(
    "/activate/{activation_token}/",
    response_model=MessageResponseSchema,
    summary="Activate User Account",
    description="Activate a user's account using their email and activation token.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Bad Request - The activation token is invalid or expired, "
                           "or the user account is already active.",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Invalid Token",
                            "value": {
                                "detail": "Invalid or expired activation token."
                            },
                        },
                        "already_active": {
                            "summary": "Account Already Active",
                            "value": {
                                "detail": "User account is already active."
                            },
                        },
                    }
                }
            },
        },
    },
)
def activate_account(
    activation_token: str,
    db: Session = Depends(get_db),
) -> MessageResponseSchema:
    """
    Endpoint to activate a user's account.

    Verifies the activation token for a user. If valid, activates the account
    and deletes the token. If invalid or expired, raises an appropriate error.
    """
    token_record = (
        db.query(ActivationTokenModel)
        .join(UserModel)
        .filter(
            ActivationTokenModel.token == activation_token,
        )
        .first()
    )

    if not token_record or cast(datetime, token_record.expires_at).replace(
            tzinfo=timezone.utc
    ) < datetime.now(timezone.utc):
        if token_record:
            db.delete(token_record)
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired activation token.",
        )

    user = token_record.user
    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is already active.",
        )

    user.is_active = True
    db.delete(token_record)
    db.commit()

    return MessageResponseSchema(
        message="User account activated successfully."
    )


@router.post(
    "/password-reset/request/",
    response_model=MessageResponseSchema,
    summary="Request Password Reset Token",
    description=(
            "Allows a user to request a password reset token. If the user exists and is active, "
            "a new token will be generated and any existing tokens will be invalidated."
    ),
    status_code=status.HTTP_200_OK,
)
def request_password_reset_token(
        data: PasswordResetRequestSchema,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
) -> MessageResponseSchema:
    """
    Endpoint to request a password reset token.

    If the user exists and is active, invalidates any existing password reset tokens and generates a new one.
    Always responds with a success message to avoid leaking user information.
    """
    user = db.query(UserModel).filter_by(email=data.email).first()

    if not user or not user.is_active:
        return MessageResponseSchema(
            message="If you are registered, you will receive an email with instructions."
        )

    db.query(PasswordResetTokenModel).filter_by(user_id=user.id).delete()

    reset_token = PasswordResetTokenModel(user_id=cast(int, user.id))
    db.add(reset_token)
    db.commit()

    # sending an email
    if user and isinstance(user, UserModel) and user.email:
        body = (f"Please click the link to reset your password: "
                f"{settings.PASSWORD_RESET_URL}. Enter your token {reset_token.token} in form")
        subject = "Password Reset Request"
        background_tasks.add_task(
            send_email,
            user.email,
            body,
            subject,
        )
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return MessageResponseSchema(
        message="If you are registered, you will receive an email with instructions."
    )


@router.post(
    "/reset-password/complete/",
    response_model=MessageResponseSchema,
    summary="Reset User Password",
    description="Reset a user's password if a valid token is provided.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Bad Request - The provided email or token is invalid, "
                           "the token has expired, or the user account is not active.",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_email_or_token": {
                            "summary": "Invalid Email or Token",
                            "value": {"detail": "Invalid email or token."},
                        },
                        "expired_token": {
                            "summary": "Expired Token",
                            "value": {"detail": "Invalid email or token."},
                        },
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error - An error occurred while resetting the password.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred while resetting the password."
                    }
                }
            },
        },
    },
)
def reset_password(
        data: PasswordResetCompleteRequestSchema,
        db: Session = Depends(get_db),
) -> MessageResponseSchema:
    """
    Endpoint for resetting a user's password.

    Validates the token and updates the user's password if the token is valid and not expired.
    Deletes the token after successful password reset.
    """
    user = db.query(UserModel).filter_by(email=data.email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or token.",
        )

    token_record = (
        db.query(PasswordResetTokenModel).filter_by(user_id=user.id).first()
    )

    expires_at = cast(datetime, token_record.expires_at).replace(
        tzinfo=timezone.utc
    )

    if (
            not token_record
            or token_record.token != data.token
            or expires_at < datetime.now(timezone.utc)
    ):
        if token_record:
            db.delete(token_record)
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or token.",
        )

    try:
        user.password = data.password
        db.delete(token_record)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting the password.",
        )

    return MessageResponseSchema(message="Password reset successfully.")


@router.post(
    "/login/",
    response_model=UserLoginResponseSchema,
    summary="User Login",
    description="Authenticate a user and return access and refresh tokens.",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {
            "description": "Unauthorized - Invalid email or password.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email or password."}
                }
            },
        },
        403: {
            "description": "Forbidden - User account is not activated.",
            "content": {
                "application/json": {
                    "example": {"detail": "User account is not activated."}
                }
            },
        },
        500: {
            "description": "Internal Server Error - An error occurred while processing the request.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred while processing the request."
                    }
                }
            },
        },
    },
)
def login_user(
        login_data: UserLoginRequestSchema,
        db: Session = Depends(get_db),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> UserLoginResponseSchema:
    """
    Endpoint for user login.

    Authenticates a user using their email and password.
    If authentication is successful, creates a new refresh token and
    returns both access and refresh tokens.
    """
    user = cast(
        UserModel,
        db.query(UserModel).filter_by(email=login_data.email).first(),
    )
    if not user or not user.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not activated.",
        )

    jwt_refresh_token = jwt_manager.create_refresh_token({"user_id": user.id})

    try:
        refresh_token = RefreshTokenModel.create(
            user_id=user.id,
            days_valid=settings.REFRESH_TOKEN_EXPIRE_DAYS,
            token=jwt_refresh_token,
        )
        db.add(refresh_token)
        db.flush()
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the request.",
        )

    jwt_access_token = jwt_manager.create_access_token({"user_id": user.id})
    return UserLoginResponseSchema(
        access_token=jwt_access_token,
        refresh_token=jwt_refresh_token,
    )


@router.post(
    "/logout/",
    summary="User Logout",
    description="Revoke the refresh token and log the user out.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {
            "description": "Bad Request - The provided refresh token is invalid or expired.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid refresh token."}
                }
            },
        },
        401: {
            "description": "Unauthorized - Refresh token not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Refresh token not found."}
                }
            },
        },
    },
)
def logout_user(
        db: Session = Depends(get_db),
        current_user_id: int = Depends(get_current_user_id),
):
    """
    Logout endpoint that revokes the refresh token.
    """
    user = db.query(UserModel).filter_by(id=current_user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    refresh_token_record = db.query(RefreshTokenModel).filter_by(user_id=user.id).first()
    if not refresh_token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found.",
        )

    db.delete(refresh_token_record)
    db.commit()


@router.post(
    "/refresh/",
    response_model=TokenRefreshResponseSchema,
    summary="Refresh Access Token",
    description="Refresh the access token using a valid refresh token.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Bad Request - The provided refresh token is invalid or expired.",
            "content": {
                "application/json": {
                    "example": {"detail": "Token has expired."}
                }
            },
        },
        401: {
            "description": "Unauthorized - Refresh token not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Refresh token not found."}
                }
            },
        },
        404: {
            "description": "Not Found - The user associated with the token does not exist.",
            "content": {
                "application/json": {"example": {"detail": "User not found."}}
            },
        },
    },
)
def refresh_access_token(
        token_data: TokenRefreshRequestSchema,
        db: Session = Depends(get_db),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> TokenRefreshResponseSchema:
    """
    Endpoint to refresh an access token.

    Validates the provided refresh token, extracts the user ID from it, and issues
    a new access token. If the token is invalid or expired, an error is returned.
    """
    try:
        decoded_token = jwt_manager.decode_refresh_token(
            token_data.refresh_token
        )
        user_id = decoded_token.get("user_id")
    except BaseSecurityError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    refresh_token_record = (
        db.query(RefreshTokenModel)
        .filter_by(token=token_data.refresh_token)
        .first()
    )
    if not refresh_token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found.",
        )

    user = db.query(UserModel).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    new_access_token = jwt_manager.create_access_token({"user_id": user_id})

    return TokenRefreshResponseSchema(access_token=new_access_token)


@router.post(
    "/resend_activation_token/",
    summary="Resend Activation Token",
    description="Resend the activation token if the previous one expired.",
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "User Not Found - The user does not exist.",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found."}
                }
            },
        },
        400: {
            "description": "Bad Request - Invalid or expired activation token.",
            "content": {
                "application/json": {
                    "example": {"detail": "Activation token expired or invalid."}
                }
            },
        },
    },
)
def resend_activation_token(
        user_data: UserRegistrationRequestSchema,
        db: Session = Depends(get_db),
):
    """
    Endpoint to resend the activation token if the previous one expired.
    """
    db_user = db.query(UserModel).filter(UserModel.email == user_data.email).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    activation_token = db.query(ActivationTokenModel).filter_by(user_id=db_user.id).first()

    if activation_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation token is still valid."
        )
    activation_token = ActivationTokenModel(
        user_id=db_user.id,
        user=db_user
    )
    db.add(activation_token)
    db.flush()
    db.refresh(activation_token)
    db.commit()

    return {"detail": "Activation token resent successfully."}


@router.put("/users/{user_id}/group", status_code=status.HTTP_200_OK)
def update_user_group(
        user_id: int,
        group_name: str,
        db: Session = Depends(get_db),
        current_user_id: int = Depends(get_current_user_id),
):
    """
    Endpoint for changing the user group
    (only available to administrators)
    """

    current_user = db.query(UserModel).filter_by(id=current_user_id).first()

    if not current_user or current_user.group.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    new_group = db.query(UserGroupModel).filter_by(name=group_name).first()
    if not new_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid group name"
        )

    user_to_update = db.query(UserModel).filter_by(id=user_id).first()
    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user_to_update.group = new_group
    db.commit()
    db.refresh(user_to_update)

    return {"message": "User group updated successfully", "user_id": user_to_update.id,
            "new_group": user_to_update.group.name}


@router.put("/users/{user_id}/activate", status_code=status.HTTP_200_OK)
def activate_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user_id: int = Depends(get_current_user_id),
):
    """
    Endpoint for activating cloud account registration
    (only available for administrators)
    """

    current_user = db.query(UserModel).filter_by(id=current_user_id).first()
    if not current_user or current_user.group.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    user_to_activate = db.query(UserModel).filter_by(id=user_id).first()
    if not user_to_activate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user_to_activate.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already active"
        )

    user_to_activate.is_active = True
    db.commit()
    db.refresh(user_to_activate)

    return {"message": "User activated successfully", "user_id": user_to_activate.id,
            "is_active": user_to_activate.is_active}
