from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from app.services.auth_services import (
    login_service,
    request_password_reset_service,
    verify_reset_code_service,
    reset_password_service,
)


def test_login_ok():
    with (
        patch("app.services.auth_services.get_user_by_email") as mock_get_user,
        patch("app.services.auth_services.bcrypt") as mock_bcrypt,
        patch("app.services.auth_services.generate_token") as mock_gen_token,
    ):
        mock_get_user.return_value = {
            "email": "test@example.com",
            "password": "hashed",
            "is_verified": True,
        }
        mock_bcrypt.checkpw.return_value = True
        mock_gen_token.return_value = "jwt_token"

        result, error = login_service(
            {"email": "test@example.com", "password": "secret123"}
        )

        assert error is None
        assert result == {"token": "jwt_token"}
        mock_gen_token.assert_called_once_with("test@example.com")


def test_login_user_not_found():
    with patch("app.services.auth_services.get_user_by_email") as mock_get_user:
        mock_get_user.return_value = None

        result, error = login_service(
            {"email": "ghost@example.com", "password": "secret123"}
        )

        assert result is None
        assert error == {"error": "Credenciais inválidas"}


def test_login_no_password_field():
    with patch("app.services.auth_services.get_user_by_email") as mock_get_user:
        mock_get_user.return_value = {
            "email": "test@example.com",
            "auth_provider": "google",
        }

        result, error = login_service(
            {"email": "test@example.com", "password": "secret123"}
        )

        assert result is None
        assert error == {"error": "Credenciais inválidas"}


def test_login_wrong_password():
    with (
        patch("app.services.auth_services.get_user_by_email") as mock_get_user,
        patch("app.services.auth_services.bcrypt") as mock_bcrypt,
    ):
        mock_get_user.return_value = {
            "email": "test@example.com",
            "password": "hashed",
            "is_verified": True,
        }
        mock_bcrypt.checkpw.return_value = False

        result, error = login_service(
            {"email": "test@example.com", "password": "wrong"}
        )

        assert result is None
        assert error == {"error": "Credenciais inválidas"}


def test_login_email_not_verified():
    with (
        patch("app.services.auth_services.get_user_by_email") as mock_get_user,
        patch("app.services.auth_services.bcrypt") as mock_bcrypt,
    ):
        mock_get_user.return_value = {
            "email": "test@example.com",
            "password": "hashed",
            "is_verified": False,
        }
        mock_bcrypt.checkpw.return_value = True

        result, error = login_service(
            {"email": "test@example.com", "password": "secret123"}
        )

        assert result is None
        assert error == {"error": "E-mail ainda não verificado"}


def test_login_validation_error():
    result, error = login_service({})

    assert result is None
    assert error is not None


def test_request_password_reset_empty_email():
    result, error = request_password_reset_service({"email": "  "})

    assert error is None
    assert result == {"message": "Se o e-mail existir, o código será enviado"}


def test_request_password_reset_user_not_found():
    with patch("app.services.auth_services.get_user_by_email") as mock_get_user:
        mock_get_user.return_value = None

        result, error = request_password_reset_service({"email": "ghost@example.com"})

        assert error is None
        assert result == {"message": "Se o e-mail existir, o código será enviado"}


def test_request_password_reset_sends_code():
    with (
        patch("app.services.auth_services.get_user_by_email") as mock_get_user,
        patch("app.services.auth_services.mongo") as mock_mongo,
        patch("app.services.auth_services.gevent") as mock_gevent,
        patch("app.services.auth_services.secrets") as mock_secrets,
    ):
        mock_get_user.return_value = {"name": "Test", "email": "test@example.com"}
        mock_secrets.randbelow.return_value = 42000

        result, error = request_password_reset_service({"email": "test@example.com"})

        assert error is None
        assert result == {"message": "Se o e-mail existir, o código será enviado"}
        mock_mongo.__getitem__.return_value.update_one.assert_called_once()
        mock_gevent.spawn.assert_called_once()


def test_verify_reset_code_missing_fields():
    result, error = verify_reset_code_service({"email": "", "code": ""})

    assert result is None
    assert error == {"error": "E-mail e código são obrigatórios"}


def test_verify_reset_code_user_not_found():
    with patch("app.services.auth_services.get_user_by_email") as mock_get_user:
        mock_get_user.return_value = None

        result, error = verify_reset_code_service(
            {"email": "test@example.com", "code": "123456"}
        )

        assert result is None
        assert error == {"error": "Código inválido ou expirado"}


def test_verify_reset_code_wrong_code():
    with patch("app.services.auth_services.get_user_by_email") as mock_get_user:
        mock_get_user.return_value = {
            "reset_code": "654321",
            "reset_code_expires": datetime.now(timezone.utc) + timedelta(minutes=5),
        }

        result, error = verify_reset_code_service(
            {"email": "test@example.com", "code": "123456"}
        )

        assert result is None
        assert error == {"error": "Código inválido ou expirado"}


def test_verify_reset_code_expired():
    with patch("app.services.auth_services.get_user_by_email") as mock_get_user:
        mock_get_user.return_value = {
            "reset_code": "123456",
            "reset_code_expires": datetime.now(timezone.utc) - timedelta(minutes=1),
        }

        result, error = verify_reset_code_service(
            {"email": "test@example.com", "code": "123456"}
        )

        assert result is None
        assert error == {"error": "Código expirado"}


def test_verify_reset_code_ok():
    with (
        patch("app.services.auth_services.get_user_by_email") as mock_get_user,
        patch("app.services.auth_services.mongo") as mock_mongo,
        patch("app.services.auth_services.uuid") as mock_uuid,
    ):
        mock_get_user.return_value = {
            "email": "test@example.com",
            "reset_code": "123456",
            "reset_code_expires": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        mock_uuid.uuid4.return_value = "some-reset-token"

        result, error = verify_reset_code_service(
            {"email": "test@example.com", "code": "123456"}
        )

        assert error is None
        assert result == {"reset_token": "some-reset-token"}
        mock_mongo.__getitem__.return_value.update_one.assert_called_once()


def test_reset_password_missing_fields():
    result, error = reset_password_service({"reset_token": "", "new_password": ""})

    assert result is None
    assert error == {"error": "reset_token e new_password são obrigatórios"}


def test_reset_password_invalid_token():
    with patch("app.services.auth_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = reset_password_service(
            {"reset_token": "bad", "new_password": "newpass123"}
        )

        assert result is None
        assert error == {"error": "Token inválido ou expirado"}


def test_reset_password_expired():
    with patch("app.services.auth_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = {
            "reset_token": "valid-token",
            "reset_token_expires": datetime.now(timezone.utc) - timedelta(minutes=1),
        }

        result, error = reset_password_service(
            {"reset_token": "valid-token", "new_password": "newpass123"}
        )

        assert result is None
        assert error == {"error": "Token expirado"}


def test_reset_password_ok():
    with (
        patch("app.services.auth_services.mongo") as mock_mongo,
        patch("app.services.auth_services.bcrypt") as mock_bcrypt,
    ):
        mock_mongo.__getitem__.return_value.find_one.return_value = {
            "reset_token": "valid-token",
            "reset_token_expires": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        mock_bcrypt.hashpw.return_value.decode.return_value = "new_hashed"
        mock_bcrypt.gensalt.return_value = b"salt"

        result, error = reset_password_service(
            {"reset_token": "valid-token", "new_password": "newpass123"}
        )

        assert error is None
        assert result == {"message": "Senha alterada com sucesso"}
        mock_mongo.__getitem__.return_value.update_one.assert_called_once()
