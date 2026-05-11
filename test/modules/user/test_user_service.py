import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from modules.user.user_service import create_user
from schemas import UserCreate


# -------------------------
# SUCCESS CASE
# -------------------------
def test_create_user_success():

    mock_db = MagicMock()

    # mock query → no existing user
    mock_db.query.return_value.filter.return_value.first.return_value = None

    user_input = UserCreate(email="test@test.com", password="123456")

    with patch("modules.user.user_service.hash_password", return_value="hashed_pass"):

        result = create_user(mock_db, user_input)

    assert result["statusCode"] == 201
    assert result["message"] == "user created successfully"

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
