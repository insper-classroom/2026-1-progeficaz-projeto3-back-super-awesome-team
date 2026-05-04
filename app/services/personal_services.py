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
        category = expense.get("expense_type") or "Sem categoria"
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
        month = _month_key(expense.get("expense_date"))
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


def get_personal_summary_service(user_email):
    try:
        expenses = list(mongo["expenses"].find({"user_email": user_email}))
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

        serialized_expenses = sorted(
            (_serialize(deepcopy(expense)) for expense in expenses),
            key=lambda item: _date_key(item.get("expense_date")),
            reverse=True,
        )
        contributions = _extract_user_contributions(goals, groups_by_id, user_email)

        total_expenses = sum(_to_number(expense.get("value")) for expense in expenses)
        total_contributions = sum(
            _to_number(contribution.get("value")) for contribution in contributions
        )

        return {
            "expenses": serialized_expenses,
            "contributions": contributions,
            "summary": {
                "total_expenses": round(total_expenses, 2),
                "total_contributions": round(total_contributions, 2),
                "balance": round(total_contributions - total_expenses, 2),
                "expense_count": len(serialized_expenses),
                "contribution_count": len(contributions),
            },
            "charts": {
                "expenses_by_category": _build_expenses_by_category(expenses),
                "contributions_by_goal": _build_contributions_by_goal(contributions),
                "monthly_flow": _build_monthly_flow(expenses, contributions),
            },
        }, None
    except Exception as e:
        return None, {"error": str(e)}
