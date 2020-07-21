from .conftest import MetaContext

from tests.testapp.views import LoginView

class TestShibDSLoginMixin(MetaContext):

    def get_shib_ds(self, request, cookies=dict()):
        request.COOKIES = cookies
        view = LoginView()
        view.setup(request)

        return view.get_context_data().get('shib_ds')
