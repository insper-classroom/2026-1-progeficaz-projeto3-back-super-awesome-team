from datetime import datetime


class Bill:
    def __init__(
        self,
        bill_type,
        total_value,
        group_id,
        pix_key,
        members_to_pay,
        created_by,
        is_paid=False,
        due_date=None,
    ):
        if not bill_type:
            raise ValueError("Tipo de conta é obrigatório")
        if not total_value or total_value <= 0:
            raise ValueError("Valor total deve ser maior que zero")
        if not group_id:
            raise ValueError("ID do grupo é obrigatório")
        if not pix_key or not str(pix_key).strip():
            raise ValueError("Chave PIX é obrigatória")
        if not members_to_pay or len(members_to_pay) == 0:
            raise ValueError("Pelo menos um membro deve pagar a conta")
        if not created_by:
            raise ValueError("Usuário criador é obrigatório")

        self.bill_type = bill_type
        self.total_value = total_value
        self.group_id = group_id
        self.pix_key = str(pix_key).strip()
        self.members_to_pay = members_to_pay
        self.created_by = created_by
        self.is_paid = is_paid
        self.due_date = due_date
        self.created_at = datetime.utcnow()

    def to_dictionary(self):
        return {
            "bill_type": self.bill_type,
            "total_value": self.total_value,
            "group_id": self.group_id,
            "pix_key": self.pix_key,
            "members_to_pay": self.members_to_pay,
            "created_by": self.created_by,
            "is_paid": self.is_paid,
            "due_date": self.due_date,
            "created_at": self.created_at,
        }
