import json
import requests

from base64 import b64decode, b64encode
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.cache import cache
from django.utils import translation

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


def get_recent_idps(request):
    """
    Returns a list of recent IdPs formatted by SHIB_DS_POST_PROCESSOR
    """
    saved_idps = [b64decode_idp(idp) for idp in request.COOKIES.get(settings.SHIB_DS_COOKIE_NAME, '').split(' ') if idp]
    idps, index = cache.get_or_set(
        'shib_ds',
        prepare_data(),
        timeout=settings.SHIB_DS_CACHE_DURATION
    )
    recent_idps = settings.SHIB_DS_POST_PROCESSOR(
        [
            localize_idp(idp) for idp in idps
            if any(saved_idp == idp.get('entity_id') for saved_idp in saved_idps)
        ]
    )
    return recent_idps

def get_context(request):
    """
    Takes a request and returns a dictionary containing some information for context
    """
    shib_ds = {
        'recent_idps' : get_recent_idps(request),
        'return_id_param' : settings.SHIB_DS_RETURN_ID_PARAM,
        'sp_url' : settings.SHIB_DS_SP_URL,
        'target' : urljoin('https://{}'.format(get_current_site(request)), request.GET.get('next', '')),
    }
    return shib_ds
