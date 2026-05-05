from unittest.mock import MagicMock, patch

from bson import ObjectId

from app.services.personal_services import get_personal_summary_service

USER_EMAIL = "test@example.com"
OTHER_EMAIL = "other@example.com"
GROUP_ID = ObjectId("507f1f77bcf86cd799439012")
GOAL_ID = ObjectId("507f1f77bcf86cd799439011")
BILL_ID = ObjectId("507f1f77bcf86cd799439010")
SECOND_BILL_ID = ObjectId("507f1f77bcf86cd799439013")
THIRD_BILL_ID = ObjectId("507f1f77bcf86cd799439017")
PENDENCY_ID = ObjectId("507f1f77bcf86cd799439014")
SECOND_PENDENCY_ID = ObjectId("507f1f77bcf86cd799439015")


def _make_mongo(groups_col, goals_col, bills_col, pendencies_col):
    mock_mongo = MagicMock()
    mock_mongo.__getitem__.side_effect = {
        "groups": groups_col,
        "goals": goals_col,
        "bills": bills_col,
        "pendencies": pendencies_col,
    }.get
    return mock_mongo


def test_get_personal_summary_aggregates_confirmed_group_expenses_and_user_contributions():
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

    bills_col = MagicMock()
    bills_col.find.return_value = [
        {
            "_id": BILL_ID,
            "bill_type": "Alimentação",
            "group_id": str(GROUP_ID),
            "total_value": 200.0,
            "created_by": OTHER_EMAIL,
            "due_date": "2026-05-05T00:00:00Z",
            "created_at": "2026-05-01T12:00:00Z",
        },
        {
            "_id": SECOND_BILL_ID,
            "bill_type": "Transporte",
            "group_id": str(GROUP_ID),
            "total_value": 90.0,
            "created_by": USER_EMAIL,
            "due_date": "2026-05-06T00:00:00Z",
            "created_at": "2026-05-02T12:00:00Z",
        },
        {
            "_id": THIRD_BILL_ID,
            "bill_type": "Internet",
            "group_id": str(GROUP_ID),
            "total_value": 30.0,
            "created_by": USER_EMAIL,
            "due_date": "2026-05-05T00:00:00Z",
            "created_at": "2026-05-02T12:00:00Z",
        },
    ]

    pendencies_col = MagicMock()
    pendencies_col.find.return_value = [
        {
            "_id": PENDENCY_ID,
            "bill_id": str(BILL_ID),
            "debtor_email": USER_EMAIL,
            "creditor_email": OTHER_EMAIL,
            "value": 80.0,
            "debtor_confirmed": True,
            "creditor_confirmed": True,
            "is_resolved": False,
            "resolved_at": "2026-05-04T12:00:00Z",
        },
        {
            "_id": SECOND_PENDENCY_ID,
            "bill_id": str(SECOND_BILL_ID),
            "debtor_email": OTHER_EMAIL,
            "creditor_email": USER_EMAIL,
            "value": 40.0,
            "is_resolved": True,
            "resolved_at": "2026-05-03T12:00:00Z",
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439016"),
            "bill_id": str(BILL_ID),
            "debtor_email": USER_EMAIL,
            "creditor_email": OTHER_EMAIL,
            "value": 25.0,
            "debtor_confirmed": True,
            "creditor_confirmed": False,
            "is_resolved": False,
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439018"),
            "bill_id": str(THIRD_BILL_ID),
            "debtor_email": OTHER_EMAIL,
            "creditor_email": USER_EMAIL,
            "value": 30.0,
            "debtor_confirmed": False,
            "creditor_confirmed": False,
            "is_resolved": False,
        },
    ]

    with patch(
        "app.services.personal_services.mongo",
        _make_mongo(groups_col, goals_col, bills_col, pendencies_col),
    ):
        result, error = get_personal_summary_service(USER_EMAIL)

    assert error is None
    assert result["summary"]["total_expenses"] == 120.0
    assert result["summary"]["total_owed"] == 25.0
    assert result["summary"]["total_paid"] == 80.0
    assert result["summary"]["total_received"] == 40.0
    assert result["summary"]["total_contributions"] == 50.0
    assert result["summary"]["owed_count"] == 1
    assert len(result["expenses"]) == 2
    assert len(result["due_expenses"]) == 4
    assert len(result["contributions"]) == 1
    assert result["due_expenses"][0]["category"] == "Alimentação"
    assert result["due_expenses"][0]["value"] == 80.0
    assert result["due_expenses"][0]["role"] == "debtor"
    assert result["due_expenses"][0]["resolved"] is True
    assert result["due_expenses"][0]["due_date"] == "2026-05-05T00:00:00Z"
    due_roles = {item["role"] for item in result["due_expenses"]}
    due_statuses = {item["resolved"] for item in result["due_expenses"]}
    assert due_roles == {"debtor", "creditor"}
    assert due_statuses == {True, False}
    assert result["expenses"][0]["category"] == "Alimentação"
    assert result["expenses"][0]["group_name"] == "Casa"
    assert result["expenses"][0]["role"] == "debtor"
    assert result["contributions"][0]["goal_name"] == "Reserva"
    assert result["contributions"][0]["group_name"] == "Casa"
    assert result["charts"]["expenses_by_category"][0]["name"] == "Alimentação"
    assert result["charts"]["contributions_by_goal"][0]["value"] == 50.0
    assert result["charts"]["monthly_flow"] == [
        {"month": "2026-05", "expenses": 120.0, "contributions": 50.0}
    ]
    pendencies_query = pendencies_col.find.call_args.args[0]
    assert "is_resolved" not in pendencies_query


def test_get_personal_summary_without_groups_skips_goal_lookup():
    groups_col = MagicMock()
    groups_col.find.return_value = []
    goals_col = MagicMock()
    bills_col = MagicMock()
    pendencies_col = MagicMock()

    with patch(
        "app.services.personal_services.mongo",
        _make_mongo(groups_col, goals_col, bills_col, pendencies_col),
    ):
        result, error = get_personal_summary_service(USER_EMAIL)

    assert error is None
    assert result["expenses"] == []
    assert result["due_expenses"] == []
    assert result["contributions"] == []
    goals_col.find.assert_not_called()
    bills_col.find.assert_not_called()
    pendencies_col.find.assert_not_called()
