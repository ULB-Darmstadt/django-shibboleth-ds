from .utils import get_context

class ShibDSLoginMixin:
    """
    Mixin class to provide some support on the login. It does provide some information as context to use later.
    """

    def get_context_data(self, **kwargs):
        """
        Creates a context with information:
            * ServiceProvider login handler
            * IdPs from cookie
        """
        context = super().get_context_data(**kwargs)

        shib_ds = get_context(self.request)

        context['shib_ds'] = shib_ds
        return context
