from unittest.mock import patch, MagicMock
from bson import ObjectId

from app.services.pendency_services import (
    create_pendencies_for_bill,
    confirm_debtor_payment_service,
    confirm_creditor_payment_service,
    get_user_pendencies_service,
    get_bill_pendencies_service,
    get_pendency_service,
    get_group_pendencies_service,
)

PENDENCY_ID = "507f1f77bcf86cd799439011"
BILL_ID = "507f1f77bcf86cd799439012"
GROUP_ID = "507f1f77bcf86cd799439013"
OBJ_PENDENCY_ID = ObjectId(PENDENCY_ID)
OBJ_BILL_ID = ObjectId(BILL_ID)
OBJ_GROUP_ID = ObjectId(GROUP_ID)

PENDENCY_DOC = {
    "_id": OBJ_PENDENCY_ID,
    "bill_id": BILL_ID,
    "debtor_email": "debtor@example.com",
    "creditor_email": "creditor@example.com",
    "value": 100.0,
    "debtor_confirmed": False,
    "creditor_confirmed": False,
    "is_resolved": False,
}

BILL_DOC = {
    "_id": OBJ_BILL_ID,
    "group_id": GROUP_ID,
    "created_by": "creditor@example.com",
    "is_paid": False,
}

GROUP_DOC = {
    "_id": OBJ_GROUP_ID,
    "name": "My Group",
    "members": ["creditor@example.com", "debtor@example.com"],
}


def _make_mongo(**collections):
    mock_mongo = MagicMock()
    mock_mongo.__getitem__.side_effect = lambda key: collections.get(key, MagicMock())
    return mock_mongo


def test_create_pendencies_skips_creditor():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        members_to_pay = [
            {"email": "creditor@example.com", "value": 500.0},
            {"email": "debtor@example.com", "value": 500.0},
        ]
        mock_result = MagicMock()
        mock_result.inserted_id = OBJ_PENDENCY_ID
        mock_mongo.__getitem__.return_value.insert_one.return_value = mock_result

        result, error = create_pendencies_for_bill(
            bill_id=BILL_ID,
            creditor_email="creditor@example.com",
            members_to_pay=members_to_pay,
        )

        assert error is None
        assert len(result) == 1
        mock_mongo.__getitem__.return_value.insert_one.assert_called_once()


def test_create_pendencies_ok():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        members_to_pay = [
            {"email": "debtor1@example.com", "value": 300.0},
            {"email": "debtor2@example.com", "value": 200.0},
        ]
        mock_result = MagicMock()
        mock_result.inserted_id = OBJ_PENDENCY_ID
        mock_mongo.__getitem__.return_value.insert_one.return_value = mock_result

        result, error = create_pendencies_for_bill(
            bill_id=BILL_ID,
            creditor_email="creditor@example.com",
            members_to_pay=members_to_pay,
        )

        assert error is None
        assert len(result) == 2


def test_confirm_debtor_not_found():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = confirm_debtor_payment_service(
            PENDENCY_ID, "debtor@example.com"
        )

        assert result is None
        assert error == {"error": "Pendência não encontrada"}


def test_confirm_debtor_not_the_debtor():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(PENDENCY_DOC)

        result, error = confirm_debtor_payment_service(PENDENCY_ID, "other@example.com")

        assert result is None
        assert error == {"error": "Apenas o devedor pode confirmar o pagamento"}


def test_confirm_debtor_ok():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(PENDENCY_DOC)

        result, error = confirm_debtor_payment_service(
            PENDENCY_ID, "debtor@example.com"
        )

        assert error is None
        assert result == {"message": "Confirmação do devedor registrada"}
        mock_mongo.__getitem__.return_value.update_one.assert_called_once()


def test_confirm_debtor_resolves_when_creditor_already_confirmed():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        doc = {**PENDENCY_DOC, "creditor_confirmed": True}
        mock_mongo.__getitem__.return_value.find_one.return_value = doc

        result, error = confirm_debtor_payment_service(
            PENDENCY_ID, "debtor@example.com"
        )

        assert error is None
        call_kwargs = mock_mongo.__getitem__.return_value.update_one.call_args
        update_data = call_kwargs[0][1]["$set"]
        assert update_data.get("is_resolved") is True


def test_confirm_creditor_not_found():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = confirm_creditor_payment_service(
            PENDENCY_ID, "creditor@example.com"
        )

        assert result is None
        assert error == {"error": "Pendência não encontrada"}


def test_confirm_creditor_not_the_creditor():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(PENDENCY_DOC)

        result, error = confirm_creditor_payment_service(
            PENDENCY_ID, "other@example.com"
        )

        assert result is None
        assert error == {"error": "Apenas o credor pode confirmar o recebimento"}


def test_confirm_creditor_ok():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(PENDENCY_DOC)

        result, error = confirm_creditor_payment_service(
            PENDENCY_ID, "creditor@example.com"
        )

        assert error is None
        assert result == {"message": "Confirmação do credor registrada"}
        mock_mongo.__getitem__.return_value.update_one.assert_called_once()


def test_confirm_creditor_resolves_when_debtor_already_confirmed():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        doc = {**PENDENCY_DOC, "debtor_confirmed": True}
        mock_mongo.__getitem__.return_value.find_one.return_value = doc

        result, error = confirm_creditor_payment_service(
            PENDENCY_ID, "creditor@example.com"
        )

        assert error is None
        call_kwargs = mock_mongo.__getitem__.return_value.update_one.call_args
        update_data = call_kwargs[0][1]["$set"]
        assert update_data.get("is_resolved") is True


def test_get_user_pendencies_ok():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        pend = {**PENDENCY_DOC, "_id": OBJ_PENDENCY_ID, "bill_id": OBJ_BILL_ID}
        pendencies_col = MagicMock()
        pendencies_col.find.return_value = [pend]
        mock_mongo.__getitem__.side_effect = {"pendencies": pendencies_col}.get

        result, error = get_user_pendencies_service("debtor@example.com")

        assert error is None
        assert "as_debtor" in result
        assert "as_creditor" in result


def test_get_user_pendencies_empty():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        pendencies_col = MagicMock()
        pendencies_col.find.return_value = []
        mock_mongo.__getitem__.side_effect = {"pendencies": pendencies_col}.get

        result, error = get_user_pendencies_service("nobody@example.com")

        assert error is None
        assert result["as_debtor"] == []
        assert result["as_creditor"] == []


def test_get_bill_pendencies_bill_not_found():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = get_bill_pendencies_service(BILL_ID, "creditor@example.com")

        assert result is None
        assert error == {"error": "Conta não encontrada"}


def test_get_bill_pendencies_user_not_in_group():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        bills_col = MagicMock()
        bills_col.find_one.return_value = dict(BILL_DOC)
        groups_col = MagicMock()
        groups_col.find_one.return_value = dict(GROUP_DOC)
        mock_mongo.__getitem__.side_effect = {
            "bills": bills_col,
            "groups": groups_col,
        }.get

        result, error = get_bill_pendencies_service(BILL_ID, "outsider@example.com")

        assert result is None
        assert error == {"error": "Você não tem permissão para acessar esta conta"}


def test_get_bill_pendencies_ok():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        pend = {**PENDENCY_DOC, "_id": OBJ_PENDENCY_ID, "bill_id": OBJ_BILL_ID}
        bills_col = MagicMock()
        bills_col.find_one.return_value = dict(BILL_DOC)
        groups_col = MagicMock()
        groups_col.find_one.return_value = dict(GROUP_DOC)
        pendencies_col = MagicMock()
        pendencies_col.find.return_value = [pend]
        mock_mongo.__getitem__.side_effect = {
            "bills": bills_col,
            "groups": groups_col,
            "pendencies": pendencies_col,
        }.get

        result, error = get_bill_pendencies_service(BILL_ID, "creditor@example.com")

        assert error is None
        assert len(result) == 1
        assert result[0]["_id"] == PENDENCY_ID


def test_get_pendency_not_found():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = get_pendency_service(PENDENCY_ID, "creditor@example.com")

        assert result is None
        assert error == {"error": "Pendência não encontrada"}


def test_get_pendency_user_not_in_group():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        pendencies_col = MagicMock()
        pendencies_col.find_one.return_value = dict(PENDENCY_DOC)
        bills_col = MagicMock()
        bills_col.find_one.return_value = dict(BILL_DOC)
        groups_col = MagicMock()
        groups_col.find_one.return_value = dict(GROUP_DOC)
        mock_mongo.__getitem__.side_effect = {
            "pendencies": pendencies_col,
            "bills": bills_col,
            "groups": groups_col,
        }.get

        result, error = get_pendency_service(PENDENCY_ID, "outsider@example.com")

        assert result is None
        assert error == {"error": "Você não tem permissão para acessar esta conta"}


def test_get_pendency_ok():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        pend = {**PENDENCY_DOC, "_id": OBJ_PENDENCY_ID, "bill_id": OBJ_BILL_ID}
        pendencies_col = MagicMock()
        pendencies_col.find_one.return_value = pend
        bills_col = MagicMock()
        bills_col.find_one.return_value = dict(BILL_DOC)
        groups_col = MagicMock()
        groups_col.find_one.return_value = dict(GROUP_DOC)
        mock_mongo.__getitem__.side_effect = {
            "pendencies": pendencies_col,
            "bills": bills_col,
            "groups": groups_col,
        }.get

        result, error = get_pendency_service(PENDENCY_ID, "creditor@example.com")

        assert error is None
        assert result["_id"] == PENDENCY_ID


def test_get_group_pendencies_group_not_found():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = get_group_pendencies_service(GROUP_ID, "creditor@example.com")

        assert result is None
        assert error == {"error": "Grupo não encontrado"}


def test_get_group_pendencies_user_not_member():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(GROUP_DOC)

        result, error = get_group_pendencies_service(GROUP_ID, "outsider@example.com")

        assert result is None
        assert error == {"error": "Você não é membro deste grupo"}


def test_get_group_pendencies_ok():
    with patch("app.services.pendency_services.mongo") as mock_mongo:
        pend = {**PENDENCY_DOC, "_id": OBJ_PENDENCY_ID, "bill_id": OBJ_BILL_ID}
        groups_col = MagicMock()
        groups_col.find_one.return_value = dict(GROUP_DOC)
        bills_col = MagicMock()
        bills_col.find.return_value = [{"_id": OBJ_BILL_ID}]
        pendencies_col = MagicMock()
        pendencies_col.find.return_value = [pend]
        mock_mongo.__getitem__.side_effect = {
            "groups": groups_col,
            "bills": bills_col,
            "pendencies": pendencies_col,
        }.get

        result, error = get_group_pendencies_service(GROUP_ID, "creditor@example.com")

        assert error is None
        assert len(result) == 1
        assert result[0]["_id"] == PENDENCY_ID
