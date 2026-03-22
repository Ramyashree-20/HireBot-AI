import re


def validate_email(email: str) -> bool:
    pattern = r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    digits = re.sub(r"[\s\-\(\)\+]", "", phone)
    return digits.isdigit() and 7 <= len(digits) <= 15
