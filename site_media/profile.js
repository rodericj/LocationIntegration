var openWindow;
var maxlat = 0
var maxlon = 0
var minlat = 360
var minlon = 360
var mydata;
function placeMarker(map, item, content, markerFunction){
	var display = item.display;
	var lat = item.venue.geolat;
	var lon = item.venue.geolong;
	if (lat > maxlat) {  maxlat = lat;}
	if (lat < minlat) { minlat = lat;}

	if (lon > maxlon) { maxlon = lon;}
	if (lon < minlon) { minlon = lon;}

	//Make a point and put it on the map
	var point = new google.maps.LatLng(lat, lon);
	//toppoint = new google.maps.LatLng(maxlat, minlon)
	//bottompoint = new google.maps.LatLng(minlat, maxlon)
	//bounds = new google.maps.LatLngBounds(bottompoint, toppoint)
	//map.set_center(bounds.getCenter());
	map.set_center(point);
	var myOptions = {zoom:4, center:point,mapTypeId: google.maps.MapTypeId.ROADMAP,}
	var marker = markerFunction(point, item);

	google.maps.event.addListener(marker, 'click', function(){
		if(openWindow != undefined){
			openWindow.close()
		}	
		openWindow = infowindow
		openWindow.open(map,marker);
		
	});

	var shout = item.shout
	if (shout == null){
		shout = ''
	}
	var venueLink = 'http://playfoursquare.com/venue/'+item.venue.id

	var infowindow = new google.maps.InfoWindow({
    	content: content
	});

}

function buildfriendFoursquareCheckinPopup(item){
	var shout = item.shout
	if (shout == null){
		shout = ''
	}
	//handles the absurd case in foursquare where someone shouts and doesn't checkin. Kinda pointless
	if(item.venue == null){
		var venueLink = ''
		var venueName = ''
	}
	else{
		if(item.venue.name == null){
			var venueName = ''
		}
		else{
			var venueName = item.venue.name
		}
		var venueLink = 'http://playfoursquare.com/venue/'+item.venue.id
	}

	var ret = '<table><tr><td><a href=# onclick=getUser('+item.user.id+')><img src=\''
						+item.user.photo+'\'</td>'
						+'<td>'+item.user.firstname+' '
						+item.user.lastname
						+'</a><br>@<a href=\''
						+venueLink+'\'>'
						+venueName+'</a><br><i>'
						+shout+'</i> <img src=\'site_media/yelp.gif\'></td></tr></table>'
	return ret
}

function buildSelfPopup(item){
	var shout = item.shout
	if (shout == null){
		shout = ''
	}
	var venueLink = 'http://playfoursquare.com/venue/'+item.venue.id
	var ret = '<table><tr><td>You were @<a href=\''
						+venueLink+'\'>'
						+item.venue.name+'</a><br><i>'
						+shout+'</i> <img src=\'site_media/yelp.gif\'></td></tr></table>'
	return ret
}

function getUser(uid){
	$.getJSON("/getUser/?uid="+uid,
		function(data){
			a = eval("("+data+")");
			}
		);
}

function putStuffInProfilePane(data){
	//Take stuff from data
	x = eval("("+data+")");
	var first = x.user.firstname
	var last = x.user.lastname
	var city = x.user.city.name
	var photo = x.user.photo
	var gender = x.user.gender
	var checkin_time = x.user.checkin.created
	if (x.user.checkin.venue == null){
		var venue = ''
		var venue_link = ''
		var venue_name = ''
	}
	else{
		var venue_link = 'http://playfoursquare.com/venue/'+venue
		var venue = x.user.checkin.venue.id
		var venue_name = x.user.checkin.venue.name
	}
	var shout = x.user.checkin.shout
	var rss = x.user.settings.feeds_key
	if (shout == null){ shout = ''; }
	var userInfo = document.getElementById('userinfo');

	//setup the new div
	var newdiv = document.createElement('div');
	newdiv.innerHTML = "<img src = "+photo+">"+shout
						+"<br><b>"+first+" "+ last +"</b><br><a href="
						+venue_link+">"+venue_name+"</a><br><font size=1> "
						+ checkin_time
						+"<br><a href=# onclick=loadMyCheckins('"+rss+"')>my checkins</a>"
						+"<br><a href=# onclick=loadMyTrips()>my trips</a>"
						//+"<br><a href=# onclick=getRSS('"+rss+"')>333my checkins</a>"
						+"</font>"
	userInfo.appendChild(newdiv);
}

function toggleSiteData(form, site){
	x = site+"_checkbox"
	if(form.checkbox.checked){
		$.getJSON("/getFriends/", gotFriends)
	}
	else{

	}
	alert(form.checkbox.checked)	
}
function myMarker(point, item){
	return  marker = new google.maps.Marker({
		position: point,
		map: map,
		title: item.venue.name,
	});
}

function gotMyCheckins(data){
	var mydata = eval(data);
	$.each(mydata, function(i,item){
		if(item.venue != null){
			placeMarker(map, item, buildSelfPopup(item), myMarker)
		}
	});
}

function loadMyTrips(){
	$.getJSON("/getMyTrips/", gotMyCheckins);
}

function loadMyCheckins(feed){
	$.getJSON("/getMyCheckins/?rss="+feed, gotMyCheckins);
}

function friendMarkers(point, item){
	var image = new google.maps.MarkerImage(item.user.photo,
					new google.maps.Size(85, 100))
	return  marker = new google.maps.Marker({
		position: point,
		icon: image,
		map: map,
		//shadow: shadow,
		title: item.user.firstname + " " + item.user.lastname,
	});
}
function gotFriends(data){
	a = eval(data);
   	$.each(a['checkins'], function(i,item){
		if(item.venue != null){
			placeMarker(map, item, buildfriendFoursquareCheckinPopup(item), friendMarkers)
		}
	});
}

function doneLoading(){
	//set up the left panel some more
	$(".siteinfo .thebody").hide();
	$(".authorizedprofile .siteinfo ul")
		.prepend("<li class='readbody'><a href='' title='expand'>Expand</a></li>");
	$(".actions li.readbody a").click(function(event){
		$(this).parents("ul").prev(".thebody").toggle();
		event.preventDefault();
	});
		//$.getJSON("/getFriends/", gotFriends)
		$.getJSON("/getUser/", putStuffInProfilePane);
}

function facebook_onlogin(){
	//Do the backend login stuff
	$.getJSON("/fb_connect/", function(data){
			var loginArea = document.getElementById('signedIn');
			loginArea.innerHTML = '<fb:name uid="'+data.username+'" ></fb:name> <fb:profile-pic uid="'+data.username+'" facebook-logo="true" size="thumb" ></fb:profile-pic> <a id="logout_user" href="logout_user" onclick="FB.Connect.ifUserConnected(null,function() { window.location = "logout_user" }); FB.Connect.logoutAndRedirect("logout_user"); return false;">Sign out</a>'
		});
	//$.getJSON("/getFriends/", gotFriends)
}

