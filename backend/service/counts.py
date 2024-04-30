"""Функции для расчетов . """


import random
import string


def generate_id():
    """Генерирует 8-значный код для id комнаты/сеанса . """
    characters = string.ascii_letters + string.digits
    id = ''.join(random.choice(characters) for _ in range(8))
    return id
