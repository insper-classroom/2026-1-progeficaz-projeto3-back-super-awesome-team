from datetime import datetime


class Expense:
    def __init__(self, expense_type, value, user_email, expense_date):
        if not expense_type:
            raise ValueError("Tipo de despesa é obrigatório")
        if not value or value <= 0:
            raise ValueError("Valor da despesa deve ser maior que zero")
        if not user_email:
            raise ValueError("Email do usuário é obrigatório")
        if not expense_date:
            raise ValueError("Data da despesa é obrigatória")

        self.expense_type = expense_type
        self.value = value
        self.user_email = user_email
        self.expense_date = expense_date
        self.created_at = datetime.utcnow()

    def to_dictionary(self):
        return {
            "expense_type": self.expense_type,
            "value": self.value,
            "user_email": self.user_email,
            "expense_date": self.expense_date,
            "created_at": self.created_at,
        }
