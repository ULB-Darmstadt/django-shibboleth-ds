import json

from urllib.parse import urlencode
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.cache import cache
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.views.generic.base import View

from .utils import prepare_data
from .utils import search
from shibboleth_discovery.utils import set_cookie


class SearchView(View):
    """
    Finds all IdP that DisplayNames match all tokens.
    Tokens are passed as single GET argument with keyword settings.SHIB_DS_QUERY_PARAMETER
    """

    def get(self, request, *args, **kwargs):
        """
        Extracts the GET query string, triggers the search and returns a localized result
        """
        query = self.request.GET.get(settings.SHIB_DS_QUERY_PARAMETER, '')
        data = self.search(query)[:settings.SHIB_DS_MAX_RESULTS]

        return JsonResponse(
            {
                'results' : settings.SHIB_DS_POST_PROCESSOR(data)
            }
        )

    def search(self, query):
        """
        Performs the search and returns a list of IdP
        :param query: Search query
        :return: result as list
        """
        # As search tokens, we allow only non-empty strings
        # The search function itself takes empty strings, they match anything, we do not want that here
        tokens = [t for t in query.split(' ') if t.strip()]
        return search(tokens)


class SetCookieView(View):
    """
    Sets a cookie with IdP entity ID to remember for next login
    """

    def post(self, request, *args, **kwargs):
        """
        Sets a cookie with POST content
        """
        try:
            entity_id = json.loads(request.body.decode('utf-8')).get('entity_id', '')
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON.")

        if not entity_id:
            return HttpResponseBadRequest("EntityID must not be empty.")

        idps, index = cache.get_or_set(
            'shib_ds',
            prepare_data(),
            timeout=settings.SHIB_DS_CACHE_DURATION
        )
        # We allow only known entityIDs to be saved
        if entity_id in [idp.get('entity_id') for idp in idps]:
            response = HttpResponse()
            set_cookie(response, self.request, entity_id)
            return response
        else:
            return HttpResponseBadRequest("EntityID does not exist.")


class RedirectView(View):
    """
    This view does a redirect to the choosen IdP via the Shibboleth SP Deamon and checks in advance, if the choosen IdP is in the cache. If so, the view sets a cookie and redirects. Otherwise raises a HttpResponseBadRequest
    """

    def get(self, request, *args, **kwargs):
        """
        Does a simple check, sets a cookie and redirects
        """
        entity_id = request.GET.get('entityID')

        if not entity_id:
            return HttpResponseBadRequest("EntityID must not be empty.")

        idps, index = cache.get_or_set(
            'shib_ds',
            prepare_data(),
            timeout=settings.SHIB_DS_CACHE_DURATION
        )
        # We allow only known entityIDs to be saved
        if any(entity_id==idp.get('entity_id') for idp in idps):
            # We construct some more parameters for the Redirect
            target = urljoin('https://{}'.format(get_current_site(request)), request.GET.get('next', ''))
            params = {
                'target' : target,
                settings.SHIB_DS_RETURN_ID_PARAM : entity_id,
            }
            url = '{}?{}'.format(
                settings.SHIB_DS_SP_URL,
                urlencode(params)
            )

            response = HttpResponseRedirect(url)

            set_cookie(response, self.request, entity_id)

            return response
        else:
            return HttpResponseBadRequest("EntityID does not exist.")
