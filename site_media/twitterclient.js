function doneLoading(){
	$.getJSON("/twitter/", gotData);
}

$(function () {
        $('#tags-ajax').tagSuggest({
            url: '/tagging',
            delay: 10
        });
});
function makeStatusRow(id, screen_name, img, user, text){
	var newdiv = document.createElement('div');
	newdiv.innerHTML = "<img src="+img+"> <b> "+user+" <i>"+screen_name+
						"</i></b> : "+text+
						" <br><label for='tags-ajax'>Tags:</label> "+
						"<input class='wide' type='text' name='tags-ajax' value='' id='tags-ajax' /> "
	return newdiv
}

function gotData(data){
		var newdiv = document.createElement('div');
		newdiv.innerHTML = " <br><label for='tags-ajax'>Tags:</label> <input class='wide' type='text' name='tags-ajax' value='' id='tags-ajax' /> "
		var twitterbody = document.getElementById("twitterclientbody")	
		$.each(data, function(i, item){
			var text = item.text;
			var user = item.user.name
			var img = item.user.profile_image_url
			var screen_name = item.user.screen_name
			var id = item.id
			twitterbody.appendChild(newdiv)
			twitterbody.appendChild(makeStatusRow(id, screen_name, img, user, text))
	}
	);
}
