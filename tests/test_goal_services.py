from unittest.mock import MagicMock, patch

from bson import ObjectId

from app.services.goal_services import (
    add_goal_contribution_service,
    create_goal_service,
    delete_goal_service,
    get_goal_service,
    get_group_goals_service,
    get_user_goals_service,
    update_goal_contribution_service,
    update_goal_service,
)

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


GOAL_PAYLOAD = {
    "name": "Meta teste",
    "target_value": 500.0,
    "group_id": GROUP_ID,
}


def test_create_goal_validation_error():
    result, error = create_goal_service({}, USER_EMAIL)

    assert result is None
    assert error is not None


def test_create_goal_group_not_found():
    groups_col = MagicMock()
    groups_col.find_one.return_value = None
    goals_col = MagicMock()

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = create_goal_service(GOAL_PAYLOAD, USER_EMAIL)

    assert result is None
    assert error == {"error": "Grupo não encontrado"}


def test_create_goal_user_not_member():
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC
    goals_col = MagicMock()

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = create_goal_service(GOAL_PAYLOAD, "outsider@example.com")

    assert result is None
    assert error == {"error": "Você não é membro deste grupo"}


def test_create_goal_member_not_in_group():
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC
    goals_col = MagicMock()
    payload = {**GOAL_PAYLOAD, "members": ["ghost@example.com"]}

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = create_goal_service(payload, USER_EMAIL)

    assert result is None
    assert "não pertence ao grupo" in error["error"]


def test_create_goal_ok():
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC
    goals_col = MagicMock()
    mock_result = MagicMock()
    mock_result.inserted_id = OBJ_GOAL_ID
    goals_col.insert_one.return_value = mock_result

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = create_goal_service(GOAL_PAYLOAD, USER_EMAIL)

    assert error is None
    assert result["message"] == "Meta criada com sucesso"
    assert result["goal_id"] == GOAL_ID
    goals_col.insert_one.assert_called_once()


def test_get_group_goals_user_not_member():
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC
    goals_col = MagicMock()

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = get_group_goals_service(GROUP_ID, "outsider@example.com")

    assert result is None
    assert error == {"error": "Você não é membro deste grupo"}


def test_get_group_goals_ok():
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC
    goals_col = MagicMock()
    goals_col.find.return_value = [{**GOAL_DOC}]

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = get_group_goals_service(GROUP_ID, USER_EMAIL)

    assert error is None
    assert len(result) == 1
    assert result[0]["_id"] == GOAL_ID


def test_get_user_goals_ok():
    groups_col = MagicMock()
    groups_col.find.return_value = [{"_id": OBJ_GROUP_ID}]
    goals_col = MagicMock()
    goals_col.find.return_value = [{**GOAL_DOC}]

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = get_user_goals_service(USER_EMAIL)

    assert error is None
    assert len(result) == 1
    assert result[0]["_id"] == GOAL_ID


def test_get_user_goals_empty():
    groups_col = MagicMock()
    groups_col.find.return_value = []
    goals_col = MagicMock()
    goals_col.find.return_value = []

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = get_user_goals_service(USER_EMAIL)

    assert error is None
    assert result == []


def test_get_goal_not_found():
    goals_col = MagicMock()
    goals_col.find_one.return_value = None
    groups_col = MagicMock()

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = get_goal_service(GOAL_ID, USER_EMAIL)

    assert result is None
    assert error == {"error": "Meta não encontrada"}


def test_get_goal_ok():
    goals_col = MagicMock()
    goals_col.find_one.return_value = {**GOAL_DOC}
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = get_goal_service(GOAL_ID, USER_EMAIL)

    assert error is None
    assert result["_id"] == GOAL_ID


def test_update_goal_validation_error():
    goals_col = MagicMock()
    goals_col.find_one.return_value = {**GOAL_DOC}
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = update_goal_service(GOAL_ID, {"target_value": -10.0}, USER_EMAIL)

    assert result is None
    assert error is not None


def test_update_goal_not_found():
    goals_col = MagicMock()
    goals_col.find_one.return_value = None
    groups_col = MagicMock()

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = update_goal_service(GOAL_ID, {"name": "Nova meta"}, USER_EMAIL)

    assert result is None
    assert error == {"error": "Meta não encontrada"}


def test_update_goal_ok():
    updated_goal = {**GOAL_DOC, "name": "Meta atualizada"}
    goals_col = MagicMock()
    goals_col.find_one.side_effect = [{**GOAL_DOC}, updated_goal]
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = update_goal_service(GOAL_ID, {"name": "Meta atualizada"}, USER_EMAIL)

    assert error is None
    assert result["message"] == "Meta atualizada com sucesso"
    goals_col.update_one.assert_called_once()


def test_update_goal_no_fields():
    goals_col = MagicMock()
    goals_col.find_one.return_value = {**GOAL_DOC}
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = update_goal_service(GOAL_ID, {}, USER_EMAIL)

    assert error is None
    assert result["message"] == "Nenhum campo para atualizar"
    goals_col.update_one.assert_not_called()


def test_delete_goal_not_found():
    goals_col = MagicMock()
    goals_col.find_one.return_value = None
    groups_col = MagicMock()

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = delete_goal_service(GOAL_ID, USER_EMAIL)

    assert result is None
    assert error == {"error": "Meta não encontrada"}


def test_delete_goal_ok():
    goals_col = MagicMock()
    goals_col.find_one.return_value = {**GOAL_DOC}
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = delete_goal_service(GOAL_ID, USER_EMAIL)

    assert error is None
    assert result == {"message": "Meta deletada com sucesso"}
    goals_col.delete_one.assert_called_once()


def test_add_goal_contribution_validation_error():
    goals_col = MagicMock()
    goals_col.find_one.return_value = {**GOAL_DOC}
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = add_goal_contribution_service(GOAL_ID, {}, USER_EMAIL)

    assert result is None
    assert error is not None


def test_add_goal_contribution_member_not_in_group():
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC
    goals_col = MagicMock()
    goals_col.find_one.return_value = {**GOAL_DOC}

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = add_goal_contribution_service(
            GOAL_ID,
            {"value": 50.0, "member_email": "ghost@example.com"},
            USER_EMAIL,
        )

    assert result is None
    assert "não pertence ao grupo" in error["error"]


def test_add_goal_contribution_member_not_in_goal():
    group_with_extra = {**GROUP_DOC, "members": [USER_EMAIL, OTHER_EMAIL, "extra@example.com"]}
    groups_col = MagicMock()
    groups_col.find_one.return_value = group_with_extra
    goals_col = MagicMock()
    goals_col.find_one.return_value = {**GOAL_DOC}

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = add_goal_contribution_service(
            GOAL_ID,
            {"value": 50.0, "member_email": "extra@example.com"},
            USER_EMAIL,
        )

    assert result is None
    assert "não pertence à meta" in error["error"]


def test_add_goal_contribution_ok():
    updated_goal = {**GOAL_DOC, "current_value": 150.0}
    goals_col = MagicMock()
    goals_col.find_one.side_effect = [{**GOAL_DOC}, updated_goal]
    groups_col = MagicMock()
    groups_col.find_one.return_value = GROUP_DOC

    with patch("app.services.goal_services.mongo", _make_mongo(goals_col, groups_col)):
        result, error = add_goal_contribution_service(
            GOAL_ID,
            {"value": 50.0, "member_email": USER_EMAIL},
            USER_EMAIL,
        )

    assert error is None
    assert result["message"] == "Aporte registrado com sucesso"
    goals_col.update_one.assert_called_once()
