from unittest.mock import patch

PENDENCY_ID = "507f1f77bcf86cd799439011"
BILL_ID = "507f1f77bcf86cd799439012"
GROUP_ID = "507f1f77bcf86cd799439013"

PENDENCY_DATA = {
    "_id": PENDENCY_ID,
    "bill_id": BILL_ID,
    "debtor_email": "debtor@example.com",
    "creditor_email": "test@example.com",
    "value": 100.0,
    "debtor_confirmed": False,
    "creditor_confirmed": False,
    "is_resolved": False,
}


def test_get_user_pendencies_no_token(client):
    response = client.get("/pendency")
    assert response.status_code == 401


@patch("app.routes.pendency.get_user_pendencies_service")
def test_get_user_pendencies_ok(mock_service, client, auth_headers):
    mock_service.return_value = (
        {"as_debtor": [], "as_creditor": [PENDENCY_DATA]},
        None,
    )
    response = client.get("/pendency", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "as_debtor" in data
    assert "as_creditor" in data
    assert len(data["as_creditor"]) == 1


def test_get_pendency_no_token(client):
    response = client.get(f"/pendency/{PENDENCY_ID}")
    assert response.status_code == 401


@patch("app.routes.pendency.get_pendency_service")
def test_get_pendency_ok(mock_service, client, auth_headers):
    mock_service.return_value = (PENDENCY_DATA, None)
    response = client.get(f"/pendency/{PENDENCY_ID}", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["_id"] == PENDENCY_ID


@patch("app.routes.pendency.get_pendency_service")
def test_get_pendency_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Pendência não encontrada"})
    response = client.get(f"/pendency/{PENDENCY_ID}", headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.pendency.get_pendency_service")
def test_get_pendency_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Você não tem permissão para acessar esta conta"},
    )
    response = client.get(f"/pendency/{PENDENCY_ID}", headers=auth_headers)
    assert response.status_code == 403


@patch("app.routes.pendency.get_bill_pendencies_service")
def test_get_bill_pendencies_ok(mock_service, client, auth_headers):
    mock_service.return_value = ([PENDENCY_DATA], None)
    response = client.get(f"/bill/{BILL_ID}/pendency", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "pendency" in data
    assert len(data["pendency"]) == 1


@patch("app.routes.pendency.get_bill_pendencies_service")
def test_get_bill_pendencies_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Conta não encontrada"})
    response = client.get(f"/bill/{BILL_ID}/pendency", headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.pendency.get_bill_pendencies_service")
def test_get_bill_pendencies_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Você não tem permissão para acessar esta conta"},
    )
    response = client.get(f"/bill/{BILL_ID}/pendency", headers=auth_headers)
    assert response.status_code == 403


@patch("app.routes.pendency.get_group_pendencies_service")
def test_get_group_pendencies_ok(mock_service, client, auth_headers):
    mock_service.return_value = ([PENDENCY_DATA], None)
    response = client.get(f"/group/{GROUP_ID}/pendency", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "pendency" in data
    assert len(data["pendency"]) == 1


@patch("app.routes.pendency.get_group_pendencies_service")
def test_get_group_pendencies_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Grupo não encontrado"})
    response = client.get(f"/group/{GROUP_ID}/pendency", headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.pendency.get_group_pendencies_service")
def test_get_group_pendencies_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Você não é membro deste grupo"})
    response = client.get(f"/group/{GROUP_ID}/pendency", headers=auth_headers)
    assert response.status_code == 403


def test_confirm_debtor_payment_no_token(client):
    response = client.put(f"/pendency/{PENDENCY_ID}/debtor-confirmation")
    assert response.status_code == 401


@patch("app.routes.pendency.confirm_debtor_payment_service")
def test_confirm_debtor_payment_ok(mock_service, client, auth_headers):
    mock_service.return_value = ({"message": "Confirmação do devedor registrada"}, None)
    response = client.put(
        f"/pendency/{PENDENCY_ID}/debtor-confirmation", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Confirmação do devedor registrada"}


@patch("app.routes.pendency.confirm_debtor_payment_service")
def test_confirm_debtor_payment_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Pendência não encontrada"})
    response = client.put(
        f"/pendency/{PENDENCY_ID}/debtor-confirmation", headers=auth_headers
    )
    assert response.status_code == 404


@patch("app.routes.pendency.confirm_debtor_payment_service")
def test_confirm_debtor_payment_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Apenas o devedor pode confirmar o pagamento"},
    )
    response = client.put(
        f"/pendency/{PENDENCY_ID}/debtor-confirmation", headers=auth_headers
    )
    assert response.status_code == 403


def test_confirm_creditor_payment_no_token(client):
    response = client.put(f"/pendency/{PENDENCY_ID}/creditor-confirmation")
    assert response.status_code == 401


@patch("app.routes.pendency.confirm_creditor_payment_service")
def test_confirm_creditor_payment_ok(mock_service, client, auth_headers):
    mock_service.return_value = ({"message": "Confirmação do credor registrada"}, None)
    response = client.put(
        f"/pendency/{PENDENCY_ID}/creditor-confirmation", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Confirmação do credor registrada"}


@patch("app.routes.pendency.confirm_creditor_payment_service")
def test_confirm_creditor_payment_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Pendência não encontrada"})
    response = client.put(
        f"/pendency/{PENDENCY_ID}/creditor-confirmation", headers=auth_headers
    )
    assert response.status_code == 404


@patch("app.routes.pendency.confirm_creditor_payment_service")
def test_confirm_creditor_payment_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Apenas o credor pode confirmar o recebimento"},
    )
    response = client.put(
        f"/pendency/{PENDENCY_ID}/creditor-confirmation", headers=auth_headers
    )
    assert response.status_code == 403
