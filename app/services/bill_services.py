from ..models import Bill
from ..extensions import mongo
from ..schemas import BillSchema
from .pendency_services import create_pendencies_for_bill
from bson.objectid import ObjectId
from datetime import datetime

schema = BillSchema()


def create_bill_service(data, created_by):
    erros = schema.validate(data)
    if erros:
        return None, erros

    try:
        group = mongo["groups"].find_one({"_id": ObjectId(data["group_id"])})
        if not group:
            return None, {"error": "Grupo não encontrado"}
        if created_by not in group["members"]:
            return None, {
                "error": "Você não tem permissão para criar conta neste grupo"
            }

        for member_data in data["members_to_pay"]:
            member_email = member_data["email"]
            if member_email not in group["members"]:
                return None, {"error": f"Membro {member_email} não pertence ao grupo"}

        bill = Bill(
            data["bill_type"],
            data["total_value"],
            data["group_id"],
            data["pix_key"],
            data["members_to_pay"],
            created_by,
            data.get("is_paid", False),
            data.get("due_date"),
        )
        result = mongo["bills"].insert_one(bill.to_dictionary())
        bill_id = str(result.inserted_id)

        pendencies, pendency_error = create_pendencies_for_bill(
            bill_id=bill_id,
            creditor_email=created_by,
            members_to_pay=data["members_to_pay"],
        )

        if pendency_error:
            mongo["bills"].delete_one({"_id": ObjectId(bill_id)})
            return None, pendency_error

        return {
            "message": "Conta criada com sucesso",
            "bill_id": bill_id,
            "pendencies_created": len(pendencies),
        }, None
    except ValueError as e:
        return None, {"error": str(e)}
    except Exception as e:
        return None, {"error": str(e)}


def get_user_bills_service(user_email):
    try:
        # Pega todos os grupos do usuário
        groups = list(mongo["groups"].find({"members": user_email}))
        group_ids = [group["_id"] for group in groups]

        # Pega todas as bills dos grupos do usuário
        bills = list(
            mongo["bills"].find({"group_id": {"$in": [str(gid) for gid in group_ids]}})
        )

        for bill in bills:
            bill["_id"] = str(bill["_id"])

        return bills, None
    except Exception as e:
        return None, {"error": str(e)}


def get_group_bills_service(group_id, user_email):
    try:
        # Valida se o grupo existe
        group = mongo["groups"].find_one({"_id": ObjectId(group_id)})
        if not group:
            return None, {"error": "Grupo não encontrado"}

        # Valida se o usuário é membro do grupo
        if user_email not in group["members"]:
            return None, {"error": "Você não é membro deste grupo"}

        # Pega todas as bills do grupo
        bills = list(mongo["bills"].find({"group_id": group_id}))

        for bill in bills:
            bill["_id"] = str(bill["_id"])

        return bills, None
    except Exception as e:
        return None, {"error": str(e)}


def get_bill_service(bill_id, user_email):
    try:
        bill = mongo["bills"].find_one({"_id": ObjectId(bill_id)})
        if not bill:
            return None, {"error": "Conta não encontrada"}

        # Valida se o usuário é membro do grupo
        group = mongo["groups"].find_one({"_id": ObjectId(bill["group_id"])})
        if not group or user_email not in group["members"]:
            return None, {"error": "Você não tem permissão para acessar esta conta"}

        bill["_id"] = str(bill["_id"])
        return bill, None
    except Exception as e:
        return None, {"error": str(e)}


def update_bill_service(bill_id, data, user_email):
    try:
        bill = mongo["bills"].find_one({"_id": ObjectId(bill_id)})
        if not bill:
            return None, {"error": "Conta não encontrada"}

        # Apenas o criador pode editar
        if bill["created_by"] != user_email:
            return None, {"error": "Apenas o criador da conta pode editá-la"}

        # Não permite editar se já foi marcada como paga
        if bill["is_paid"]:
            return None, {"error": "Não é possível editar uma conta já paga"}

        update_data = {}

        # Atualiza campos básicos
        if "bill_type" in data:
            update_data["bill_type"] = data["bill_type"]
        if "total_value" in data:
            update_data["total_value"] = data["total_value"]
        if "pix_key" in data:
            pix_key = str(data["pix_key"]).strip()
            if not pix_key:
                return None, {"error": "Chave PIX é obrigatória"}
            update_data["pix_key"] = pix_key
        if "due_date" in data:
            update_data["due_date"] = data["due_date"]

        # Se houver mudança em members_to_pay, atualiza as pendências
        if "members_to_pay" in data:
            new_members_to_pay = data["members_to_pay"]

            # Valida se os novos membros pertencem ao grupo
            group = mongo["groups"].find_one({"_id": ObjectId(bill["group_id"])})
            for member_data in new_members_to_pay:
                member_email = member_data["email"]
                if member_email not in group["members"]:
                    return None, {
                        "error": f"Membro {member_email} não pertence ao grupo"
                    }

            # Deleta as pendências antigas
            mongo["pendencies"].delete_many({"bill_id": bill_id})

            # Cria novas pendências com os novos valores
            pendencies, pendency_error = create_pendencies_for_bill(
                bill_id=bill_id,
                creditor_email=bill["created_by"],
                members_to_pay=new_members_to_pay,
            )

            if pendency_error:
                return None, pendency_error

            update_data["members_to_pay"] = new_members_to_pay

        mongo["bills"].update_one({"_id": ObjectId(bill_id)}, {"$set": update_data})

        # Retorna a conta atualizada
        updated_bill = mongo["bills"].find_one({"_id": ObjectId(bill_id)})
        updated_bill["_id"] = str(updated_bill["_id"])

        return {
            "message": "Conta atualizada com sucesso",
            "bill": updated_bill,
        }, None
    except Exception as e:
        return None, {"error": str(e)}


def delete_bill_service(bill_id, user_email):
    try:
        bill = mongo["bills"].find_one({"_id": ObjectId(bill_id)})
        if not bill:
            return None, {"error": "Conta não encontrada"}

        # Apenas o criador pode deletar
        if bill["created_by"] != user_email:
            return None, {"error": "Apenas o criador da conta pode deletá-la"}

        # Deleta todas as pendências associadas
        mongo["pendencies"].delete_many({"bill_id": bill_id})

        # Deleta a bill
        mongo["bills"].delete_one({"_id": ObjectId(bill_id)})

        return {"message": "Conta e suas pendências foram deletadas com sucesso"}, None
    except Exception as e:
        return None, {"error": str(e)}


def mark_bill_as_paid_service(bill_id, user_email):
    try:
        bill = mongo["bills"].find_one({"_id": ObjectId(bill_id)})

        if not bill:
            return None, {"error": "Conta não encontrada"}

        if bill["created_by"] != user_email:
            return None, {"error": "Apenas o criador da conta pode marcá-la como paga"}

        resolved_at = datetime.utcnow()
        mongo["bills"].update_one(
            {"_id": ObjectId(bill_id)}, {"$set": {"is_paid": True}}
        )
        mongo["pendencies"].update_many(
            {"bill_id": bill_id},
            {
                "$set": {
                    "debtor_confirmed": True,
                    "creditor_confirmed": True,
                    "debtor_confirmed_at": resolved_at,
                    "creditor_confirmed_at": resolved_at,
                    "is_resolved": True,
                    "resolved_at": resolved_at,
                }
            },
        )

        return {"message": "Conta marcada como paga e pendências resolvidas"}, None
    except Exception as e:
        return None, {"error": str(e)}
