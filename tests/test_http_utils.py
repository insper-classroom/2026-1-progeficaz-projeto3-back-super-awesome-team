from app.utils.http_utils import http_status_for_service_error


def test_non_dict_returns_500():
    assert http_status_for_service_error("string error") == 500
    assert http_status_for_service_error(None) == 500
    assert http_status_for_service_error(404) == 500


def test_empty_dict_returns_500():
    assert http_status_for_service_error({}) == 500


def test_dict_without_error_key_returns_400():
    assert http_status_for_service_error({"message": "ok"}) == 400


def test_non_string_error_value_returns_400():
    assert http_status_for_service_error({"error": 404}) == 400
    assert http_status_for_service_error({"error": None}) == 400


def test_not_found_errors_return_404():
    assert http_status_for_service_error({"error": "Grupo não encontrado"}) == 404
    assert http_status_for_service_error({"error": "Conta não encontrada"}) == 404
    assert http_status_for_service_error({"error": "Despesa não encontrada"}) == 404
    assert http_status_for_service_error({"error": "Pendência não encontrada"}) == 404
    assert http_status_for_service_error({"error": "Meta não encontrada"}) == 404
    assert http_status_for_service_error({"error": "Usuário ghost@example.com não encontrado"}) == 404


def test_permission_errors_return_403():
    assert http_status_for_service_error({"error": "Você não tem permissão para acessar esta conta"}) == 403
    assert http_status_for_service_error({"error": "Você não tem permissão para editar esta despesa"}) == 403
    assert http_status_for_service_error({"error": "Apenas o criador da conta pode editá-la"}) == 403
    assert http_status_for_service_error({"error": "Apenas o criador da conta pode deletá-la"}) == 403
    assert http_status_for_service_error({"error": "Apenas o criador da conta pode marcá-la como paga"}) == 403
    assert http_status_for_service_error({"error": "Apenas o criador do grupo pode deletá-lo"}) == 403
    assert http_status_for_service_error({"error": "Apenas o criador do grupo pode editá-lo"}) == 403
    assert http_status_for_service_error({"error": "Apenas o devedor pode confirmar o pagamento"}) == 403
    assert http_status_for_service_error({"error": "Apenas o credor pode confirmar o recebimento"}) == 403
    assert http_status_for_service_error({"error": "Você não é membro deste grupo"}) == 403


def test_conflict_errors_return_409():
    assert http_status_for_service_error({"error": "Não é possível excluir a conta: você criou grupos."}) == 409
    assert http_status_for_service_error({"error": "Não é possível deletar o grupo: o grupo possui outros membros."}) == 409
    assert http_status_for_service_error({"error": "Não é possível editar uma conta já paga"}) == 409
    assert http_status_for_service_error({"error": "Não é possível remover member@example.com pois está vinculado a bills não pagas"}) == 409


def test_email_already_registered_returns_409():
    assert http_status_for_service_error({"error": "email já cadastrado"}) == 409
    assert http_status_for_service_error({"error": "Email já cadastrado"}) == 409


def test_generic_error_returns_400():
    assert http_status_for_service_error({"error": "Senha incorreta"}) == 400
    assert http_status_for_service_error({"error": "Nenhum campo alterado"}) == 400
    assert http_status_for_service_error({"error": "Chave PIX é obrigatória"}) == 400
