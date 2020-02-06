from django.views.generic import TemplateView

from shibboleth_discovery import mixins


class LoginView(mixins.ShibDSLoginMixin, TemplateView):

    template_name = 'login_template.html'
