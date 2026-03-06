def parse_cop_to_int(raw: str) -> int:
    clean = (
        raw.replace(".", "")
        .replace(",", "")
        .replace(" ", "")
        .replace("$", "")
        .strip()
    )
    if clean == "" or not clean.isdigit():
        raise ValueError("Monto inválido")
    return int(clean)


def format_cop(amount: int) -> str:
    # 1234567 -> "1.234.567"
    return f"{amount:,}".replace(",", ".")