var technology_name = null,
	technology_id = null,
	technology_type = null;

$( document ).ready(function() {

	$('#master-cancel').removeClass('hide');

	$(function () {
	  $('[data-toggle="tooltip"]').tooltip()
	});

	$('#technology').on('change keyup paste', function() {
		technology_name = $(this).val();
		check_save_ready();
	});

	$('.selection_tile').on('click', function() {
		$('.selection_tile').removeClass('active')
		$(this).addClass('active')
		technology_type = $(this).data('abstract_tech')
		technology_id = $(this).data('technology_id')
		check_save_ready();
	});

	$('#master-save').on('click', function() {
		var model_uuid = $('#header').data('model_uuid');
		$("#master-save").attr("disabled", true);
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/api/add_technology/',
			type: 'POST',
			data: {
				'model_uuid': model_uuid,
				'technology_name': technology_name,
				'technology_id': technology_id,
				'technology_type': technology_type,
				'csrfmiddlewaretoken': getCookie('csrftoken'),
			},
			dataType: 'json',
			success: function (data) {
				location.href = "/"+model_uuid+"/technologies/";
			}
		});
	});

	$('#master-cancel').on('click', function() {
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/technologies/';
	});

	placeholder_blinker();

});

function check_save_ready() {
	if ((technology_name != null) & (technology_type != null)) {
		if ((technology_name.length > 0) & (technology_type.length > 0)) {
			$('#master-save').removeClass('hide');
		} else {
			$('#master-save').addClass('hide');
		};
	} else {
		$('#master-save').addClass('hide');
	}
}