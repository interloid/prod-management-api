from fastapi import APIRouter, Cookie, Depends, Request, Response, status

from app.api.dependencies import get_auth_service, get_current_user
from app.core.constants import ROLE_PERMISSIONS, RoleEnum
from app.core.cookies import delete_cookie, set_cookie
from app.core.rate_limiter import enforce_read_rate_limit, limiter
from app.core.settings import settings
from app.exceptions.global_exception import AUTH_ERROR_RESPONSES
from app.models.user_model import User
from app.schemas.auth_schema import (
    LoginRequest,
)
from app.schemas.response import ApiResponse
from app.schemas.user_schema import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["JWT Authentication"],
)


@router.post(
    "/login",
    response_model=ApiResponse[None],
    responses=AUTH_ERROR_RESPONSES,
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[None]:

    (result, access_token, raw_refresh_token, refresh_max_age) = await service.login(
        login_data
    )

    set_cookie(
        response=response,
        access_token=access_token,
        raw_refresh_token=raw_refresh_token,
        refresh_max_age=refresh_max_age,
    )

    return result


@router.post(
    "/refresh",
    response_model=ApiResponse[None],
    responses=AUTH_ERROR_RESPONSES,
)
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(
        default=None,
        alias=settings.REFRESH_TOKEN_COOKIE_NAME,
    ),
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[None]:
    (
        result,
        access_token,
        new_raw_refresh_token,
        refresh_max_age,
    ) = await service.refresh_token(
        raw_refresh_token=refresh_token,
    )

    set_cookie(
        response=response,
        access_token=access_token,
        raw_refresh_token=new_raw_refresh_token,
        refresh_max_age=refresh_max_age,
    )

    return result


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=AUTH_ERROR_RESPONSES,
)
async def logout_current_device(
    response: Response,
    refresh_token: str | None = Cookie(
        default=None,
        alias=settings.REFRESH_TOKEN_COOKIE_NAME,
    ),
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.logout_current_device(refresh_token)

    delete_cookie(response=response)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=AUTH_ERROR_RESPONSES,
)
async def logout_all_devices(
    response: Response,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.logout_all_devices(user_id=current_user.id)

    delete_cookie(response=response)


@router.get(
    "/me",
    dependencies=[Depends(enforce_read_rate_limit)],
    response_model=ApiResponse[UserResponse],
    responses=AUTH_ERROR_RESPONSES,
)
async def get_current_user_details(
    current_user: User = Depends(get_current_user),
):
    role = RoleEnum(current_user.role)
    permissions = sorted(
        ROLE_PERMISSIONS[role], key=lambda permission: permission.value
    )

    return ApiResponse[UserResponse](
        message="Current user retrieved successfully",
        data=UserResponse(
            id=current_user.id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            avatar_url=current_user.avatar_url,
            is_active=current_user.is_active,
            role=role,
            permissions=permissions,
        ),
    )
