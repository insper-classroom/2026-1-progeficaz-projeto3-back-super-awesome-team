from marshmallow import Schema, fields, validate


class MemberToPaySchema(Schema):
    email = fields.Str(required=True)
    value = fields.Float(required=True, validate=validate.Range(min=0.01))


class BillSchema(Schema):
    bill_type = fields.Str(required=True)
    total_value = fields.Float(required=True, validate=validate.Range(min=0.01))
    group_id = fields.Str(required=True)
    members_to_pay = fields.List(
        fields.Nested(MemberToPaySchema), required=True, validate=validate.Length(min=1)
    )
    is_paid = fields.Bool(required=False, load_default=False)
