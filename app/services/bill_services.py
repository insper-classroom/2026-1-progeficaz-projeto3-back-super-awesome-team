from ..models import Bill
from ..extensions import mongo
from ..schemas import BillSchema
from .pendency_services import create_pendencies_for_bill
from bson.objectid import ObjectId

schema = BillSchema()

def create_bill_service(data, created_by):
    erros = schema.validate(data)
    if erros:
        return None, erros
    
    try:
        group = mongo['groups'].find_one({'_id': ObjectId(data["group_id"])})
        if not group:
            return None, {'error': 'Grupo não encontrado'}
        
        for member_data in data["members_to_pay"]:
            member_email = member_data["email"]
            if member_email not in group['members']:
                return None, {'error': f'Membro {member_email} não pertence ao grupo'}
        
        bill = Bill(
            data["bill_type"],
            data["total_value"],
            data["group_id"],
            data["members_to_pay"],
            created_by,
            data.get("is_paid", False)
        )
        result = mongo['bills'].insert_one(bill.to_dictionary())
        bill_id = str(result.inserted_id)
        
        pendencies, pendency_error = create_pendencies_for_bill(
            bill_id=bill_id,
            creditor_email=created_by,
            members_to_pay=data["members_to_pay"]
        )
        
        if pendency_error:
            mongo['bills'].delete_one({'_id': ObjectId(bill_id)})
            return None, pendency_error
        
        return {
            'message': 'Conta criada com sucesso',
            'bill_id': bill_id,
            'pendencies_created': len(pendencies)
        }, None
    except ValueError as e:
        return None, {'error': str(e)}
    except Exception as e:
        return None, {'error': str(e)}
