from unittest.mock import patch

GOAL_ID = "507f1f77bcf86cd799439011"
USER_EMAIL = "test@example.com"
OTHER_EMAIL = "other@example.com"

GOAL_DATA = {
    "_id": GOAL_ID,
    "name": "Meta teste",
    "group_id": "507f1f77bcf86cd799439012",
    "members": [USER_EMAIL, OTHER_EMAIL],
    "current_value": 130.0,
    "contributions": [
        {
            "member_email": USER_EMAIL,
            "value": 40.0,
            "contributed_at": "2026-05-01T12:00:00Z",
        },
        {
            "member_email": OTHER_EMAIL,
            "value": 90.0,
            "contributed_at": "2026-05-03T12:00:00Z",
        },
    ],
}


def test_update_goal_contribution_no_token(client):
    response = client.put(f"/goal/{GOAL_ID}/contribution/1", json={"value": 90.0})

    assert response.status_code == 401


@patch("app.routes.goal.update_goal_contribution_service")
def test_update_goal_contribution_ok(mock_service, client, auth_headers):
    payload = {
        "value": 90.0,
        "member_email": OTHER_EMAIL,
        "contributed_at": "2026-05-03T12:00:00Z",
    }
    mock_service.return_value = (
        {"message": "Aporte atualizado com sucesso", "goal": GOAL_DATA},
        None,
    )

    response = client.put(
        f"/goal/{GOAL_ID}/contribution/1", json=payload, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.get_json()["goal"]["current_value"] == 130.0
    mock_service.assert_called_once_with(GOAL_ID, 1, payload, USER_EMAIL)


@patch("app.routes.goal.update_goal_contribution_service")
def test_update_goal_contribution_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Aporte não encontrado"})

    response = client.put(
        f"/goal/{GOAL_ID}/contribution/99",
        json={"value": 90.0},
        headers=auth_headers,
    )

    assert response.status_code == 404
