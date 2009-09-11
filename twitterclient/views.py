# Create your views here.
from django.http import HttpResponse
from django.utils import simplejson
import twitterclient.twitter as twitterapi
from django.shortcuts import render_to_response

def twitterstore(username, password):
	print "Store: "+username+password
	
def twitterlogin(request):
	print "hi"
	if(request.POST.get('twitterusername', 0)):
		#get the login info and return the latest
		username = request.POST['twitterusername']
		password = request.POST['twitterpassword']
		twitterstore(username, password)
		return render_to_response('twitterclient.html', {'login':1})
	else:
		print "no post"
		return render_to_response('profile.html', {'login':0})

def twitter(request):
	username = ""#request.POST['twitterusername']
	password = ""# request.POST['twitterpassword']
	api = twitterapi.Api(username=username, password=password)	
	print '2'
	friendTimeline = api.GetFriendsTimeline()
	print '3'
	data = [eval(str(a).replace('false', 'False').replace('true', 'True')) for a in friendTimeline]	
	#newdata = eval(data[0].replace('false', 'False').replace('true', 'True'))
	#print type(newdata)
	#print newdata.keys()

	return HttpResponse(simplejson.dumps(data), mimetype='application/json')
