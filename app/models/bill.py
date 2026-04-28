from datetime import datetime

class Bill:
    def __init__(self, bill_type, value, group_id, members_to_pay, created_by, is_paid=False):
        if not bill_type:
            raise ValueError("Tipo de conta é obrigatório")
        if not value or value <= 0:
            raise ValueError("Valor deve ser maior que zero")
        if not group_id:
            raise ValueError("ID do grupo é obrigatório")
        if not members_to_pay or len(members_to_pay) == 0:
            raise ValueError("Pelo menos um membro deve pagar a conta")
        if not created_by:
            raise ValueError("Usuário criador é obrigatório")

        self.bill_type = bill_type
        self.value = value
        self.group_id = group_id
        self.members_to_pay = members_to_pay
        self.created_by = created_by
        self.is_paid = is_paid
        self.created_at = datetime.utcnow()

    def to_dictionary(self):
        return {
            "bill_type": self.bill_type,
            "value": self.value,
            "group_id": self.group_id,
            "members_to_pay": self.members_to_pay,
            "created_by": self.created_by,
            "is_paid": self.is_paid,
            "created_at": self.created_at
        }
