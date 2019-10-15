from django.conf import settings

DEFAULT_DATETIME_INPUT_FORMAT = getattr(
    settings, 'DEFAULT_DATETIME_INPUT_FORMAT', '%d/%m/%Y %H:%M')

DEFAULT_DATE_INPUT_FORMAT = getattr(
    settings, 'DEFAULT_DATE_INPUT_FORMAT', '%d/%m/%Y')

FEED_HEADER_SIZE = getattr(
    settings, 'FEED_HEADER_SIZE', {'event': [1920, 500], 'news': [1920, 1000]})

