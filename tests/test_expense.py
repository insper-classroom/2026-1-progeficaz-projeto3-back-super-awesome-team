from unittest.mock import patch

EXPENSE_ID = "507f1f77bcf86cd799439011"

EXPENSE_PAYLOAD = {
    "expense_type": "Alimentação",
    "value": 50.0,
    "expense_date": "2024-01-15T00:00:00",
}

EXPENSE_DATA = {
    "_id": EXPENSE_ID,
    "expense_type": "Alimentação",
    "value": 50.0,
    "expense_date": "2024-01-15T00:00:00",
    "user_email": "test@example.com",
}


def test_create_expense_no_token(client):
    response = client.post("/expense", json=EXPENSE_PAYLOAD)
    assert response.status_code == 401


@patch("app.routes.expense.create_expense_service")
def test_create_expense_ok(mock_service, client, auth_headers):
    mock_service.return_value = (
        {"message": "Despesa criada com sucesso", "expense_id": EXPENSE_ID},
        None,
    )
    response = client.post("/expense", json=EXPENSE_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201
    assert response.get_json()["expense_id"] == EXPENSE_ID


@patch("app.routes.expense.create_expense_service")
def test_create_expense_validation_error(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"expense_type": ["Missing data for required field."]},
    )
    response = client.post("/expense", json={}, headers=auth_headers)
    assert response.status_code == 400


def test_get_expense_no_token(client):
    response = client.get(f"/expense/{EXPENSE_ID}")
    assert response.status_code == 401


@patch("app.routes.expense.get_expense_service")
def test_get_expense_ok(mock_service, client, auth_headers):
    mock_service.return_value = (EXPENSE_DATA, None)
    response = client.get(f"/expense/{EXPENSE_ID}", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["_id"] == EXPENSE_ID


@patch("app.routes.expense.get_expense_service")
def test_get_expense_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Despesa não encontrada"})
    response = client.get(f"/expense/{EXPENSE_ID}", headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.expense.get_expense_service")
def test_get_expense_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Você não tem permissão para acessar esta despesa"},
    )
    response = client.get(f"/expense/{EXPENSE_ID}", headers=auth_headers)
    assert response.status_code == 403


def test_get_user_expenses_no_token(client):
    response = client.get("/expense")
    assert response.status_code == 401


@patch("app.routes.expense.get_user_expenses_service")
def test_get_user_expenses_ok(mock_service, client, auth_headers):
    mock_service.return_value = ([EXPENSE_DATA], None)
    response = client.get("/expense", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "expenses" in data
    assert len(data["expenses"]) == 1


@patch("app.routes.expense.get_user_expenses_service")
def test_get_user_expenses_empty(mock_service, client, auth_headers):
    mock_service.return_value = ([], None)
    response = client.get("/expense", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json() == {"expenses": []}


@patch("app.routes.expense.update_expense_service")
def test_update_expense_ok(mock_service, client, auth_headers):
    updated = {**EXPENSE_DATA, "value": 75.0}
    mock_service.return_value = (
        {"message": "Despesa atualizada com sucesso", "expense": updated},
        None,
    )
    response = client.put(
        f"/expense/{EXPENSE_ID}", json={"value": 75.0}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.get_json()["message"] == "Despesa atualizada com sucesso"


@patch("app.routes.expense.update_expense_service")
def test_update_expense_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Despesa não encontrada"})
    response = client.put(
        f"/expense/{EXPENSE_ID}", json={"value": 75.0}, headers=auth_headers
    )
    assert response.status_code == 404


@patch("app.routes.expense.update_expense_service")
def test_update_expense_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Você não tem permissão para editar esta despesa"},
    )
    response = client.put(
        f"/expense/{EXPENSE_ID}", json={"value": 75.0}, headers=auth_headers
    )
    assert response.status_code == 403


@patch("app.routes.expense.delete_expense_service")
def test_delete_expense_ok(mock_service, client, auth_headers):
    mock_service.return_value = ({"message": "Despesa deletada com sucesso"}, None)
    response = client.delete(f"/expense/{EXPENSE_ID}", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json() == {"message": "Despesa deletada com sucesso"}


@patch("app.routes.expense.delete_expense_service")
def test_delete_expense_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Despesa não encontrada"})
    response = client.delete(f"/expense/{EXPENSE_ID}", headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.expense.delete_expense_service")
def test_delete_expense_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Você não tem permissão para deletar esta despesa"},
    )
    response = client.delete(f"/expense/{EXPENSE_ID}", headers=auth_headers)
    assert response.status_code == 403
