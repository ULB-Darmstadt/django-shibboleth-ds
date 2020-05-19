import json

from datetime import datetime
from datetime import timedelta

from django.core.cache import cache
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.views.generic.base import View

from .conf import COOKIE_NAME
from .conf import settings
from .utils import b64decode_idp, b64encode_idp
from .utils import prepare_data
from .utils import search


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
            idps = [b64decode_idp(idp) for idp in request.COOKIES.get(COOKIE_NAME, '').split(' ') if idp]
            # We delete the entity_id / IdP from the list and then append the list to our new entity id.
            # This way, the new entity id is the first
            try:
                idps.remove(entity_id)
            except ValueError:
                pass

            idps = [b64encode_idp(idp) for idp in [entity_id] + idps]
            # We set the cookie, then return the HttpResponse
            response = HttpResponse()

            response.set_cookie(
                COOKIE_NAME,
                value=' '.join(idps[:settings.SHIB_DS_MAX_IDP]),
                expires=datetime.now() + timedelta(days=365),
            )
            return response
        else:
            return HttpResponseBadRequest("EntityID does not exist.")
