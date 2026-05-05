from unittest.mock import patch, MagicMock
from bson import ObjectId

from app.services.group_services import (
    create_group_service,
    get_user_groups_service,
    get_group_service,
    update_group_service,
    delete_group_service,
)

GROUP_ID = "507f1f77bcf86cd799439011"
OBJ_GROUP_ID = ObjectId(GROUP_ID)

GROUP_DOC = {
    "_id": OBJ_GROUP_ID,
    "name": "My Group",
    "description": "A test group",
    "members": ["creator@example.com", "member@example.com"],
    "created_by": "creator@example.com",
}


def _make_mongo(**collections):
    mock_mongo = MagicMock()
    mock_mongo.__getitem__.side_effect = lambda key: collections.get(key, MagicMock())
    return mock_mongo


def test_create_group_validation_error():
    result, error = create_group_service({}, "creator@example.com")

    assert result is None
    assert error is not None


def test_create_group_member_not_found():
    with patch("app.services.group_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = create_group_service(
            {"name": "My Group", "members": ["ghost@example.com"]},
            "creator@example.com",
        )

        assert result is None
        assert "não encontrado" in error["error"]


def test_create_group_ok():
    with patch("app.services.group_services.mongo") as mock_mongo:
        users_col = MagicMock()
        users_col.find_one.return_value = {"email": "creator@example.com"}
        groups_col = MagicMock()
        mock_result = MagicMock()
        mock_result.inserted_id = OBJ_GROUP_ID
        groups_col.insert_one.return_value = mock_result
        mock_mongo.__getitem__.side_effect = {
            "users": users_col,
            "groups": groups_col,
        }.get

        result, error = create_group_service(
            {"name": "My Group", "members": ["creator@example.com"]},
            "creator@example.com",
        )

        assert error is None
        assert result["message"] == "Grupo criado com sucesso"
        assert "group_id" in result
        groups_col.insert_one.assert_called_once()


def test_create_group_with_image_ok():
    with patch("app.services.group_services.mongo") as mock_mongo:
        users_col = MagicMock()
        users_col.find_one.return_value = {"email": "creator@example.com"}
        groups_col = MagicMock()
        mock_result = MagicMock()
        mock_result.inserted_id = OBJ_GROUP_ID
        groups_col.insert_one.return_value = mock_result
        mock_mongo.__getitem__.side_effect = {
            "users": users_col,
            "groups": groups_col,
        }.get

        result, error = create_group_service(
            {
                "name": "My Group",
                "members": ["creator@example.com"],
                "image": "https://example.com/group.jpg",
            },
            "creator@example.com",
        )

        assert error is None
        assert result["message"] == "Grupo criado com sucesso"
        call_args = groups_col.insert_one.call_args[0][0]
        assert call_args["image"] == "https://example.com/group.jpg"


def test_create_group_adds_creator_if_missing():
    with patch("app.services.group_services.mongo") as mock_mongo:
        users_col = MagicMock()
        users_col.find_one.return_value = {"email": "creator@example.com"}
        groups_col = MagicMock()
        mock_result = MagicMock()
        mock_result.inserted_id = OBJ_GROUP_ID
        groups_col.insert_one.return_value = mock_result
        mock_mongo.__getitem__.side_effect = {
            "users": users_col,
            "groups": groups_col,
        }.get

        result, error = create_group_service(
            {"name": "My Group"},
            "creator@example.com",
        )

        assert error is None
        assert result["message"] == "Grupo criado com sucesso"


def test_get_user_groups_ok():
    with patch("app.services.group_services.mongo") as mock_mongo:
        doc = {**GROUP_DOC, "_id": OBJ_GROUP_ID}
        mock_mongo.__getitem__.return_value.find.return_value = [doc]

        result, error = get_user_groups_service("creator@example.com")

        assert error is None
        assert len(result) == 1
        assert result[0]["_id"] == GROUP_ID


def test_get_user_groups_empty():
    with patch("app.services.group_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find.return_value = []

        result, error = get_user_groups_service("creator@example.com")

        assert error is None
        assert result == []


def test_get_group_not_found():
    with patch("app.services.group_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = get_group_service(GROUP_ID, "creator@example.com")

        assert result is None
        assert error == {"error": "Grupo não encontrado"}


def test_get_group_user_not_member():
    with patch("app.services.group_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(GROUP_DOC)

        result, error = get_group_service(GROUP_ID, "outsider@example.com")

        assert result is None
        assert error == {"error": "Você não é membro deste grupo"}


def test_get_group_ok():
    with patch("app.services.group_services.mongo") as mock_mongo:
        doc = {**GROUP_DOC, "_id": OBJ_GROUP_ID}
        mock_mongo.__getitem__.return_value.find_one.return_value = doc

        result, error = get_group_service(GROUP_ID, "creator@example.com")

        assert error is None
        assert result["_id"] == GROUP_ID


def test_get_group_includes_member_details():
    with patch("app.services.group_services.mongo") as mock_mongo:
        groups_col = MagicMock()
        groups_col.find_one.return_value = {**GROUP_DOC, "_id": OBJ_GROUP_ID}
        users_col = MagicMock()
        users_col.find.return_value = [
            {"email": "creator@example.com", "name": "Creator User"},
            {"email": "member@example.com", "name": "Member User"},
        ]
        mock_mongo.__getitem__.side_effect = {
            "groups": groups_col,
            "users": users_col,
        }.get

        result, error = get_group_service(GROUP_ID, "creator@example.com")

        assert error is None
        assert result["member_details"] == [
            {"email": "creator@example.com", "name": "Creator User", "image": None},
            {"email": "member@example.com", "name": "Member User", "image": None},
        ]


def test_update_group_image_ok():
    with patch("app.services.group_services.mongo") as mock_mongo:
        doc = {**GROUP_DOC, "_id": OBJ_GROUP_ID}
        mock_mongo.__getitem__.return_value.find_one.return_value = doc

        result, error = update_group_service(
            GROUP_ID,
            {"image": "https://example.com/group.jpg"},
            "creator@example.com",
        )

        assert error is None
        assert result["message"] == "Grupo atualizado com sucesso"
        mock_mongo.__getitem__.return_value.update_one.assert_called_once()


def test_update_group_not_found():
    with patch("app.services.group_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = update_group_service(
            GROUP_ID, {"name": "New"}, "creator@example.com"
        )

        assert result is None
        assert error == {"error": "Grupo não encontrado"}


def test_update_group_user_not_member():
    with patch("app.services.group_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(GROUP_DOC)

        result, error = update_group_service(
            GROUP_ID, {"name": "New"}, "outsider@example.com"
        )

        assert result is None
        assert error == {"error": "Você não é membro deste grupo"}


def test_update_group_name_ok():
    with patch("app.services.group_services.mongo") as mock_mongo:
        doc = {**GROUP_DOC, "_id": OBJ_GROUP_ID}
        mock_mongo.__getitem__.return_value.find_one.return_value = doc

        result, error = update_group_service(
            GROUP_ID, {"name": "New Name"}, "creator@example.com"
        )

        assert error is None
        assert result["message"] == "Grupo atualizado com sucesso"
        mock_mongo.__getitem__.return_value.update_one.assert_called_once()


def test_update_group_add_nonexistent_member():
    with patch("app.services.group_services.mongo") as mock_mongo:
        groups_col = MagicMock()
        groups_col.find_one.return_value = {**GROUP_DOC, "_id": OBJ_GROUP_ID}
        users_col = MagicMock()
        users_col.find_one.return_value = None
        bills_col = MagicMock()
        bills_col.find.return_value = []
        mock_mongo.__getitem__.side_effect = {
            "groups": groups_col,
            "users": users_col,
            "bills": bills_col,
        }.get

        result, error = update_group_service(
            GROUP_ID,
            {
                "members": [
                    "creator@example.com",
                    "member@example.com",
                    "ghost@example.com",
                ]
            },
            "creator@example.com",
        )

        assert result is None
        assert "não encontrado" in error["error"]


def test_update_group_not_creator():
    with patch("app.services.group_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(GROUP_DOC)

        result, error = update_group_service(
            GROUP_ID, {"name": "New Name"}, "member@example.com"
        )

        assert result is None
        assert error == {"error": "Apenas o criador do grupo pode editá-lo"}


def test_update_group_transfer_ownership_same_owner():
    with patch("app.services.group_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(GROUP_DOC)

        result, error = update_group_service(
            GROUP_ID, {"created_by": "creator@example.com"}, "creator@example.com"
        )

        assert result is None
        assert error == {"error": "O novo dono deve ser diferente do dono atual"}


def test_update_group_transfer_ownership_non_member():
    with patch("app.services.group_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(GROUP_DOC)

        result, error = update_group_service(
            GROUP_ID, {"created_by": "outsider@example.com"}, "creator@example.com"
        )

        assert result is None
        assert error == {"error": "O novo dono deve ser membro do grupo"}


def test_update_group_transfer_ownership_ok():
    with patch("app.services.group_services.mongo") as mock_mongo:
        updated_doc = {**GROUP_DOC, "_id": OBJ_GROUP_ID, "created_by": "member@example.com"}
        mock_mongo.__getitem__.return_value.find_one.side_effect = [
            dict(GROUP_DOC),
            updated_doc,
        ]

        result, error = update_group_service(
            GROUP_ID, {"created_by": "member@example.com"}, "creator@example.com"
        )

        assert error is None
        assert result["message"] == "Grupo atualizado com sucesso"
        mock_mongo.__getitem__.return_value.update_one.assert_called_once()


def test_update_group_empty_members():
    with patch("app.services.group_services.mongo") as mock_mongo:
        groups_col = MagicMock()
        groups_col.find_one.return_value = {**GROUP_DOC, "_id": OBJ_GROUP_ID}
        bills_col = MagicMock()
        bills_col.find.return_value = []
        mock_mongo.__getitem__.side_effect = {
            "groups": groups_col,
            "bills": bills_col,
        }.get

        result, error = update_group_service(
            GROUP_ID, {"members": []}, "creator@example.com"
        )

        assert result is None
        assert error == {"error": "O grupo deve ter pelo menos um membro"}


def test_update_group_remove_member_with_active_bill():
    with patch("app.services.group_services.mongo") as mock_mongo:
        groups_col = MagicMock()
        groups_col.find_one.return_value = {**GROUP_DOC, "_id": OBJ_GROUP_ID}
        bills_col = MagicMock()
        bills_col.find.return_value = [{"_id": "some_bill"}]
        mock_mongo.__getitem__.side_effect = {
            "groups": groups_col,
            "bills": bills_col,
        }.get

        result, error = update_group_service(
            GROUP_ID,
            {"members": ["creator@example.com"]},
            "creator@example.com",
        )

        assert result is None
        assert "bills não pagas" in error["error"]


def test_delete_group_not_found():
    with patch("app.services.group_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = None

        result, error = delete_group_service(GROUP_ID, "creator@example.com")

        assert result is None
        assert error == {"error": "Grupo não encontrado"}


def test_delete_group_not_creator():
    with patch("app.services.group_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(GROUP_DOC)

        result, error = delete_group_service(GROUP_ID, "member@example.com")

        assert result is None
        assert error == {"error": "Apenas o criador do grupo pode deletá-lo"}


def test_delete_group_with_other_members():
    with patch("app.services.group_services.mongo") as mock_mongo:
        mock_mongo.__getitem__.return_value.find_one.return_value = dict(GROUP_DOC)

        result, error = delete_group_service(GROUP_ID, "creator@example.com")

        assert result is None
        assert "outros membros" in error["error"]


def test_delete_group_ok():
    with patch("app.services.group_services.mongo") as mock_mongo:
        solo_group = {**GROUP_DOC, "_id": OBJ_GROUP_ID, "members": ["creator@example.com"]}
        groups_col = MagicMock()
        groups_col.find_one.return_value = solo_group
        bills_col = MagicMock()
        bills_col.find.return_value.distinct.return_value = []
        pendencies_col = MagicMock()
        goals_col = MagicMock()
        mock_mongo.__getitem__.side_effect = {
            "groups": groups_col,
            "bills": bills_col,
            "pendencies": pendencies_col,
            "goals": goals_col,
        }.get

        result, error = delete_group_service(GROUP_ID, "creator@example.com")

        assert error is None
        assert result == {
            "message": "Grupo e seus dados associados foram deletados com sucesso"
        }
        goals_col.delete_many.assert_called_once_with({"group_id": GROUP_ID})
        groups_col.delete_one.assert_called_once()
