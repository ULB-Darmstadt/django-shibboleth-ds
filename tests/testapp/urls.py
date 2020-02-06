from django.urls import include, path

from . import views

urlpatterns = [
    path('login', views.LoginView.as_view(), name='login-mixin'),
    path('login-light', views.LoginView.as_view(), name='login-light-mixin'),
    path('shib-ds/', include('shibboleth_discovery.urls')),
]
