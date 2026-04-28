from ..models import Bill
from ..extensions import mongo
from ..schemas import BillSchema
from bson.objectid import ObjectId

schema = BillSchema()

def create_bill_service(data):
    erros = schema.validate(data)
    if erros:
        return None, erros
    
    try:
        group = mongo['groups'].find_one({'_id': ObjectId(data["group_id"])})
        if not group:
            return None, {'error': 'Grupo não encontrado'}
        
        for member in data["members_to_pay"]:
            if member not in group['members']:
                return None, {'error': f'Membro {member} não pertence ao grupo'}
        
        bill = Bill(data["bill_type"], data["value"], data["group_id"], data["members_to_pay"])
        result = mongo['bills'].insert_one(bill.to_dictionary())
        
        return {'message': 'Conta criada com sucesso', 'bill_id': str(result.inserted_id)}, None
    except ValueError as e:
        return None, {'error': str(e)}
    except Exception as e:
        return None, {'error': str(e)}
