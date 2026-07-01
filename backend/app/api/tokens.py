import secrets


def generate_confirm_token() -> str:
    return secrets.token_urlsafe(32)


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def generate_unsubscribe_token() -> str:
    return secrets.token_urlsafe(32)
