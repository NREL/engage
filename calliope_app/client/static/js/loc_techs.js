var map_mode = 'loc_techs';

$( document ).ready(function() {

	initiate_units();

	$('#master-new').remove();

	$('#technology').on('change', function() {
		get_loc_techs();
	});

	get_loc_techs();

	// Save modified parameters
	$('#master-save').on('click', function() {

		if (validate_params()) {

			var form_data = filter_param_inputs($("#form_data :input")).serializeJSON();

			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/update_loc_tech_params/',
				type: 'POST',
				data: {
					'model_uuid': $('#header').data('model_uuid'),
					'loc_tech_id': $('tr.loc_tech_row.table-primary').data('loc_tech_id'),
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

	$('#master-cancel').on('click', function() {
		window.onbeforeunload = null;
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/loc_techs/';
	});

});