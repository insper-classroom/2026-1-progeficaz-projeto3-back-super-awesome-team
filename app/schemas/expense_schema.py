from marshmallow import Schema, fields, validate


class ExpenseSchema(Schema):
    expense_type = fields.Str(required=True)
    value = fields.Float(required=True, validate=validate.Range(min=0.01))
    expense_date = fields.DateTime(required=True)
