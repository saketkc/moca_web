function encode_ajax_submit(encodeid){
	$.ajax({
		url: '/encode',
		dataType: 'json',
		method: 'POST',
		data: JSON.stringify({encodeid: encodeid}),
		error: function(xhr_data) {
		
		},
		success: function(xhr_data) {
			console.log(xhr_data);;
			if (xhr_data.status == 'error'){
				// Fix Me
				$("#encodetable").html("Errored:" + xhr_data.response['title']);
				$("#encodetable").removeClass("hide");
				
			}
			
			else{	
		
				$("#encodetable").removeClass("hide");
				$(".insertedrow").html("");
					for(i in xhr_data.peak_files){
						var f = xhr_data.peak_files[i];
						var url = '/encodejob/'+f.dataset+'/'+f.title;
						var str='<div class="row insertedrow" >'+
									'<div class="col-md-2">'+f.title+'</div>'+
									'<div class="col-md-3">'+f.file_type+'</div>'+
									'<div class="col-md-2">'+f.tech_repl_number+'</div>'+
									'<div class="col-md-2">'+f.bio_repl_number+'</div>'+
									'<div class="col-md-3"><a href="'+url+'" target="_blank"><button class="btn btn-primary btn-sm" class="runencode" id='+ f.title +'>Run</button></a></div>'+
								 '<div>';
									
										
						$("#encodetable").append(str);
					}
				}
		},           
		contentType: 'application/json'
	});
};

$("#encodesubmit").click(function(){
	encode_ajax_submit($("#encodeidinput").val());
});
