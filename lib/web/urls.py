from django.urls import path
from django.conf.urls import url
from .views import index, userdetails, delete_integration


urlpatterns = [

    path("user/", userdetails, name="userdetails"),
    path('user/<int:integrationId>/delete/', delete_integration, name='delete'),
    url(r"^(?P<path>.*)$", index, name="home"),
]
