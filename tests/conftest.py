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

RECENT_IDP_SCENARIOS = [
    ([], []),
    ([''], []),
    ([' ', []]),
    (['https:/does.nost.exist/'], []),
    (['https://idp.hrz.tu-darmstadt.de/idp/shibboleth',], ['https://idp.hrz.tu-darmstadt.de/idp/shibboleth',]),
    (['https://idp.hrz.tu-darmstadt.de/idp/shibboleth', 'https://idp.hrz.uni-kassel.de/idp/shibboleth-idp'], ['https://idp.hrz.tu-darmstadt.de/idp/shibboleth', 'https://idp.hrz.uni-kassel.de/idp/shibboleth-idp']),
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
