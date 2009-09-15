function doneLoading(){
	$.getJSON("/twitter/", gotData);
}

function tagTweet(tweet, twitter_id){
	tags = document.getElementById(tweet).value
	$.getJSON("/twittertag?tags="+tags+"&tweet="+tweet+"&twitter_id="+twitter_id, gotTweetTags);
}

function gotTweetTags(data){
	alert(data)
}

function makeStatusRow(id, twitter_id, img, user, text, tags){
	var newdiv = document.createElement('div');
	newdiv.innerHTML = "<img src="+img+"> <b> "+user+" <i>"+twitter_id+
						"</i></b> : "+text+" "+id
						+"<br><input type=\"text\" id=\""+id+"\" name=\"test\">"
						+"<a href=\"#\" onClick=\"tagTweet("+id+", \'"+twitter_id+"\')\">"
						+"Tagit</a>"
						for (i=0; i < tags.length; i++){
							//newdiv.innerHTML += tags[i].tag
							newdiv.innerHTML += "<font color=greet>"+ tags[i].count+" "+tags[i].tag+" </font>"
						}
						//+"<form action=\"tagTweet(\""+id+"\");\" method=\"post\">"
						//+"tags:"
						//+"<input type=\"text\" name=\"tags\">"
						//+"<input type=\"hidden\" name=\"tweet\" value=\""+id+"\">"
						//+"<input type=\"submit\" value=\"Tag\">"
//
						//+"<a onClick=\"tagTwee1t(tweet)\">Tag These</a></form>"
						//+" <br><label for='tags-ajax'>Tags:</label> "+
						//"<input class='wide' type='text' name='tags-ajax' value='' id='tags-ajax' /> "
	return newdiv
}

function gotData(data){
		var newdiv = document.createElement('div');
		//newdiv.innerHTML = " <br><label for='tags-ajax'>Tags:</label> <input class='wide' type='text' name='tags-ajax' value='' id='tags-ajax' /> "
		var twitterbody = document.getElementById("twitterclientbody")	
		$.each(data, function(i, item){
			var text = item.text;
			var user = item.user.name
			var img = item.user.profile_image_url
			var screen_name = item.user.screen_name
			var id = item.id
			var tags = item.tags
			//twitterbody.appendChild(newdiv)
			twitterbody.appendChild(makeStatusRow(id, screen_name, img, user, text, tags))
	}
	);
}
