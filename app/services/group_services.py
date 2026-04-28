from ..models.group import Group
from ..extensions import mongo
from ..schemas.group_schema import GroupSchema

schema = GroupSchema()

def create_group_service(data):
    erros = schema.validate(data)
    if erros:
        return None, erros
    
    try:
        group = Group(data["name"], data["members"], data.get("description"))
        mongo['groups'].insert_one(group.to_dictionary())
        return {'message': 'Grupo criado com sucesso'}, None
    except ValueError as e:
        return None, {'error': str(e)}
