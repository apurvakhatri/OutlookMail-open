import datetime
from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class YellowUserToken(models.Model):
    user = models.IntegerField()
    yellowant_token = models.CharField(max_length=100)
    yellowant_id = models.IntegerField(default=0)
    yellowant_integration_invoke_name = models.CharField(max_length=100)
    yellowant_integration_id = models.IntegerField(default=0)
    outlook_access_token = models.CharField(max_length=2048)
    subscription_id = models.CharField(max_length=100, default="")
    outlook_refresh_token = models.CharField(max_length=2048)
    token_update = models.DateTimeField(default=datetime.datetime.utcnow)
    subscription_update = models.DateTimeField(default=datetime.datetime.utcnow)

class YellowAntRedirectState(models.Model):
    user = models.IntegerField()
    state = models.CharField(max_length=512, null=False)
    subdomain = models.CharField(max_length=128)

class AppRedirectState(models.Model):
    user_integration = models.ForeignKey(YellowUserToken, on_delete=models.CASCADE)
    state = models.CharField(max_length=512, null=False)