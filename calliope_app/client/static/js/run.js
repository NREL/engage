var metrics = ['Production', 'Consumption', 'Storage', 'Costs'],
	labels = ['Production Capacity', 'Consumption Capacity', 'Storage Capacity', 'Fixed Cost'],
	units = ['kW', 'kW', 'kWh', '$'],
	hold_refresh = false,
	pause_start = null,
	pause_interval = null,
	submitdata = {},
	refreshTimeout,
	month_dict = {
		'01': 'January',
		'02': 'February',
		'03': 'March',
		'04': 'April',
		'05': 'May',
		'06': 'June',
		'07': 'July',
		'08': 'August',
		'09': 'September',
		'10': 'October',
		'11': 'November',
		'12': 'December'
	}

$(document).ready(function () {

	// Resize Dashboard
	splitter_resize();

	// Switch Scenarios
	$('#scenario').on('change', get_scenario);
	get_scenario();

	// New Scenario
	$('#master-new').on('click', function () {
		var model_uuid = $('#header').data('model_uuid'),
			scenario_id = $("#scenario option:selected").data('id');
		window.location = '/' + model_uuid + '/add_runs/' + scenario_id;
	});

	submitdata['model_uuid'] = $('#header').data('model_uuid');
	submitdata['csrfmiddlewaretoken'] = getCookie('csrftoken');

});

function get_scenario() {
	hold_refresh = false;
	clearInterval(pause_interval);
	$('#updates_paused').hide();
	var scenario_id = $("#scenario option:selected").data('id');
	if (scenario_id != undefined) {
		refresh_run_dashboard(true);
		$('#master-new').removeClass('hide');
	} else {
		$('#master-new').addClass('hide');
		toggle_viz_spinner(false);
		$('#build-error').html("No results yet...");
		$('#run_dashboard').html('<div class="col-12 text-center"><br/><br/><h4>Please create a scenario first!</h4></div>');
	}
}

function refresh_run_dashboard(open_viz) {
	var scenario_id = $("#scenario option:selected").data('id')
	if (hold_refresh == false) {
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/component/run_dashboard/',
			type: 'POST',
			data: {
				'model_uuid': $('#header').data('model_uuid'),
				'scenario_id': scenario_id,
				'csrfmiddlewaretoken': getCookie('csrftoken'),
			},
			dataType: 'json',
			success: function (data) {
				$('[data-toggle="tooltip"]').tooltip('hide')
				$('#run_dashboard').html(data['html'])
				$('[data-toggle="tooltip"]').tooltip()
				activate_runs();
				if (open_viz == true) {
					var vo = $('.btn-viz-outputs').first(),
						vl = $('.btn-viz-logs').first();
					if (vo.length > 0) {
						vo.click();
					} else if (vl.length > 0) {
						vl.click();
					} else {
						toggle_viz_spinner(false);
						$('#viz_logs_container').hide();
						$('#viz_outputs_container').hide();
						$('#build-error').html("No results yet...");
					}
				};
			}
		});
	};

	if (refreshTimeout) { clearTimeout(refreshTimeout) };
	refreshTimeout = setTimeout(function () {
		refresh_run_dashboard(false);
	}, 4000);
}

function timeSince(date) {
	var seconds = Math.floor((new Date() - date) / 1000);
	var interval = Math.floor(seconds / 31536000);
	if (interval > 1) {
		return interval + " years";
	}
	interval = Math.floor(seconds / 2592000);
	if (interval > 1) {
		return interval + " months";
	}
	interval = Math.floor(seconds / 86400);
	if (interval > 1) {
		return interval + " days";
	}
	interval = Math.floor(seconds / 3600);
	if (interval > 1) {
		return interval + " hours";
	}
	interval = Math.floor(seconds / 60);
	if (interval > 1) {
		return interval + " minutes";
	}
	return Math.floor(seconds) + " seconds";
}

function updatePauseTime() {
	$('#pause_time').text(timeSince(pause_start));
}

function bindEditable() {
	$(".run-description").editable("/" + LANGUAGE_CODE + "/api/update_run_description/", {
		type: "textarea",
		event: "dblclick",
		before: function () {
			hold_refresh = true;
			pause_start = new Date();
			updatePauseTime();
			pause_interval = setInterval(updatePauseTime, 1000);
			$('#updates_paused').show();
			$('.run-description').unbind();
		},
		callback: function (result, settings, submitdata) {
			hold_refresh = false;
			clearInterval(pause_interval);
			$('#updates_paused').hide();
			bindEditable();
		},
		cssclass: '',
		maxlength: 2000,
		placeholder: '&nbsp;&nbsp;-&nbsp;&nbsp;',
		onreset: function () {
			hold_refresh = false;
			clearInterval(pause_interval);
			$('#updates_paused').hide();
			bindEditable();
		},
		submit: '<button class="btn btn-success"><i class="fas fa-save" /> Save</button>',
		cancel: '<button class="btn btn-danger"><i class="fas fa-times" /> Cancel</button>',
		submitdata: submitdata,
		tooltip: "Double-click to edit...",
		cols: 50,
		rows: 4
	});
}

function toggle_viz_spinner(on) {
	$('#build-error').html("");
	if (on == true) {
		$('.viz-spinner').show();
		// $('#viz_logs_container').hide();
		// $('#viz_outputs_container').hide();
	} else {
		$('.viz-spinner').hide();
	};
}

function activate_runs() {

	bindEditable();
	select_run_row();

	$('.btn-run-inputs').unbind();
	$('.btn-run-inputs').on('click', function () {
		var run_id = $(this).data('run_id')

		$.ajax({
			url: '/' + LANGUAGE_CODE + '/api/optimize/',
			type: 'POST',
			data: {
				'model_uuid': $('#header').data('model_uuid'),
				'run_id': run_id,
				'csrfmiddlewaretoken': getCookie('csrftoken'),
			},
			dataType: 'json',
			success: function (data) {
				refresh_run_dashboard();
			}
		});
	});
	$('.btn-run-inputs').click();

	$('.btn-viz-logs').unbind();
	$('.btn-viz-logs').on('click', function () {
		toggle_viz_spinner(true);
		var run_id = $(this).data('run_id');
		$('#run_outputs').attr('data-run_id', run_id);
		select_run_row();
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/component/show_logs/',
			type: 'POST',
			data: {
				'model_uuid': $('#header').data('model_uuid'),
				'run_id': run_id,
				'csrfmiddlewaretoken': getCookie('csrftoken'),
			},
			success: function (data) {
				toggle_viz_spinner(false);
				$('#viz_logs_container').show().html(data);
				$('#viz_outputs_container').hide();
			},
			error: function () {
				toggle_viz_spinner(false);
				$('#viz_logs_container').hide();
				$('#viz_outputs_container').hide();
				$('#build-error').html("An error occurred...");
			}
		});
	});

	$('.btn-viz-outputs').unbind();
	$('.btn-viz-outputs').on('click', function () {
		toggle_viz_spinner(true);
		var run_id = $(this).data('run_id');
		$('#run_outputs').attr('data-run_id', run_id);
		select_run_row();
		get_viz_outputs();
	});

	$('.btn-map-outputs').unbind();
	$('.btn-map-outputs').on('click', function () {
		if (
			(window.navigator.userAgent.indexOf("MSIE ") > -1) ||
			(!!window.MSInputMethodContext && !!document.documentMode) ||
			(!(window.ActiveXObject) && "ActiveXObject" in window)
		) {
			$('#build-error').html('Internet Explorer does not support the map visualization. Please use ' +
				'<a href="https://www.firefox.com/" target="_blank" rel="noreferrer">Firefox</a> or ' +
				'<a href="https://www.google.com/chrome/" target="_blank" rel="noreferrer">Chrome</a>.');
			return false;
		}
	});

	$('.run-delete').unbind();
	$('.run-delete').on('click', function () {
		var run_id = $(this).data('run_id');
		var confirmation = confirm('This will permanently remove all input and output files for this run.\nAre you sure you want to delete?');
		if (confirmation) {
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/delete_run/',
				type: 'POST',
				data: {
					'model_uuid': $('#header').data('model_uuid'),
					'run_id': run_id,
					'csrfmiddlewaretoken': getCookie('csrftoken'),
				},
				dataType: 'json',
				complete: function (data) {
					$('#viz_logs_container').hide();
					$('#viz_outputs_container').hide();
					$('#build-error').html("Run deleted...");
				}
			});
		};
	});

	$('.run-cambium').unbind();
	$('.run-cambium').on('click', function () {
		var url = $('#header').data('cambium_url');
		var win = window.open(url, '_blank');
		if (win) { win.focus() } else { alert('Please allow popups for this website') };
	});

	$('.run-publish').unbind();
	$('.run-publish').on('click', function () {
		var run_id = $(this).data('run_id');
		var confirmation = confirm('Are you sure you want to publish these results?\nAnyone with the link will be able to access this data!');
		if (confirmation) {
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/publish_run/',
				data: {
					'model_uuid': $('#header').data('model_uuid'),
					'run_id': run_id,
					'csrfmiddlewaretoken': getCookie('csrftoken'),
				},
				type: 'POST',
				dataType: 'json',
				success: function (data) {
					console.log(data);
					refresh_run_dashboard();
				}
			});
		};
	});

	$('.run-version-old').unbind();
	$('.run-version-old').on('click', function () {
		$(this).html('<i class="fas fa-spinner fa-spin"></i>');
		$(this).attr('disabled', true);
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/api/build/',
			data: {
				'model_uuid': $('#header').data('model_uuid'),
				'scenario_id': $("#scenario option:selected").data('id'),
				'start_date': $(this).attr('data-dates').split(' to ')[0],
				'end_date': $(this).attr('data-dates').split(' to ')[1],
				'cluster': $(this).attr('cluster')
			},
			dataType: 'json',
			success: function (data) {
				console.log(data['status']);
			}
		});
	});

	$('#run_carrier, #run_location, #run_month').unbind();
	$('#run_carrier, #run_location, #run_month').on('change', function () {
		toggle_viz_spinner(true);
		get_viz_outputs();
	});

	$('.btn-upload-outputs').unbind();
	$('.btn-upload-outputs').on('click', function () {
		var run_id = $(this).data('run_id');
		console.log(run_id);
		//hold_refresh = true;
		//$('.file-add-row').toggleClass('hide');
		$('#submit_outputs').click();

		var model_uuid = $('#header').data('model_uuid');

		var uploadForm = document.createElement('form');
		uploadForm.id = 'uploadForm';
		uploadForm.method = 'post';
		uploadForm.action = '/' + LANGUAGE_CODE + '/api/upload_outputs/';
		uploadForm.enctype = 'multipart/form-data';
		var modelInput = document.createElement('input');
		modelInput.name = 'model_uuid';
		modelInput.value = model_uuid;
		uploadForm.appendChild(modelInput);
		var runInput = document.createElement('input');
		runInput.name = 'run_id';
		runInput.value = run_id;
		uploadForm.appendChild(runInput);
		var csrfInput = document.createElement('input');
		csrfInput.name = 'csrfmiddlewaretoken';
		csrfInput.value = getCookie('csrftoken');
		uploadForm.appendChild(csrfInput);
		var fileInput = document.createElement('input');
		var submit_outputs = document.createElement('input');
		submit_outputs.type = 'submit';
		submit_outputs.id = 'submit_outputs';
		uploadForm.appendChild(submit_outputs);

		fileInput.type = 'file';
		fileInput.name = 'myfile';
		fileInput.multiple = false;
		fileInput.onchange = function () {

			$('#submit_outputs').click();
			uploadForm.remove();
		};

		uploadForm.appendChild(fileInput);
		$(document.body.append(uploadForm));
		fileInput.click();


	});

};

function get_viz_outputs() {
	var carrier = $('#run_carrier').val(),
		location = $('#run_location').val(),
		month = $('#run_month').val(),
		run_id = $('#run_outputs').attr('data-run_id');
	$.ajax({
		url: '/' + LANGUAGE_CODE + '/component/plot_outputs/',
		type: 'POST',
		data: {
			'model_uuid': $('#header').data('model_uuid'),
			'run_id': run_id,
			'carrier': carrier,
			'location': location,
			'month': month,
			'csrfmiddlewaretoken': getCookie('csrftoken'),
		},
		success: function (data) {
			toggle_viz_spinner(false);
			$('#viz_logs_container').hide();
			$('#viz_outputs_container').show();
			render_barcharts(data);
			render_timeseries(data);
			update_viz_options(data['options']);
		},
		error: function () {
			toggle_viz_spinner(false);
			$('#viz_logs_container').hide();
			$('#viz_outputs_container').hide();
			$('#build-error').html("An error occurred...");
		}
	});
}

function update_viz_options(options) {
	// Carriers
	var carrier_options = [],
		last_carrier = $("#run_carrier").val();
	options['carrier'].forEach(function (val) { carrier_options.push({ text: val, value: val }) });
	$("#run_carrier").replaceOptions(carrier_options);
	if (options['carrier'].includes(last_carrier)) { $("#run_carrier").val(last_carrier) };
	// Locations
	var loc_options = [{ text: 'All Locations', value: '' }],
		last_location = $("#run_location").val();
	options['location'].forEach(function (val) { loc_options.push({ text: val.replace('_', ' '), value: val }) });
	$("#run_location").replaceOptions(loc_options);
	if (options['location'].includes(last_location)) { $("#run_location").val(last_location) };
	// Months
	if (options['month'].length > 0) {
		var month_options = [],
			last_month = $("#run_month").val();
		options['month'].forEach(function (val) { month_options.push({ text: month_dict[val], value: val }) });
		$("#run_month").replaceOptions(month_options);
		if (options['month'].includes(last_month)) { $("#run_month").val(last_month) };
		$("#run_month, label[for='run_month']").show();
	} else {
		$("#run_month, label[for='run_month']").hide();
	}
}

function select_run_row() {
	var run_id = $('#run_outputs').attr('data-run_id'),
		row = $('tr[data-run_id="' + run_id + '"]');
	$('tr').removeClass('table-primary');
	row.addClass('table-primary');
}

(function ($, window) {
	$.fn.replaceOptions = function (options) {
		var self, $option;
		this.empty();
		self = this;
		$.each(options, function (index, option) {
			$option = $("<option></option>")
				.attr("value", option.value)
				.text(option.text);
			self.append($option);
		});
	};
})(jQuery, window);
