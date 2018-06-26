"""outlookapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from django.conf.urls import include
from lib.web import urls as web_urls
from lib.records.views import redirectToYellowAntAuthenticationPage, yellowantredirecturl, get_signin_url, gettoken, \
    integrate_app_account, yellowant_api, webhook

urlpatterns = [

    path('admin/', admin.site.urls),
    path('yellowantauthurl/', redirectToYellowAntAuthenticationPage),
    path('redirecturl/', yellowantredirecturl),
    path('outlookauthurl/', get_signin_url),
    path('outlookredirect/', gettoken),
    path('outlookredirecttoken/', gettoken),
    path("integrate_app", integrate_app_account),
    path("apiurl/", yellowant_api),
    url('webhook/(?P<hash_str>[^/]+)/$', webhook, name='webhook'),
    path('', include(web_urls))
]
