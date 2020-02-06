import pytest

from django.urls import reverse

from shibboleth_discovery.helpers import select2_processor

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

class TestShibDSLightLoginMixin:

    login_url = reverse('login-mixin')


    @pytest.mark.parametrize('shib_ds, get, expected, error', ENTITY_ID_TEST_CASES)
    def test_entity_id(self, client, settings, shib_ds, get, expected, error):
        settings.SHIB_DS_ENTITY_ID = shib_ds
        r = client.get(self.login_url + get)
        shib_ds = r.context.get('shib_ds')
        assert shib_ds.get('entity_id') == expected
        assert shib_ds.get('error') == error

    @pytest.mark.parametrize('get, expected', IS_PASSIVE_TEST_CASES)
    def test_is_passive(self, client, get, expected):
        r = client.get(self.login_url + get)
        shib_ds = r.context.get('shib_ds')
        assert shib_ds.get('is_passive') is expected

    @pytest.mark.parametrize('get, expected, error', POLICY_TEST_CASES)
    def test_policy(self, client, get, expected, error):
        r = client.get(self.login_url + get)
        shib_ds = r.context.get('shib_ds')
        assert shib_ds.get('policy') == expected
        assert shib_ds.get('error') == error

    def test_recent_idps(self, client):
        shib_ds = client.get(self.login_url).context.get('shib_ds')

        # We have no IdP saved yet, so we assume empty list
        assert shib_ds.get('recent_idps') == []

        idp_da = 'https://idp.hrz.tu-darmstadt.de/idp/shibboleth'
        idp_ks = 'https://idp.hrz.uni-kassel.de/idp/shibboleth-idp'

        # If we save an IdP, this must be in the list
        client.post(reverse('shib_ds:remember-idp'), {'entity_id': idp_da}, 'application/json')
        shib_ds = client.get(self.login_url).context.get('shib_ds')
        assert shib_ds.get('recent_idps')[0].get('entity_id') == idp_da
        for key in ['name', 'description', 'logo']:
            assert key in shib_ds.get('recent_idps')[0]

        # If we add another, both must be in the list
        client.post(reverse('shib_ds:remember-idp'), {'entity_id': idp_ks}, 'application/json')
        shib_ds = client.get(self.login_url).context.get('shib_ds')
        assert len(shib_ds.get('recent_idps')) == 2
        assert all(idp_da or idp_ks in idp.get('entity_id') for idp in shib_ds.get('recent_idps'))

    @pytest.mark.parametrize('get, default, reg, expected, error', RETURN_TEST_CASES)
    def test_return(self, client, settings, get, default, reg, expected, error):
        settings.SHIB_DS_DEFAULT_RETURN = default
        settings.SHIB_DS_VALID_RETURN_PATTERN = reg
        r = client.get(self.login_url + get)
        shib_ds = r.context.get('shib_ds')
        assert shib_ds.get('return') == expected
        assert shib_ds.get('error') == error

    def test_return_id_param_by_get(self, client):
        r = client.get(self.login_url + '?returnIDParam=spam')
        shib_ds = r.context.get('shib_ds')
        assert shib_ds.get('return_id_param') == 'spam'

    @pytest.mark.parametrize('get', ['', '?returnIDParam='])
    def test_return_id_param_default(self, client, settings, get):
        r = client.get(self.login_url + get)
        shib_ds = r.context.get('shib_ds')
        assert shib_ds.get('return_id_param') == settings.SHIB_DS_RETURN_ID_PARAM


    def test_select2_post_processor(self, client, settings):
        settings.SHIB_DS_POST_PROCESSOR = select2_processor
        idp_da = 'https://idp.hrz.tu-darmstadt.de/idp/shibboleth'
        client.post(reverse('shib_ds:remember-idp'), {'entity_id': idp_da}, 'application/json')
        shib_ds = client.get(self.login_url).context.get('shib_ds')
        assert shib_ds.get('recent_idps')[0].get('id') == idp_da
        assert shib_ds.get('recent_idps')[0].get('text') == 'Technische Universität Darmstadt'
