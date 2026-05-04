from unittest.mock import patch

USER_EMAIL = "test@example.com"


def test_get_personal_summary_no_token(client):
    response = client.get("/personal/summary")

    assert response.status_code == 401


@patch("app.routes.personal.get_personal_summary_service")
def test_get_personal_summary_ok(mock_service, client, auth_headers):
    mock_service.return_value = (
        {
            "expenses": [],
            "contributions": [],
            "summary": {
                "total_expenses": 0,
                "total_contributions": 0,
                "balance": 0,
                "expense_count": 0,
                "contribution_count": 0,
            },
            "charts": {
                "expenses_by_category": [],
                "contributions_by_goal": [],
                "monthly_flow": [],
            },
        },
        None,
    )

    response = client.get("/personal/summary", headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json()["summary"]["balance"] == 0
    mock_service.assert_called_once_with(USER_EMAIL)


@patch("app.routes.personal.get_personal_summary_service")
def test_get_personal_summary_error(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "falha"})

    response = client.get("/personal/summary", headers=auth_headers)

    assert response.status_code == 400
    assert response.get_json() == {"error": "falha"}
