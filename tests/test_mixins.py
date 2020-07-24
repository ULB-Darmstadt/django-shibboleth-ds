import pytest

from shibboleth_discovery.conf import COOKIE_NAME
from shibboleth_discovery.utils import b64encode_idp

from django.urls import reverse

from tests.conftest import ENTITY_ID_TEST_CASES
from tests.conftest import POLICY_TEST_CASES
from tests.conftest import IS_PASSIVE_TEST_CASES
from tests.conftest import RECENT_IDP_SCENARIOS
from tests.conftest import RETURN_TEST_CASES

class TestShibDSLoginMixin:

    login_url = reverse('login-mixin')

    @pytest.mark.parametrize('entity_id, get, expected, error', ENTITY_ID_TEST_CASES)
    def test_entity_id(self, client, settings, entity_id, get, expected, error):
        settings.SHIB_DS_ENTITY_ID = entity_id
        shib_ds = client.get(self.login_url + get).context['shib_ds']
        assert shib_ds.get('entity_id') == expected
        assert shib_ds.get('error') == error

    @pytest.mark.parametrize('get, expected', IS_PASSIVE_TEST_CASES)
    def test_is_passive(self, client, get, expected):
        shib_ds = client.get(self.login_url + get).context['shib_ds']
        assert shib_ds.get('is_passive') is expected

    @pytest.mark.parametrize('get, expected, error', POLICY_TEST_CASES)
    def test_policy(self, client, get, expected, error):
        shib_ds = client.get(self.login_url + get).context['shib_ds']
        assert shib_ds.get('policy') == expected
        assert shib_ds.get('error') == error

    @pytest.mark.parametrize('idps, expected', RECENT_IDP_SCENARIOS)
    def test_recent_idps(self, client, idps, expected):
        cookie_value = " ".join(map(b64encode_idp, idps))
        if cookie_value:
            client.cookies[COOKIE_NAME] = cookie_value
        shib_ds = client.get(self.login_url).context['shib_ds']
        assert set(idp.get('entity_id') for idp in shib_ds.get('recent_idps')) == set(expected)

    @pytest.mark.parametrize('get, default, reg, expected, error', RETURN_TEST_CASES)
    def test_return(self, client, settings, get, default, reg, expected, error):
        settings.SHIB_DS_DEFAULT_RETURN = default
        settings.SHIB_DS_VALID_RETURN_PATTERN = reg
        shib_ds = client.get(self.login_url + get).context['shib_ds']
        assert shib_ds.get('return') == expected
        assert shib_ds.get('error') == error

    def test_return_id_param_by_get(self, client):
        shib_ds = client.get(self.login_url + '?returnIDParam=spam').context.get('shib_ds')
        assert shib_ds.get('return_id_param') == 'spam'

    @pytest.mark.parametrize('get', ['', '?returnIDParam='])
    def test_return_id_param_default(self, client, settings, get):
        shib_ds = client.get(self.login_url + get).context.get('shib_ds')
        assert shib_ds.get('return_id_param') == settings.SHIB_DS_RETURN_ID_PARAM
