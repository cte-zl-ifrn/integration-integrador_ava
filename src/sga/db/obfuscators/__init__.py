def last4(value: str) -> str:
    """Exibe apenas os 4 últimos caracteres: ****1234"""
    return "****" + value[-4:]


def first4(value: str) -> str:
    """Exibe apenas os 4 primeiros caracteres: 1234****"""
    return value[:4] + "****"


def mask_all(value: str) -> str:
    """Oculta todos os caracteres: ********"""
    return "*" * len(value)


def middle(value: str) -> str:
    """Exibe os 2 primeiros e os 2 últimos, oculta o meio: AB****YZ"""
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def email(value: str) -> str:
    """Ofusca o nome de usuário de um e-mail: us**@exemplo.com"""
    if "@" not in value:
        return last4(value)
    user, domain = value.split("@", 1)
    masked_user = user[:2] + "*" * max(len(user) - 2, 0) if len(user) > 2 else "*" * len(user)
    return f"{masked_user}@{domain}"
