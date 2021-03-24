var hold_refresh = false,
	pause_start = null,
	pause_interval = null,
	submitdata = {},
	refreshTimeout;

$( document ).ready(function() {

	$('#scenario').on('change', get_scenario);
	get_scenario();
	
	$('#master-new').on('click', function() {
		var model_uuid = $('#header').data('model_uuid'),
			scenario_id = $("#scenario option:selected").data('id');
		window.location = '/' + model_uuid + '/add_runs/' + scenario_id;
	});

	var scenario_id = $("#scenario option:selected").data('id');

	/* this will make the save.php script take a long time so you can see the spinner ;) */
	submitdata['model_uuid'] = $('#header').data('model_uuid');
	submitdata['csrfmiddlewaretoken'] = getCookie('csrftoken');

});

function get_scenario() {
	hold_refresh = false;
	clearInterval(pause_interval);
	$('#updates_paused').slideUp();
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
						$('#viz_logs_container').empty().hide();
						$('#viz_outputs_container').empty().show();
						$('#build-error').html("No results yet...");
					}
				};
			}
		});
	};

	if (refreshTimeout) { clearTimeout(refreshTimeout) };
	refreshTimeout = setTimeout(function() {
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
			before: function() {
				hold_refresh = true;
				pause_start = new Date();
				updatePauseTime();
				pause_interval = setInterval(updatePauseTime, 1000);
				$('#updates_paused').slideDown();
				$('.run-description').unbind();
			},
			callback: function(result, settings, submitdata) {
				hold_refresh = false;
				clearInterval(pause_interval);
				$('#updates_paused').slideUp();
				bindEditable();
			},
			cssclass: '',
			maxlength: 2000,
			placeholder: '&nbsp;&nbsp;-&nbsp;&nbsp;',
			onreset: function() {
				hold_refresh = false;
				clearInterval(pause_interval);
				$('#updates_paused').slideUp();
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
		$('#viz_logs_container').empty().hide();
		$('#viz_outputs_container').empty().show();
	} else {
		$('.viz-spinner').hide();
	};
}

function activate_runs() {
	
	bindEditable();

	$('.btn-run-inputs').unbind();
	$('.btn-run-inputs').on('click', function() {
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

	$('.btn-viz-logs').unbind();
	$('.btn-viz-logs').on('click', function() {
		toggle_viz_spinner(true);
		var run_id = $(this).data('run_id');
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
				$('#viz_outputs_container').empty().hide();
			},
			error: function () {
				toggle_viz_spinner(false);
				$('#viz_logs_container').empty().show();
				$('#viz_outputs_container').empty().hide();
				$('#build-error').html("An error occurred...");
			}
		});
	});

	$('.btn-viz-outputs').unbind();
	$('.btn-viz-outputs').on('click', function() {
		toggle_viz_spinner(true);
		var run_id = $(this).data('run_id');
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/component/plot_outputs/',
			type: 'POST',
			data: {
				'model_uuid': $('#header').data('model_uuid'),
				'run_id': run_id,
				'csrfmiddlewaretoken': getCookie('csrftoken'),
			},
			success: function (data) {
				toggle_viz_spinner(false);
				$('#viz_logs_container').empty().hide();
				$('#viz_outputs_container').show().html(data);
			},
			error: function () {
				toggle_viz_spinner(false);
				$('#viz_logs_container').empty().hide();
				$('#viz_outputs_container').empty().show();
				$('#build-error').html("An error occurred...");
			}
		});
	});

	$('.btn-map-outputs').unbind();
	$('.btn-map-outputs').on('click', function() {
		if (
			(window.navigator.userAgent.indexOf("MSIE ") > -1) ||
			(!!window.MSInputMethodContext && !!document.documentMode) ||
			(!(window.ActiveXObject) && "ActiveXObject" in window)
		) {
			$('#viz_outputs_container').show()
				.addClass('alert alert-danger')
				.html('Internet Explorer does not support the map visualization. Please use ' +
					'<a href="https://www.firefox.com/" target="_blank" rel="noreferrer">Firefox</a> or ' +
					'<a href="https://www.google.com/chrome/" target="_blank" rel="noreferrer">Chrome</a>.');
			return false;
		}
	});

	$('.run-delete').unbind();
	$('.run-delete').on('click', function() {
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
					$('#viz_logs_container').empty().hide();
					$('#viz_outputs_container').empty().show();
					$('#build-error').html("Run deleted...");
				}
			});
		};
	});

	$('.run-cambium').unbind();
	$('.run-cambium').on('click', function() {
		var url = $('#header').data('cambium_url');
		var win = window.open(url, '_blank');
		if (win) { win.focus() } else { alert('Please allow popups for this website') };
	});

	$('.run-publish').unbind();
	$('.run-publish').on('click', function() {
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
	$('.run-version-old').on('click', function() {
		$(this).html('<i class="fas fa-spinner fa-spin"></i>');
		$(this).attr('disabled', true);
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/api/build/',
			data: {
			  'model_uuid': $('#header').data('model_uuid'),
			  'scenario_id': $("#scenario option:selected").data('id'),
			  'start_date': $(this).attr('data-dates').split(' to ')[0],
			  'end_date': $(this).attr('data-dates').split(' to ')[1]
			},
			dataType: 'json',
			success: function (data) {
				console.log(data['status']);
			}
		});
	});

}



