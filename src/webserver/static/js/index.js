function toggler(divId) {
    $("#" + divId).toggle();
}
function ajax_request(job_id) {
  $.ajax({
    url: '/status/'+job_id, // JSON_URL is a global variable
    dataType: 'json',
    error: function(xhr_data) {
      // terminate the script
    },
    success: function(xhr_data) {
      if (xhr_data.status == 'pending') {
        // continue polling
      } else {
        success(xhr_data);
      }
    },
    contentType: 'application/json'
  });
}

$('#advancedbtn').click(function(){
	$('#advanced').toggleClass("hide");
});

function get_job_history(){
	if(localStorage["jobs"] != undefined){
		var jobs =  JSON.parse(localStorage["jobs"]);
		var html="";
		for(job in jobs){
			html += "<br/>" + "<a href='/results/"+jobs[job]+"'>" + jobs[job]+"</a>";
		}
		return html;
	}
	else{
		return "";
	}
}

$('#jobhistory').html(get_job_history());

