from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
	userID = models.ForeignKey(User, related_name='userID', unique=True)
	apiKey = models.TextField()
	isConsumer = models.BooleanField()
	datastoreAddress = models.TextField()

	def __unicode__(self):      
		return "%s's Profile" % self.userID.username
