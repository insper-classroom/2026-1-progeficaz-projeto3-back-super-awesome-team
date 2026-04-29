from marshmallow import Schema, fields, validate

class PendencySchema(Schema):
    bill_id = fields.Str(required=True)
    debtor_id = fields.Str(required=True)
    creditor_id = fields.Str(required=True)
    value = fields.Float(required=True, validate=validate.Range(min=0.01))
    debtor_confirmed = fields.Bool(required=False, load_default=False)
    creditor_confirmed = fields.Bool(required=False, load_default=False)
