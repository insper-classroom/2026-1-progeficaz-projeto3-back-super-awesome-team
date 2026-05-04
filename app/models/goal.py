from datetime import datetime


class Goal:
    def __init__(
        self,
        name,
        target_value,
        group_id,
        created_by,
        members,
        due_date=None,
        description=None,
        icon=None,
        current_value=0,
    ):
        if not name:
            raise ValueError("Nome da meta é obrigatório")
        if not target_value or target_value <= 0:
            raise ValueError("Valor alvo deve ser maior que zero")
        if not group_id:
            raise ValueError("ID do grupo é obrigatório")
        if not created_by:
            raise ValueError("Usuário criador é obrigatório")
        if not members or len(members) == 0:
            raise ValueError("Pelo menos um membro é obrigatório")

        self.name = name
        self.target_value = target_value
        self.group_id = group_id
        self.created_by = created_by
        self.members = members
        self.due_date = due_date
        self.description = description
        self.icon = icon
        self.current_value = current_value
        self.contributions = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dictionary(self):
        return {
            "name": self.name,
            "target_value": self.target_value,
            "group_id": self.group_id,
            "created_by": self.created_by,
            "members": self.members,
            "due_date": self.due_date,
            "description": self.description,
            "icon": self.icon,
            "current_value": self.current_value,
            "contributions": self.contributions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
