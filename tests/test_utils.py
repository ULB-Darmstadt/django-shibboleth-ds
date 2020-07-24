import json
import pytest
import responses

from django.conf import settings

from shibboleth_discovery.conf import COOKIE_NAME
from shibboleth_discovery.utils import b64decode_idp, b64encode_idp
from shibboleth_discovery.utils import get_context
from shibboleth_discovery.utils import get_feed
from shibboleth_discovery.utils import get_recent_idps
from shibboleth_discovery.utils import prepare_data
from shibboleth_discovery.utils import search

from tests.conftest import ENTITY_ID_TEST_CASES
from tests.conftest import POLICY_TEST_CASES
from tests.conftest import IS_PASSIVE_TEST_CASES
from tests.conftest import RECENT_IDP_SCENARIOS
from tests.conftest import RETURN_TEST_CASES


class TestIdPbase64():
    decoded = 'spam'
    encoded = 'c3BhbQ=='

    def test_decode(self):
        assert b64decode_idp(self.encoded) == self.decoded

    def test_encode(self):
        assert b64encode_idp(self.decoded) == self.encoded


class TestGetFeed():

    SHIB_DS_DISCOFEED_URL = 'https://shib.ds/DiscoFeed'

    @responses.activate
    def test_get_by_url(self, settings):
        with open(settings.SHIB_DS_DISCOFEED_PATH, 'r') as fin:
            r = fin.read()

        responses.add(
            responses.GET,
            self.SHIB_DS_DISCOFEED_URL,
            content_type='application/json',
            body=r
        )

        settings.SHIB_DS_DISCOFEED_URL = self.SHIB_DS_DISCOFEED_URL

        feed = get_feed()
        assert json.loads(r) == feed

    def test_get_by_url_exception(self, settings):
        settings.SHIB_DS_DISCOFEED_URL = self.SHIB_DS_DISCOFEED_URL
        with pytest.raises(Exception):
            get_feed()

    
    def test_get_by_path(self):
        with open(settings.SHIB_DS_DISCOFEED_PATH, 'r') as fin:
            r = fin.read()

        feed = get_feed()
        assert json.loads(r) == feed

    def test_get_by_path_exception(self, settings):
        settings.SHIB_DS_DISCOFEED_PATH = 'spam'
        with pytest.raises(Exception):
            get_feed()


class TestPrepareData:

    def test_prepare_data(self):
        idps, index = prepare_data()

        assert len(idps) == len(index)

        # entitiy_id must be there
        assert all(idp.get('entity_id') for idp in idps)

        # name must be there
        assert all(idp.get('name') for idp in idps)

        # and desfription must be there
        assert all(idp.get('description') for idp in idps)

        # and a logo entry must be there (can be None)
        assert all('logo' in idp for idp in idps)

        # indexed names must be in lower
        assert all(index_entry.islower() for index_entry in index)

        # Confirm, that concatenation has worked
        names = ['bochum', 'hochschule', 'university']
        assert all(name in index[2] for name in names)


    def test_get_largest_logo(self):
        idps, index = prepare_data()

        # Kassel has no logo
        assert idps[1].get('logo') is None

        # Bochum has two logos
        assert idps[2].get('logo') == 'https://idp.hs-bochum.de/aai/bo-logo.jpg'


SEARCH_SCENARIOS = [
    # No token, no result
    (
        [], []
    ),
    # Empty token, all
    (
        [''], ['https://idp.hrz.tu-darmstadt.de/idp/shibboleth', 'https://idp.hrz.uni-kassel.de/idp/shibboleth-idp', 'https://idp.hs-bochum.de/idp/shibboleth']
    ),
    # Darmstadt is one in the list, one result
    (
        ['Darmstadt'], ['https://idp.hrz.tu-darmstadt.de/idp/shibboleth']
    ),
    # Technische Universität Darmstadt must match
    (
        ['Darmstadt', 'Technische'], ['https://idp.hrz.tu-darmstadt.de/idp/shibboleth']
    ),
    # Two matches for Universität
    (
        ['Universität'], ['https://idp.hrz.tu-darmstadt.de/idp/shibboleth', 'https://idp.hrz.uni-kassel.de/idp/shibboleth-idp']
    ),
    # No matches for Universitat (umlaut)
    (
        ['Universitat'], []
    ),
    # Bochum has different DisplayNames for English and German, both must match
    (
        ['Hochschule'], ['https://idp.hs-bochum.de/idp/shibboleth']
    ),
    (
        ['University'] , ['https://idp.hs-bochum.de/idp/shibboleth']
    ),
    # Bochum has different DisplayNames for English and German, combination in both locals match
    (
        ['Hochschule', 'Applied'], ['https://idp.hs-bochum.de/idp/shibboleth']
    ),
    # Match indepent of lower and upper case
    (
        ['darmstADT'], ['https://idp.hrz.tu-darmstadt.de/idp/shibboleth']
    ),
    # Additional whitespace characters are stripped
    (
        ['Darmstadt\t'], ['https://idp.hrz.tu-darmstadt.de/idp/shibboleth']
    ),
]

class TestSearch:

    @pytest.mark.parametrize('tokens, expected', SEARCH_SCENARIOS)
    def test_search(self, tokens, expected):
        results = [result.get('entity_id') for result in search(tokens)]
        assert results == expected


class TestGetRecentIdPs:

    url = '/' # Does not matter

    @pytest.mark.parametrize("idps, expected", RECENT_IDP_SCENARIOS)
    def test_get_recent_idps(self, rf, idps, expected):
        cookie_value = " ".join(map(b64encode_idp, idps))
        if cookie_value:
            cookies = {
                COOKIE_NAME : cookie_value
            }
        else:
            cookies = dict()
        request = rf.get('/')
        request.COOKIES = cookies
        recent_idps = get_recent_idps(request)
        assert set(idp.get('entity_id') for idp in recent_idps) == set(expected)


class TestGetContext:

    base_url = '/'

    @pytest.fixture(autouse=True)
    def set_rf(self, rf):
        self.rf = rf

    def get_shib_ds(self, extra_url='', cookies=dict()):
        request = self.rf.get(self.base_url + extra_url)
        request.COOKIES = cookies

        return get_context(request)

    @pytest.mark.parametrize('entity_id, get, expected, error', ENTITY_ID_TEST_CASES)
    def test_entity_id(self, settings, entity_id, get, expected, error):
        settings.SHIB_DS_ENTITY_ID = entity_id
        shib_ds = self.get_shib_ds(get)
        assert shib_ds.get('entity_id') == expected
        assert shib_ds.get('error') == error

    @pytest.mark.parametrize('get, expected', IS_PASSIVE_TEST_CASES)
    def test_is_passive(self, get, expected):
        shib_ds = self.get_shib_ds(get)
        assert shib_ds.get('is_passive') is expected

    @pytest.mark.parametrize('get, expected, error', POLICY_TEST_CASES)
    def test_policy(self, get, expected, error):
        shib_ds = self.get_shib_ds(get)
        assert shib_ds.get('policy') == expected
        assert shib_ds.get('error') == error

    @pytest.mark.parametrize('idps, expected', RECENT_IDP_SCENARIOS)
    def test_recent_idps(self, idps, expected):
        cookie_value = " ".join(map(b64encode_idp, idps))
        if cookie_value:
            cookies = {
                COOKIE_NAME : cookie_value
            }
        else:
            cookies = dict()
        shib_ds = self.get_shib_ds(cookies=cookies)
        assert set(idp.get('entity_id') for idp in shib_ds.get('recent_idps')) == set(expected)

    @pytest.mark.parametrize('get, default, reg, expected, error', RETURN_TEST_CASES)
    def test_return(self, settings, get, default, reg, expected, error):
        settings.SHIB_DS_DEFAULT_RETURN = default
        settings.SHIB_DS_VALID_RETURN_PATTERN = reg
        shib_ds = self.get_shib_ds(get)
        assert shib_ds.get('return') == expected
        assert shib_ds.get('error') == error

    def test_return_id_param_by_get(self, client):
        shib_ds = self.get_shib_ds('?returnIDParam=spam')
        assert shib_ds.get('return_id_param') == 'spam'

    @pytest.mark.parametrize('get', ['', '?returnIDParam='])
    def test_return_id_param_default(self, client, settings, get):
        shib_ds = self.get_shib_ds(get)
        assert shib_ds.get('return_id_param') == settings.SHIB_DS_RETURN_ID_PARAM
