from datetime import datetime


class Pendency:
    def __init__(
        self,
        bill_id,
        debtor_email,
        creditor_email,
        value,
        debtor_confirmed=False,
        creditor_confirmed=False,
    ):
        if not bill_id:
            raise ValueError("Bill ID é obrigatório")
        if not debtor_email:
            raise ValueError("Email do devedor é obrigatório")
        if not creditor_email:
            raise ValueError("Email do credor é obrigatório")
        if not value or value <= 0:
            raise ValueError("Valor deve ser maior que zero")
        if debtor_email == creditor_email:
            raise ValueError("Devedor e credor não podem ser a mesma pessoa")

        self.bill_id = bill_id
        self.debtor_email = debtor_email
        self.creditor_email = creditor_email
        self.value = value
        self.debtor_confirmed = debtor_confirmed
        self.creditor_confirmed = creditor_confirmed
        self.is_resolved = False
        self.created_at = datetime.utcnow()
        self.resolved_at = None

    def to_dictionary(self):
        return {
            "bill_id": self.bill_id,
            "debtor_email": self.debtor_email,
            "creditor_email": self.creditor_email,
            "value": self.value,
            "debtor_confirmed": self.debtor_confirmed,
            "creditor_confirmed": self.creditor_confirmed,
            "is_resolved": self.is_resolved,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }
