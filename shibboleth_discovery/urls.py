from django.urls import path

from . import views

app_name = 'shib_ds'

urlpatterns = [
    path('search/', views.SearchView.as_view(), name='search'),
    path('set_idp_cookie/', views.SetCookieView.as_view(), name='remember-idp'),

]
