from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class UserSchema(Schema):
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    confirm_password = fields.Str(required=True)
    image = fields.Str(required=False, allow_none=True, load_default=None)

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        if data.get("password") != data.get("confirm_password"):
            raise ValidationError(
                "As senhas não coincidem.", field_name="confirm_password"
            )


class UpdateUserSchema(Schema):
    name = fields.Str(required=False)
    password = fields.Str(required=False, validate=validate.Length(min=6))
    current_password = fields.Str(required=False)
    image = fields.Str(required=False, allow_none=True)


class DeleteUserSchema(Schema):
    password = fields.Str(
        required=False,
        allow_none=True,
        load_default=None,
    )
