Django Shibboleth Discovery
===========================

This is a Shibboleth discovery service for Django.
It is easy to use, complies with `Identity Provider Discovery Service Protocol and Profile <http://docs.oasis-open.org/security/saml/Post2.0/sstc-saml-idp-discovery.pdf>`_ and yet gives you enough freedom for your UI decisions.
So you can use your favourite autocompletition tool or, in case you have just a few, create a nice dropdown or whatever you like.

In contrast to Shibboleth Embedded Discovery you can really fully customize your UI and use a mobile first approach.
The downside of course is, that you have to work on your UI and implement the redirect.
But there's of course a mixin to support you!

Django Shibboleth Discovery uses simple AJAX requests for the search.
Under the hood, the DiscoFeed, that can be quite big, is cached using Djangos caching framework.

Django Shibboleth Discovery has little dependencies and works with Django 2.2 and 3.0.

Installation
------------

1. Install Django Shibboleth Discovery with pip:

   .. code:: bash

       pip install django-shibboleth-ds

2. Add ``shibboleth_discovery`` to your ``INSTALLED_APPS`` in your project settings.

3. Add ``shibboleth_discovery`` to your ``urls.py`` to enabe the AJAX search.

   .. code:: python

       path('shib-ds/', include('shibboleth_discovery.urls')),

Documentation
-------------

Usage
~~~~~

Making Queries
``````````````

You get the URL with ``reverse('shib_ds:search')``.
To make a search call, simply query the URL with appending ``?q=<term>``.

Your ``<term>`` can be an arbitrary string, like ``'Kassel'`` or ``Applied Bochum``.
The search gives you results where *all* given tokens match.
Tokens in the search are separated by spaces.
It tries matching against the English DisplayName and, if available, against a localized DisplayName.

You get the following back:

.. code:: JSON

   {
       "results" : [
           {
               "entity_id" : "https://idp.hrz.uni-kassel.de/idp/shibboleth-idp",
               "name" : "Universität Kassel",
               "description" : Universität Kassel - Shibboleth Identity Provider",
               "logo" : null
            }
       ]
   }

Note ``name`` and ``description`` will be localized according to how Django determines the users language. If the DiscoFeed does not provide localized ``name`` or ``description``, Django Shibboleth Discovery defaults to English.

Remember Choosen IdP
````````````````````

In order to remember a choosen IdP, you can set a cookie in the users browser.

The cookie is named ``_saml_idp`` and is simply a space character separated list of base64 encoded entity IDs, see chapter 3.5 in the `official recommondation <https://www.google.com/url?q=https://docs.oasis-open.org/security/saml/v2.0/saml-core-2.0-os.pdf>`_.
Either set it directly with your JS or make a AJAX call to ``reverse('shib_ds:remember-idp')`` where you pass a single IdP as

.. code:: JSON

   {
       "entity_id" : "https://idp.hrz.uni-kassel.de/idp/shibboleth-idp"
   }

You can access the saved IdPs via ``ShibDSLoginMixin``.

Options
~~~~~~~

SHIB_DS_CACHE_DURATION (Default: 60*60)
    Internally, Django Shibboleth Discovery uses a cache to store the DiscoFeed.
    That way, not for each AJAX request to DiscoFeed is reloaded, which is quite expensive.
    The feed ist stored in a prepared (smaller) version, once it is accessed.

    To manually renew the cache, call

    .. code:: python

        ./manage.py update_shib_ds_cache

SHIB_DS_DEFAULT_RETURN (Default: '')
    Usually this is ``https://<your-domain>/Shibboleth.sso/Login?target=https://<your-domain>/``.
    You will need this, if your discovery service is directly approached, i.e. if you do not entirely rely on forwarding from your service provider.

    If you set this value, make sure to add it so ``SHIB_DS_VALID_RETURN_PATTERN``.

SHIB_DS_DISCOFEED_PATH
    If your SP is configured, to output the DiscoFeed in a file, you can set the path here.
    The file must be readable by the user running your Django project.

SHIB_DS_DISCOFEED_URL
    Usually the DiscoFeed is served as URL.

SHIB_DS_ENTITY_ID (Default: None)
    The entityID to use.
    If set, only this entityID is allowed.

SHIB_DS_MAX_RESULTS (Deftault: 10)
    The number of results when querying the API.

SHIB_DS_MAX_IDP (Default: 3)
    The number of recently chosen IdPs to be stored in the users browser (as cookie)

SHIB_DS_POLICIES (Default: ['urn:oasis:names:tc:SAML:profiles:SSO:idpdiscovery-protocol:single', ])
    A list of policies that is allowed.
    Usually the default is sufficient.

SHIB_DS_POST_PROCESSOR (Default: lambda x: x)
    Pass a function, that changes a list of IdP-dictionaries.
    The processor is always used, whenever you retrieve IdPs.

    As a helper function, there is a processor for Select2.

    .. code:: python

        from shibboleth_discovery.helpers import select2_processor
        SHIB_DS_POST_PROCESSOR = select2_processor

SHIB_DS_QUERY_PARAMETER (Default: 'q')
    In case you need a different GET parameter for your query, you can set it here. Note that the default value works fine with Select2.

SHIB_DS_RETURN_ID_PARAM (Default: entityID)
    If you need another param name when you pass the chosen IdP to the SP.

SHIB_DS_VALID_RETURN_PATTERN (Default: [])
    Usually the SP passes a ``return`` to the discovery system.
    Here you can define a list of regular expressions for allowed values of ``return``.
    They will be compiled when needed, so you pass them uncompiled.

    In case that you set SHIB_DS_DEFAULT_RETURN make sure that this values matches!

    If you do not set this value, any ``return`` is valid.

Mixins
~~~~~~

Django Shibboleth Discovery is quipped with a login mixin, that can be used with any view that supports ``get_context_data``.

.. code:: python

    from shibboleth_discovery.views import ShibDSLoginMixin
    from django.views.generic import TemplateView

    class LoginView(ShibDSLoginMixin, TemplateView):
         template_name = 'login_template.html'

         def get_context_data(self, **kwargs):
             context = super().get_context_data(**kwargs)
             # your own context 
             return context

Within ``context`` lives the dictionary ``shib_ds``.
It is populated with the following values:

entity_id
    The entityID of the service provider (if known).
    If ``SHIB_DS_ENTITY_ID`` is set, the passed entityID is validated.

error
    Set whenever some value is not valid.
    Possible values are: None, entity_id, policy or return

is_passive
    Will be ``True`` if ``'true'`` and ``False`` otherwise.
    In case of ``True`` it is your task, to behave accordingly.

policy
    The policy, defaults to ``urn:oasis:names:tc:SAML:profiles:SSO:idpdiscovery-protocol:single``.
    The policy has been validated against ``SHIB_DS_POLICIES``.

recent_idps
    A list of recently used IdPs taken from ``_saml_idp`` cookie.
    The SHIB_DS_POST_PROCESSOR is applied to this list.

return
    The place where to send the user client after choosing an IdP.
    This value is validated against ``SHIB_DS_VALID_RETURN_PATTERN``.

return_id_param
    Paramter with which you pass the choosen IdP to the SP.


The mixin itself does not throw any errors.
This has the benefit, that you can use it as a mixin without sorrows and use your own translation.
The easiest way to deal with errors is in the template.

.. code:: html

   {% if shibd_ds.error %}
       <p>{% trans "Sorry, something went wrong, you can't log in with Shibboleth, but our other authentication systems are still working!" %}</p>
   {% else %}
       Your shibboleth authentication logic
   {% endif %}

In case you want to respond differently, e.g. with another template or HTTP status code, you can overwrite ``render_to_response``.
