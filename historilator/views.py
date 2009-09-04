# Create your views here.
from LocationIntegration.historilator.models import Auth_temp_storage

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson
from BeautifulSoup import BeautifulStoneSoup

import urllib
import urllib2
import logging
import config
import tripit
import feedparser
import cStringIO
import Image

def xd_receiver(request):
	return render_to_response('xd_receiver.html')

#@login_required(redirect_field_name='/login')
def start(request):
	print "in start"
	print type(request)
	ret = {}
	ret['username'] = request.user.username
	ret['services'] = ['foursquare', 'yelp']
	return render_to_response('profile.html', ret)

def register(request):
    emailAddress = request.POST['emailaddress']
    username = request.POST['username']
    password = request.POST['password']
    confirmpassword = request.POST['confirmpassword']
    user = authenticate(username=username, password=password)
    ret = {}

    dest = '/login'
    if user is not None:
        ret['registerret'] =  "An account with that username already exists"
    else:
        #time to set up a new user
        verifyRegisterParams(emailAddress, username, password, confirmpassword)
        user = User.objects.create_user(username, emailAddress, password)
        user.isActive = True
        user.save()
        ret['registerret'] = "Success, you are known as " + username
        #now to authenticate
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
				ret['registerret'] =  "You provided a correct username and password!"
				login(request, user)
            else:
                ret['registerret'] = "Your account has been disabled!"
        else:
            ret['registerret'] = "Your username and password were incorrect1."
        dest = '/'

    return HttpResponseRedirect(dest+'?ret='+ret['registerret'])

def weblogin(request):
    emailAddress = request.POST['emailaddress']
    password = request.POST['password']
    user = authenticate(username=emailAddress, password=password)
    dest = 'login'
    if user is not None:
        if user.is_active:
            ret['loginret'] =  "You provided a correct username and password!"
            ret['rc'] = 0
            dest = 'profile'   
        else:
            ret['loginret'] = "Your account has been disabled!"
    else:
        ret['loginret'] = "Your username and password were incorrect2."
        ret['rc'] = 0

    return HttpResponseRedirect(dest, ret)

def addServices(request):
	print "addServices"
	stage=config.storage_stage['first']
	ret = {}
	ret['username'] = request.user.username
	this_user = User.objects.get(username=request.user.username)
	
	#for i in config.oauthsite:
		#print i
		#ret[i] = doAuthorizeStep(this_user, i, config.oauthsite[i].get('options', ''))
		
	ret['foursquare_link'] = doAuthorizeStep(this_user, 'foursquare')
	ret['tripit_link'] = doAuthorizeStep(this_user, 'tripit', '&oauth_callback=http://localhost:8000/auth?site=tripit')

	return render_to_response('login.html', ret)

def auth(request):
	this_user = User.objects.get(username=request.user.username)
	if request.GET.get('site',0) == 'tripit':
		site = config.oauthsite['tripit']
	elif request.META.get('HTTP_REFERER', 0).count('playfoursquare'):
		site = config.oauthsite['foursquare']
	else:
		logging.warn("Something is wrong. We are getting oauth requests NOT from a source supported")

	#from site specific config dict
	consumer_key = site['consumer_key']
	consumer_secret = site['consumer_secret']
	api_url = site['api_access_token_url']
	id = site['id']

	#need to get the oauth consumer secret and key from db (or preferably cache)
	key_row = Auth_temp_storage.objects.filter(user=request.user, site=id)
	request_token = key_row[0].token
	request_token_secret = key_row[0].token_secret

	oauth_credential = tripit.OAuthConsumerCredential(oauth_consumer_key=consumer_key, oauth_consumer_secret=consumer_secret, oauth_token=request_token, oauth_token_secret=request_token_secret)
	t = tripit.TripIt(oauth_credentials = oauth_credential, api_url = api_url)
	access_token_batch = t.get_access_token()
	access_token = access_token_batch['oauth_token']
	access_token_secret = access_token_batch['oauth_token_secret']
	
	#store this final token
	tmp = this_user.auth_temp_storage_set.create(site=site['id'], token=access_token, token_secret=access_token_secret, stage=config.storage_stage['second'])
	tmp.save()

	return render_to_response('profile.html', {})

def doAuthorizeStep(this_user, site_name, options=''):
		site = config.oauthsite[site_name]
		print "Starting " + site_name + " OAuth Process"
		oauth_credential = tripit.OAuthConsumerCredential(oauth_consumer_key=site['consumer_key'], oauth_consumer_secret=site['consumer_secret'])
	
		t = tripit.TripIt(oauth_credentials = oauth_credential, api_url = site['api_url'])
		
		request_token_batch = t.get_request_token()
		print "this is the request token batch"	
		print request_token_batch
		request_token = request_token_batch['oauth_token']
		request_token_secret = request_token_batch['oauth_token_secret']

		link = site['api_authorize_url']+"?oauth_token="+request_token+options
	
		#need to save the request_token
		#delete all keys that already exist, we need to replace them
		this_user.auth_temp_storage_set.filter(site=site['id'], stage=config.storage_stage['first']).delete()
		tmp = this_user.auth_temp_storage_set.create(site=site['id'], token=request_token, token_secret=request_token_secret, stage=1)
	
		tmp.save()
		return link

def verifyRegisterParams(emailAddress, username, password, confirmpassword):
    #passwords are the same

    #emailAdd looks like an email addy
    return True

def getUserPhoto(img_path):
	img_name = img_path.split('/')[-1:][0]
	#should look up to see if the image is in our servers
	
	ret = ''
	try:
		#if not, make it
		fp = urllib.urlopen(img_path)
		img = cStringIO.StringIO(fp.read())

		avatar = Image.open(img)
		bg = Image.open("site_media/background.jpg")
		print img_path
		bg.paste(avatar,(5,5))
		png_name = img_name.replace('.jpg', '.png')
		print "saving as: "+png_name
		bg.save('site_media/photos/'+png_name, "PNG")
		ret = 'site_media/photos/'+png_name
	
	except:
		print "exception in Image"
		ret = 'site_media/photos/'+img_path
		ret = img_path
	return ret

def performRequest(url, site, this_user):
	#Gather Authentication details
	oauth_info = this_user.auth_temp_storage_set.filter(site=site['id'], stage=config.storage_stage['second'])

	request_url = url
	consumer_key = site['consumer_key']
	consumer_secret = site['consumer_secret']
	access_token = oauth_info[0].token
	access_token_secret = oauth_info[0].token_secret

	#Where the tripit demo code starts
	oauth_credential = tripit.OAuthConsumerCredential(oauth_consumer_key=consumer_key, oauth_consumer_secret=consumer_secret, oauth_token=access_token, oauth_token_secret=access_token_secret)
	oauth_consumer = tripit.OAuthConsumer(oauth_credential)
	oauth_parameters = oauth_consumer.generate_oauth_parameters('GET', request_url)
	authorization_header = oauth_consumer.generate_authorization_header(request_url)
	new_request = urllib2.Request(request_url)
	new_request.add_header('Authorization', authorization_header);

	stream = None
	try:
		stream = urllib2.urlopen(new_request)
	except urllib2.HTTPError, http_error:
		if http_error.code == 404:
			stream = http_error
		else:
			raise
	data = stream.read()
	stream.close()
	print type(data)
	return data

def getMyTrips(request):
	url = 'https://api.tripit.com/v1/list/trip'
	site = config.oauthsite['tripit']
	this_user = User.objects.get(username=request.user.username)
	data = performRequest(url, site, this_user)
	data1 = feedparser.parse(data)
	return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def getMyCheckins(request):
	kml = 'http://feeds.playfoursquare.com/history/17f32ec6b65e8577d3ea14b0806fd42f.kml'
	urlobj = urllib.urlopen(kml)
	kmlfeed = urlobj.read()
	soup = BeautifulStoneSoup(kmlfeed)
	placemarks = soup.findAll('placemark')
	ret = {}
	for i in range(len(placemarks)):
		soup = BeautifulStoneSoup(str(placemarks[i]))
		long,lat = str(soup.findAll('coordinates')[0])[13:-14].split(',')
		ret[i] = {'venue':{'name': str(soup.findAll('name')[0])[6:-7],
				'updated': str(soup.findAll('updated')[0])[9:-10],
				'geolat': lat,
				'geolong': long,},
				'display': str(soup.findAll('description')[0])[13:-14],
				}
	return HttpResponse(simplejson.dumps(ret), mimetype='application/json')

def getVenue(venueId):
	print "get Venue"
	
def getUser(request):
	site = config.oauthsite['foursquare']
	if request.GET.has_key('uid'):
		request_url = 'http://api.playfoursquare.com/v1/user.json?uid='+request.GET['uid']
	else:
		request_url = 'http://api.playfoursquare.com/v1/user.json'
	this_user = User.objects.get(username=request.user.username)
	data = performRequest(request_url, site, this_user)
	return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def getFriends(request):
	site = config.oauthsite['foursquare']
	request_url = 'http://api.playfoursquare.com/v1/checkins.json'
	this_user = User.objects.get(username=request.user.username)

	data = performRequest(request_url, site, this_user)

	#change the picture location for this user
	print "Friend Data"
	######ERROR CASE!!!!
	data = '{"checkins":[{"id":959567,"user":{"id":9546,"firstname":"Terry","lastname":"Chay","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/9546_1238974047.jpg","gender":"male"},"venue":{"id":30936,"name":"Steffs Bar","address":"141 2nd St","crossstreet":"Mission and 2nd","geolat":37.7876,"geolong":-122.399},"display":"Terry C. @ Steffs Bar","created":"Fri, 04 Sep 09 02:10:15 +0000"},{"id":955635,"user":{"id":958,"firstname":"Rod","lastname":"Begbie","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/4a5f997bbd132.jpg","gender":"male"},"venue":{"id":41551,"name":"Slide, Inc.","address":"301 Brannan St","crossstreet":"2nd","geolat":37.7814,"geolong":-122.392},"display":"Rod B. @ Slide, Inc.","created":"Thu, 03 Sep 09 21:50:22 +0000"},{"id":954599,"user":{"id":36678,"firstname":"Andy","lastname":"Denmark","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/blank_boy.png","gender":"male"},"venue":{"id":51018,"name":"Tripit","address":"444 De Haro St","crossstreet":"17th St","geolat":37.7642,"geolong":-122.402},"display":"Andy D. @ Tripit","created":"Thu, 03 Sep 09 20:04:48 +0000"},{"id":954569,"user":{"id":13250,"firstname":"Roderic","lastname":"Campbell","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/13250_1242521904.jpg","gender":"male"},"venue":{"id":38901,"name":"Whole Foods - Potrero Hill","address":"450 Rhode Island St","crossstreet":"17th St","geolat":37.7642,"geolong":-122.402},"display":"Roderic C. @ Whole Foods - Potrero Hill","shout":"Bean salad","created":"Thu, 03 Sep 09 20:02:24 +0000"},{"id":954434,"user":{"id":19282,"firstname":"Beth","lastname":"Hamilton","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/4a5b6757a8ae3.jpg","gender":"female"},"venue":{"id":65300,"name":"Crepevine - Berkeley","address":"1600 Shattuck Ave","crossstreet":"Cedar Street","geolat":37.8784,"geolong":-122.269},"display":"Beth H. @ Crepevine - Berkeley","shout":"No potatoes","created":"Thu, 03 Sep 09 19:49:29 +0000"},{"id":953743,"user":{"id":13739,"firstname":"Jacob","lastname":"Robinson","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/blank_boy.png","gender":"male"},"display":"Jacob R. @ [off the grid]","created":"Thu, 03 Sep 09 18:48:05 +0000"},{"id":949410,"user":{"id":13202,"firstname":"Bobby","lastname":"Joe","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/4a75e658bfc2e.jpg","gender":"male"},"venue":{"id":30547,"name":"Farmer Brown","address":"25 Mason","crossstreet":"Market","geolat":37.7839,"geolong":-122.409},"display":"Bobby J. @ Farmer Brown","created":"Thu, 03 Sep 09 04:02:57 +0000"},{"id":948685,"user":{"id":14285,"firstname":"Jesse","lastname":"Hammons","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/14285_1243723179.jpg","gender":"male"},"venue":{"id":32052,"name":"Citizen Space","address":"425 2nd St","crossstreet":"Harrison","geolat":37.7841,"geolong":-122.394},"display":"Jesse H. @ Citizen Space","created":"Thu, 03 Sep 09 02:54:27 +0000"},{"id":948429,"user":{"id":17608,"firstname":"Anna","lastname":"Lin","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/blank_girl.png","gender":"female"},"venue":{"id":22443,"name":"Sushi Ran","address":"107 Caledonia St","crossstreet":"at Pine","geolat":37.8587,"geolong":-122.486},"display":"Anna L. @ Sushi Ran","created":"Thu, 03 Sep 09 02:35:53 +0000"},{"id":944562,"user":{"id":466,"firstname":"Coley","lastname":"Wopperer","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/466_1236303556.jpg","gender":"female"},"venue":{"id":41288,"name":"Chez Colvin","address":"Connecticut St","crossstreet":"20th","geolat":37.7581,"geolong":-122.397},"display":"Coley W. @ Chez Colvin","created":"Wed, 02 Sep 09 22:09:03 +0000"},{"id":939362,"user":{"id":8829,"firstname":"Matt","lastname":"Billenstein","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/blank_boy.png","gender":"male"},"venue":{"id":2886,"name":"The Mint / Hot N Chunky","address":"1942 Market St","geolat":37.7703,"geolong":-122.426},"display":"Matt B. @ The Mint / Hot N Chunky","created":"Wed, 02 Sep 09 07:39:47 +0000"},{"id":924295,"user":{"id":2954,"firstname":"Adam","lastname":"Christian","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/2954_1237321147.jpg","gender":"male"},"venue":{"id":19061,"name":"Primo Patio Cafe","address":"214 Townsend St","geolat":37.7785,"geolong":-122.393},"display":"Adam C. @ Primo Patio Cafe","created":"Mon, 31 Aug 09 21:40:59 +0000"},{"id":915643,"user":{"id":32311,"firstname":"Alexander","lastname":"Shusta","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/blank_boy.png","gender":"male"},"venue":{"id":37545,"name":"Californias Great America","address":"4701 Great America Pkwy","crossstreet":"at Old Glory Ln","geolat":37.3999,"geolong":-121.978},"display":"Alexander S. @ Californias Great America","created":"Mon, 31 Aug 09 02:14:31 +0000"},{"id":910208,"user":{"id":11333,"firstname":"Morgan","lastname":"Sherwood","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/11333_1240256594.jpg","gender":"female"},"venue":{"id":46457,"name":"Starbucks - 4th & Brannan","address":"490 Brannan St","crossstreet":"at 4th St","geolat":37.7789,"geolong":-122.396},"display":"Morgan S. @ Starbucks - 4th & Brannan","created":"Sun, 30 Aug 09 19:36:29 +0000"},{"id":895871,"user":{"id":35364,"firstname":"jinen","lastname":"kamdar","photo":"http://playfoursquare.s3.amazonaws.com/userpix_thumbs/blank_boy.png","gender":"male"},"venue":{"id":75686,"name":"Jamba Juice","address":"22 Battery","crossstreet":"Market","geolat":37.7916,"geolong":-122.399},"display":"jinen k. @ Jamba Juice","created":"Sat, 29 Aug 09 19:00:12 +0000"}]}'
	print data
	strippedData = data.replace("'", "")
	print "stripped data"
	print strippedData
	print "fail eval"
	data = eval(strippedData)
	for checkin in data['checkins']:
		img_url = checkin['user']['photo']
		print img_url
		#Till we figure out the "decoder jpeg not available"
		cachedImg = getUserPhoto(img_url)
		#cachedImg = img_url
		checkin['user']['photo'] = cachedImg
	str(data)
	json = simplejson.dumps(data)
	return HttpResponse(json, mimetype='application/json')
