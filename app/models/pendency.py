from datetime import datetime

class Pendency:
    def __init__(self, bill_id, debtor_id, creditor_id, value, debtor_confirmed=False, creditor_confirmed=False):
        if not bill_id:
            raise ValueError("Bill ID é obrigatório")
        if not debtor_id:
            raise ValueError("ID do devedor é obrigatório")
        if not creditor_id:
            raise ValueError("ID do credor é obrigatório")
        if not value or value <= 0:
            raise ValueError("Valor deve ser maior que zero")
        if debtor_id == creditor_id:
            raise ValueError("Devedor e credor não podem ser a mesma pessoa")

        self.bill_id = bill_id
        self.debtor_id = debtor_id
        self.creditor_id = creditor_id
        self.value = value
        self.debtor_confirmed = debtor_confirmed
        self.creditor_confirmed = creditor_confirmed
        self.created_at = datetime.utcnow()

    def to_dictionary(self):
        return {
            "bill_id": self.bill_id,
            "debtor_id": self.debtor_id,
            "creditor_id": self.creditor_id,
            "value": self.value,
            "debtor_confirmed": self.debtor_confirmed,
            "creditor_confirmed": self.creditor_confirmed,
            "created_at": self.created_at
        }
