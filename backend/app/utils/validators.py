import re


def is_valid_symbol(symbol: str) -> bool:
    return bool(re.match(r"^[A-Z]{2}\d{6}$", symbol))


def sanitize_input(text: str, max_length: int = 500) -> str:
    cleaned = text.strip().replace("<", "").replace(">", "")
    return cleaned[:max_length]
