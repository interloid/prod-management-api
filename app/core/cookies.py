from fastapi import Response

from app.core.settings import settings


def set_access_cookie(response: Response, access_token: str) -> None:
    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def set_cookie(
    *,
    response: Response,
    access_token: str,
    raw_refresh_token: str,
    refresh_max_age: int,
) -> None:

    set_access_cookie(response, access_token)

    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=raw_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=refresh_max_age,
    )


def delete_cookie(response: Response) -> None:

    response.delete_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )

    response.delete_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )
