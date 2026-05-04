from ..models import Group
from ..extensions import mongo
from ..schemas import GroupSchema
from bson.objectid import ObjectId

schema = GroupSchema()


def create_group_service(data, user_email):
    erros = schema.validate(data)
    if erros:
        return None, erros

    try:
        members = data.get("members", []) or []
        if user_email not in members:
            members.insert(0, user_email)

        # Remove duplicatas
        members = list(dict.fromkeys(members))

        # Valida se todos os membros existem como usuários
        for member_email in members:
            user = mongo["users"].find_one({"email": member_email})
            if not user:
                return None, {"error": f"Usuário {member_email} não encontrado"}

        group = Group(data["name"], members, user_email, data.get("description"))
        result = mongo["groups"].insert_one(group.to_dictionary())
        return {
            "message": "Grupo criado com sucesso",
            "group_id": str(result.inserted_id),
        }, None
    except ValueError as e:
        return None, {"error": str(e)}


def get_user_groups_service(user_email):
    try:
        groups = list(mongo["groups"].find({"members": user_email}))
        for group in groups:
            group["_id"] = str(group["_id"])
        return groups, None
    except Exception as e:
        return None, {"error": str(e)}


def get_group_service(group_id, user_email):
    try:
        group = mongo["groups"].find_one({"_id": ObjectId(group_id)})
        if not group:
            return None, {"error": "Grupo não encontrado"}

        # Valida se o usuário é membro do grupo
        if user_email not in group["members"]:
            return None, {"error": "Você não é membro deste grupo"}

        group["_id"] = str(group["_id"])
        return group, None
    except Exception as e:
        return None, {"error": str(e)}


def update_group_service(group_id, data, user_email):
    try:
        group = mongo["groups"].find_one({"_id": ObjectId(group_id)})
        if not group:
            return None, {"error": "Grupo não encontrado"}

        # Valida se o usuário é membro do grupo
        if user_email not in group["members"]:
            return None, {"error": "Você não é membro deste grupo"}

        update_data = {}

        # Atualiza nome e descrição se fornecidos
        if "name" in data:
            update_data["name"] = data["name"]
        if "description" in data:
            update_data["description"] = data["description"]

        # Processa adição e remoção de membros
        if "members" in data:
            new_members_list = data["members"]
            current_members = group["members"]

            # Membros a remover
            members_to_remove = set(current_members) - set(new_members_list)

            # Valida remoção de membros
            for member_to_remove in members_to_remove:
                # Verifica se o membro está em bills não pagas
                active_bills = list(
                    mongo["bills"].find(
                        {
                            "group_id": group_id,
                            "is_paid": False,
                            "members_to_pay": {
                                "$elemMatch": {"email": member_to_remove}
                            },
                        }
                    )
                )

                if active_bills:
                    return None, {
                        "error": f"Não é possível remover {member_to_remove} pois está vinculado a bills não pagas"
                    }

            # Membros a adicionar
            members_to_add = set(new_members_list) - set(current_members)

            # Valida se novos membros existem
            for member_email in members_to_add:
                user = mongo["users"].find_one({"email": member_email})
                if not user:
                    return None, {"error": f"Usuário {member_email} não encontrado"}

            # Remove duplicatas
            new_members_list = list(dict.fromkeys(new_members_list))

            # Precisa ter pelo menos 1 membro
            if len(new_members_list) == 0:
                return None, {"error": "O grupo deve ter pelo menos um membro"}

            update_data["members"] = new_members_list

        mongo["groups"].update_one({"_id": ObjectId(group_id)}, {"$set": update_data})

        # Retorna o grupo atualizado
        updated_group = mongo["groups"].find_one({"_id": ObjectId(group_id)})
        updated_group["_id"] = str(updated_group["_id"])

        return {
            "message": "Grupo atualizado com sucesso",
            "group": updated_group,
        }, None
    except Exception as e:
        return None, {"error": str(e)}


def delete_group_service(group_id, user_email):
    try:
        group = mongo["groups"].find_one({"_id": ObjectId(group_id)})
        if not group:
            return None, {"error": "Grupo não encontrado"}

        # Apenas o criador pode deletar o grupo
        if group["created_by"] != user_email:
            return None, {"error": "Apenas o criador do grupo pode deletá-lo"}

        # Deleta todas as pendencies associadas às bills do grupo
        bills_ids = list(
            mongo["bills"].find({"group_id": group_id}, {"_id": 1}).distinct("_id")
        )

        for bill_id in bills_ids:
            mongo["pendencies"].delete_many({"bill_id": str(bill_id)})

        # Deleta todas as bills do grupo
        mongo["bills"].delete_many({"group_id": group_id})

        # Deleta todas as metas do grupo
        mongo["goals"].delete_many({"group_id": group_id})

        # Deleta o grupo
        mongo["groups"].delete_one({"_id": ObjectId(group_id)})

        return {
            "message": "Grupo e seus dados associados foram deletados com sucesso"
        }, None
    except Exception as e:
        return None, {"error": str(e)}
