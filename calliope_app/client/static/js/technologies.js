$( document ).ready(function() {

	initiate_units();

	$('#master-new').removeClass('hide');

	if ($("#technology option").length == 0) {
		$('#tech_essentials').html('<div class="col-12 text-center"><br/><br/><h4>Create a technology by clicking the "+ New" button above!</h4></div>');
	} else {
		$('#technology').on('change', function() {
			get_tech_parameters();
		});
		get_tech_parameters();
	}

	// Save modified parameters
	$('#master-save').on('click', function() {

		if (validate_params()) {

			var form_data_1 = $("#form_data_1 :input").serializeJSON();
			var form_data_2 = filter_param_inputs($("#form_data_2 :input")).serializeJSON();
			var form_data = Object.assign({}, form_data_1, form_data_2);

			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/update_tech_params/',
				type: 'POST',
				data: {
					'model_uuid': $('#header').data('model_uuid'),
					'technology_id': $("#technology option:selected").data('id'),
					'form_data': JSON.stringify(form_data),
					'csrfmiddlewaretoken': getCookie('csrftoken'),
				},
				dataType: 'json',
				success: function (data) {
					window.onbeforeunload = null;
					location.reload();
				}
			});

		};
	});

	$('#master-new').on('click', function() {
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/add_technologies/';
	});

	$('#master-cancel').on('click', function() {
		window.onbeforeunload = null;
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/technologies/';
	});

	$('#master-bulk-up').removeClass('hide');
	$('#master-bulk-up').on('click', function(){
		var model_uuid = $('#header').data('model_uuid');
		//e.stopPropagation();
		var uploadForm = document.createElement('form');
		uploadForm.id = 'uploadForm';
		uploadForm.method='post';
		uploadForm.action='/' + LANGUAGE_CODE + '/api/upload_techs/';
		uploadForm.enctype = 'multipart/form-data';
		var modelInput = document.createElement('input');
		modelInput.name = 'model_uuid';
		modelInput.value = model_uuid;
		uploadForm.appendChild(modelInput);
		var csrfInput = document.createElement('input');
		csrfInput.name = 'csrfmiddlewaretoken';
		csrfInput.value = getCookie('csrftoken');
		uploadForm.appendChild(csrfInput);
    	var fileInput = document.createElement('input');
		var submit_outputs= document.createElement('input');
		submit_outputs.type = 'submit';
		submit_outputs.id = 'submit_outputs';
		uploadForm.appendChild(submit_outputs);

    	fileInput.type = 'file';
    	fileInput.name = 'myfile';
    	fileInput.multiple = false;
		fileInput.onchange = function(){

			$('#submit_outputs').click();
			uploadForm.remove();
		};

		uploadForm.appendChild(fileInput);
		$(document.body.append(uploadForm));
		fileInput.click();
	});

	$('#master-bulk-down').removeClass('hide');
	$('#master-bulk-down').attr("href", function() { return $(this).attr("href")+"&file_list=technologies"});

});
