from django.core.validators import RegexValidator


def validate_name(value):
    """Check that name has min 2 letters, only letters."""
    validator = RegexValidator(
        regex=r"^[a-zа-яё]{2,}$",
        message="Имя должно содержать только буквы, минимум 2 буквы",
    )
    validator(value.lower())
