from django.urls import path
from django.contrib.auth.views import LogoutView

# allauth
from allauth.socialaccount.providers.google.urls import urlpatterns as allauth_urlpatterns

urlpatterns = [
    path('logout/', LogoutView.as_view(), name='logout'),
]

urlpatterns += allauth_urlpatterns
