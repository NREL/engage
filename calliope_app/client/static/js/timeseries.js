var ts_id = 0, file_id = 0;

$( document ).ready(function() {

	// file functions...
	$('.file-delete').on('click', function(){
		var row = $(this).parents('tr'),
			file_id = row.data('file_id');

		var confirmation = confirm('This will remove this file permanently. Are you sure you want to delete?');

		if (confirmation) {
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/delete_file/',
				type: 'POST',
				data: {
					'model_uuid': $('#header').data('model_uuid'),
					'file_id': file_id,
					'csrfmiddlewaretoken': getCookie('csrftoken'),
				},
				dataType: 'json',
				success: function (data) {
					location.reload();
				}
			});
		};
	});

	$('.file-add').on('click', function(){
		$('.file-add-row').toggleClass('hide');
	});

	$('.file-row').on('click', function() {
		file_id = $(this).data('file_id');
		select_file(true);
	});

	active_timeseries_table_click();
	refresh_timeseries_table(true);
	setInterval(function () {
		refresh_timeseries_table(false);
	}, 2000);

});


function refresh_timeseries_table(open_viz) {
	var model_uuid = $('#header').data('model_uuid');
	$.ajax({
		url: '/' + LANGUAGE_CODE + '/' + model_uuid + '/timeseries_table/',
		type: 'GET',
		success: function (response) {
			$('[data-toggle="tooltip"]').tooltip('hide')
			$("#timeseries-container").html(response);
			$('[data-toggle="tooltip"]').tooltip()
			select_file(false);
			select_timeseries(false);
			active_timeseries_table_click();
			if (open_viz == true) {
				var tr = $('.timeseries-row').first(),
					fr = $('.file-row').first();
				if (tr.length == 0) {
					fr.click();
				} else {
					tr.click();
				};
			};
		}
	});
}

function select_file(activate) {
	if (typeof activate !== 'boolean') activate = true;
	$('.file-row').removeClass('table-primary');
	var row = $('.file-row[data-file_id="' + file_id + '"]');
	row.addClass('table-primary');
	if (!activate) return;
	ts_id = 0;
	$('.timeseries-row').removeClass('table-primary');
	timeseries_new(file_id);
	timeseries_content(file_id, null);
}

function select_timeseries(activate) {
	if (typeof activate !== 'boolean') activate = true;
	$('.timeseries-row').removeClass('table-primary');
	var row = $('.timeseries-row[data-timeseries_id="' + ts_id + '"]');
	row.addClass('table-primary');
	if (!activate) return;
	file_id = 0;
	timeseries_new();
	$('.file-row').removeClass('table-primary');
	timeseries_content(null);
	$('.timeseries_viz').removeClass('hide');
	activate_charts(0, ts_id)
}


function active_timeseries_table_click() {

	$('.timeseries-delete').unbind();
	$('.timeseries-delete').on('click', function(e) {
		e.stopPropagation();

		var row = $(this).parents('tr'),
			timeseries_id = row.data('timeseries_id');

		var confirmation = confirm('This will remove this timeseries permanently. Are you sure you want to delete?');

		if (confirmation) {
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/delete_timeseries/',
				type: 'POST',
				data: {
					'model_uuid': $('#header').data('model_uuid'),
					'timeseries_id': timeseries_id,
					'csrfmiddlewaretoken': getCookie('csrftoken'),
				},
				dataType: 'json',
				success: function (data) {
					location.reload();
				}
			});
		};

	});

	$('.timeseries-row').unbind();
	$('.timeseries-row').on('click', function() {
		ts_id = $(this).data('timeseries_id');
		select_timeseries(true);
	});

	$('#timeseries_new_btn').unbind();
	$('#timeseries_new_btn').on('click', function() {
		$('#timeseries-container').toggleClass('hide');
		$('#timeseries-container-new').toggleClass('hide');
		$(this).toggleClass('btn-success btn-danger');
		var cancel = $(this).hasClass('btn-danger');
		var icon = $(this).find('i.fas').first();
		var text = cancel ? '&nbsp; Cancel' : ' Create Timeseries';
		icon.toggleClass('fa-plus fa-times');
		// replace button text:
		$(this).contents().filter(function() { return this.nodeType == 3; }).first().replaceWith(text);
	});

}

function timeseries_new(file_id) {
	var model_uuid = $('#header').data('model_uuid');

	if (typeof file_id !== 'undefined') {
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/component/timeseries_new/',
			data: {
			  'model_uuid': model_uuid,
			  'file_id': file_id
			},
			dataType: 'json',
			success: function (data) {
				$('#timeseries-container-new').html(data['html']);

				function updateHeader() {
					var hasHeader = $('#has_header').is(':checked');
					if (hasHeader) {
						$('.csv-header').show();
						$('.letter-header').hide();
						$('#timestamp_col option').each(function(i) {
							$(this).text(columns[i]);
						});
						$('#value_col option').each(function(i) {
							$(this).text(columns[i]);
						});
					} else {
						$('.csv-header').hide();
						$('.letter-header').show();
						$('#timestamp_col option').each(function(i) {
							$(this).text(letters[i]);
						});
						$('#value_col option').each(function(i) {
							$(this).text(letters[i]);
						});
					}
				}

				$('#has_header').on('click', updateHeader);
				updateHeader();

				$('#upload_timeseries').on('click', function() {
					var model_uuid = $('#header').data('model_uuid'),
						file_id = $('.file-row.table-primary').data('file_id'),
						timeseries_name = $('#timeseries_name').val(),
						loc_id = $('.content_navigation').data('loc_id'),
						timestamp_col = $('#timestamp_col').prop('selectedIndex'),
						value_col = $('#value_col').prop('selectedIndex'),
						has_header = $('#has_header').is(':checked');

					if (timeseries_name) {
						$.ajax({
							url: '/' + LANGUAGE_CODE + '/api/upload_timeseries/',
							data: {
								'model_uuid': model_uuid,
								'file_id': file_id,
								'timeseries_name': timeseries_name,
								'loc_id': loc_id,
								'timestamp_col': timestamp_col,
								'value_col': value_col,
								'has_header': has_header
							},
							dataType: 'json',
							success: function (data) {
								if (data['status'] === 'Success') {
									location.reload();
								} else {
									$('#error-message').html(data['message']);
									$('select, input').attr('disabled', false);
								};
							}
						});
					} else {
						$('#error-message').html('Must provide a name.');
					}
				});
			}
		});
	} else {
		$('#timeseries-container-new').html("<br><b>Choose a file from the left!</b>");
	};
};

function timeseries_content(file_id) {
	var model_uuid = $('#header').data('model_uuid');

	if (file_id != undefined) {
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/component/timeseries_content/',
			data: {
			  'model_uuid': model_uuid,
			  'file_id': file_id
			},
			dataType: 'json',
			success: function (data) {
				$('.timeseries_viz').addClass('hide');
				$('#timeseries-content').html(data['html']);
				$('#timeseries-placeholder').hide();
			}
		});
	} else {
		$('#timeseries-content').html("");
	};
};
