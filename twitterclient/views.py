# Create your views here.
from django.http import HttpResponse
from django.utils import simplejson
import twitterclient.twitter as twitterapi
from django.shortcuts import render_to_response
from LocationIntegration.twitterclient.models import Tag, TweetToTag, TwitterUser, UserToTag


def userprofile(request, twitter_id):
	print twitter_id
	ret = {}
	ret['twitter_id'] = twitter_id

	#TODO what if the user doesn't exist. I guess we need a 404
	twitter_user = TwitterUser.objects.get(twitter_id=twitter_id)
	tags = twitter_user.usertotag_set.all()	
	ret['tags'] = [taglink.tag.tag for taglink in tags]

	return render_to_response('userprofile.html', ret)

def twitterstore(username, password):
	print "Store: "+username+password
	
def twittertag(request):
	print "in twitter tag"
	tags = request.GET.get('tags', '').split()
	tweet = request.GET.get('tweet', '')
	twitter_id = request.GET.get('twitter_id', '')
	print twitter_id
	twitter_user_results = TwitterUser.objects.filter(twitter_id=twitter_id)
	print twitter_user_results
	if len(twitter_user_results) > 1:
		raise "We've got multiple users with teh same name. Bad"
	elif len(twitter_user_results) == 0:
		tu = TwitterUser(twitter_id=twitter_id)
		print tu
		tu.save()
	else:
		twitter_user = twitter_user_results[0]

	ret=[]
	#save these tags in the database if they do not already exist
	for tag in tags:
		print "lookup for: "+ tag
		tagrows = Tag.objects.filter(tag=tag)
		if not tagrows:
			print tag + " is not in the db"
			t = Tag(tag=tag)
			t.save()
			row = t
		else:
			row = tagrows[0]

		#associate this tag with the twitter user who posted it
		twitter_user.usertotag_set.create(tag=row)

		#associate this tweet with each of the tags: 
		#i.e. create a row in the database mapping this tweet number to each of the tags
		row.tweettotag_set.create(tweetid=tweet, user=345)
		ret.append(tag)

	print ret
	return HttpResponse(simplejson.dumps(ret), mimetype='application/json')

def twitterlogin(request):
	print "hi"
	print request
	if(request.POST.get('twitterusername', 0)):
		#get the login info and return the latest
		username = request.POST['twitterusername']
		password = request.POST['twitterpassword']
		twitterstore(username, password)
		return render_to_response('twitterclient.html', {'login':1})
	elif(request.GET.get('tags', 0)):
		return render_to_response('twitterclient.html', {'login':1})
	else:
		print "no post"
		return render_to_response('profile.html', {'login':0})

def getTagsForTweet(tweet_id):
	#Separated so we can cacheify this
	ids = TweetToTag.objects.filter(tweetid=tweet_id)
	list = [link.tag.tag for link in ids]
	ret = [{'tag':tag, 'count':list.count(tag)} for tag in set(list)]
	return ret
	
def twitter(request):
	username = "rodericj"#request.POST['twitterusername']
	password = "ThlE1I8X"# request.POST['twitterpassword']
	api = twitterapi.Api(username=username, password=password)	

	print request.GET
	if request.GET.get('user', 0):
		friendTimeline = api.GetUserTimeline(request.GET.get('user'))
	else:
		friendTimeline = api.GetFriendsTimeline()
		
	data = [eval(str(a).replace('false', 'False').replace('true', 'True')) for a in friendTimeline]	

	for tweet in data:
		tweet['tags'] = getTagsForTweet(tweet['id'])
	
	return HttpResponse(simplejson.dumps(data), mimetype='application/json')
