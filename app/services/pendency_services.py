from ..models import Pendency
from ..extensions import mongo
from ..schemas import PendencySchema
from bson.objectid import ObjectId
from datetime import datetime

schema = PendencySchema()


def create_pendencies_for_bill(bill_id, creditor_email, members_to_pay):
    try:
        pendencies = []
        for member_data in members_to_pay:
            member_email = member_data["email"]
            member_value = member_data["value"]

            if member_email == creditor_email:
                continue

            pendency = Pendency(
                bill_id=bill_id,
                debtor_email=member_email,
                creditor_email=creditor_email,
                value=member_value,
            )
            result = mongo["pendencies"].insert_one(pendency.to_dictionary())
            pendencies.append(str(result.inserted_id))

        return pendencies, None
    except ValueError as e:
        return None, {"error": str(e)}
    except Exception as e:
        return None, {"error": str(e)}


def confirm_debtor_payment_service(pendency_id, user_email):
    try:
        pendency = mongo["pendencies"].find_one({"_id": ObjectId(pendency_id)})

        if not pendency:
            return None, {"error": "Pendência não encontrada"}

        if pendency["debtor_email"] != user_email:
            return None, {"error": "Apenas o devedor pode confirmar o pagamento"}

        update_data = {"debtor_confirmed": True}
        confirmed_at = pendency.get("debtor_confirmed_at")
        if not pendency.get("debtor_confirmed") or not confirmed_at:
            confirmed_at = datetime.utcnow()
            update_data["debtor_confirmed_at"] = confirmed_at

        # Se o credor já confirmou, marcar como resolvida
        if pendency["creditor_confirmed"]:
            update_data["is_resolved"] = True
            update_data["resolved_at"] = pendency.get("resolved_at") or confirmed_at

        mongo["pendencies"].update_one(
            {"_id": ObjectId(pendency_id)}, {"$set": update_data}
        )

        return {"message": "Confirmação do devedor registrada"}, None
    except Exception as e:
        return None, {"error": str(e)}


def confirm_creditor_payment_service(pendency_id, user_email):
    try:
        pendency = mongo["pendencies"].find_one({"_id": ObjectId(pendency_id)})

        if not pendency:
            return None, {"error": "Pendência não encontrada"}

        if pendency["creditor_email"] != user_email:
            return None, {"error": "Apenas o credor pode confirmar o recebimento"}

        update_data = {"creditor_confirmed": True}
        confirmed_at = pendency.get("creditor_confirmed_at")
        if not pendency.get("creditor_confirmed") or not confirmed_at:
            confirmed_at = datetime.utcnow()
            update_data["creditor_confirmed_at"] = confirmed_at

        # Se o devedor já confirmou, marcar como resolvida
        if pendency["debtor_confirmed"]:
            update_data["is_resolved"] = True
            update_data["resolved_at"] = pendency.get("resolved_at") or confirmed_at

        mongo["pendencies"].update_one(
            {"_id": ObjectId(pendency_id)}, {"$set": update_data}
        )

        return {"message": "Confirmação do credor registrada"}, None
    except Exception as e:
        return None, {"error": str(e)}


def get_user_pendencies_service(user_email):
    try:
        pendencies_as_debtor = list(
            mongo["pendencies"].find({"debtor_email": user_email})
        )
        pendencies_as_creditor = list(
            mongo["pendencies"].find({"creditor_email": user_email})
        )

        # Convert ObjectId to string for JSON serialization
        for p in pendencies_as_debtor + pendencies_as_creditor:
            p["_id"] = str(p["_id"])
            p["bill_id"] = str(p["bill_id"])

        return {
            "as_debtor": pendencies_as_debtor,
            "as_creditor": pendencies_as_creditor,
        }, None
    except Exception as e:
        return None, {"error": str(e)}


def get_bill_pendencies_service(bill_id, user_email):
    try:
        bill = mongo["bills"].find_one({"_id": ObjectId(bill_id)})
        if not bill:
            return None, {"error": "Conta não encontrada"}

        group = mongo["groups"].find_one({"_id": ObjectId(bill["group_id"])})
        if not group or user_email not in group["members"]:
            return None, {"error": "Você não tem permissão para acessar esta conta"}

        pendencies = list(mongo["pendencies"].find({"bill_id": bill_id}))

        # Convert ObjectId to string for JSON serialization
        for p in pendencies:
            p["_id"] = str(p["_id"])
            p["bill_id"] = str(p["bill_id"])

        return pendencies, None
    except Exception as e:
        return None, {"error": str(e)}


def get_pendency_service(pendency_id, user_email):
    try:
        pendency = mongo["pendencies"].find_one({"_id": ObjectId(pendency_id)})

        if not pendency:
            return None, {"error": "Pendência não encontrada"}

        bill = mongo["bills"].find_one({"_id": ObjectId(pendency["bill_id"])})
        if not bill:
            return None, {"error": "Conta não encontrada"}

        group = mongo["groups"].find_one({"_id": ObjectId(bill["group_id"])})
        if not group or user_email not in group["members"]:
            return None, {"error": "Você não tem permissão para acessar esta conta"}

        pendency["_id"] = str(pendency["_id"])
        pendency["bill_id"] = str(pendency["bill_id"])

        return pendency, None
    except Exception as e:
        return None, {"error": str(e)}


def get_group_pendencies_service(group_id, user_email):
    try:
        # Valida se o grupo existe
        group = mongo["groups"].find_one({"_id": ObjectId(group_id)})
        if not group:
            return None, {"error": "Grupo não encontrado"}

        # Valida se o usuário é membro do grupo
        if user_email not in group["members"]:
            return None, {"error": "Você não é membro deste grupo"}

        # Pega todas as bills do grupo
        bills = list(mongo["bills"].find({"group_id": group_id}, {"_id": 1}))
        bill_ids = [str(bill["_id"]) for bill in bills]

        # Pega todas as pendências dessas bills
        pendencies = list(mongo["pendencies"].find({"bill_id": {"$in": bill_ids}}))

        for p in pendencies:
            p["_id"] = str(p["_id"])
            p["bill_id"] = str(p["bill_id"])

        return pendencies, None
    except Exception as e:
        return None, {"error": str(e)}
