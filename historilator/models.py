from django.db import models
from django.contrib.auth.models import User


# Create your models here.
AUTHORIZABLE_SERVICES = (
	('4S', 'Foursquare'),
	('TR', 'Tripit'),
)

class FacebookId(models.Model):
	user = models.ForeignKey(User)
	facebookId = models.CharField(max_length=265)

class Auth_temp_storage(models.Model):
	user = models.ForeignKey(User)
	site = models.CharField(max_length=2, choices=AUTHORIZABLE_SERVICES)
	token = models.CharField(max_length=256)
	token_secret = models.CharField(max_length=256)
	stage = models.IntegerField()
	
	def __unicode__(self):
		return self.site+" "+self.token
