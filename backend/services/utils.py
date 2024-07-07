"""Служебные функции . """


def format_date(date):
    # возвращает дату сеанса в отформатированном виде
    months = [
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    ]
    day = date.day
    month = months[date.month - 1]
    year = date.year

    return f"{day} {month} {year}"
