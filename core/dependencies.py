from fastapi import Depends, HTTPException, status

from exceptions import BaseSecurityError
from security.http import get_token
from security.interfaces import JWTAuthManagerInterface
from security.token_manager import JWTAuthManager
from core.config import settings


def get_jwt_auth_manager() -> JWTAuthManagerInterface:
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )


def get_current_user_id(
        token: str = Depends(get_token),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager)
) -> int:
    """
    Extracts the user ID from the provided JWT token.
    """
    try:
        payload = jwt_manager.decode_access_token(token)
        return payload.get("user_id")
    except BaseSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        )
