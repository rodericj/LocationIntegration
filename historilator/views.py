# Create your views here.
from LocationIntegration.historilator.models import Auth_temp_storage

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson
from BeautifulSoup import BeautifulStoneSoup

from datetime import datetime
import os
import time
import urllib
import urllib2
import logging
import config
import tripit
import feedparser
import cStringIO
import Image
import md5

def test(request):
	print "xd_receiver test"
	return render_to_response('test.html')

def logout_user(request):
	logout(request)
	return HttpResponseRedirect('/')
	#return render_to_response('profile.html', {})

# Generates signatures for FB requests/cookies
def get_facebook_signature(values_dict, is_cookie_check=False):
	signature_keys = []
	API_KEY = config.facebook['apikey']
	API_SECRET = config.facebook['secret']
	for key in sorted(values_dict.keys()):
		if (is_cookie_check and key.startswith(API_KEY + '_')):
			signature_keys.append(key)
		elif (is_cookie_check is False):
			signature_keys.append(key)

	if (is_cookie_check):
		signature_string = ''.join(['%s=%s' % (x.replace(API_KEY + '_',''), values_dict[x]) for x in signature_keys])
	else:
		signature_string = ''.join(['%s=%s' % (x, values_dict[x]) for x in signature_keys])
	signature_string = signature_string + API_SECRET

	return md5.new(signature_string).hexdigest()

def fb_connect(request):
	data = {}
	REST_SERVER = 'http://api.facebook.com/restserver.php'
	api_key =  config.facebook['apikey']
	secret_key =  config.facebook['secret']
	cookies = request.COOKIES
	if not request.user.is_authenticated() and api_key in cookies:
		print "user is not authenticated and api key is in the cookies"
		if get_facebook_signature(cookies, True) == cookies[api_key]:
			print "facebook signature is the apikey"
			api_timestamp = datetime.fromtimestamp(float(cookies[api_key+"_expires"]))
			
			if(api_timestamp > datetime.now()):
				print "cookies not expired"
				fb_user= cookies[api_key+'_user']
				password = md5.new(fb_user+secret_key).hexdigest()
				try:
					print "Getting user based on connect login"
					django_user = User.objects.get(username=fb_user)
					user = authenticate(username=fb_user,
										password=password)
					if user is not None:
						if user.is_active:
							print "logging in"
							data['username'] = fb_user
							login(request, user)
							#self.facebook_user_is_authenticated = True	
						else:
							request.facebook_message = "Account disabled"
							delete_fb_cookies = True
					else:
						request.facebook_message = "Account problem error"	
						delete_fb_cookies = True
			
				except User.DoesNotExist:
					#There is no django account, make one
					# Make request to FB API to get user's first and last name
					print "user doesn't exist, creating one"
					user_info= { 'method': 'Users.getInfo', 'api_key': api_key,
									'call_id': time.time(), 'v': '1.0', 'uids': fb_user,
									'fields': 'first_name,last_name', 'format': 'json',
									}
					user_info_hash = get_facebook_signature(user_info)
					user_info['sig'] = user_info_hash 
					user_info= urllib.urlencode(user_info) 
					user_info_response  = simplejson.load(urllib.urlopen(REST_SERVER, user_info))
					print user_info_response
	
					user = User.objects.create_user(fb_user, '', password)
					user.first_name = user_info_response[0]['first_name']
					data['username'] = user.first_name
					user.last_name = user_info_response[0]['last_name']
					user.save()

					#Auth and login
					print "authenticating and logging in"
					user = authenticate(username=fb_user, password=password)
					if user is not None:
						if user.is_active:
							login(request, user)
							facebook_user_is_authenticated = True
						else:
							request.facebook_message = "Account disabled error"
							delete_fb_cookies = True
					else:
						request.facebook_message = "account problem error"
						delete_fb_cookies = True

			#cookie session expired
			else:
				print "session expired"
				logout(request)
				delete_fb_cookies = True

		#cookie values don't match hash
		else:
			print "cookie value don't match hash"
			logout(request)
			delete_fb_cookies = True
		#if get_facebook_signature(cookies, True) == cookies[apikey]:
			#api_timestamp = datetime.fromtimestamp(float(cookies[api_key+"_expires"]))
	else:
		print "User was already logged in"
	print "Data is: "+ str(data)

	return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def xd_receiver(request):
	print "xd_receiver view"
	return render_to_response('xd_receiver.html')

#@login_required(redirect_field_name='/login')
def start(request):
	print "in start"
	print type(request)
	ret = {}
	ret['username'] = request.user.username
	ret['services'] = ['foursquare', 'yelp']
	ret['fbkey'] = config.facebook['apikey']

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
	
	for i in config.oauthsite:
		print i
		ret[i+'_link'] = doAuthorizeStep(this_user, i, config.oauthsite[i].get('options', ''))

	return render_to_response('login.html', ret)

def tripitauth(request):
	return auth(request, site = config.oauthsite['tripit'])
	
def foursquareauth(request):
	return auth(request, site = config.oauthsite['foursquare'])
	
def twitterauth(request):
	return auth(request, site = config.oauthsite['twitter'])
	
def auth(request, site):
	this_user = request.user
	#this_user = User.objects.get(username=request.user.username)
	#if request.GET.get('site',0) == 'tripit':
		#site = config.oauthsite['tripit']
	#elif request.META.get('HTTP_REFERER', 0).count('foursquare'):
		#site = config.oauthsite['foursquare']
	#else:
		#logging.warn("Something is wrong. We are getting oauth requests NOT from a source supported")

	#from site specific config dict
	consumer_key = site['consumer_key']
	consumer_secret = site['consumer_secret']
	api_url = site['api_access_token_url']
	id = site['id']

	#need to get the oauth consumer secret and key from db (or preferably cache)
	key_row = Auth_temp_storage.objects.filter(user=request.user, site=id)
	print key_row
	request_token = key_row[0].token
	request_token_secret = key_row[0].token_secret

	oauth_credential = tripit.OAuthConsumerCredential(oauth_consumer_key=consumer_key, oauth_consumer_secret=consumer_secret, oauth_token=request_token, oauth_token_secret=request_token_secret)
	print oauth_credential
	print api_url
	t = tripit.TripIt(oauth_credentials = oauth_credential, api_url = api_url)
	access_token_batch = t.get_access_token()
	print access_token_batch
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

		#print request_token_batch
		request_token = request_token_batch['oauth_token']
		request_token_secret = request_token_batch['oauth_token_secret']

		link = site['api_authorize_url']+"?oauth_token="+request_token+options
	
		#need to save the request_token
		#delete all keys that already exist, we need to replace them
		this_user.auth_temp_storage_set.filter(site=site['id'], stage=config.storage_stage['first']).delete()
		tmp = this_user.auth_temp_storage_set.create(site=site['id'], token=request_token, token_secret=request_token_secret, stage=1)
	
		tmp.save()
		print link
		return link

def verifyRegisterParams(emailAddress, username, password, confirmpassword):
    #passwords are the same

    #emailAdd looks like an email addy
    return True

def getUserPhoto(img_path):
	img_name = img_path.split('/')[-1:][0]
	if True:
		return 'site_media/photos/'+img_path
	#should look up to see if the image is in our servers
	print "Trying to open file "+img_name
	if os.path.exists('site_media/photos/'+img_name):
		print "it exists"
		return 'site_media/photos/+img_name'
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
	print oauth_info
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
	kml = 'http://feeds.foursquare.com/history/17f32ec6b65e8577d3ea14b0806fd42f.kml'
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
		request_url = 'http://api.foursquare.com/v1/user.json?uid='+request.GET['uid']
	else:
		request_url = 'http://api.foursquare.com/v1/user.json'
	this_user = User.objects.get(username=request.user.username)
	data = performRequest(request_url, site, this_user)
	return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def getFriends(request):
	site = config.oauthsite['foursquare']
	request_url = 'http://api.foursquare.com/v1/checkins.json'
	this_user = User.objects.get(username=request.user.username)

	data = performRequest(request_url, site, this_user)

	#change the picture location for this user
	strippedData = data.replace("'", "")
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
