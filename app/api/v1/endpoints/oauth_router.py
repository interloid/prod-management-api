from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_auth_service
from app.core.cookies import set_cookie
from app.core.logging import get_logger
from app.core.settings import settings
from app.exceptions.base import AppException
from app.exceptions.global_exception import AUTH_ERROR_RESPONSES
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["OAUTH"],
)

logger = get_logger(__name__)


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


@router.get("/{provider}/callback", responses=AUTH_ERROR_RESPONSES)
async def oauth_callback(
    provider: str,
    state: str | None = None,
    code: str | None = None,
    error: str | None = None,
    service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    login_url = f"{settings.YOUR_REACT_URL}/login"

    if error or not code or not state:
        return RedirectResponse(f"{login_url}?error=oauth_denied", status_code=302)

    try:
        (
            _result,
            access_token,
            raw_refresh_token,
            refresh_max_age,
        ) = await service.oauth_callback(provider=provider, code=code, state=state)
    except AppException as exc:
        return RedirectResponse(
            f"{login_url}?error={quote(exc.error_code)}", status_code=302
        )
    except Exception:
        logger.exception("OAuth callback failed | provider=%s", provider)
        return RedirectResponse(f"{login_url}?error=oauth_failed", status_code=302)

    response = RedirectResponse(url=settings.YOUR_REACT_URL, status_code=302)
    set_cookie(
        response=response,
        access_token=access_token,
        raw_refresh_token=raw_refresh_token,
        refresh_max_age=refresh_max_age,
    )
    return response
