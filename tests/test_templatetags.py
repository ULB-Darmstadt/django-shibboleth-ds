import pytest

from shibboleth_discovery.conf import COOKIE_NAME
from shibboleth_discovery.template_tags.shibboleth_discovery import shib_ds_context
from shibboleth_discovery.utils import b64encode_idp

from django.template import RequestContext
from django.urls import reverse

from tests.conftest import ENTITY_ID_TEST_CASES
from tests.conftest import POLICY_TEST_CASES
from tests.conftest import IS_PASSIVE_TEST_CASES
from tests.conftest import RECENT_IDP_SCENARIOS
from tests.conftest import RETURN_TEST_CASES

class TestShibDS:

    base_url = reverse('login-mixin')

    @pytest.fixture(autouse=True)
    def set_rf(self, rf):
        self.rf = rf

    def get_shib_ds(self, extra_url='', cookies=dict()):
        request = self.rf.get(self.base_url + extra_url)
        request.COOKIES = cookies
        context = RequestContext(request, {})

        return shib_ds_context(context)

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
