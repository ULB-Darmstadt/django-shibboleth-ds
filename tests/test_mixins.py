import pytest

from shibboleth_discovery.utils import b64encode_idp

from django.conf import settings
from django.urls import reverse

from tests.conftest import RECENT_IDP_SCENARIOS

class TestShibDSLoginMixin:

    login_url = reverse('login-mixin')

    @pytest.mark.parametrize('idps, expected', RECENT_IDP_SCENARIOS)
    def test_recent_idps(self, client, idps, expected):
        cookie_value = " ".join(map(b64encode_idp, idps))
        if cookie_value:
            client.cookies[settings.SHIB_DS_COOKIE_NAME] = cookie_value
        shib_ds = client.get(self.login_url).context['shib_ds']
        assert set(idp.get('entity_id') for idp in shib_ds.get('recent_idps')) == set(expected)

    def test_return_id_param(self, client):
        shib_ds = client.get(self.login_url).context.get('shib_ds')
        assert shib_ds.get('return_id_param') == settings.SHIB_DS_RETURN_ID_PARAM

    def test_sp_url(self, client):
        shib_ds = client.get(self.login_url).context.get('shib_ds')
        assert shib_ds.get('sp_url') == settings.SHIB_DS_SP_URL

    def test_target(self, client):
        shib_ds = client.get(self.login_url + '?next=spam').context.get('shib_ds')
        assert shib_ds.get('target') == 'https://testserver/spam'
