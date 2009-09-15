from django.shortcuts import render_to_response, HttpResponseRedirect
from django.contrib.auth import logout
from historilator import views as historilator

def test(request):
	ret = {}
	#if True:
		#return HttpResponseRedirect("http://www.facebook.com/login.php?v=1.0&api_key=e7a58d119544c26309adc80a5706f3c9&next=localhost:8000/fbtripit&canvas=")
	authenticated = request.user.is_authenticated()
	ret['loggedIn'] = authenticated
	#if not authenticated:
		#need to get the authentication link
		#historilator.doAuthorizeStep()
	print "I'm inthe fb view"
	return render_to_response('fb.html', ret)
