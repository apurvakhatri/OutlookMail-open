from django.urls import path
from .views import index, userdetails, delete_integration


urlpatterns = [
    path("", index, name="home"),
    path("user/", userdetails, name="home"),
    path('user/<int:integrationId>/delete/', delete_integration, name='home')
]
