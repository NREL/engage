var map_mode = 'locations';

$(document).ready(function () {

	retrieve_map(false);

	$(function () {
		$('[data-toggle="tooltip"]').tooltip()
	});

	$('#model_name').on('change keyup paste', function () {
		if ($(this).val() == "") {
			$('#add_model_btn').removeClass('btn-success');
			$('#add_model_btn').addClass('btn-outline-success');
		} else {
			$('#add_model_btn').removeClass('btn-outline-success');
			$('#add_model_btn').addClass('btn-success');
		}
	});

	// Add model
	$('#add_model_btn').on('click', function () {

		var model_name = $.trim($("#model_name").val());
		var model_clean_name = $("<div>").html(model_name).text();
		var template_model_uuid = $("#add_model_template").val();

		if (model_clean_name != '') {
			$('#add_model_btn').addClass('hide');
			$('#adding').removeClass('hide');
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/add_model/',
				type: 'POST',
				data: {
					'model_name': model_clean_name,
					'template_model_uuid': template_model_uuid,
					'csrfmiddlewaretoken': getCookie('csrftoken'),
				},
				dataType: 'json',
				success: function (data) {
					if (data['message'] == undefined) {
						window.onbeforeunload = null;
						location.reload();
					} else {
						$('#add_model_btn').removeClass('hide');
						$('#adding').addClass('hide');
						$('#add_model_message').text(data['message']);
						$('#add_model_message').removeClass('hide');
						$('#add_model_btn').prop('selectedIndex', 0);
					}
				},
				error: function (data) {
					$('#add_model_message').text("Oops! An error occurred!");
					$('#add_model_message').removeClass('hide');
				}
			});
		} else {
			$('#add_model_btn').prop('selectedIndex', 0);
			alert('Please provide a name for your new model.');
		}
	});
	// Remove model
	$('.model-remove').on('click', function () {
		var model_uuid = $(this).data('model_uuid');
		var confirmation = confirm('Are you sure? You will be dropped as a collaborator!');
		if (confirmation) {
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/remove_model/',
				type: 'POST',
				data: {
					'model_uuid': model_uuid,
					'csrfmiddlewaretoken': getCookie('csrftoken'),
				},
				dataType: 'json',
				success: function (data) {
					location.reload();
				}
			});
		};
	});
});