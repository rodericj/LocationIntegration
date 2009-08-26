# Create your views here.
from LocationIntegration.historilator.models import Auth_temp_storage

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson

import urllib
import urllib2
import logging
import config
import tripit

@login_required(redirect_field_name='login')
def start(request):
    ret = {}
    ret['username'] = request.user.username
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
	stage=config.storage_stage['first']
	ret = {}
	ret['username'] = request.user.username
	this_user = User.objects.get(username=request.user.username)
	
	ret['foursquare_link'] = doAuthorizeStep(this_user, 'foursquare')
	ret['tripit_link'] = doAuthorizeStep(this_user, 'tripit')

	return render_to_response('login.html', ret)

def auth(request):
	this_user = User.objects.get(username=request.user.username)
	if request.META['HTTP_REFERER'].count('tripit'):
		site = config.oauthsite['tripit']
	elif request.META['HTTP_REFERER'].count('playfoursquare'):
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

def doAuthorizeStep(this_user, site_name):
		site = config.oauthsite[site_name]
		print "Starting " + site_name + " OAuth Process"
		oauth_credential = tripit.OAuthConsumerCredential(oauth_consumer_key=site['consumer_key'], oauth_consumer_secret=site['consumer_secret'])
	
		t = tripit.TripIt(oauth_credentials = oauth_credential, api_url = site['api_url'])
		
		request_token_batch = t.get_request_token()
		request_token = request_token_batch['oauth_token']
		request_token_secret = request_token_batch['oauth_token_secret']

		link = site['api_authorize_url']+"?oauth_token="+request_token
	
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
	return data

def getUser(request):
	print "in getUser"
	site = config.oauthsite['foursquare']
	if request.GET.has_key('uid'):
		request_url = 'http://api.playfoursquare.com/v1/user.json?uid='+request.GET['uid']
	else:
		request_url = 'http://api.playfoursquare.com/v1/user.json'
	this_user = User.objects.get(username=request.user.username)
	
	data = performRequest(request_url, site, this_user)
	print simplejson.dumps(data)
	return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def getMyCheckins(request):
	site = config.oauthsite['foursquare']
	request_url = 'http://api.playfoursquare.com/v1/checkins.json'
	this_user = User.objects.get(username=request.user.username)

	data = performRequest(request_url, site, this_user)
	json = simplejson.dumps(data)
	return HttpResponse(json, mimetype='application/json')
