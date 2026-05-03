from datetime import datetime


class Group:
    def __init__(self, name, members, created_by, description=None):
        if not name:
            raise ValueError("Nome obrigatório")
        if not members or len(members) == 0:
            raise ValueError("Pelo menos um membro é obrigatório")
        if not created_by:
            raise ValueError("Criador do grupo é obrigatório")

        self.name = name
        self.members = members
        self.created_by = created_by
        self.description = description
        self.created_at = datetime.utcnow()

    def to_dictionary(self):
        return {
            "name": self.name,
            "members": self.members,
            "created_by": self.created_by,
            "description": self.description,
            "created_at": self.created_at,
        }
