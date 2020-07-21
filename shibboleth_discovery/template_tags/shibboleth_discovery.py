from django import template

from shibboleth_discovery.utils import get_context

register = template.Library()

@register.simple_tag(takes_context=True)
def shib_ds_context(context):
    """
    Creates a dictionary with information:
        * ServiceProvider login handler
        * IdPs from cookie
    """
    return get_context(context.request)
