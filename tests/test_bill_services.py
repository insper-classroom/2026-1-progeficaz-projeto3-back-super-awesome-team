from unittest.mock import patch, MagicMock
from bson import ObjectId

from app.services.bill_services import (
    create_bill_service,
    get_user_bills_service,
    get_group_bills_service,
    get_bill_service,
    update_bill_service,
    delete_bill_service,
    mark_bill_as_paid_service,
)

BILL_ID = "507f1f77bcf86cd799439011"
GROUP_ID = "507f1f77bcf86cd799439012"
OBJ_BILL_ID = ObjectId(BILL_ID)
OBJ_GROUP_ID = ObjectId(GROUP_ID)

GROUP_DOC = {
    "_id": OBJ_GROUP_ID,
    "name": "My Group",
    "members": ["creator@example.com", "member@example.com"],
    "created_by": "creator@example.com",
}

BILL_DOC = {
    "_id": OBJ_BILL_ID,
    "bill_type": "Aluguel",
    "total_value": 1000.0,
    "group_id": GROUP_ID,
    "pix_key": "creator@example.com",
    "members_to_pay": [{"email": "member@example.com", "value": 500.0}],
    "created_by": "creator@example.com",
    "is_paid": False,
}

BILL_PAYLOAD = {
    "bill_type": "Aluguel",
    "total_value": 1000.0,
    "group_id": GROUP_ID,
    "pix_key": "creator@example.com",
    "members_to_pay": [{"email": "member@example.com", "value": 500.0}],
}


def _make_mongo(**collections):
    mock_mongo = MagicMock()
    mock_mongo.__getitem__.side_effect = lambda key: collections.get(key, MagicMock())
    return mock_mongo


def test_create_bill_validation_error():
    result, error = create_bill_service({}, "creator@example.com")

    assert result is None
    assert error is not None


def test_create_bill_group_not_found():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = create_bill_service(BILL_PAYLOAD, "creator@example.com")

        assert result is None
        assert error == {"error": "Grupo não encontrado"}


def test_create_bill_user_not_member():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(GROUP_DOC)

        result, error = create_bill_service(BILL_PAYLOAD, "outsider@example.com")

        assert result is None
        assert error == {"error": "Você não tem permissão para criar conta neste grupo"}


def test_create_bill_member_not_in_group():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(GROUP_DOC)
        payload = {
            **BILL_PAYLOAD,
            "members_to_pay": [{"email": "outsider@example.com", "value": 500.0}],
        }

        result, error = create_bill_service(payload, "creator@example.com")

        assert result is None
        assert "não pertence ao grupo" in error["error"]


def test_create_bill_ok():
    with (
        patch("app.services.bill_services.mongo") as mock_mongo,
        patch(
            "app.services.bill_services.create_pendencies_for_bill"
        ) as mock_pendencies,
    ):
        groups_col = MagicMock()
        groups_col.find_one.return_value = dict(GROUP_DOC)
        bills_col = MagicMock()
        mock_result = MagicMock()
        mock_result.inserted_id = OBJ_BILL_ID
        bills_col.insert_one.return_value = mock_result
        mock_mongo.__getitem__.side_effect = {
            "groups": groups_col,
            "bills": bills_col,
        }.get
        mock_pendencies.return_value = (["pend_id_1"], None)

        payload = {**BILL_PAYLOAD, "due_date": "2026-06-10T00:00:00"}

        result, error = create_bill_service(payload, "creator@example.com")

        assert error is None
        assert result["message"] == "Conta criada com sucesso"
        assert "bill_id" in result
        assert result["pendencies_created"] == 1
        inserted_bill = bills_col.insert_one.call_args.args[0]
        assert inserted_bill["due_date"] == "2026-06-10T00:00:00"
        assert inserted_bill["pix_key"] == "creator@example.com"


def test_create_bill_pendency_error_rolls_back():
    with (
        patch("app.services.bill_services.mongo") as mock_mongo,
        patch(
            "app.services.bill_services.create_pendencies_for_bill"
        ) as mock_pendencies,
    ):
        groups_col = MagicMock()
        groups_col.find_one.return_value = dict(GROUP_DOC)
        bills_col = MagicMock()
        mock_result = MagicMock()
        mock_result.inserted_id = OBJ_BILL_ID
        bills_col.insert_one.return_value = mock_result
        mock_mongo.__getitem__.side_effect = {
            "groups": groups_col,
            "bills": bills_col,
        }.get
        mock_pendencies.return_value = (None, {"error": "Erro ao criar pendências"})

        result, error = create_bill_service(BILL_PAYLOAD, "creator@example.com")

        assert result is None
        assert error == {"error": "Erro ao criar pendências"}
        bills_col.delete_one.assert_called_once()


def test_get_user_bills_ok():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        bill_doc = {**BILL_DOC, "_id": OBJ_BILL_ID}
        groups_col = MagicMock()
        groups_col.find.return_value = [{"_id": OBJ_GROUP_ID}]
        bills_col = MagicMock()
        bills_col.find.return_value = [bill_doc]
        mock_mongo.__getitem__.side_effect = {
            "groups": groups_col,
            "bills": bills_col,
        }.get

        result, error = get_user_bills_service("creator@example.com")

        assert error is None
        assert len(result) == 1
        assert result[0]["_id"] == BILL_ID


def test_get_user_bills_no_groups():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        groups_col = MagicMock()
        groups_col.find.return_value = []
        bills_col = MagicMock()
        bills_col.find.return_value = []
        mock_mongo.__getitem__.side_effect = {
            "groups": groups_col,
            "bills": bills_col,
        }.get

        result, error = get_user_bills_service("creator@example.com")

        assert error is None
        assert result == []


def test_get_group_bills_group_not_found():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = get_group_bills_service(GROUP_ID, "creator@example.com")

        assert result is None
        assert error == {"error": "Grupo não encontrado"}


def test_get_group_bills_user_not_member():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(GROUP_DOC)

        result, error = get_group_bills_service(GROUP_ID, "outsider@example.com")

        assert result is None
        assert error == {"error": "Você não é membro deste grupo"}


def test_get_group_bills_ok():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        bill_doc = {**BILL_DOC, "_id": OBJ_BILL_ID}
        groups_col = MagicMock()
        groups_col.find_one.return_value = dict(GROUP_DOC)
        bills_col = MagicMock()
        bills_col.find.return_value = [bill_doc]
        mock_mongo.__getitem__.side_effect = {
            "groups": groups_col,
            "bills": bills_col,
        }.get

        result, error = get_group_bills_service(GROUP_ID, "creator@example.com")

        assert error is None
        assert len(result) == 1
        assert result[0]["_id"] == BILL_ID


def test_get_bill_not_found():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = get_bill_service(BILL_ID, "creator@example.com")

        assert result is None
        assert error == {"error": "Conta não encontrada"}


def test_get_bill_user_not_in_group():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        bills_col = MagicMock()
        bills_col.find_one.return_value = {**BILL_DOC, "_id": OBJ_BILL_ID}
        groups_col = MagicMock()
        groups_col.find_one.return_value = dict(GROUP_DOC)
        mock_mongo.__getitem__.side_effect = {
            "bills": bills_col,
            "groups": groups_col,
        }.get

        result, error = get_bill_service(BILL_ID, "outsider@example.com")

        assert result is None
        assert error == {"error": "Você não tem permissão para acessar esta conta"}


def test_get_bill_ok():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        bills_col = MagicMock()
        bills_col.find_one.return_value = {**BILL_DOC, "_id": OBJ_BILL_ID}
        groups_col = MagicMock()
        groups_col.find_one.return_value = dict(GROUP_DOC)
        mock_mongo.__getitem__.side_effect = {
            "bills": bills_col,
            "groups": groups_col,
        }.get

        result, error = get_bill_service(BILL_ID, "creator@example.com")

        assert error is None
        assert result["_id"] == BILL_ID


def test_update_bill_not_found():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = update_bill_service(
            BILL_ID, {"bill_type": "Luz"}, "creator@example.com"
        )

        assert result is None
        assert error == {"error": "Conta não encontrada"}


def test_update_bill_not_creator():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = {
            **BILL_DOC,
            "_id": OBJ_BILL_ID,
        }

        result, error = update_bill_service(
            BILL_ID, {"bill_type": "Luz"}, "member@example.com"
        )

        assert result is None
        assert error == {"error": "Apenas o criador da conta pode editá-la"}


def test_update_bill_already_paid():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = {
            **BILL_DOC,
            "_id": OBJ_BILL_ID,
            "is_paid": True,
        }

        result, error = update_bill_service(
            BILL_ID, {"bill_type": "Luz"}, "creator@example.com"
        )

        assert result is None
        assert error == {"error": "Não é possível editar uma conta já paga"}


def test_update_bill_ok():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        bill_doc = {**BILL_DOC, "_id": OBJ_BILL_ID}
        mock_mongo.__getitem__.return_value.find_one.return_value = bill_doc

        result, error = update_bill_service(
            BILL_ID,
            {"bill_type": "Luz", "pix_key": "11999999999"},
            "creator@example.com",
        )

        assert error is None
        assert result["message"] == "Conta atualizada com sucesso"
        mock_mongo.__getitem__.return_value.update_one.assert_called_once()
        update_data = mock_mongo.__getitem__.return_value.update_one.call_args.args[1]
        assert update_data["$set"]["pix_key"] == "11999999999"


def test_delete_bill_not_found():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = delete_bill_service(BILL_ID, "creator@example.com")

        assert result is None
        assert error == {"error": "Conta não encontrada"}


def test_delete_bill_not_creator():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = {
            **BILL_DOC,
            "_id": OBJ_BILL_ID,
        }

        result, error = delete_bill_service(BILL_ID, "member@example.com")

        assert result is None
        assert error == {"error": "Apenas o criador da conta pode deletá-la"}


def test_delete_bill_ok():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        bills_col = MagicMock()
        bills_col.find_one.return_value = {**BILL_DOC, "_id": OBJ_BILL_ID}
        pendencies_col = MagicMock()
        mock_mongo.__getitem__.side_effect = {
            "bills": bills_col,
            "pendencies": pendencies_col,
        }.get

        result, error = delete_bill_service(BILL_ID, "creator@example.com")

        assert error is None
        assert result == {
            "message": "Conta e suas pendências foram deletadas com sucesso"
        }
        pendencies_col.delete_many.assert_called_once()
        bills_col.delete_one.assert_called_once()


def test_mark_bill_as_paid_not_found():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = mark_bill_as_paid_service(BILL_ID, "creator@example.com")

        assert result is None
        assert error == {"error": "Conta não encontrada"}


def test_mark_bill_as_paid_not_creator():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = {
            **BILL_DOC,
            "_id": OBJ_BILL_ID,
        }

        result, error = mark_bill_as_paid_service(BILL_ID, "member@example.com")

        assert result is None
        assert error == {"error": "Apenas o criador da conta pode marcá-la como paga"}


def test_mark_bill_as_paid_ok():
    with patch("app.services.bill_services.mongo") as mock_mongo:
        bills_col = MagicMock()
        bills_col.find_one.return_value = {
            **BILL_DOC,
            "_id": OBJ_BILL_ID,
        }
        pendencies_col = MagicMock()
        mock_mongo.__getitem__.side_effect = {
            "bills": bills_col,
            "pendencies": pendencies_col,
        }.get

        result, error = mark_bill_as_paid_service(BILL_ID, "creator@example.com")

        assert error is None
        assert result == {"message": "Conta marcada como paga e pendências resolvidas"}
        bills_col.update_one.assert_called_once()
        pendencies_col.update_many.assert_called_once()

        update_query, update_data = pendencies_col.update_many.call_args.args
        assert update_query == {"bill_id": BILL_ID}
        assert update_data["$set"]["debtor_confirmed"] is True
        assert update_data["$set"]["creditor_confirmed"] is True
        assert "debtor_confirmed_at" in update_data["$set"]
        assert "creditor_confirmed_at" in update_data["$set"]
        assert update_data["$set"]["is_resolved"] is True
        assert "resolved_at" in update_data["$set"]
