from django.template import RequestContext

from shibboleth_discovery.template_tags.shibboleth_discovery import shib_ds_context

from .conftest import MetaContext

class TestShibDS(MetaContext):

    def get_shib_ds(self, request, cookies=dict()):
        request.COOKIES = cookies
        context = RequestContext(request, {})

        return shib_ds_context(context)
