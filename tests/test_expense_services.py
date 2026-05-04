from unittest.mock import patch, MagicMock
from bson import ObjectId

from app.services.expense_services import (
    create_expense_service,
    get_expense_service,
    get_user_expenses_service,
    update_expense_service,
    delete_expense_service,
)

EXPENSE_ID = "507f1f77bcf86cd799439011"
OBJ_EXPENSE_ID = ObjectId(EXPENSE_ID)

EXPENSE_DOC = {
    "_id": OBJ_EXPENSE_ID,
    "expense_type": "Alimentação",
    "value": 50.0,
    "expense_date": "2024-01-15T00:00:00",
    "user_email": "test@example.com",
}

EXPENSE_PAYLOAD = {
    "expense_type": "Alimentação",
    "value": 50.0,
    "expense_date": "2024-01-15T00:00:00",
}


def test_create_expense_validation_error():
    result, error = create_expense_service({}, "test@example.com")

    assert result is None
    assert error is not None


def test_create_expense_user_not_found():
    with patch("app.services.expense_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = create_expense_service(EXPENSE_PAYLOAD, "ghost@example.com")

        assert result is None
        assert error == {"error": "Usuário não encontrado"}


def test_create_expense_ok():
    with patch("app.services.expense_services.mongo") as mock_mongo:
        users_col = MagicMock()
        users_col.find_one.return_value = {"email": "test@example.com"}
        expenses_col = MagicMock()
        mock_result = MagicMock()
        mock_result.inserted_id = OBJ_EXPENSE_ID
        expenses_col.insert_one.return_value = mock_result
        mock_mongo.__getitem__.side_effect = {
            "users": users_col,
            "expenses": expenses_col,
        }.get

        result, error = create_expense_service(EXPENSE_PAYLOAD, "test@example.com")

        assert error is None
        assert result["message"] == "Despesa criada com sucesso"
        assert "expense_id" in result
        expenses_col.insert_one.assert_called_once()


def test_get_expense_not_found():
    with patch("app.services.expense_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = get_expense_service(EXPENSE_ID, "test@example.com")

        assert result is None
        assert error == {"error": "Despesa não encontrada"}


def test_get_expense_wrong_owner():
    with patch("app.services.expense_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(EXPENSE_DOC)

        result, error = get_expense_service(EXPENSE_ID, "other@example.com")

        assert result is None
        assert error == {"error": "Você não tem permissão para acessar esta despesa"}


def test_get_expense_ok():
    with patch("app.services.expense_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = {
            **EXPENSE_DOC,
            "_id": OBJ_EXPENSE_ID,
        }

        result, error = get_expense_service(EXPENSE_ID, "test@example.com")

        assert error is None
        assert result["_id"] == EXPENSE_ID


def test_get_user_expenses_ok():
    with patch("app.services.expense_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find.return_value = [
            {**EXPENSE_DOC, "_id": OBJ_EXPENSE_ID}
        ]

        result, error = get_user_expenses_service("test@example.com")

        assert error is None
        assert len(result) == 1
        assert result[0]["_id"] == EXPENSE_ID


def test_get_user_expenses_empty():
    with patch("app.services.expense_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find.return_value = []

        result, error = get_user_expenses_service("test@example.com")

        assert error is None
        assert result == []


def test_update_expense_not_found():
    with patch("app.services.expense_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = update_expense_service(
            EXPENSE_ID, {"value": 75.0}, "test@example.com"
        )

        assert result is None
        assert error == {"error": "Despesa não encontrada"}


def test_update_expense_wrong_owner():
    with patch("app.services.expense_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(EXPENSE_DOC)

        result, error = update_expense_service(
            EXPENSE_ID, {"value": 75.0}, "other@example.com"
        )

        assert result is None
        assert error == {"error": "Você não tem permissão para editar esta despesa"}


def test_update_expense_ok():
    with patch("app.services.expense_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = {
            **EXPENSE_DOC,
            "_id": OBJ_EXPENSE_ID,
        }

        result, error = update_expense_service(
            EXPENSE_ID, {"value": 75.0}, "test@example.com"
        )

        assert error is None
        assert result["message"] == "Despesa atualizada com sucesso"
        assert result["expense"]["value"] == 75.0
        mock_mongo.__getitem__.return_value.update_one.assert_called_once()


def test_delete_expense_not_found():
    with patch("app.services.expense_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = delete_expense_service(EXPENSE_ID, "test@example.com")

        assert result is None
        assert error == {"error": "Despesa não encontrada"}


def test_delete_expense_wrong_owner():
    with patch("app.services.expense_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(EXPENSE_DOC)

        result, error = delete_expense_service(EXPENSE_ID, "other@example.com")

        assert result is None
        assert error == {"error": "Você não tem permissão para deletar esta despesa"}


def test_delete_expense_ok():
    with patch("app.services.expense_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = {
            **EXPENSE_DOC,
            "_id": OBJ_EXPENSE_ID,
        }

        result, error = delete_expense_service(EXPENSE_ID, "test@example.com")

        assert error is None
        assert result == {"message": "Despesa deletada com sucesso"}
        mock_mongo.__getitem__.return_value.delete_one.assert_called_once()
