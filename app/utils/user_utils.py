from ..extensions import mongo


def get_user_by_email(email):
    try:
        return mongo["users"].find_one({"email": email})
    except Exception as e:
        print(f"Erro ao buscar usuário pelo email: {str(e)}")
        return None
