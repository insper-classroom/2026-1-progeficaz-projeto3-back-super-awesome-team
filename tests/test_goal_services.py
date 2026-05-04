from unittest.mock import MagicMock, patch

from bson import ObjectId

from app.services.goal_services import update_goal_contribution_service

GOAL_ID = "507f1f77bcf86cd799439011"
GROUP_ID = "507f1f77bcf86cd799439012"
OBJ_GOAL_ID = ObjectId(GOAL_ID)
OBJ_GROUP_ID = ObjectId(GROUP_ID)
USER_EMAIL = "test@example.com"
OTHER_EMAIL = "other@example.com"

GOAL_DOC = {
    "_id": OBJ_GOAL_ID,
    "name": "Meta teste",
    "group_id": GROUP_ID,
    "members": [USER_EMAIL, OTHER_EMAIL],
    "current_value": 100.0,
    "contributions": [
        {
            "member_email": USER_EMAIL,
            "value": 40.0,
            "contributed_at": "2026-05-01T12:00:00Z",
        },
        {
            "member_email": OTHER_EMAIL,
            "value": 60.0,
            "contributed_at": "2026-05-02T12:00:00Z",
        },
    ],
}

GROUP_DOC = {
    "_id": OBJ_GROUP_ID,
    "members": [USER_EMAIL, OTHER_EMAIL],
}


def _make_mongo(goals_col, groups_col):
    mock_mongo = MagicMock()
    mock_mongo.__getitem__.side_effect = {
        "goals": goals_col,
        "groups": groups_col,
    }.get
    return mock_mongo


def test_update_goal_contribution_ok_adjusts_current_value_delta():
    updated_goal = {
        **GOAL_DOC,
        "_id": OBJ_GOAL_ID,
        "current_value": 130.0,
        "contributions": [
            GOAL_DOC["contributions"][0],
            {
                "member_email": OTHER_EMAIL,
                "value": 90.0,
                "contributed_at": "2026-05-03T12:00:00Z",
            },
        ],
    }
    goals_col = MagicMock()
    goals_col.find_one.side_effect = [{**GOAL_DOC}, updated_goal]
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = update_goal_contribution_service(
            GOAL_ID,
            1,
            {
                "value": 90.0,
                "member_email": OTHER_EMAIL,
                "contributed_at": "2026-05-03T12:00:00Z",
            },
            USER_EMAIL,
        )

    update = goals_col.update_one.call_args.args[1]

    assert error is None
    assert result["goal"]["_id"] == GOAL_ID
    assert result["goal"]["current_value"] == 130.0
    assert update["$inc"]["current_value"] == 30.0
    assert update["$set"]["contributions.1"]["value"] == 90.0
    assert update["$set"]["contributions.1"]["updated_by"] == USER_EMAIL


def test_update_goal_contribution_invalid_index():
    goals_col = MagicMock()
    goals_col.find_one.return_value = {**GOAL_DOC}
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = update_goal_contribution_service(
            GOAL_ID,
            99,
            {"value": 90.0},
            USER_EMAIL,
        )

    assert result is None
    assert error == {"error": "Aporte não encontrado"}
    goals_col.update_one.assert_not_called()
