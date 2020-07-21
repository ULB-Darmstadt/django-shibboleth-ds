import pytest

from django.urls import reverse

from shibboleth_discovery.conf import COOKIE_NAME
from shibboleth_discovery.helpers import select2_processor
from shibboleth_discovery.utils import b64encode_idp

ENTITY_ID_TEST_CASES = [
    (None, '', None, None),
    (None, '?entity_id=', None, None),
    (None, '?entity_id=urn:spam', 'urn:spam', None),
    ('urn:spam', '?entity_id=urn:spam', 'urn:spam', None),
    ('urn:spam', '', None, 'entity_id'),
    ('urn:spam', '?entity_id=urn:ham', None, 'entity_id'),
]

IS_PASSIVE_TEST_CASES = [
    ('?isPassive=true', True),
    ('', False),
    ('?isPassive=', False),
    ('?isPassive=false', False),
    ('?isPassive=spam', False),
]

POLICY_TEST_CASES = [
    ('', 'urn:oasis:names:tc:SAML:profiles:SSO:idpdiscovery-protocol:single', None),
    ('?policy=', 'urn:oasis:names:tc:SAML:profiles:SSO:idpdiscovery-protocol:single', None),
    ('?policy=urn:oasis:names:tc:SAML:profiles:SSO:idpdiscovery-protocol:single', 'urn:oasis:names:tc:SAML:profiles:SSO:idpdiscovery-protocol:single', None),
    ('?policy=urn:spam', None, 'policy'),
]

RETURN_TEST_CASES = [
    ('', '', [], None, 'return'),
    ('', '', ['https://sp.shib.ds/'], None, 'return'),
    ('', 'https://sp.shib.ds/', [], 'https://sp.shib.ds/', None),
    ('', 'https://sp.shib.ds/', [r'https://sp\.shib.*'], 'https://sp.shib.ds/', None),
    ('', 'https://sp.shib.ds/', [r'https://sp\.shib'], 'https://sp.shib.ds/', None),
    ('', 'https://sp.shib.ds/', [r'ttps://sp\.shib'], None, 'return'),
    ('', 'https://sp.shib.ds/', [r'https://sp\.shib$'], None, 'return'),
    ('?return=',  'https://sp.shib.ds/', [], 'https://sp.shib.ds/', None),
    ('?return=', 'https://sp.shib.ds/', [r'https://sp\.shib$'], None, 'return'),
    ('?return=https://sp2.shib.ds/', 'https://sp.shib.ds/', [], 'https://sp2.shib.ds/', None),
    ('?return=https://sp2.shib.ds/', 'https://sp.shib.ds/', ['https://sp2.shib.ds/'], 'https://sp2.shib.ds/', None),
    ('?return=https://sp2.shib.ds/', 'https://sp.shib.ds/', [], 'https://sp2.shib.ds/', None),
    ('?return=https://sp2.shib.ds/', 'https://sp.shib.ds/', [r'https://sp2\.shib.*'], 'https://sp2.shib.ds/', None),
    ('?return=https://sp2.shib.ds/', 'https://sp.shib.ds/', [r'https://sp2\.shib'], 'https://sp2.shib.ds/', None),
    ('?return=https://sp2.shib.ds/', 'https://sp.shib.ds/', [r'ttps://sp2\.shib'], None, 'return'),
    ('?return=https://sp2.shib.ds/', 'https://sp.shib.ds/', [r'https://sp2\.shib$'], None, 'return'),
]

class MetaContext:

    login_url = reverse('login-mixin')


    @pytest.mark.parametrize('shib_ds, get, expected, error', ENTITY_ID_TEST_CASES)
    def test_entity_id(self, rf, settings, shib_ds, get, expected, error):
        settings.SHIB_DS_ENTITY_ID = shib_ds
        request = rf.get(self.login_url + get)
        shib_ds = self.get_shib_ds(request)
        assert shib_ds.get('entity_id') == expected
        assert shib_ds.get('error') == error

    @pytest.mark.parametrize('get, expected', IS_PASSIVE_TEST_CASES)
    def test_is_passive(self, rf, get, expected):
        request = rf.get(self.login_url + get)
        shib_ds = self.get_shib_ds(request)
        assert shib_ds.get('is_passive') is expected

    @pytest.mark.parametrize('get, expected, error', POLICY_TEST_CASES)
    def test_policy(self, rf, get, expected, error):
        request = rf.get(self.login_url + get)
        shib_ds = self.get_shib_ds(request)
        assert shib_ds.get('policy') == expected
        assert shib_ds.get('error') == error

    def test_recent_idps(self, rf, settings):
        request = rf.get(self.login_url)
        shib_ds = self.get_shib_ds(request)

        # We have no IdP saved yet, so we assume empty list
        assert shib_ds.get('recent_idps') == []

        idp_da = 'https://idp.hrz.tu-darmstadt.de/idp/shibboleth'
        idp_ks = 'https://idp.hrz.uni-kassel.de/idp/shibboleth-idp'

        # If we save an IdP, this must be in the list
        cookies = {
            COOKIE_NAME : b64encode_idp(idp_da)
        }
        shib_ds = self.get_shib_ds(request, cookies=cookies)
        assert shib_ds.get('recent_idps')[0].get('entity_id') == idp_da
        for key in ['name', 'description', 'logo']:
            assert key in shib_ds.get('recent_idps')[0]

        # If we add another, both must be in the list
        cookies = {
            COOKIE_NAME : b64encode_idp(idp_da ) + ' ' +b64encode_idp(idp_ks)
        }
        shib_ds = self.get_shib_ds(request, cookies=cookies)
        assert len(shib_ds.get('recent_idps')) == 2
        assert all(idp_da or idp_ks in idp.get('entity_id') for idp in shib_ds.get('recent_idps'))

    @pytest.mark.parametrize('get, default, reg, expected, error', RETURN_TEST_CASES)
    def test_return(self, rf, settings, get, default, reg, expected, error):
        settings.SHIB_DS_DEFAULT_RETURN = default
        settings.SHIB_DS_VALID_RETURN_PATTERN = reg
        request = rf.get(self.login_url + get)
        shib_ds = self.get_shib_ds(request)
        assert shib_ds.get('return') == expected
        assert shib_ds.get('error') == error

    def test_return_id_param_by_get(self, rf):
        request = rf.get(self.login_url + '?returnIDParam=spam')
        shib_ds = self.get_shib_ds(request)
        assert shib_ds.get('return_id_param') == 'spam'

    @pytest.mark.parametrize('get', ['', '?returnIDParam='])
    def test_return_id_param_default(self, rf , settings, get):
        request = rf.get(self.login_url + get)
        shib_ds = self.get_shib_ds(request)
        assert shib_ds.get('return_id_param') == settings.SHIB_DS_RETURN_ID_PARAM

    def test_select2_post_processor(self, rf, settings):
        settings.SHIB_DS_POST_PROCESSOR = select2_processor
        idp_da = 'https://idp.hrz.tu-darmstadt.de/idp/shibboleth'
        cookies = {
            COOKIE_NAME : b64encode_idp(idp_da)
        }
        request = rf.get(self.login_url)
        shib_ds = self.get_shib_ds(request, cookies=cookies)
        assert shib_ds.get('recent_idps')[0].get('id') == idp_da
        assert shib_ds.get('recent_idps')[0].get('text') == 'Technische Universität Darmstadt'
