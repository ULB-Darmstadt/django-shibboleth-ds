import json
import pytest

from urllib.parse import parse_qs
from urllib.parse import urlparse
from urllib.parse import urlunparse
from django.conf import settings
from django.urls import reverse

from shibboleth_discovery.helpers import select2_processor
from shibboleth_discovery.utils import b64encode_idp

from .test_utils import SEARCH_SCENARIOS


SEARCH_SCENARIOS[1] = ([''], []) # Empty list does not return a result
SEARCH_SCENARIOS += [
        # Additional whitespace characters are eliminated
        (
            ['Darmstadt   \t'], ['https://idp.hrz.tu-darmstadt.de/idp/shibboleth']
        ),
        (
            ['\t'], []
        ),
    ]

class TestSearchView:

    @pytest.mark.parametrize('tokens, expected', SEARCH_SCENARIOS)
    def test_search(self, tokens, expected, client):
        url = reverse('shib_ds:search') + "?{}=".format(settings.SHIB_DS_QUERY_PARAMETER) + " ".join(tokens)
        r = client.get(url)
        results = [result.get('entity_id') for result in json.loads(r.content.decode('utf-8')).get('results')]
        assert results == expected

    @pytest.mark.parametrize('language, expected', [('en', 'Bochum University Of Applied Sciences'), ('de', 'Hochschule Bochum')])
    def test_search_localization(self, language, expected, client):
        client.cookies.load({settings.LANGUAGE_COOKIE_NAME : language})
        url = reverse('shib_ds:search') + "?q=Bochum"
        r = client.get(url)
        assert json.loads(r.content.decode('utf-8')).get('results')[0].get('name') == expected
        assert json.loads(r.content.decode('utf-8')).get('results')[0].get('description') == expected

    @pytest.mark.parametrize('token, expected', [('Kassel', None), ('Bochum', 'https://idp.hs-bochum.de/aai/bo-logo.jpg')])
    def test_search_logo(self,token, expected, client):
        url = reverse('shib_ds:search') + "?q=" + token
        r = client.get(url)
        assert json.loads(r.content.decode('utf-8')).get('results')[0].get('logo') == expected

    def test_search_query_parameter(self, settings, client):
        param = 'spam'
        settings.SHIB_DS_QUERY_PARAMETER = param
        url = reverse('shib_ds:search') + "?{}=Kassel".format(param)
        r = client.get(url)
        assert json.loads(r.content.decode('utf-8')).get('results') != []


    def test_search_max_results(self, settings, client):
        settings.SHIB_DS_MAX_RESULTS = 1
        url = reverse('shib_ds:search') + "?q=a"
        r = client.get(url)
        assert len(json.loads(r.content.decode('utf-8')).get('results')) == 1


    def test_select2_post_processor(self, client, settings):
        settings.SHIB_DS_POST_PROCESSOR = select2_processor
        url = reverse('shib_ds:search') + "?q=Bochum"
        r = client.get(url)
        assert json.loads(r.content.decode('utf-8')).get('results')[0].get('id') == 'https://idp.hs-bochum.de/idp/shibboleth'
        assert json.loads(r.content.decode('utf-8')).get('results')[0].get('text') == 'Bochum University Of Applied Sciences'


class TestSetCookieView:

    def test_set_cookie(self, client):
        # We do not have a cookie set
        assert client.cookies.get(settings.SHIB_DS_COOKIE_NAME) is None

        idp_da = 'https://idp.hrz.tu-darmstadt.de/idp/shibboleth'
        idp_ks = 'https://idp.hrz.uni-kassel.de/idp/shibboleth-idp'

        # First we set a cookie
        r = client.post(reverse('shib_ds:remember-idp'), {'entity_id': idp_da}, 'application/json')
        assert r.status_code == 200
        assert client.cookies.get(settings.SHIB_DS_COOKIE_NAME).value == b64encode_idp(idp_da)

        # If we set the cookie again, nothing changes
        r = client.post(reverse('shib_ds:remember-idp'), {'entity_id': idp_da}, 'application/json')
        assert r.status_code == 200
        assert client.cookies.get(settings.SHIB_DS_COOKIE_NAME).value == b64encode_idp(idp_da)

        # We set another idp cookie, this must be first
        r = client.post(reverse('shib_ds:remember-idp'), {'entity_id': idp_ks}, 'application/json')
        assert r.status_code == 200
        assert client.cookies.get(settings.SHIB_DS_COOKIE_NAME).value == ' '.join([b64encode_idp(idp_ks), b64encode_idp(idp_da)])

    def test_max_idps(self, client, settings):
        settings.SHIB_DS_MAX_IDP = 1
        idp_da = 'https://idp.hrz.tu-darmstadt.de/idp/shibboleth'
        idp_ks = 'https://idp.hrz.uni-kassel.de/idp/shibboleth-idp'
        client.post(reverse('shib_ds:remember-idp'), {'entity_id': idp_da}, 'application/json')
        client.post(reverse('shib_ds:remember-idp'), {'entity_id': idp_ks}, 'application/json')
        assert client.cookies.get(settings.SHIB_DS_COOKIE_NAME).value == b64encode_idp(idp_ks)

    def test_invalid_json(self, client):
        r = client.post(reverse('shib_ds:remember-idp'), 'This is not JSON', 'text/plain')
        assert r.status_code == 400

    def test_missing_entity_id(self, client):
        r = client.post(reverse('shib_ds:remember-idp'), {'spam' : 'ham'}, 'application/json')
        assert r.status_code == 400

    def test_entity_not_found(self, client):
        r = client.post(reverse('shib_ds:remember-idp'), {'entity_id' : 'ham'}, 'application/json')
        assert r.status_code == 400


class TestRedirectView:
    """
    Groups tests about redirect
    """

    def test_redirect(self, client):
        """
        We pass a valid entityID, so that there should be a redirect and a cookie
        """
        idp_da = 'https://idp.hrz.tu-darmstadt.de/idp/shibboleth'
        r = client.get(reverse('shib_ds:redirect'), {'entityID' : idp_da, 'next' : 'spam'})
        assert r.status_code == 302
        parts = urlparse(r.url)
        params = parse_qs(parts.query)
        assert settings.SHIB_DS_SP_URL == urlunparse([parts.scheme, parts.netloc, parts.path, '','',''])
        assert params.get('entityID')[0] == idp_da
        assert params.get('target')[0] == 'https://testserver/spam'
        assert client.cookies.get(settings.SHIB_DS_COOKIE_NAME).value == b64encode_idp(idp_da)

    def test_entity_id_missing(self, client):
        r = client.get(reverse('shib_ds:redirect'))
        assert r.status_code == 400

    def test_entity_id_unknown(self, client):
        r = client.get(reverse('shib_ds:redirect'), {'entityID' : 'spam'})
        assert r.status_code == 400
