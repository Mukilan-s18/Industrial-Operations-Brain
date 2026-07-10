import os
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from fastapi import HTTPException
from jose import JWTError
from backend.dependencies import compute_corpus_coverage, get_current_user, _JWKS_CACHE
import backend.dependencies as deps


def test_compute_corpus_coverage_file_exists():
    mock_data = json.dumps([{"id": 1}, {"id": 2}])
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_data)):
            coverage = compute_corpus_coverage()
            assert coverage == 100.0


def test_compute_corpus_coverage_empty_file():
    mock_data = json.dumps([])
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_data)):
            coverage = compute_corpus_coverage()
            assert coverage == 0.0


def test_compute_corpus_coverage_exception():
    with patch("os.path.exists", side_effect=Exception("Test Exception")):
        coverage = compute_corpus_coverage()
        assert coverage == 0.0


def test_get_current_user_local_mock_domain():
    token = "fake_token"
    mock_payload = {"sub": "test_user", "role": "operator"}
    with patch(
        "os.getenv",
        side_effect=lambda k, d=None: (
            "mock-domain.auth0.com" if k == "AUTH0_DOMAIN" else d
        ),
    ):
        with patch("backend.dependencies.jwt.decode", return_value=mock_payload):
            user = get_current_user(token)
            assert user == {"username": "test_user", "role": "operator"}


def test_get_current_user_missing_role():
    token = "fake_token"
    mock_payload = {"sub": "test_user"}
    with patch(
        "os.getenv",
        side_effect=lambda k, d=None: (
            "mock-domain.auth0.com" if k == "AUTH0_DOMAIN" else d
        ),
    ):
        with patch("backend.dependencies.jwt.decode", return_value=mock_payload):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(token)
            assert exc_info.value.status_code == 401


def test_get_current_user_auth0_flow_success():
    token = "fake_token"
    mock_payload = {"sub": "test_user", "role": "engineer"}
    mock_jwks = {
        "keys": [{"kid": "123", "kty": "RSA", "use": "sig", "n": "n", "e": "e"}]
    }

    with patch(
        "os.getenv",
        side_effect=lambda k, d=None: "real.auth0.com" if k == "AUTH0_DOMAIN" else d,
    ):
        with patch("backend.dependencies.requests.get") as mock_get:
            mock_get.return_value.json.return_value = mock_jwks
            with patch(
                "backend.dependencies.jwt.get_unverified_header",
                return_value={"kid": "123"},
            ):
                with patch(
                    "backend.dependencies.jwt.decode", return_value=mock_payload
                ):
                    # Force JWKS CACHE None to test fetch
                    deps._JWKS_CACHE = None
                    user = get_current_user(token)
                    assert user == {"username": "test_user", "role": "engineer"}
                    assert deps._JWKS_CACHE == mock_jwks


def test_get_current_user_auth0_flow_key_not_found():
    token = "fake_token"
    mock_jwks = {
        "keys": [{"kid": "456", "kty": "RSA", "use": "sig", "n": "n", "e": "e"}]
    }

    with patch(
        "os.getenv",
        side_effect=lambda k, d=None: "real.auth0.com" if k == "AUTH0_DOMAIN" else d,
    ):
        with patch("backend.dependencies.requests.get") as mock_get:
            mock_get.return_value.json.return_value = mock_jwks
            with patch(
                "backend.dependencies.jwt.get_unverified_header",
                return_value={"kid": "123"},
            ):
                deps._JWKS_CACHE = None
                with pytest.raises(HTTPException) as exc_info:
                    get_current_user(token)
                assert exc_info.value.status_code == 401
