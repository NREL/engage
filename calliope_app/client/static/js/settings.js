$(document).ready(function () {

	$('#model_uuid').on('change', function () {
		var model_uuid = $.trim($(this).val());
		filter_collaborators(model_uuid);
	})
	filter_collaborators($.trim($('#model_uuid').val()))

	// Add model
	$('#add_collaborator_btn, #add_collaborator_btn_view_only, #remove_collaborator_btn').on('click', function () {

		var model_uuid = $.trim($("#model_uuid").val());
		var collaborator_id = $.trim($("#collaborator_id").val());
		var collaborator_can_edit = $(this).data('collaborator_can_edit');

		if ((model_uuid != '') && (collaborator_id != '')) {
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/add_collaborator/',
				type: 'POST',
				data: {
					'model_uuid': model_uuid,
					'collaborator_id': collaborator_id,
					'collaborator_can_edit': +collaborator_can_edit,
					'csrfmiddlewaretoken': getCookie('csrftoken'),
				},
				dataType: 'json',
				success: function (data) {
					if (['Updated collaborator.', 'Added collaborator.', 'Collaborator removed.'].includes(data['message'])) {
						window.onbeforeunload = null;
						location.reload();
					} else {
						$('#collaborator_message').text(data['message']);
						$('#collaborator_message').removeClass('hide');
					}
				}
			});
		};

	});
});

function filter_collaborators(model_uuid) {
	if ($(".colab-row[data-uuid='" + model_uuid + "']").length > 0) {
		$(".colab-row").addClass('hide');
		$(".colab-row[data-uuid='" + model_uuid + "']").removeClass('hide');
	};
}