from appconf import AppConf

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class ShibbolethDiscoveryConf(AppConf):

    CACHE_DURATION = 60*60*2 # 2 hours
    COOKIE_NAME = '_saml_idp'
    DISCOFEED_PATH = None
    DISCOFEED_URL = None
    MAX_RESULTS = 10
    MAX_IDP = 3
    POST_PROCESSOR = lambda x: x
    QUERY_PARAMETER = 'q'
    RETURN_ID_PARAM = 'entityID'
    TARGET_SP_URL = ''

    class Meta:
        prefix = 'shib_ds'

# SHIB_DS_TARGET_SP_URL must be set
if not settings.SHIB_DS_TARGET_SP_URL:
    raise ImproperlyConfigured("TARGET SP URL for redirect to IdP missing")

# Either SHIB_DS_DISCOFEED_URL or SHIB_DS_DISCOFEED_PATH must be set
if not settings.SHIB_DS_DISCOFEED_URL and not settings.SHIB_DS_DISCOFEED_PATH:
    raise ImproperlyConfigured("No source to DiscoFeed provided. Please set either SHIB_DS_DISCOFEED_URL or SHIB_DS_DISCOFEED_PATH")

# SHIB_DS_RETURN_ID_PARAM must be set, since this this is rarely overwridden by GET parameter
if not settings.SHIB_DS_RETURN_ID_PARAM:
    raise ImproperlyConfigured("No returnIDParam set. Please set SHIB_DS_RETURN_ID_PARAM")


