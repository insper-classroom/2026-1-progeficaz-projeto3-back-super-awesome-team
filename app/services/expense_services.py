from ..models import Expense
from ..extensions import mongo
from ..schemas import ExpenseSchema
from bson.objectid import ObjectId

schema = ExpenseSchema()


def create_expense_service(data, user_email):
    erros = schema.validate(data)
    if erros:
        return None, erros

    try:
        user = mongo["users"].find_one({"email": user_email})
        if not user:
            return None, {"error": "Usuário não encontrado"}

        expense = Expense(
            data["expense_type"],
            data["value"],
            user_email,
            data["expense_date"],
        )
        result = mongo["expenses"].insert_one(expense.to_dictionary())
        expense_id = str(result.inserted_id)

        return {
            "message": "Despesa criada com sucesso",
            "expense_id": expense_id,
        }, None
    except Exception as e:
        return None, {"error": str(e)}


def get_expense_service(expense_id):
    try:
        expense = mongo["expenses"].find_one({"_id": ObjectId(expense_id)})
        if not expense:
            return None, {"error": "Despesa não encontrada"}

        expense["_id"] = str(expense["_id"])
        return expense, None
    except Exception as e:
        return None, {"error": str(e)}


def get_user_expenses_service(user_email):
    try:
        expenses = list(mongo["expenses"].find({"user_email": user_email}))
        for expense in expenses:
            expense["_id"] = str(expense["_id"])

        return expenses, None
    except Exception as e:
        return None, {"error": str(e)}


def update_expense_service(expense_id, data, user_email):
    erros = schema.validate(data, partial=True)
    if erros:
        return None, erros

    try:
        expense = mongo["expenses"].find_one({"_id": ObjectId(expense_id)})
        if not expense:
            return None, {"error": "Despesa não encontrada"}

        if expense["user_email"] != user_email:
            return None, {"error": "Você não tem permissão para editar esta despesa"}

        update_data = {}
        if "expense_type" in data:
            update_data["expense_type"] = data["expense_type"]
        if "value" in data:
            update_data["value"] = data["value"]
        if "expense_date" in data:
            update_data["expense_date"] = data["expense_date"]

        mongo["expenses"].update_one(
            {"_id": ObjectId(expense_id)}, {"$set": update_data}
        )

        expense.update(update_data)
        expense["_id"] = str(expense["_id"])

        return {
            "message": "Despesa atualizada com sucesso",
            "expense": expense,
        }, None
    except Exception as e:
        return None, {"error": str(e)}


def delete_expense_service(expense_id, user_email):
    try:
        expense = mongo["expenses"].find_one({"_id": ObjectId(expense_id)})
        if not expense:
            return None, {"error": "Despesa não encontrada"}

        if expense["user_email"] != user_email:
            return None, {"error": "Você não tem permissão para deletar esta despesa"}

        mongo["expenses"].delete_one({"_id": ObjectId(expense_id)})

        return {"message": "Despesa deletada com sucesso"}, None
    except Exception as e:
        return None, {"error": str(e)}
