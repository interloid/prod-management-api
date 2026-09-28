from http.cookies import SimpleCookie

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.cookies import set_access_cookie
from app.core.settings import settings


class AuthCookieMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        access_token = getattr(request.state, "renewed_access_token", None)

        if access_token is not None:
            for header in response.headers.getlist("set-cookie"):
                cookies = SimpleCookie()
                cookies.load(header)
                if settings.ACCESS_TOKEN_COOKIE_NAME in cookies:
                    return response
            set_access_cookie(response, access_token)

        return response
