import re

from django.core.cache import cache

from .conf import settings

from .conf import COOKIE_NAME
from .utils import b64decode_idp
from .utils import prepare_data
from .utils import localize_idp


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

        shib_ds = dict()

        # First we check if the entityID from settings and GET match if the first one is set
        if settings.SHIB_DS_ENTITY_ID and settings.SHIB_DS_ENTITY_ID != self.request.GET.get('entity_id'):
            shib_ds['error'] = 'entity_id'
        # If settings.SHIB_DS_ENTITY_ID is not set set or settings.SHIB_DS_ENTITY_ID is set and the values are identical, set entity_id
        else:
            shib_ds['entity_id'] = self.request.GET.get('entity_id') or settings.SHIB_DS_ENTITY_ID

        # Next we look for the policy. It must be one of settings.SHIB_DS_POLICIES or None
        # If no policy is given, the default must be used
        policy = self.request.GET.get('policy') or 'urn:oasis:names:tc:SAML:profiles:SSO:idpdiscovery-protocol:single'
        if policy in settings.SHIB_DS_POLICIES:
            shib_ds['policy'] = policy
        else:
            shib_ds['error'] = 'policy'

        # The return value is where to send the user client after choosing an IdP
        # Must satisfy any of some regexp, so that forwarding is to the desired SP
        # If no return value is set, settings.DEFAULT_RETURN is used
        return_val = self.request.GET.get('return') or settings.SHIB_DS_DEFAULT_RETURN
        if return_val and len(settings.SHIB_DS_VALID_RETURN_PATTERN) == 0 or any(re.match(reg, return_val) for reg in settings.SHIB_DS_VALID_RETURN_PATTERN):
            shib_ds['return'] = return_val
        else:
            shib_ds['error'] = 'return'

        # If we get a returnIDParam passed use it, otherwise settings.SHIB_DS_RETURN_ID_PARAM
        shib_ds['return_id_param'] = self.request.GET.get('returnIDParam') or settings.SHIB_DS_RETURN_ID_PARAM

        # Recently used IdPs
        saved_idps = [b64decode_idp(idp) for idp in self.request.COOKIES.get(COOKIE_NAME, '').split(' ') if idp]
        idps, index = cache.get_or_set(
            'shib_ds',
            prepare_data(),
            timeout=settings.SHIB_DS_CACHE_DURATION
        )
        shib_ds['recent_idps'] = settings.SHIB_DS_POST_PROCESSOR(
            [
                localize_idp(idp) for idp in idps
                if any(saved_idp in idp.get('entity_id') for saved_idp in saved_idps)
            ]
        )

        # Check if isPassive was passed
        if self.request.GET.get('isPassive', '') == 'true':
            shib_ds['is_passive'] = True
        else:
            shib_ds['is_passive'] = False

        context['shib_ds'] = shib_ds
        return context
