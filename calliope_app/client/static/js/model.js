$( document ).ready(function() {

	// Add model
	$('#add_model_comment_btn').on('click', function() {

		var model_uuid = $('#header').data('model_uuid');
		var comment = $.trim($("#model_comment").val());

		if (comment != '') {
			$("#add_model_comment_btn").attr("disabled", true);
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/add_model_comment/',
				type: 'POST',
				data: {
					'model_uuid': model_uuid,
					'comment': comment,
					'csrfmiddlewaretoken': getCookie('csrftoken'),
				},
				dataType: 'json',
				success: function (data) {
					if (data['message'] == 'Added comment.') {
						location.reload();
					} else {
						$('#comment_message').text(data['message']);
						$('#comment_message').removeClass('hide');
						$("#add_model_comment_btn").attr("disabled", false);
					}
				}
			});
		};

	});

	$('#snapshot_model_btn').on('click', function() {

		var model_uuid = $('#header').data('model_uuid');

		$('#snapshot_model_btn').addClass('hide');
		$('#snapping').removeClass('hide');

		$.ajax({
			url: '/' + LANGUAGE_CODE + '/api/duplicate_model/',
			type: 'POST',
			data: {
				'model_uuid': model_uuid,
				'csrfmiddlewaretoken': getCookie('csrftoken'),
			},
			dataType: 'json',
			success: function (data) {
				alert('Initiating a snapshot. Check back on this page later to find a link to it below');
			},
			error: function () {
				$('#snapping').addClass('hide');
				$('#snap_fail').removeClass('hide');
			}
		});

	});

	$('.activity-header').on('click', function() {
		var rows = $(this).nextUntil('.activity-header').not('.comment-activity, .version-activity');
		if ($(this).hasClass('hiding_rows')) {
			rows.removeClass('hide');
			$(this).removeClass('hiding_rows');
			$(this).find('.fa-caret-up').removeClass('hide');
			$(this).find('.fa-caret-down').addClass('hide');
		} else {
			rows.addClass('hide');
			$(this).addClass('hiding_rows');
			$(this).find('.fa-caret-up').addClass('hide');
			$(this).find('.fa-caret-down').removeClass('hide');
		}
	});
});