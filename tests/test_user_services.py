from unittest.mock import patch, MagicMock
from bson import ObjectId

from app.services.user_services import (
    create_user_service,
    get_current_user_service,
    update_user_service,
    delete_user_service,
    verify_email_service,
)

USER_ID = ObjectId("507f1f77bcf86cd799439011")

USER_DOC = {
    "_id": USER_ID,
    "name": "Test User",
    "email": "test@example.com",
    "password": "hashed_password",
    "is_verified": True,
}


def _make_mongo(**collections):
    mock_mongo = MagicMock()
    mock_mongo.__getitem__.side_effect = lambda key: collections.get(key, MagicMock())
    return mock_mongo


def test_create_user_validation_error():
    result, error = create_user_service({})

    assert result is None
    assert error is not None


def test_create_user_passwords_do_not_match():
    result, error = create_user_service(
        {
            "name": "Test",
            "email": "test@example.com",
            "password": "secret123",
            "confirm_password": "different",
        }
    )

    assert result is None
    assert error is not None


def test_create_user_email_exists():
    with patch("app.services.user_services.get_user_by_email") as mock_get_user:
        mock_get_user.return_value = USER_DOC

        result, error = create_user_service(
            {
                "name": "Test",
                "email": "test@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            }
        )

        assert result is None
        assert error == {"error": "email já cadastrado"}


def test_create_user_ok():
    with (
        patch("app.services.user_services.get_user_by_email") as mock_get_user,
        patch("app.services.user_services.mongo") as mock_mongo,
        patch("app.services.user_services.bcrypt") as mock_bcrypt,
        patch("app.services.user_services.gevent") as mock_gevent,
    ):
        mock_get_user.return_value = None
        mock_bcrypt.hashpw.return_value.decode.return_value = "hashed_password"
        mock_bcrypt.gensalt.return_value = b"salt"

        result, error = create_user_service(
            {
                "name": "Test",
                "email": "new@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            }
        )

        assert error is None
        assert result == {"message": "OK ✅"}
        mock_mongo.__getitem__.return_value.insert_one.assert_called_once()
        mock_gevent.spawn.assert_called_once()


def test_get_current_user_not_found():
    with patch("app.services.user_services.get_user_by_email") as mock_get_user:
        mock_get_user.return_value = None

        result, error = get_current_user_service("ghost@example.com")

        assert result is None
        assert error == {"error": "Usuário não encontrado"}


def test_get_current_user_ok():
    with patch("app.services.user_services.get_user_by_email") as mock_get_user:
        mock_get_user.return_value = dict(USER_DOC)

        result, error = get_current_user_service("test@example.com")

        assert error is None
        assert result["email"] == "test@example.com"
        assert "password" not in result
        assert "_id" in result


def test_get_current_user_strips_sensitive_fields():
    with patch("app.services.user_services.get_user_by_email") as mock_get_user:
        mock_get_user.return_value = {
            **USER_DOC,
            "verification_token": "tok",
            "reset_code": "123456",
            "reset_token": "abc",
        }

        result, error = get_current_user_service("test@example.com")

        assert error is None
        assert "verification_token" not in result
        assert "reset_code" not in result
        assert "reset_token" not in result


def test_update_user_not_found():
    with patch("app.services.user_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = update_user_service("ghost@example.com", {"name": "New Name"})

        assert result is None
        assert error == {"error": "Usuário não encontrado"}


def test_update_user_name_ok():
    with patch("app.services.user_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(USER_DOC)

        result, error = update_user_service("test@example.com", {"name": "New Name"})

        assert error is None
        assert result == {"message": "Usuário atualizado com sucesso"}
        mock_mongo.__getitem__.return_value.update_one.assert_called_once()


def test_update_user_no_fields():
    with patch("app.services.user_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(USER_DOC)

        result, error = update_user_service("test@example.com", {})

        assert result is None
        assert error == {"error": "Nenhum campo alterado"}


def test_update_user_password_without_current():
    with patch("app.services.user_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(USER_DOC)

        result, error = update_user_service(
            "test@example.com", {"password": "newpass123"}
        )

        assert result is None
        assert error == {
            "error": "É necessário inserir a senha atual para trocar a senha"
        }


def test_update_user_password_wrong_current():
    with (
        patch("app.services.user_services.mongo") as mock_mongo,
        patch("app.services.user_services.bcrypt") as mock_bcrypt,
    ):
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(USER_DOC)
        mock_bcrypt.checkpw.return_value = False

        result, error = update_user_service(
            "test@example.com",
            {"password": "newpass123", "current_password": "wrong"},
        )

        assert result is None
        assert error == {"error": "Senha atual incorreta"}


def test_update_user_password_ok():
    with (
        patch("app.services.user_services.mongo") as mock_mongo,
        patch("app.services.user_services.bcrypt") as mock_bcrypt,
    ):
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(USER_DOC)
        mock_bcrypt.checkpw.return_value = True
        mock_bcrypt.hashpw.return_value.decode.return_value = "new_hashed"
        mock_bcrypt.gensalt.return_value = b"salt"

        result, error = update_user_service(
            "test@example.com",
            {"password": "newpass123", "current_password": "secret123"},
        )

        assert error is None
        assert result == {"message": "Usuário atualizado com sucesso"}


def test_delete_user_not_found():
    with patch("app.services.user_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = delete_user_service(
            "ghost@example.com", {"password": "secret123"}
        )

        assert result is None
        assert error == {"error": "Usuário não encontrado"}


def test_delete_user_wrong_password():
    with (
        patch("app.services.user_services.mongo") as mock_mongo,
        patch("app.services.user_services.bcrypt") as mock_bcrypt,
    ):
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(USER_DOC)
        mock_bcrypt.checkpw.return_value = False

        result, error = delete_user_service("test@example.com", {"password": "wrong"})

        assert result is None
        assert error == {"error": "Senha incorreta"}


def test_delete_user_has_groups():
    with (
        patch("app.services.user_services.mongo") as mock_mongo,
        patch("app.services.user_services.bcrypt") as mock_bcrypt,
    ):
        users_col = MagicMock()
        users_col.find_one.return_value = dict(USER_DOC)
        groups_col = MagicMock()
        groups_col.count_documents.return_value = 1
        mock_mongo.__getitem__.side_effect = {
            "users": users_col,
            "groups": groups_col,
        }.get
        mock_bcrypt.checkpw.return_value = True

        result, error = delete_user_service(
            "test@example.com", {"password": "secret123"}
        )

        assert result is None
        assert "você criou grupos" in error["error"]


def test_delete_user_has_open_bills():
    with (
        patch("app.services.user_services.mongo") as mock_mongo,
        patch("app.services.user_services.bcrypt") as mock_bcrypt,
    ):
        users_col = MagicMock()
        users_col.find_one.return_value = dict(USER_DOC)
        groups_col = MagicMock()
        groups_col.count_documents.return_value = 0
        bills_col = MagicMock()
        bills_col.count_documents.return_value = 1
        mock_mongo.__getitem__.side_effect = {
            "users": users_col,
            "groups": groups_col,
            "bills": bills_col,
        }.get
        mock_bcrypt.checkpw.return_value = True

        result, error = delete_user_service(
            "test@example.com", {"password": "secret123"}
        )

        assert result is None
        assert "contas em aberto" in error["error"]


def test_delete_user_ok():
    with (
        patch("app.services.user_services.mongo") as mock_mongo,
        patch("app.services.user_services.bcrypt") as mock_bcrypt,
    ):
        users_col = MagicMock()
        users_col.find_one.return_value = dict(USER_DOC)
        groups_col = MagicMock()
        groups_col.count_documents.return_value = 0
        bills_col = MagicMock()
        bills_col.count_documents.return_value = 0
        mock_mongo.__getitem__.side_effect = {
            "users": users_col,
            "groups": groups_col,
            "bills": bills_col,
            "expenses": MagicMock(),
            "pendencies": MagicMock(),
        }.get
        mock_bcrypt.checkpw.return_value = True

        result, error = delete_user_service(
            "test@example.com", {"password": "secret123"}
        )

        assert error is None
        assert result == {"message": "Usuário deletado com sucesso"}
        users_col.delete_one.assert_called_once()


def test_verify_email_invalid_token():
    with patch("app.services.user_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = verify_email_service("bad-token")

        assert result is None
        assert error == {"error": "Token inválido ou expirado"}


def test_verify_email_already_verified():
    with patch("app.services.user_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = {
            "_id": USER_ID,
            "email": "test@example.com",
            "is_verified": True,
            "verification_token": "some-token",
        }

        result, error = verify_email_service("some-token")

        assert error is None
        assert result == {"message": "Conta já verificada"}


def test_verify_email_ok():
    with (
        patch("app.services.user_services.mongo") as mock_mongo,
        patch("app.services.user_services.gevent") as mock_gevent,
    ):
        mock_mongo.__getitem__.return_value.find_one.return_value = {
            "_id": USER_ID,
            "name": "Test",
            "email": "test@example.com",
            "is_verified": False,
            "verification_token": "valid-token",
        }

        result, error = verify_email_service("valid-token")

        assert error is None
        assert result == {"message": "E-mail confirmado com sucesso"}
        mock_mongo.__getitem__.return_value.update_one.assert_called_once()
        mock_gevent.spawn.assert_called_once()
