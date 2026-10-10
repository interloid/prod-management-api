from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.category_schema import CategoryResponse
from app.schemas.session_schema import SessionResponse


def test_category_response_missing_id():
    with pytest.raises(ValidationError):
        CategoryResponse(
            name="Electronics",
        )


def test_category_response_missing_name():
    with pytest.raises(ValidationError):
        CategoryResponse(
            id=uuid4(),
        )


def test_category_response_invalid_uuid():
    with pytest.raises(ValidationError):
        CategoryResponse(
            id="not-a-uuid",
            name="Electronics",
        )


def test_session_response_invalid_user():
    with pytest.raises(ValidationError):
        SessionResponse(
            user={
                "id": "invalid-id",
                "email": "john@example.com",
            }
        )
