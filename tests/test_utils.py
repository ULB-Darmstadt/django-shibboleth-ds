import json
import pytest
import responses

from django.conf import settings

from shibboleth_discovery.utils import b64decode_idp, b64encode_idp
from shibboleth_discovery.utils import get_feed
from shibboleth_discovery.utils import prepare_data
from shibboleth_discovery.utils import search


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
