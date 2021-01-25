var map_timeout_queue = 0;
var map_mode = 'scenarios';
var loc_techs = [];

$( document ).ready(function() {

	$('#master-new').removeClass('hide');

	$('#scenario').on('change', function() {
		get_scenario_configuration();
	});

	$('#master-settings').on('click', function() {
		$('.master-btn').addClass('hide')
		$('#master-save').removeClass('hide')
		$('#master-cancel').removeClass('hide')

		$('#form_scenario_settings').removeClass('hide')
		$('#scenario_configuration').addClass('hide')
	});

	$('#master-save').on('click', function() {
		$('.master-btn').addClass('hide')
		$('#master-settings').removeClass('hide');

		$('#form_scenario_settings').addClass('hide');
		$('#scenario_configuration').removeClass('hide')
		save_scenario_settings();
	});

	$('#master-new').on('click', function() {
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/add_scenarios/';
	});

	$('#master-cancel').on('click', function() {
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/scenarios/';
	});

	get_scenario_configuration();

});

function save_scenario_settings() {

	var model_uuid = $('#header').data('model_uuid'),
		scenario_id = $("#scenario option:selected").data('id')
		form_data = $("#form_scenario_settings :input").serializeJSON();

	$.ajax({
		url: '/' + LANGUAGE_CODE + '/api/update_scenario_params/',
		type: 'POST',
		data: {
			'model_uuid': model_uuid,
			'scenario_id': scenario_id,
			'form_data': JSON.stringify(form_data),
			'csrfmiddlewaretoken': getCookie('csrftoken'),
		},
		dataType: 'json',
		success: function (data) {
			window.onbeforeunload = null;
			location.reload();
		}
	});

}

function get_scenario_configuration() {
	var model_uuid = $('#header').data('model_uuid'),
		scenario_id = $("#scenario option:selected").data('id');
	
	if (scenario_id != undefined) {
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/component/scenario/',
			data: {
			  'model_uuid': model_uuid,
			  'scenario_id': scenario_id,
			},
			dataType: 'json',
			success: function (data) {
				loc_techs = data['loc_techs'];
				$('#scenario_settings').html(data['scenario_settings']);
				activate_scenario_settings();

				activate_table();
				$('#scenario_configuration').html(data['scenario_configuration']);
				$('#scenario_configuration').data('scenario_id', data['scenario_id']);
				retrieve_map(false, scenario_id, undefined);

				$('.add_loc_tech').on('change', function(e) {
					var loc_tech_id = $(this).parents('tr').data('loc_tech_id');
					if (e.target.checked) {
						toggle_scenario_loc_tech(loc_tech_id, true)
						$(this).parents('tr').addClass('table-info')
					} else {
						toggle_scenario_loc_tech(loc_tech_id, false)
						$(this).parents('tr').removeClass('table-info')
					}
				})
				$('#add_loc_techs').on('change', function(e) {
					if (e.target.checked) {
						var visible_loc_techs = $(".node").not(".hide").find(".add_loc_tech:not(:checked)");
						visible_loc_techs.each( function() {
							$(this).prop( "checked", true ).change();
						});
					} else {
						var visible_loc_techs = $(".node").not(".hide").find(".add_loc_tech:checked");
						visible_loc_techs.each( function() {
							$(this).prop( "checked", false ).change();
						});
					}
				})
				$('#tech-filter, #tag-filter, #location-filter').on('change', function(e) {
					$('.node').addClass('hide')
					var tech = $('#tech-filter').val(),
						tag = $('#tag-filter').val(),
						location = $('#location-filter').val(),
						filter_selection = $('.node');
					if (tech != '') { filter_selection = filter_selection.filter('*[data-tech="' + tech + '"]'); filter = true; }
					if (tag != '') { filter_selection = filter_selection.filter('*[data-tag="' + tag + '"]'); filter = true; }
					if (location != '') { filter_selection = filter_selection.filter('*[data-locations*="' + "'" + location + "'" + '"]'); filter = true; }
					filter_selection.removeClass('hide') 
				})
				$('#edit-scenario').on('click', function() {
					var is_unlocked = $('.fa-lock').hasClass('hide');
					if (is_unlocked) {
						$('.fa-lock').removeClass('hide');
						$('.fa-unlock').addClass('hide');
						$('.add_loc_tech, #add_loc_techs').prop('disabled', true);
					} else {
						$('.fa-lock').addClass('hide');
						$('.fa-unlock').removeClass('hide');
						$('.add_loc_tech, #add_loc_techs').prop('disabled', false);
					}
				})
				if ($('#master-cancel').hasClass('hide')) {
					$('#master-settings').removeClass('hide');
				}
				$('#scenario-delete').on('click', function() {
					var model_uuid = $('#header').data('model_uuid'),
						scenario_id = $("#scenario option:selected").data('id');
					var confirmation = confirm('This will remove all configurations and runs for this scenario.\nAre you sure you want to delete?');
					if (confirmation) {
						$.ajax({
							url: '/' + LANGUAGE_CODE + '/api/delete_scenario/',
							type: 'POST',
							data: {
								'model_uuid': model_uuid,
								'scenario_id': scenario_id,
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
			}
		});
	} else {
		$('#map').remove();
		$('#scenario_configuration').html('<div class="col-12 text-center"><br/><br/><h4>Select or create a scenario above!</h4></div>');
	};
};

function activate_scenario_settings() {
	$('.run-parameter-value, .run-parameter-year').on('change keyup paste', function() {
		$(this).parents('tr').addClass('table-warning')
	});
	$('.run-parameter-value-add').on('click', function() {
		var row = $(this).parents('tr'),
			param_id = row.data('param_id'),
			add_row = row.nextAll('.param_header_add[data-param_id='+param_id+']').first().clone();
		add_row.insertAfter($('tr[data-param_id='+param_id+']').last());
		add_row.show()
	});
	$('.run-parameter-value-remove').on('click', function() {
		var row = $(this).parents('tr')
		row.addClass('table-danger')
		row.find('.check_delete').prop("checked", true)
	});
	
}

function toggle_scenario_loc_tech(loc_tech_id, add) {
	var model_uuid = $('#header').data('model_uuid'),
		scenario_id = $("#scenario option:selected").data('id');
	$.ajax({
		url: '/' + LANGUAGE_CODE + '/api/toggle_scenario_loc_tech/',
		type: 'POST',
		data: {
		  'model_uuid': model_uuid,
		  'scenario_id': scenario_id,
		  'loc_tech_id': loc_tech_id,
		  'add': +add,
		  'csrfmiddlewaretoken': getCookie('csrftoken'),
		},
		dataType: 'json',
		success: function (data) {
			map_timeout_queue++
			setTimeout(function(){
				if (map_timeout_queue == 1) { retrieve_map(false, scenario_id, undefined); };
				map_timeout_queue--;
			}, 500);
		}
	});
}