.. image:: https://travis-ci.com/ULB-Darmstadt/django-shibboleth-ds.svg?branch=master
    :target: https://travis-ci.com/ULB-Darmstadt/django-shibboleth-ds
    :alt: Build status
  
.. image:: https://coveralls.io/repos/github/ULB-Darmstadt/django-shibboleth-ds/badge.svg?branch=master
    :target: https://coveralls.io/github/ULB-Darmstadt/django-shibboleth-ds?branch=master
    :alt: Coverage


Django Shibboleth Discovery
===========================

This is a simple Shibboleth discovery service for Django.
Feed the app with a DiscoFeed and its Login-Site and you're almost done.

Django Shibboleth Discovery will do some preparations of the DiscoFeed and expose its own cached version.
So you can use your favourite autocompletition tool or, in case you have just a few, create a nice dropdown or whatever you like.

The downside of course is, that you have to work on your UI and implement the redirect.
But there are of course a mixin and a templatetag to support you!

Django Shibboleth Discovery uses simple AJAX requests for the search.
Under the hood, the DiscoFeed, that can be quite big, is cached using Djangos caching framework.

Django Shibboleth Discovery has little dependencies and works with Django 2.2 and 3.0.

Note that it does not comply with `Identity Provider Discovery Service Protocol and Profile <http://docs.oasis-open.org/security/saml/Post2.0/sstc-saml-idp-discovery.pdf>`_, because it is meant for single Service Providers.

Installation
------------

1. Install Django Shibboleth Discovery with pip:

   .. code:: bash

       pip install git+https://github.com/ULB-Darmstadt/django-shibboleth-ds.git

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
               "description" : "Universität Kassel - Shibboleth Identity Provider",
               "logo" : null
            }
       ]
   }

Note ``name`` and ``description`` will be localized according to how Django determines the users language. If the DiscoFeed does not provide localized ``name`` or ``description``, Django Shibboleth Discovery defaults to English.

Redirect to the IdP
```````````````````

The Shibboleth SP Deamon is capable of redirecting to the choosen IdP.
You need to hit its login page with GET parameters ``entityID`` and ``target``, where ``entityID`` is the choosen IdP and ``target`` is URL to redirect the user after successful authentication.

You can initiate the redirect via ``reverse(shib_ds:redirect)`` and pass ``entityID`` and ``next`` as parameters.
The view will check if the entityID is known and cnstruct a full ``target`` URL with ``django.contrib.sites.shortcuts.get_current_site`` and the value of ``next``.
The protocol is always `https`.

The view will also set a cookie, see below.

If no ``entityID`` is given or is unknown, the view returns a 400, *Bad Request*.

Remember Choosen IdP
````````````````````

In order to remember a choosen IdP, you can set a cookie in the users browser.

The cookie is named ``_saml_idp`` and is simply a space character separated list of base64 encoded entity IDs, see chapter 3.5 in the `official recommondation <https://www.google.com/url?q=https://docs.oasis-open.org/security/saml/v2.0/saml-core-2.0-os.pdf>`_.
Either set it directly with your JS or make a AJAX call to ``reverse('shib_ds:remember-idp')`` where you pass a single IdP as

.. code:: JSON

   {
       "entity_id" : "https://idp.hrz.uni-kassel.de/idp/shibboleth-idp"
   }

You can access the saved IdPs via ``ShibDSLoginMixin`` or the templatetag.

Options
~~~~~~~

SHIB_DS_CACHE_DURATION (Default: 60*60)
    Internally, Django Shibboleth Discovery uses a cache to store the DiscoFeed.
    That way, not for each AJAX request to DiscoFeed is reloaded, which can be quite expensive even if the shibboleth deamon does cache it.
    The feed is stored in a prepared (smaller) version once it was accessed.

    To manually renew the cache, call

    .. code:: python

        ./manage.py update_shib_ds_cache

SHIB_DS_COOKIE_NAME (Default: '_saml_idp')
    Name of the cookie to store the choosen IdP.

SHIB_DS_DISCOFEED_PATH
    If your SP is configured, to output the DiscoFeed in a file, you can set the path here.
    The file must be readable by the user running your Django project.

SHIB_DS_DISCOFEED_URL
    Usually the DiscoFeed is served as URL.

SHIB_DS_MAX_RESULTS (Deftault: 10)
    The number of results when querying the API.

SHIB_DS_MAX_IDP (Default: 3)
    The number of recently chosen IdPs to be stored in the users browser (as cookie)

SHIB_DS_POST_PROCESSOR (Default: lambda x: x)
    Pass a function that changes a list of IdP-dictionaries.
    The processor is always used, whenever you retrieve IdPs.

    As a helper function, there is a processor for Select2.

    .. code:: python

        from shibboleth_discovery.helpers import select2_processor
        SHIB_DS_POST_PROCESSOR = select2_processor

    Of course, if you use Select2's ``templateResult`` this processor is reduntant.

SHIB_DS_QUERY_PARAMETER (Default: 'q')
    In case you need a different GET parameter for your query, you can set it here. Note that the default value works fine with Select2.

SHIB_DS_SP_URL (*required*)
    Usually this is ``https://<your-domain>/Shibboleth.sso/Login?target=https://<your-domain>/``.
    Essentially it is the URL of your Shibboleth Service Provider Deamon that will finally redirect to the chosen Identity Provider.

SHIB_DS_RETURN_ID_PARAM (Default: entityID)
    If you need another param name when you pass the chosen IdP to the SP.


Mixins
~~~~~~

Django Shibboleth Discovery is equipped with a login mixin, that can be used with any view that supports ``get_context_data``.

.. code:: python

    from shibboleth_discovery.mixins import ShibDSLoginMixin
    from django.views.generic import TemplateView

    class LoginView(ShibDSLoginMixin, TemplateView):
         template_name = 'login_template.html'

         def get_context_data(self, **kwargs):
             context = super().get_context_data(**kwargs)
             # your own context 
             return context

Within ``context`` lives the dictionary ``shib_ds``.
It is populated with the following values:

recent_idps
    A list of recently used IdPs taken from ``_saml_idp`` cookie.
    The SHIB_DS_POST_PROCESSOR is applied to this list.

return_id_param
    Paramter with which you pass the choosen IdP to the SP.

next
    This is simply ``request.GET.get('next', '')`` and should be passed to the redirect view.

sp_url
    URL to the Shibboleth SP Deamon.


The mixin itself does not throw any errors.
This has the benefit that you can use it as a mixin without sorrows and use your own translations.
The easiest way to deal with errors is in the template:

Templatetag
~~~~~~~~~~~

In case you do not want to use a mixin, e.g. if shibboleth authentication is optional in your app, you can also use a templatetag.

.. code:: html

   <!-- Load the templatetags -->
   {% load shibboleth_discovery %}

   {% shib_ds_context as shib_ds %}

Then you have a dict as provided by the mixin.


Forms
~~~~~

This app does not provide a form as part of the philosophy.
Since chosing an IdP requires only a simple form, there is not much effort in it.
Self-defining a form is probably easier than to struggle with a pre-existing form.
