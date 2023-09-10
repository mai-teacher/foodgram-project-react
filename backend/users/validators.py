from rest_framework.serializers import ValidationError


def validate_me(username):
    if username == "me":
        raise ValidationError('Пользователя нельзя называть "me".')
    return username
