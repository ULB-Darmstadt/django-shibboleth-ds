RECENT_IDP_SCENARIOS = [
    ([], []),
    ([''], []),
    ([' ', []]),
    (['https:/does.not.exist/'], []),
    (['https://idp.hrz.tu-darmstadt.de/idp/shibboleth',], ['https://idp.hrz.tu-darmstadt.de/idp/shibboleth',]),
    (['https://idp.hrz.tu-darmstadt.de/idp/shibboleth', 'https://idp.hrz.uni-kassel.de/idp/shibboleth-idp'], ['https://idp.hrz.tu-darmstadt.de/idp/shibboleth', 'https://idp.hrz.uni-kassel.de/idp/shibboleth-idp']),
]
