"""
security.py — Firebase JWT authentication middleware for FastAPI.

Every protected endpoint calls get_current_user() as a dependency.
It validates the Firebase ID token from the Authorization header.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# FastAPI security scheme — expects "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer(auto_error=True)


class AuthenticatedUser(BaseModel):
    """Represents a verified Firebase user extracted from JWT."""
    uid: str
    email: str
    email_verified: bool = False
    name: str = ""
    picture: str = ""

    @property
    def display_name(self) -> str:
        """Returns name if available, else email prefix."""
        return self.name or self.email.split("@")[0]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> AuthenticatedUser:
    """
    FastAPI dependency that verifies a Firebase ID token and returns the user.

    Raises:
        HTTPException 401: If token is missing, expired, or invalid.
    """
    token = credentials.credentials

    try:
        decoded = firebase_auth.verify_id_token(token, check_revoked=True)
    except firebase_auth.ExpiredIdTokenError:
        logger.warning("auth_token_expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except firebase_auth.RevokedIdTokenError:
        logger.warning("auth_token_revoked")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (firebase_auth.InvalidIdTokenError, FirebaseError) as exc:
        logger.warning("auth_token_invalid", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as exc:
        logger.error("auth_unexpected_error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error.",
        )

    return AuthenticatedUser(
        uid=decoded.get("uid", ""),
        email=decoded.get("email", ""),
        email_verified=decoded.get("email_verified", False),
        name=decoded.get("name", ""),
        picture=decoded.get("picture", ""),
    )


# Convenience type alias
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
