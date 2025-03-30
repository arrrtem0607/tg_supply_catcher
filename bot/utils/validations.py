import re

def normalize_phone_number(raw_phone: str) -> str:
    # Удаляем все символы, кроме цифр
    digits = re.sub(r"\D", "", raw_phone)

    # Приводим к формату на 7 (если начинается с 8 или 7)
    if digits.startswith("8"):
        digits = "7" + digits[1:]
    elif digits.startswith("7"):
        pass
    elif digits.startswith("9") and len(digits) == 10:
        # Если ввели без кода (например, 9991234567) — добавляем 7
        digits = "7" + digits

    # Проверка длины
    if len(digits) != 11:
        raise ValueError(f"❌ Некорректный номер телефона: {raw_phone}")

    return digits
