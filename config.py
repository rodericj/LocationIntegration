storage_stage = {
			'first':1,
			'second':2,
	}

facebook = {
	'apikey':'6866a1ec2beb71f4eb5040b057b24910',
	'secret':'69015ebc781a10ab98bd30c022caaed4'
	}
oauthsite = {
	'twitter':{
		'id' : 'tw',
		#'api_url' : 'https://twitter.com/twitter_app/oauth/request_token',
		'api_url' : 'http://twitter.com/',
		'api_access_token_url' : 'http://twitter.com/oauth/access_token',
		#'api_access_token_url' : 'http://twitter.com/',
		'api_authorize_url' : 'http://twitter.com/oauth/authorize',
		#'api_url' : 'https://twitter.com/oauth/request_token',
		#'api_access_token_url' : 'http://twitter.com/oauth/access_token',
		#'api_authorize_url' : 'http://twitter.com/oauth/authorize',
		'consumer_key' : 'N9cn8pDGJlCCgIPpGZJHCQ',
		'consumer_secret' : 'JzX4gNb97Yg98gQzibSaAG0dWPQVlA4M4XaewNsg',
	},
	'foursquare':{
		'id' : '4s',
		'api_url' : 'http://foursquare.com/oauth/request_token',
		'api_access_token_url' : 'http://foursquare.com/oauth/access_token',
		'api_authorize_url' : 'http://foursquare.com/oauth/authorize',
		'consumer_key' : '52e6db5e1d8bd8c481e8e1e3f798652004a7fbfc8',
		'consumer_secret' : '57c1aac04b076d8743664e2d935da13b',
	},
	'tripit':{
		'options' : '&oauth_callback=http://localhost:8000/auth?site=tripit',
		'id' : 'tr',
		'api_url' : 'https://api.tripit.com/oauth/request_token',
		'api_access_token_url' : 'https://api.tripit.com/oauth/access_token',
		'api_authorize_url' : 'https://www.tripit.com/oauth/authorize',
		'consumer_key' : 'a004e722790bbcc3ab628480b85bd7b76f2a783a',
		'consumer_secret' : '96de3bdf33bfa359718e71249394e4d9945b96b3',
	}
}
