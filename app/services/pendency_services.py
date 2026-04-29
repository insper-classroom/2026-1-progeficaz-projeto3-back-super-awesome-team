from ..models import Pendency
from ..extensions import mongo
from ..schemas import PendencySchema
from bson.objectid import ObjectId

schema = PendencySchema()

def create_pendencies_for_bill(bill_id, creditor_email, members_to_pay):
    try:
        pendencies = []
        for member_data in members_to_pay:
            member_email = member_data["email"]
            member_value = member_data["value"]
            
            if member_email == creditor_email:
                continue
            
            pendency = Pendency(
                bill_id=bill_id,
                debtor_email=member_email,
                creditor_email=creditor_email,
                value=member_value
            )
            result = mongo['pendencies'].insert_one(pendency.to_dictionary())
            pendencies.append(str(result.inserted_id))
        
        return pendencies, None
    except ValueError as e:
        return None, {'error': str(e)}
    except Exception as e:
        return None, {'error': str(e)}


def confirm_debtor_payment_service(pendency_id, user_email):
    try:
        pendency = mongo['pendencies'].find_one({'_id': ObjectId(pendency_id)})
        
        if not pendency:
            return None, {'error': 'Pendência não encontrada'}
        
        if pendency['debtor_email'] != user_email:
            return None, {'error': 'Apenas o devedor pode confirmar o pagamento'}
        
        mongo['pendencies'].update_one(
            {'_id': ObjectId(pendency_id)},
            {'$set': {'debtor_confirmed': True}}
        )
        
        return {'message': 'Confirmação do devedor registrada'}, None
    except Exception as e:
        return None, {'error': str(e)}


def confirm_creditor_payment_service(pendency_id, user_email):
    try:
        pendency = mongo['pendencies'].find_one({'_id': ObjectId(pendency_id)})
        
        if not pendency:
            return None, {'error': 'Pendência não encontrada'}
        
        if pendency['creditor_email'] != user_email:
            return None, {'error': 'Apenas o credor pode confirmar o recebimento'}
        
        mongo['pendencies'].update_one(
            {'_id': ObjectId(pendency_id)},
            {'$set': {'creditor_confirmed': True}}
        )
        
        return {'message': 'Confirmação do credor registrada'}, None
    except Exception as e:
        return None, {'error': str(e)}


def get_user_pendencies_service(user_email):
    try:
        pendencies_as_debtor = list(mongo['pendencies'].find({'debtor_email': user_email}))
        pendencies_as_creditor = list(mongo['pendencies'].find({'creditor_email': user_email}))
        
        # Convert ObjectId to string for JSON serialization
        for p in pendencies_as_debtor + pendencies_as_creditor:
            p['_id'] = str(p['_id'])
            p['bill_id'] = str(p['bill_id'])
        
        return {
            'as_debtor': pendencies_as_debtor,
            'as_creditor': pendencies_as_creditor
        }, None
    except Exception as e:
        return None, {'error': str(e)}


def get_bill_pendencies_service(bill_id):
    try:
        pendencies = list(mongo['pendencies'].find({'bill_id': bill_id}))
        
        # Convert ObjectId to string for JSON serialization
        for p in pendencies:
            p['_id'] = str(p['_id'])
            p['bill_id'] = str(p['bill_id'])
        
        return pendencies, None
    except Exception as e:
        return None, {'error': str(e)}


def get_pendency_service(pendency_id):
    try:
        pendency = mongo['pendencies'].find_one({'_id': ObjectId(pendency_id)})
        
        if not pendency:
            return None, {'error': 'Pendência não encontrada'}
        
        pendency['_id'] = str(pendency['_id'])
        pendency['bill_id'] = str(pendency['bill_id'])
        
        return pendency, None
    except Exception as e:
        return None, {'error': str(e)}
