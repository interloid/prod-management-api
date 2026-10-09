from typing import Any
from urllib.parse import quote

from botocore.exceptions import ClientError, EndpointConnectionError
from fastapi import Request

from app.core.logging import get_logger
from app.core.settings import settings
from app.exceptions.custom import InternalServerException, ServiceUnavailableException

logger = get_logger(__name__)


class S3Service:
    def __init__(self, client: Any) -> None:
        self.client = client
        self.bucket_name = settings.S3_BUCKET_NAME

    async def upload_file(
        self, data: bytes, object_key: str, content_type: str
    ) -> None:

        try:
            await self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=data,
                ContentType=content_type,
            )
        except ClientError:
            logger.warning(
                "S3 put_object failed | object_key=%s",
                object_key,
            )
            raise InternalServerException(
                message="Failed to upload file",
            )

        except EndpointConnectionError:
            logger.warning(
                "Unable to connect to S3 | object_key=%s",
                object_key,
            )
            raise ServiceUnavailableException(
                message="File storage service is unavailable",
            )

    async def delete_file(self, object_key: str) -> None:

        try:
            await self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )

        except ClientError:
            logger.warning(
                "S3 delete_object failed | object_key=%s",
                object_key,
            )
            raise InternalServerException(
                message="Failed to delete file",
            )

        except EndpointConnectionError:
            logger.warning(
                "Unable to connect to S3 | object_key=%s",
                object_key,
            )
            raise ServiceUnavailableException(
                message="File storage service is unavailable",
            )

    async def generate_cloudfront_urls(
        self,
        object_keys: list[str],
    ) -> dict[str, str]:

        base_url = str(settings.CLOUDFRONT_BASE_URL).rstrip("/")

        return {
            object_key: (f"{base_url}/{quote(object_key.lstrip('/'), safe='/')}")
            for object_key in object_keys
        }


def get_s3_service(request: Request) -> S3Service:
    return S3Service(client=request.app.state.s3)
