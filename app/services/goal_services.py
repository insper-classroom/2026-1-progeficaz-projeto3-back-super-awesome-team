from datetime import datetime

from bson.objectid import ObjectId

from ..extensions import mongo
from ..models import Goal
from ..schemas import GoalContributionSchema, GoalSchema

schema = GoalSchema()
contribution_schema = GoalContributionSchema()


def _serialize_goal(goal):
    goal["_id"] = str(goal["_id"])
    return goal


def _get_group_for_member(group_id, user_email):
    group = mongo["groups"].find_one({"_id": ObjectId(group_id)})
    if not group:
        return None, {"error": "Grupo não encontrado"}
    if user_email not in group["members"]:
        return None, {"error": "Você não é membro deste grupo"}
    return group, None


def _get_goal_for_member(goal_id, user_email):
    goal = mongo["goals"].find_one({"_id": ObjectId(goal_id)})
    if not goal:
        return None, None, {"error": "Meta não encontrada"}

    group, error = _get_group_for_member(goal["group_id"], user_email)
    if error:
        return None, None, error

    return goal, group, None


def _normalize_goal_members(data_members, group_members):
    members = data_members or group_members
    members = list(dict.fromkeys(members))

    if len(members) == 0:
        return None, {"error": "Pelo menos um membro é obrigatório"}

    for member_email in members:
        if member_email not in group_members:
            return None, {"error": f"Membro {member_email} não pertence ao grupo"}

    return members, None


def create_goal_service(data, user_email):
    errors = schema.validate(data)
    if errors:
        return None, errors

    try:
        group, error = _get_group_for_member(data["group_id"], user_email)
        if error:
            return None, error

        members, members_error = _normalize_goal_members(
            data.get("members"), group["members"]
        )
        if members_error:
            return None, members_error

        goal = Goal(
            name=data["name"],
            target_value=data["target_value"],
            group_id=data["group_id"],
            created_by=user_email,
            members=members,
            due_date=data.get("due_date"),
            description=data.get("description"),
            icon=data.get("icon"),
            current_value=data.get("current_value", 0),
        )
        result = mongo["goals"].insert_one(goal.to_dictionary())

        return {
            "message": "Meta criada com sucesso",
            "goal_id": str(result.inserted_id),
        }, None
    except Exception as e:
        return None, {"error": str(e)}


def get_group_goals_service(group_id, user_email):
    try:
        _, error = _get_group_for_member(group_id, user_email)
        if error:
            return None, error

        goals = list(mongo["goals"].find({"group_id": group_id}))
        return [_serialize_goal(goal) for goal in goals], None
    except Exception as e:
        return None, {"error": str(e)}


def get_user_goals_service(user_email):
    try:
        groups = list(mongo["groups"].find({"members": user_email}, {"_id": 1}))
        group_ids = [str(group["_id"]) for group in groups]

        goals = list(mongo["goals"].find({"group_id": {"$in": group_ids}}))
        return [_serialize_goal(goal) for goal in goals], None
    except Exception as e:
        return None, {"error": str(e)}


def get_goal_service(goal_id, user_email):
    try:
        goal, _, error = _get_goal_for_member(goal_id, user_email)
        if error:
            return None, error

        return _serialize_goal(goal), None
    except Exception as e:
        return None, {"error": str(e)}


def update_goal_service(goal_id, data, user_email):
    errors = schema.validate(data, partial=True)
    if errors:
        return None, errors

    try:
        goal, group, error = _get_goal_for_member(goal_id, user_email)
        if error:
            return None, error

        update_data = {}

        if "name" in data:
            update_data["name"] = data["name"]
        if "target_value" in data:
            update_data["target_value"] = data["target_value"]
        if "due_date" in data:
            update_data["due_date"] = data["due_date"]
        if "description" in data:
            update_data["description"] = data["description"]
        if "icon" in data:
            update_data["icon"] = data["icon"]
        if "current_value" in data:
            update_data["current_value"] = data["current_value"]
        if "members" in data:
            members, members_error = _normalize_goal_members(
                data.get("members"), group["members"]
            )
            if members_error:
                return None, members_error
            update_data["members"] = members

        if not update_data:
            return {
                "message": "Nenhum campo para atualizar",
                "goal": _serialize_goal(goal),
            }, None

        update_data["updated_at"] = datetime.utcnow()
        mongo["goals"].update_one({"_id": ObjectId(goal_id)}, {"$set": update_data})

        updated_goal = mongo["goals"].find_one({"_id": ObjectId(goal_id)})
        return {
            "message": "Meta atualizada com sucesso",
            "goal": _serialize_goal(updated_goal),
        }, None
    except Exception as e:
        return None, {"error": str(e)}


def delete_goal_service(goal_id, user_email):
    try:
        _, _, error = _get_goal_for_member(goal_id, user_email)
        if error:
            return None, error

        mongo["goals"].delete_one({"_id": ObjectId(goal_id)})
        return {"message": "Meta deletada com sucesso"}, None
    except Exception as e:
        return None, {"error": str(e)}


def add_goal_contribution_service(goal_id, data, user_email):
    errors = contribution_schema.validate(data)
    if errors:
        return None, errors

    try:
        goal, group, error = _get_goal_for_member(goal_id, user_email)
        if error:
            return None, error

        member_email = data.get("member_email", user_email)
        if member_email not in group["members"]:
            return None, {"error": f"Membro {member_email} não pertence ao grupo"}
        if member_email not in goal["members"]:
            return None, {"error": f"Membro {member_email} não pertence à meta"}

        contribution = {
            "member_email": member_email,
            "value": data["value"],
            "contributed_at": data.get("contributed_at") or datetime.utcnow(),
            "registered_by": user_email,
        }

        mongo["goals"].update_one(
            {"_id": ObjectId(goal_id)},
            {
                "$push": {"contributions": contribution},
                "$inc": {"current_value": data["value"]},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

        updated_goal = mongo["goals"].find_one({"_id": ObjectId(goal_id)})
        return {
            "message": "Aporte registrado com sucesso",
            "goal": _serialize_goal(updated_goal),
        }, None
    except Exception as e:
        return None, {"error": str(e)}
