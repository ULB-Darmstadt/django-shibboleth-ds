import json
import re
import requests

from base64 import b64decode, b64encode

from django.core.cache import cache
from django.utils import translation

from .conf import COOKIE_NAME
from .conf import settings

def b64decode_idp(idp):
    """
    Decodes an idp from base64 to string
    :param idp: base64 encoded string object
    :return: string object
    """
    return str(b64decode(idp.encode('utf-8')), 'utf-8')

def b64encode_idp(idp):
    """
    Encodes an idp from base64 to string
    :param idp: string object
    :return: base64 encoded string object
    """
    return str(b64encode(idp.encode('utf-8')), 'utf-8')

def get_feed_by_url(url):
    """
    This fetches the feed from a given URL
    :param url: A (valid) URL
    :return: DiscoFeed as python object
    """
    try:
        r = requests.get(
            url,
            timeout=5
        )
        return r.json()
    except:
        raise Exception("Could not reach DiscoFeed or received invalid JSON")

def get_feed_by_path(path):
    """
    This fetches the feed from a given path
    :param path: Full path to file
    :return: DiscoFeed as python object
    """
    try:
        with open(path, 'r') as fin:
            return json.load(fin)
    except:
        raise Exception("Could not read file or received invalid JSON")


def get_feed():
    """
    This fetches the feed, either from a file or a remote
    :return: DiscoFeed as python object
    """
    if settings.SHIB_DS_DISCOFEED_URL:
        return get_feed_by_url(settings.SHIB_DS_DISCOFEED_URL)

    if settings.SHIB_DS_DISCOFEED_PATH:
        return get_feed_by_path(settings.SHIB_DS_DISCOFEED_PATH)


def get_largest_logo(logos):
    """
    Given a list of logos, this one finds the largest in terms of perimeter
    :param logos: List of logos
    :return: Largest logo or None
    """
    if len(logos) >= 1:
        logo = max(logos, key=lambda x: int(x.get('height', 0)) + int(x.get('width', 0))).get('value')
        return logo


def prepare_data():
    """
    This function prepares the data.
    The strategy is the following:
    We assign to each IdP a unique id (integer).
    Then we create two lists
    The first one containes structered informationen about the IdP (entityId, name, logo)
    The second one is for easyily finding matches
    :return: Tuple containing the DiscoFeed and list of names
    """
    feed = get_feed()

    idps = [
        {
            'entity_id' : idp.get('entityID'),
            'name' : {
                entry.get('lang'):entry.get('value') for entry in idp.get('DisplayNames', [])
            },
            'description' : {
                entry.get('lang'):entry.get('value') for entry in idp.get('Descriptions', [])
            },
            'logo' : get_largest_logo(idp.get('Logos', []))

        }
        for idp in feed
    ]

    index = [' '.join(idp.get('name', {}).values()).strip().lower() for idp in idps]

    return (idps, index)


def localize_idp(idp):
    """
    Localizes a given IdP, e.g. try to set a locale string. Else English string is used
    :param idp: IdP as prepared by prepare_data
    :return: IdP with local names
    """
    language = translation.get_language()
    idp['name'] = idp.get('name', {}).get(language, idp.get('name', {}).get('en', ''))
    idp['description'] = idp.get('description', {}).get(language, idp.get('description', {}).get('en', ''))
    return idp


def search(tokens):
    """
    Searches in the cached index after the tokens and returns the localized result
    :param tokens: list of token (empty token matches)
    :return: list of entityIds
    """
    # No token shall lead to no result
    if not tokens:
        return []

    tokens = [token.lower().strip() for token in tokens]

    idps, index = cache.get_or_set(
        'shib_ds',
        prepare_data(),
        timeout=settings.SHIB_DS_CACHE_DURATION
    )

    result = [localize_idp(idp) for idp, idx in zip(idps, index) if all(token in idx for token in tokens)]

    return result


def get_context(request):
    """
    Takes a request and produces a dictionary containing various information, mainly a ServiceProvider login handler and IdPs from cookies
    """
    shib_ds = dict()

    # First we check if the entityID from settings and GET match if the first one is set
    if settings.SHIB_DS_ENTITY_ID and settings.SHIB_DS_ENTITY_ID != request.GET.get('entity_id'):
        shib_ds['error'] = 'entity_id'
    # If settings.SHIB_DS_ENTITY_ID is not set set or settings.SHIB_DS_ENTITY_ID is set and the values are identical, set entity_id
    else:
        shib_ds['entity_id'] = request.GET.get('entity_id') or settings.SHIB_DS_ENTITY_ID

    # Next we look for the policy. It must be one of settings.SHIB_DS_POLICIES or None
    # If no policy is given, the default must be used
    policy = request.GET.get('policy') or 'urn:oasis:names:tc:SAML:profiles:SSO:idpdiscovery-protocol:single'
    if policy in settings.SHIB_DS_POLICIES:
        shib_ds['policy'] = policy
    else:
        shib_ds['error'] = 'policy'

    # The return value is where to send the user client after choosing an IdP
    # Must satisfy any of some regexp, so that forwarding is to the desired SP
    # If no return value is set, settings.DEFAULT_RETURN is used
    return_val = request.GET.get('return') or settings.SHIB_DS_DEFAULT_RETURN
    if return_val and len(settings.SHIB_DS_VALID_RETURN_PATTERN) == 0 or any(re.match(reg, return_val) for reg in settings.SHIB_DS_VALID_RETURN_PATTERN):
        shib_ds['return'] = return_val
    else:
        shib_ds['error'] = 'return'

    # If we get a returnIDParam passed use it, otherwise settings.SHIB_DS_RETURN_ID_PARAM
    shib_ds['return_id_param'] = request.GET.get('returnIDParam') or settings.SHIB_DS_RETURN_ID_PARAM

    # Recently used IdPs
    saved_idps = [b64decode_idp(idp) for idp in request.COOKIES.get(COOKIE_NAME, '').split(' ') if idp]
    idps, index = cache.get_or_set(
        'shib_ds',
        prepare_data(),
        timeout=settings.SHIB_DS_CACHE_DURATION
    )
    shib_ds['recent_idps'] = settings.SHIB_DS_POST_PROCESSOR(
        [
            localize_idp(idp) for idp in idps
            if any(saved_idp in idp.get('entity_id') for saved_idp in saved_idps)
        ]
    )

    # Check if isPassive was passed
    if request.GET.get('isPassive', '') == 'true':
        shib_ds['is_passive'] = True
    else:
        shib_ds['is_passive'] = False

    return shib_ds
