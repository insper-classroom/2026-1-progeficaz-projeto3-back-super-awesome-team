from marshmallow import Schema, fields, validate


class GoalSchema(Schema):
    name = fields.Str(required=True)
    target_value = fields.Float(required=True, validate=validate.Range(min=0.01))
    group_id = fields.Str(required=True)
    due_date = fields.Date(required=False, allow_none=True)
    description = fields.Str(required=False, allow_none=True)
    icon = fields.Str(required=False, allow_none=True)
    members = fields.List(fields.Str(), required=False, validate=validate.Length(min=0))
    current_value = fields.Float(required=False, validate=validate.Range(min=0))


class GoalContributionSchema(Schema):
    value = fields.Float(required=True, validate=validate.Range(min=0.01))
    member_email = fields.Str(required=False)
    contributed_at = fields.DateTime(required=False)
