from ..models import Bill
from ..extensions import mongo
from ..schemas import BillSchema
from .pendency_services import create_pendencies_for_bill
from bson.objectid import ObjectId
from datetime import date, datetime
import unicodedata

schema = BillSchema()

VALID_BILL_FILTER_STATUSES = {"abertas", "minhas", "vencidas", "concluidas"}


def _serialize_bill(bill):
    serialized = dict(bill)
    serialized["_id"] = str(serialized["_id"])
    return serialized


def _get_group_for_member(group_id, user_email):
    group = mongo["groups"].find_one({"_id": ObjectId(group_id)})
    if not group:
        return None, {"error": "Grupo não encontrado"}
    if user_email not in group["members"]:
        return None, {"error": "Você não é membro deste grupo"}
    return group, None


def _normalize_text(value):
    text = str(value or "")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.lower()


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)

    text = str(value).strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"

    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo:
            return parsed.replace(tzinfo=None)
        return parsed
    except ValueError:
        return None


def _bill_reference_date(bill):
    return _parse_date(bill.get("due_date")) or _parse_date(bill.get("created_at"))


def _bill_created_date(bill):
    return _parse_date(bill.get("created_at"))


def _bill_month_key(bill):
    reference_date = _bill_reference_date(bill)
    if not reference_date:
        return None
    return f"{reference_date.year}-{reference_date.month:02d}"


def _bill_search_text(bill):
    members = bill.get("members_to_pay") or []
    members_text = " ".join(
        " ".join(str(member.get(field) or "") for field in ("email", "name", "nome"))
        for member in members
    )
    return _normalize_text(
        " ".join(
            (
                str(bill.get("bill_type") or ""),
                str(bill.get("created_by") or ""),
                str(bill.get("pix_key") or ""),
                members_text,
            )
        )
    )


def _bill_is_due(bill):
    if bill.get("is_paid"):
        return False

    due_date = _parse_date(bill.get("due_date"))
    if not due_date:
        return False

    today = datetime.utcnow().date()
    return due_date.date() < today


def _active_pendency_bill_ids(user_email):
    pendencies = list(
        mongo["pendencies"].find(
            {"debtor_email": user_email, "is_resolved": False},
            {"bill_id": 1},
        )
    )
    return {str(pendency.get("bill_id")) for pendency in pendencies}


def _apply_bill_filters(bills, filters, user_email):
    filters = filters or {}
    status = filters.get("status")
    search = filters.get("search") or filters.get("q")
    month = filters.get("month")

    if status and status not in VALID_BILL_FILTER_STATUSES:
        return None, {"error": "Filtro de status inválido"}
    if month and month != "todos" and not _valid_month_key(month):
        return None, {"error": "Filtro de mês inválido"}

    filtered_bills = list(bills)

    if status == "abertas":
        filtered_bills = [bill for bill in filtered_bills if not bill.get("is_paid")]
    elif status == "concluidas":
        filtered_bills = [bill for bill in filtered_bills if bill.get("is_paid")]
    elif status == "vencidas":
        filtered_bills = [bill for bill in filtered_bills if _bill_is_due(bill)]
    elif status == "minhas":
        active_bill_ids = _active_pendency_bill_ids(user_email)
        filtered_bills = [
            bill
            for bill in filtered_bills
            if str(bill.get("_id")) in active_bill_ids and not bill.get("is_paid")
        ]

    if month and month != "todos":
        filtered_bills = [
            bill for bill in filtered_bills if _bill_month_key(bill) == month
        ]

    if search:
        normalized_search = _normalize_text(search)
        filtered_bills = [
            bill
            for bill in filtered_bills
            if normalized_search in _bill_search_text(bill)
        ]

    return filtered_bills, None


def _valid_month_key(month):
    if not month or len(month) != 7 or month[4] != "-":
        return False
    year, month_number = month.split("-")
    if not year.isdigit() or not month_number.isdigit():
        return False
    return 1 <= int(month_number) <= 12


def _month_from_key(month):
    if month and _valid_month_key(month):
        year, month_number = month.split("-")
        return int(year), int(month_number)

    today = datetime.utcnow()
    return today.year, today.month


def _heatmap_level(value, highest_value):
    if not value or not highest_value:
        return 0

    ratio = value / highest_value
    if ratio >= 0.76:
        return 4
    if ratio >= 0.51:
        return 3
    if ratio >= 0.26:
        return 2
    return 1


def _build_bill_heatmap(bills, month):
    year, month_number = _month_from_key(month)
    month_key = f"{year}-{month_number:02d}"
    first_day = date(year, month_number, 1)
    if month_number == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month_number + 1, 1)
    days_in_month = (next_month - first_day).days

    totals_by_day = {}
    for bill in bills:
        created_at = _bill_created_date(bill)
        if not created_at:
            continue
        if created_at.year != year or created_at.month != month_number:
            continue

        day_key = f"{created_at.year}-{created_at.month:02d}-{created_at.day:02d}"
        totals_by_day[day_key] = totals_by_day.get(day_key, 0) + float(
            bill.get("total_value") or 0
        )

    values = list(totals_by_day.values())
    highest_value = max(values) if values else 0
    total_month = sum(values)
    highest_day_entry = (
        max(totals_by_day.items(), key=lambda entry: entry[1])
        if totals_by_day
        else None
    )

    cells = []
    for index in range((first_day.weekday() + 1) % 7):
        cells.append({"type": "empty", "id": f"empty-{index}"})

    for day in range(1, days_in_month + 1):
        day_key = f"{year}-{month_number:02d}-{day:02d}"
        value = totals_by_day.get(day_key, 0)
        cells.append(
            {
                "type": "day",
                "id": day_key,
                "day": day,
                "value": value,
                "level": _heatmap_level(value, highest_value),
            }
        )

    return {
        "month": month_key,
        "total_month": total_month,
        "highest_value": highest_value,
        "highest_day": int(highest_day_entry[0].split("-")[2])
        if highest_day_entry
        else None,
        "days_with_bills": len(totals_by_day),
        "cells": cells,
    }


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

        return [_serialize_bill(bill) for bill in bills], None
    except Exception as e:
        return None, {"error": str(e)}


def get_group_bills_service(group_id, user_email, filters=None):
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
        bills, filters_error = _apply_bill_filters(bills, filters, user_email)
        if filters_error:
            return None, filters_error

        return [_serialize_bill(bill) for bill in bills], None
    except Exception as e:
        return None, {"error": str(e)}


def get_group_bills_heatmap_service(group_id, user_email, month=None):
    try:
        _, error = _get_group_for_member(group_id, user_email)
        if error:
            return None, error

        if month and not _valid_month_key(month):
            return None, {"error": "Filtro de mês inválido"}

        bills = list(mongo["bills"].find({"group_id": group_id}))
        return _build_bill_heatmap(bills, month), None
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
