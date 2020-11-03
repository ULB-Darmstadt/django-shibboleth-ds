import pytest

from shibboleth_discovery.template_tags.shibboleth_discovery import shib_ds_context
from shibboleth_discovery.utils import b64encode_idp

from django.conf import settings
from django.template import RequestContext
from django.urls import reverse

from tests.conftest import RECENT_IDP_SCENARIOS

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

    @pytest.mark.parametrize('idps, expected', RECENT_IDP_SCENARIOS)
    def test_recent_idps(self, idps, expected):
        cookie_value = " ".join(map(b64encode_idp, idps))
        if cookie_value:
            cookies = {
                settings.SHIB_DS_COOKIE_NAME : cookie_value
            }
        else:
            cookies = dict()
        shib_ds = self.get_shib_ds(cookies=cookies)
        assert set(idp.get('entity_id') for idp in shib_ds.get('recent_idps')) == set(expected)

    def test_return_id_param(self):
        shib_ds = self.get_shib_ds()
        assert shib_ds.get('return_id_param') == settings.SHIB_DS_RETURN_ID_PARAM

    def test_sp_url(self):
        shib_ds = self.get_shib_ds()
        assert shib_ds.get('sp_url') == settings.SHIB_DS_SP_URL

    def test_target(self, client):
        shib_ds = self.get_shib_ds('?next=spam')
        assert shib_ds.get('target') == 'https://testserver/spam'
