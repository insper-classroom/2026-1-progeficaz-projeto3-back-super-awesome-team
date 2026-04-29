from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))


class UpdateUserSchema(Schema):
    name = fields.Str(required=False)
    password = fields.Str(required=False, validate=validate.Length(min=6))
    current_password = fields.Str(required=False)
