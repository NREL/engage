var hold_refresh = false;
var pause_start = null;
var pause_interval = null;
var loc_techs = [];
var submitdata = {};

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
	var model_uuid = $('#header').data('model_uuid');
	var scenario_id = $("#scenario option:selected").data('id');
	
	// The following is a stripped-down version of the AJAX call in
	// get_scenario_configuration() in scenarios.js.
	// We use it to set the loc_techs variable for the map popups.
	if (scenario_id != undefined) {
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/component/scenario/',
			data: {
			  'model_uuid': model_uuid,
			  'scenario_id': scenario_id,
			},
			dataType: 'json',
			success: function (data) {
				refresh_run_dashboard();
				
				loc_techs = data['loc_techs'];
				retrieve_map(false, scenario_id, undefined);
				$('#master-new').removeClass('hide');
			}
		});
		
	} else {
		$('#master-new').addClass('hide');
		$('#run_dashboard').html('<div class="col-12 text-center"><br/><br/><h4>Please create a scenario first!</h4></div>');
	}
}

function refresh_run_dashboard() {
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
			}
		});
	};
	setTimeout(function(){
		refresh_run_dashboard();
	}, 2000);
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
				if (!$('.hidden').is(':visible')) {
					hold_refresh = false;
					clearInterval(pause_interval);
					$('#updates_paused').slideUp();
				};
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

function activate_runs() {
	
	bindEditable();

	$('.run-version').on('click', function() {
		if ($('.hidden').is(':visible')) {
			$('.hidden').toggle('hide')
			hold_refresh = false;
			clearInterval(pause_interval);
			$('#updates_paused').slideUp();
		} else {
			$('.hidden').toggle('hide')
			hold_refresh = true;
			pause_start = new Date();
			updatePauseTime();
			pause_interval = setInterval(updatePauseTime, 1000);
			$('#updates_paused').slideDown();
		};
	});

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
			}
		});
	});

	$('.btn-viz-logs').unbind();
	$('.btn-viz-logs').on('click', function() {
		var logs_path = $(this).data('path');

		$.ajax({
			url: '/' + LANGUAGE_CODE + '/component/show_logs/',
			type: 'POST',
			data: {
				'model_uuid': $('#header').data('model_uuid'),
				'logs_path': logs_path,
				'csrfmiddlewaretoken': getCookie('csrftoken'),
			},
			dataType: 'json',
			complete: function (data) {
				$('#viz_logs_container').show().html(data.responseText);
				$('#viz_outputs_container').empty().hide();
				$([document.documentElement, document.body]).animate({
			        scrollTop: $("#viz_logs_container").offset().top
			    }, 1000);
			}
		});
	});

	$('.btn-viz-outputs').unbind();
	$('.btn-viz-outputs').on('click', function() {
		var plots_path = $(this).data('path')

		$.ajax({
			url: '/' + LANGUAGE_CODE + '/component/plot_outputs/',
			type: 'POST',
			data: {
				'model_uuid': $('#header').data('model_uuid'),
				'plots_path': plots_path,
				'csrfmiddlewaretoken': getCookie('csrftoken'),
			},
			dataType: 'json',
			complete: function (data) {
				$('#viz_logs_container').empty().hide();
				$('#viz_outputs_container').show().html(data.responseText);
				setTimeout(function(){
					$([document.documentElement, document.body]).animate({
				        scrollTop: $("#viz_outputs_container").offset().top
				    }, 1000);
				}, 100);
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
					$('#viz_outputs_container').empty().hide();
				}
			});
		};
	});

}



