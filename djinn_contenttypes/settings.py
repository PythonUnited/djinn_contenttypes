from django.conf import settings

DEFAULT_DATETIME_INPUT_FORMAT = getattr(
    settings, 'DEFAULT_DATETIME_INPUT_FORMAT', '%d/%m/%Y %H:%M')

DEFAULT_DATE_INPUT_FORMAT = getattr(
    settings, 'DEFAULT_DATE_INPUT_FORMAT', '%d/%m/%Y')