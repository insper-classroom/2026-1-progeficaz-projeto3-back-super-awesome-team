from marshmallow import Schema, fields, validate


class GroupSchema(Schema):
    name = fields.Str(required=True)
    members = fields.List(fields.Str(), required=False, validate=validate.Length(min=0))
    description = fields.Str(required=False)
