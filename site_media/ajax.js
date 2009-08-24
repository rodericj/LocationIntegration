<script>

function getCheckins(){
	$.getJSON("/getMyCheckins/",
        function(data){
			alert("hi");
        });
}



//function getCheckins() {
  //$.getJSON("/getMyCheckins/", 
//{ 
//pk:{{ object.pk }}, 
//vote: kind }, 
//function(json){
    //alert("Was successful?: " + json['success']);
  //}
//);
//}


//function getCheckins(){
//	$.getJSON("/getMyCheckins", { pk:{{ object.pk }}, vote: kind }, function(json){
 //   alert("Was successful?: " + json['success']);
//	});
function addClickHandlers() {
    $("#getMyCheckins").click( function() { getCheckins() });
 }
$(document).ready(addClickHandlers);


</script>
