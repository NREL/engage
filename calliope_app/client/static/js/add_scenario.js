var scenario_id = null,
	scenario_name = null;

$( document ).ready(function() {

	$('#master-cancel').removeClass('hide');

	$('#scenario').on('change keyup paste', function() {
		scenario_name = $(this).val();
		check_save_ready();
	});

	$('#master-save').on('click', function() {
		var model_uuid = $('#header').data('model_uuid');
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/api/add_scenario/',
			type: 'POST',
			data: {
				'model_uuid': model_uuid,
				'scenario_id': scenario_id,
				'scenario_name': scenario_name,
				'csrfmiddlewaretoken': getCookie('csrftoken'),
			},
			dataType: 'json',
			success: function (data) {
				location.href = "/"+model_uuid+"/scenarios/";
			}
		});
	});

	$('#master-cancel').on('click', function() {
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/scenarios/';
	});

	$('.selection_tile').on('click', function() {
		$('.selection_tile').removeClass('active')
		$(this).addClass('active')
		scenario_id = $(this).data('scenario_id')
	});

	placeholder_blinker();

});

function check_save_ready() {
	if (scenario_name != null) {
		if (scenario_name.length > 0) {
			$('#master-save').removeClass('hide');
		} else {
			$('#master-save').addClass('hide');
		};
	} else {
		$('#master-save').addClass('hide');
	}
}