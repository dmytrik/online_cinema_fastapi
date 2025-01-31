from security.interfaces import JWTAuthManagerInterface
from security.token_manager import JWTAuthManager
from core.config import settings


def get_jwt_auth_manager() -> JWTAuthManagerInterface:
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )
