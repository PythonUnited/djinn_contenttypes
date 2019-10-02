from django.conf import settings

DEFAULT_DATETIME_INPUT_FORMAT = getattr(
    settings, 'DEFAULT_DATETIME_INPUT_FORMAT', '%d/%m/%Y %H:%M')

DEFAULT_DATE_INPUT_FORMAT = getattr(
    settings, 'DEFAULT_DATE_INPUT_FORMAT', '%d/%m/%Y')

FEED_HEADER_HIGH_SIZE = getattr(
    settings, 'FEED_HEADER_HIGH_SIZE', [1000, 500])

FEED_HEADER_NORMAL_SIZE = getattr(
    settings, 'FEED_HEADER_NORMAL_SIZE', [800, 600])