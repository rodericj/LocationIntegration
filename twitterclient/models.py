from django.db import models
from django.contrib.auth.models import User

class Tag(models.Model):
	#id = models.IntegerField()
	tag = models.CharField(max_length=10)
	
	def __unicode__(self):
		return str(self.id)+ ' '+str(self.tag)

class TwitterUser(models.Model):
	twitter_id = models.CharField(max_length=15)

	def __unicode__(self):
		return str(self.id)+ ' '+str(self.twitter_id)

class UserToTag(models.Model):
	tag = models.ForeignKey(Tag)
	user = models.ForeignKey(TwitterUser)

	def __unicode__(self):
		return str(user)+ " " + str(tag)

class TweetToTag(models.Model):
	user = models.IntegerField()
	tweetid = models.IntegerField()
	tag = models.ForeignKey(Tag)

	def __unicode__(self):
		return str(self.user)+' '+str(self.tag)+' '+ str(self.tweetid)

