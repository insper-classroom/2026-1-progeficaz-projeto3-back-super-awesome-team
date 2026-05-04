from unittest.mock import patch

BILL_ID = "507f1f77bcf86cd799439011"
GROUP_ID = "507f1f77bcf86cd799439012"

BILL_PAYLOAD = {
    "bill_type": "Aluguel",
    "total_value": 1000.0,
    "group_id": GROUP_ID,
    "pix_key": "test@example.com",
    "members_to_pay": [{"email": "other@example.com", "value": 500.0}],
}

BILL_DATA = {
    "_id": BILL_ID,
    "bill_type": "Aluguel",
    "total_value": 1000.0,
    "group_id": GROUP_ID,
    "pix_key": "test@example.com",
    "members_to_pay": [{"email": "other@example.com", "value": 500.0}],
    "created_by": "test@example.com",
    "is_paid": False,
}


def test_create_bill_no_token(client):
    response = client.post("/bill", json=BILL_PAYLOAD)
    assert response.status_code == 401


@patch("app.routes.bill.create_bill_service")
def test_create_bill_ok(mock_service, client, auth_headers):
    mock_service.return_value = (
        {"message": "Conta criada com sucesso", "bill_id": BILL_ID, "pendencies_created": 1},
        None,
    )
    response = client.post("/bill", json=BILL_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201
    assert response.get_json()["bill_id"] == BILL_ID


@patch("app.routes.bill.create_bill_service")
def test_create_bill_validation_error(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"bill_type": ["Missing data for required field."]})
    response = client.post("/bill", json={}, headers=auth_headers)
    assert response.status_code == 400


@patch("app.routes.bill.create_bill_service")
def test_create_bill_group_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Grupo não encontrado"})
    response = client.post("/bill", json=BILL_PAYLOAD, headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.bill.create_bill_service")
def test_create_bill_not_a_member(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Você não tem permissão para criar conta neste grupo"},
    )
    response = client.post("/bill", json=BILL_PAYLOAD, headers=auth_headers)
    assert response.status_code == 403


@patch("app.routes.bill.get_user_bills_service")
def test_get_user_bills_ok(mock_service, client, auth_headers):
    mock_service.return_value = ([BILL_DATA], None)
    response = client.get("/bill", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "bills" in data
    assert len(data["bills"]) == 1


def test_get_user_bills_no_token(client):
    response = client.get("/bill")
    assert response.status_code == 401


@patch("app.routes.bill.get_group_bills_service")
def test_get_group_bills_ok(mock_service, client, auth_headers):
    mock_service.return_value = ([BILL_DATA], None)
    response = client.get(f"/group/{GROUP_ID}/bill", headers=auth_headers)
    assert response.status_code == 200
    assert "bills" in response.get_json()


@patch("app.routes.bill.get_group_bills_service")
def test_get_group_bills_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Grupo não encontrado"})
    response = client.get(f"/group/{GROUP_ID}/bill", headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.bill.get_group_bills_service")
def test_get_group_bills_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Você não é membro deste grupo"})
    response = client.get(f"/group/{GROUP_ID}/bill", headers=auth_headers)
    assert response.status_code == 403


@patch("app.routes.bill.get_bill_service")
def test_get_bill_ok(mock_service, client, auth_headers):
    mock_service.return_value = (BILL_DATA, None)
    response = client.get(f"/bill/{BILL_ID}", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["_id"] == BILL_ID


@patch("app.routes.bill.get_bill_service")
def test_get_bill_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Conta não encontrada"})
    response = client.get(f"/bill/{BILL_ID}", headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.bill.get_bill_service")
def test_get_bill_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Você não tem permissão para acessar esta conta"},
    )
    response = client.get(f"/bill/{BILL_ID}", headers=auth_headers)
    assert response.status_code == 403


@patch("app.routes.bill.update_bill_service")
def test_update_bill_ok(mock_service, client, auth_headers):
    mock_service.return_value = (
        {"message": "Conta atualizada com sucesso", "bill": BILL_DATA},
        None,
    )
    response = client.put(
        f"/bill/{BILL_ID}", json={"bill_type": "Luz"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.get_json()["message"] == "Conta atualizada com sucesso"


@patch("app.routes.bill.update_bill_service")
def test_update_bill_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Conta não encontrada"})
    response = client.put(
        f"/bill/{BILL_ID}", json={"bill_type": "Luz"}, headers=auth_headers
    )
    assert response.status_code == 404


@patch("app.routes.bill.update_bill_service")
def test_update_bill_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Apenas o criador da conta pode editá-la"},
    )
    response = client.put(
        f"/bill/{BILL_ID}", json={"bill_type": "Luz"}, headers=auth_headers
    )
    assert response.status_code == 403


@patch("app.routes.bill.update_bill_service")
def test_update_bill_already_paid(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Não é possível editar uma conta já paga"},
    )
    response = client.put(
        f"/bill/{BILL_ID}", json={"bill_type": "Luz"}, headers=auth_headers
    )
    assert response.status_code == 409


@patch("app.routes.bill.delete_bill_service")
def test_delete_bill_ok(mock_service, client, auth_headers):
    mock_service.return_value = (
        {"message": "Conta e suas pendências foram deletadas com sucesso"},
        None,
    )
    response = client.delete(f"/bill/{BILL_ID}", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json() == {
        "message": "Conta e suas pendências foram deletadas com sucesso"
    }


@patch("app.routes.bill.delete_bill_service")
def test_delete_bill_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Conta não encontrada"})
    response = client.delete(f"/bill/{BILL_ID}", headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.bill.delete_bill_service")
def test_delete_bill_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Apenas o criador da conta pode deletá-la"},
    )
    response = client.delete(f"/bill/{BILL_ID}", headers=auth_headers)
    assert response.status_code == 403


@patch("app.routes.bill.mark_bill_as_paid_service")
def test_mark_bill_as_paid_ok(mock_service, client, auth_headers):
    mock_service.return_value = (
        {"message": "Conta marcada como paga e pendências resolvidas"},
        None,
    )
    response = client.put(f"/bill/{BILL_ID}/mark-as-paid", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json() == {
        "message": "Conta marcada como paga e pendências resolvidas"
    }


@patch("app.routes.bill.mark_bill_as_paid_service")
def test_mark_bill_as_paid_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Conta não encontrada"})
    response = client.put(f"/bill/{BILL_ID}/mark-as-paid", headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.bill.mark_bill_as_paid_service")
def test_mark_bill_as_paid_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Apenas o criador da conta pode marcá-la como paga"},
    )
    response = client.put(f"/bill/{BILL_ID}/mark-as-paid", headers=auth_headers)
    assert response.status_code == 403
