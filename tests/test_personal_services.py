from unittest.mock import MagicMock, patch

from bson import ObjectId

from app.services.personal_services import get_personal_summary_service

USER_EMAIL = "test@example.com"
OTHER_EMAIL = "other@example.com"
GROUP_ID = ObjectId("507f1f77bcf86cd799439012")
GOAL_ID = ObjectId("507f1f77bcf86cd799439011")
EXPENSE_ID = ObjectId("507f1f77bcf86cd799439010")


def _make_mongo(expenses_col, groups_col, goals_col):
    mock_mongo = MagicMock()
    mock_mongo.__getitem__.side_effect = {
        "expenses": expenses_col,
        "groups": groups_col,
        "goals": goals_col,
    }.get
    return mock_mongo


def test_get_personal_summary_aggregates_expenses_and_user_contributions():
    expenses_col = MagicMock()
    expenses_col.find.return_value = [
        {
            "_id": EXPENSE_ID,
            "expense_type": "Alimentação",
            "value": 80.0,
            "user_email": USER_EMAIL,
            "expense_date": "2026-05-01T12:00:00Z",
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "expense_type": "Transporte",
            "value": 40.0,
            "user_email": USER_EMAIL,
            "expense_date": "2026-05-02T12:00:00Z",
        },
    ]

    groups_col = MagicMock()
    groups_col.find.return_value = [
        {
            "_id": GROUP_ID,
            "name": "Casa",
        }
    ]

    goals_col = MagicMock()
    goals_col.find.return_value = [
        {
            "_id": GOAL_ID,
            "name": "Reserva",
            "group_id": str(GROUP_ID),
            "contributions": [
                {
                    "member_email": USER_EMAIL,
                    "value": 50.0,
                    "contributed_at": "2026-05-03T12:00:00Z",
                },
                {
                    "member_email": OTHER_EMAIL,
                    "value": 70.0,
                    "contributed_at": "2026-05-04T12:00:00Z",
                },
            ],
        }
    ]

    with patch(
        "app.services.personal_services.mongo",
        _make_mongo(expenses_col, groups_col, goals_col),
    ):
        result, error = get_personal_summary_service(USER_EMAIL)

    assert error is None
    assert result["summary"]["total_expenses"] == 120.0
    assert result["summary"]["total_contributions"] == 50.0
    assert result["summary"]["balance"] == -70.0
    assert len(result["expenses"]) == 2
    assert len(result["contributions"]) == 1
    assert result["contributions"][0]["goal_name"] == "Reserva"
    assert result["contributions"][0]["group_name"] == "Casa"
    assert result["charts"]["expenses_by_category"][0]["name"] == "Alimentação"
    assert result["charts"]["contributions_by_goal"][0]["value"] == 50.0
    assert result["charts"]["monthly_flow"] == [
        {"month": "2026-05", "expenses": 120.0, "contributions": 50.0}
    ]


def test_get_personal_summary_without_groups_skips_goal_lookup():
    expenses_col = MagicMock()
    expenses_col.find.return_value = []
    groups_col = MagicMock()
    groups_col.find.return_value = []
    goals_col = MagicMock()

    with patch(
        "app.services.personal_services.mongo",
        _make_mongo(expenses_col, groups_col, goals_col),
    ):
        result, error = get_personal_summary_service(USER_EMAIL)

    assert error is None
    assert result["expenses"] == []
    assert result["contributions"] == []
    assert result["summary"]["balance"] == 0
    goals_col.find.assert_not_called()
