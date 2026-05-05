def http_status_for_service_error(error):
    if not isinstance(error, dict) or not error:
        return 500
    if "error" not in error:
        return 400
    err = error["error"]
    if not isinstance(err, str):
        return 400

    if "não encontrad" in err:
        return 404

    if any(
        m in err
        for m in (
            "Você não tem permissão",
            "Apenas o criador da conta",
            "Apenas o criador do grupo",
            "Apenas o devedor",
            "Apenas o credor",
            "Você não é membro deste grupo",
        )
    ):
        return 403

    if any(
        m in err
        for m in (
            "Não é possível excluir",
            "Não é possível deletar",
            "Não é possível editar uma conta já paga",
            "Não é possível remover",
        )
    ):
        return 409

    if "email já cadastrado" in err.lower():
        return 409

    return 400
