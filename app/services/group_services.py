from ..models import Group
from ..extensions import mongo
from ..schemas import GroupSchema

schema = GroupSchema()


def create_group_service(data, user_email):
    erros = schema.validate(data)
    if erros:
        return None, erros

    try:
        members = data.get("members", []) or []
        if user_email not in members:
            members.insert(0, user_email)

        group = Group(data["name"], members, data.get("description"))
        mongo["groups"].insert_one(group.to_dictionary())
        return {"message": "Grupo criado com sucesso"}, None
    except ValueError as e:
        return None, {"error": str(e)}
