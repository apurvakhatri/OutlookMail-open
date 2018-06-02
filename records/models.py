from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class YellowUserToken(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    yellowant_token = models.CharField(max_length=100)
    yellowant_id = models.IntegerField(default=0)
    yellowant_integration_invoke_name = models.CharField(max_length=100)
    yellowant_intergration_id = models.IntegerField(default=0)
    outlook_access_token = models.CharField(max_length=2048)
    #webhook_id = models.CharField(max_length=100, default="")
    #webhook_last_updated = models.DateTimeField(default=datetime.datetime.utcnow)

class YellowAntRedirectState(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    state = models.CharField(max_length = 512, null = False)

class AppRedirectState(models.Model):
    user_integration = models.ForeignKey(YellowUserToken, on_delete=models.CASCADE)
    state = models.CharField(max_length=512, null = False)