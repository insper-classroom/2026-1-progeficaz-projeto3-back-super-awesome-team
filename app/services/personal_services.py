from collections import defaultdict
from copy import deepcopy
from datetime import datetime

from bson.objectid import ObjectId

from ..extensions import mongo


def _to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _serialize(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


def _date_key(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return ""


def _month_key(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m")
    if isinstance(value, str) and len(value) >= 7:
        return value[:7]
    return "Sem data"


def _build_expenses_by_category(expenses):
    totals = defaultdict(float)
    for expense in expenses:
        category = expense.get("category") or "Sem categoria"
        totals[category] += _to_number(expense.get("value"))

    total = sum(totals.values())
    categories = []
    for name, value in totals.items():
        percentage = (value / total * 100) if total else 0
        categories.append(
            {
                "name": name,
                "value": round(value, 2),
                "percentage": round(percentage, 2),
            }
        )

    return sorted(categories, key=lambda item: item["value"], reverse=True)


def _build_contributions_by_goal(contributions):
    totals = defaultdict(lambda: {"goal_id": None, "goal_name": "", "value": 0.0})

    for contribution in contributions:
        goal_id = contribution.get("goal_id")
        item = totals[goal_id]
        item["goal_id"] = goal_id
        item["goal_name"] = contribution.get("goal_name") or "Meta"
        item["value"] += _to_number(contribution.get("value"))

    return sorted(
        (
            {
                "goal_id": item["goal_id"],
                "goal_name": item["goal_name"],
                "value": round(item["value"], 2),
            }
            for item in totals.values()
        ),
        key=lambda item: item["value"],
        reverse=True,
    )


def _build_monthly_flow(expenses, contributions):
    months = defaultdict(lambda: {"month": "", "expenses": 0.0, "contributions": 0.0})

    for expense in expenses:
        month = _month_key(expense.get("date"))
        months[month]["month"] = month
        months[month]["expenses"] += _to_number(expense.get("value"))

    for contribution in contributions:
        month = _month_key(contribution.get("contributed_at"))
        months[month]["month"] = month
        months[month]["contributions"] += _to_number(contribution.get("value"))

    return [
        {
            "month": item["month"],
            "expenses": round(item["expenses"], 2),
            "contributions": round(item["contributions"], 2),
        }
        for item in sorted(months.values(), key=lambda item: item["month"])
    ]


def _extract_user_contributions(goals, groups_by_id, user_email):
    contributions = []

    for goal in goals:
        goal_id = str(goal.get("_id"))
        group_id = str(goal.get("group_id"))
        group = groups_by_id.get(group_id, {})

        for index, contribution in enumerate(goal.get("contributions") or []):
            if contribution.get("member_email") != user_email:
                continue

            contribution_data = deepcopy(contribution)
            contribution_data.update(
                {
                    "contribution_index": index,
                    "goal_id": goal_id,
                    "goal_name": goal.get("name"),
                    "group_id": group_id,
                    "group_name": group.get("name"),
                }
            )
            contributions.append(_serialize(contribution_data))

    return sorted(
        contributions,
        key=lambda item: _date_key(item.get("contributed_at")),
        reverse=True,
    )


def _get_pendency_date(pendency, bill):
    return (
        pendency.get("resolved_at")
        or pendency.get("creditor_confirmed_at")
        or pendency.get("debtor_confirmed_at")
        or bill.get("created_at")
    )


def _is_confirmed_group_expense(pendency, bill):
    return bool(
        bill.get("is_paid")
        or pendency.get("is_resolved")
        or (pendency.get("debtor_confirmed") and pendency.get("creditor_confirmed"))
    )


def _extract_confirmed_group_expenses(pendencies, bills_by_id, groups_by_id, user_email):
    expenses = []

    for pendency in pendencies:
        bill_id = str(pendency.get("bill_id"))
        bill = bills_by_id.get(bill_id)
        if not bill:
            continue
        if not _is_confirmed_group_expense(pendency, bill):
            continue

        group_id = str(bill.get("group_id"))
        group = groups_by_id.get(group_id, {})
        role = "creditor" if pendency.get("creditor_email") == user_email else "debtor"
        date = _get_pendency_date(pendency, bill)

        expenses.append(
            _serialize(
                {
                    "_id": pendency.get("_id"),
                    "bill_id": bill_id,
                    "group_id": group_id,
                    "group_name": group.get("name"),
                    "category": bill.get("bill_type") or "Sem categoria",
                    "value": _to_number(pendency.get("value")),
                    "date": date,
                    "role": role,
                    "debtor_email": pendency.get("debtor_email"),
                    "creditor_email": pendency.get("creditor_email"),
                    "debtor_confirmed_at": pendency.get("debtor_confirmed_at"),
                    "creditor_confirmed_at": pendency.get("creditor_confirmed_at"),
                    "resolved_at": pendency.get("resolved_at"),
                }
            )
        )

    return sorted(
        expenses,
        key=lambda item: _date_key(item.get("date")),
        reverse=True,
    )


def _extract_due_expenses(pendencies, bills_by_id, groups_by_id, user_email):
    due_expenses = []

    for pendency in pendencies:
        bill_id = str(pendency.get("bill_id"))
        bill = bills_by_id.get(bill_id)
        if not bill:
            continue

        due_date = bill.get("due_date")
        if not due_date:
            continue

        group_id = str(bill.get("group_id"))
        group = groups_by_id.get(group_id, {})
        role = "creditor" if pendency.get("creditor_email") == user_email else "debtor"
        resolved = _is_confirmed_group_expense(pendency, bill)
        due_expenses.append(
            _serialize(
                {
                    "_id": pendency.get("_id"),
                    "bill_id": bill_id,
                    "group_id": group_id,
                    "group_name": group.get("name"),
                    "category": bill.get("bill_type") or "Sem categoria",
                    "value": _to_number(pendency.get("value")),
                    "due_date": due_date,
                    "role": role,
                    "resolved": resolved,
                    "debtor_email": pendency.get("debtor_email"),
                    "creditor_email": pendency.get("creditor_email"),
                    "debtor_confirmed": pendency.get("debtor_confirmed"),
                    "creditor_confirmed": pendency.get("creditor_confirmed"),
                    "resolved_at": pendency.get("resolved_at"),
                }
            )
        )

    return sorted(
        due_expenses,
        key=lambda item: _date_key(item.get("due_date")),
    )


def get_personal_summary_service(user_email):
    try:
        groups = list(
            mongo["groups"].find(
                {"members": user_email},
                {"_id": 1, "name": 1},
            )
        )
        group_ids = [str(group["_id"]) for group in groups]
        groups_by_id = {str(group["_id"]): group for group in groups}

        goals = []
        if group_ids:
            goals = list(mongo["goals"].find({"group_id": {"$in": group_ids}}))

        bills = []
        pendencies = []
        if group_ids:
            bills = list(mongo["bills"].find({"group_id": {"$in": group_ids}}))
            bill_ids = [str(bill["_id"]) for bill in bills]
            if bill_ids:
                pendencies = list(
                    mongo["pendencies"].find(
                        {
                            "bill_id": {"$in": bill_ids},
                            "$or": [
                                {"debtor_email": user_email},
                                {"creditor_email": user_email},
                            ],
                        }
                    )
                )

        bills_by_id = {str(bill["_id"]): bill for bill in bills}
        contributions = _extract_user_contributions(goals, groups_by_id, user_email)
        group_expenses = _extract_confirmed_group_expenses(
            pendencies,
            bills_by_id,
            groups_by_id,
            user_email,
        )
        due_expenses = _extract_due_expenses(
            pendencies,
            bills_by_id,
            groups_by_id,
            user_email,
        )

        total_expenses = sum(
            _to_number(expense.get("value")) for expense in group_expenses
        )
        total_paid = sum(
            _to_number(expense.get("value"))
            for expense in group_expenses
            if expense.get("role") == "debtor"
        )
        total_received = sum(
            _to_number(expense.get("value"))
            for expense in group_expenses
            if expense.get("role") == "creditor"
        )
        total_contributions = sum(
            _to_number(contribution.get("value")) for contribution in contributions
        )

        return {
            "expenses": group_expenses,
            "due_expenses": due_expenses,
            "contributions": contributions,
            "summary": {
                "total_expenses": round(total_expenses, 2),
                "total_paid": round(total_paid, 2),
                "total_received": round(total_received, 2),
                "total_contributions": round(total_contributions, 2),
                "expense_count": len(group_expenses),
                "contribution_count": len(contributions),
                "group_count": len(groups),
            },
            "charts": {
                "expenses_by_category": _build_expenses_by_category(group_expenses),
                "contributions_by_goal": _build_contributions_by_goal(contributions),
                "monthly_flow": _build_monthly_flow(group_expenses, contributions),
            },
        }, None
    except Exception as e:
        return None, {"error": str(e)}
