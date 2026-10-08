from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_auth_service
from app.core.cookies import set_cookie
from app.core.settings import settings
from app.exceptions.base import AppException
from app.exceptions.global_exception import AUTH_ERROR_RESPONSES
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["OAUTH"],
)


@router.get(
    "/{provider}",
    responses=AUTH_ERROR_RESPONSES,
)
async def oauth(
    provider: str,
    service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    authorization_url = await service.start_oauth(
        provider=provider,
    )

    return RedirectResponse(
        url=authorization_url,
        status_code=302,
    )


@router.get(
    "/{provider}/callback",
    responses=AUTH_ERROR_RESPONSES,
)
async def oauth_callback(
    provider: str,
    state: str | None = None,
    code: str | None = None,
    error: str | None = None,
    service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:

    try:
        (
            _result,
            access_token,
            raw_refresh_token,
            refresh_max_age,
        ) = await service.oauth_callback(
            provider=provider,
            code=code,
            state=state,
        )

        response = RedirectResponse(
            url=settings.YOUR_REACT_URL,
            status_code=302,
        )

        set_cookie(
            response=response,
            access_token=access_token,
            raw_refresh_token=raw_refresh_token,
            refresh_max_age=refresh_max_age,
        )

        return response

    except AppException as exc:
        error_code = quote(exc.code)

        return RedirectResponse(
            url=f"{settings.YOUR_REACT_URL}/login?error={error_code}",
            status_code=302,
        )
