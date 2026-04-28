from marshmallow import Schema, fields, validate

class GroupSchema(Schema):
    name = fields.Str(required=True)
    members = fields.List(fields.Str(), required=True, validate=validate.Length(min=1))
    description = fields.Str(required=False)
