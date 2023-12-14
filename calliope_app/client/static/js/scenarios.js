var bulk_confirmation = false,
	map_mode = 'scenarios';

$( document ).ready(function() {

	// Resize Dashboard
	splitter_resize();

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

	initVerticalBar();

	get_scenario_configuration();

});


function initVerticalBar() {
    const leftPanel = $('.left-panel');
    const verticalBar = $('#vertical-bar');
    const rightPanel = $('.right-panel');
    const map = $('#map');

    let isResizing = false;
    let startX = 0;
    let startY = 0;

    verticalBar.mousedown(function(e) {
        e.preventDefault();
        isResizing = true;
        startX = e.clientX;
        startY = e.clientY;
        const container = $('#splitter');
        const leftPanel = $('.left-panel');
        const rightPanel = $('.right-panel');

        $(document).mousemove(function(e) {
            if (isResizing) {
                const deltaX = e.clientX - startX;
                const containerWidth = container.width();
                const newLeftPanelWidth = ((leftPanel.width() + deltaX) / containerWidth) * 100;
                const newRightPanelWidth = ((rightPanel.width() - deltaX) / containerWidth) * 100;

                if (newLeftPanelWidth > 20 && newRightPanelWidth > 20) {
                    leftPanel.css('flex', newLeftPanelWidth + '%');
                    rightPanel.css('flex', newRightPanelWidth + '%');
                }

                //const rightPanelHeight = container.height() - $('#subheader2').outerHeight();
               // $('#map').css('height', rightPanelHeight + 'px');
			   adjustMapContainerHeight();

                startX = e.clientX;
                startY = e.clientY;
            }
        });
    });

    $('#vertical-bar').mouseup(function() {
        isResizing = false;
        console.log('Before map resize()');
        map.resize();
        console.log('After map resize()');
        map.resize();
        console.log('After map resize() 2nd');
        $('#vertical-bar').off('mousemove');
    });
}

function adjustMapContainerHeight() {
    const rightPanelHeight = $('.right-panel').height();
    $('#map').css('height', rightPanelHeight + 'px');
}

// function initVerticalBar() {
//     // Get references to elements
//     const leftPanel = $('.left-panel');
//     const verticalBar = $('#vertical-bar');
//     const rightPanel = $('.right-panel');
// 	const map = $('#map');

//     let isResizing = false;
//     let startX = 0;
// 	//let startY = 0;

//     // Event listeners to start and stop resizing
//     verticalBar.mousedown(function(e) {
//         e.preventDefault();
//         isResizing = true;
//         startX = e.clientX;
// 		startY = e.clientY;
//         $(document).mousemove(function(e) {
//             if (isResizing) {
// 				const deltaX = e.clientX - startX;
//                 //const deltaY = e.clientY - startY;
//                 const containerWidth = leftPanel.width() + rightPanel.width();
//                 const newLeftPanelWidth = ((leftPanel.width() + deltaX) / containerWidth) * 100;
//                 const newRightPanelWidth = ((rightPanel.width() - deltaX) / containerWidth) * 100;

//                 // Set limits for panel width (adjust as needed)
//                 if (newLeftPanelWidth > 20 && newRightPanelWidth > 20) {
//                     leftPanel.css('flex', newLeftPanelWidth + '%');
//                     rightPanel.css('flex', newRightPanelWidth + '%');
//                 }

// 				const sliderPosition = e.clientY - $('#map_container').offset().top;
//                 const mapContainerHeight = $('#map_container').height();
//                 const mapHeight = (sliderPosition / mapContainerHeight) * 100;
//                 map.css('height', mapHeight + '%');

//                 startX = e.clientX;
// 				//startY = e.clientY;
//             }
//         });
//     });

//     $(document).mouseup(function() {
//         isResizing = false;
//         $(document).off('mousemove');
//     });

// 	// Update the map's height dynamically based on the vertical bar's position
//     $(document).on('mousemove', function(e) {
//         if (isResizing) {
//             const sliderPosition = e.clientY - $('#map_container').offset().top;
//             const mapContainerHeight = $('#map_container').height();
//             const mapHeight = (sliderPosition / mapContainerHeight) * 100;
//             $('#map').css('height', mapHeight + '%');
//         }
//     });
// }

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
	$('.viz-spinner').show();
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
				active_lt_ids = data['active_lt_ids'];
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
						toggle_scenario_loc_tech([loc_tech_id], true)
						$(this).parents('tr').addClass('table-info')
					} else {
						toggle_scenario_loc_tech([loc_tech_id], false)
						$(this).parents('tr').removeClass('table-info')
					}
				})
				$('#add_loc_techs').on('change', function(e) {
					if (bulk_confirmation == false) {
						bulk_confirmation = confirm('This will toggle every node shown below.\nAre you sure you want to enable bulk editing?');
					};
					if (bulk_confirmation == true) {
						var loc_tech_ids = [];
						if (e.target.checked) {
							var visible_loc_techs = $(".node").not(".hide").find(".add_loc_tech:not(:checked)");
							visible_loc_techs.each( function() {
								var row = $(this).parents('tr');
								loc_tech_ids.push(row.data('loc_tech_id'));
								$(this).prop( "checked", true );
								row.addClass('table-info');
							});
							toggle_scenario_loc_tech(loc_tech_ids, true);
						} else {
							var visible_loc_techs = $(".node").not(".hide").find(".add_loc_tech:checked");
							visible_loc_techs.each( function() {
								var row = $(this).parents('tr');
								loc_tech_ids.push(row.data('loc_tech_id'));
								$(this).prop( "checked", false );
								row.removeClass('table-info');
							});
							toggle_scenario_loc_tech(loc_tech_ids, false);
						}
					} else {
						$(this).prop("checked", !$(this).is(":checked"));
						return false;
					}
				})
				$('#tech-filter, #tag-filter, #location-filter').on('change', function(e) {
					filter_nodes();
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
				
				$('#edit-scenario-name').on('click', function() {
					var currentScenarioName = prompt('Enter the new scenario name:','');
					if(currentScenarioName !==null) {
						$('#scenario-name').text(currentScenarioName);
						update_scenario_name(currentScenarioName);
					}
				});
			}
		});
	} else {
		$('.viz-spinner').hide();
		$('#map').remove();
		$('#scenario_configuration').html('<div class="col-12 text-center"><br/><br/><h4>Select or create a scenario above!</h4></div>');
	};
};

function update_scenario_name(newScenarioName) {
    var model_uuid = $('#header').data('model_uuid'),
    scenario_id = $("#scenario option:selected").data('id');
    $.ajax({
        url: '/' + LANGUAGE_CODE + '/api/update_scenario_name/',
        type: 'POST',
        data: {
            'model_uuid': model_uuid,
            'scenario_id': scenario_id,
            'new_scenario_name': newScenarioName,
            'csrfmiddlewaretoken': getCookie('csrftoken'),
        },
        dataType: 'json',
        success: function (data) {
            window.onbeforeunload = null;
            location.reload();
            alert('Scenario Name Updated Successfully.');
        },
        error: function() {
            alert('Failed to update scenario name. Please try again.');
        }
    });
}

function activate_scenario_settings() {
	$('.run-parameter-value, .run-parameter-year').on('input change paste', function() {
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

function filter_nodes() {
	$('.node').addClass('hide')
	var tech = $('#tech-filter').val(),
		tag = $('#tag-filter').val(),
		location = $('#location-filter').val(),
		filter_selection = $('.node');
	if (tech != '') { filter_selection = filter_selection.filter('*[data-tech="' + tech + '"]'); filter = true; }
	if (tag != '') { filter_selection = filter_selection.filter('*[data-tag="' + tag + '"]'); filter = true; }
	if (location != '') { filter_selection = filter_selection.filter('*[data-locations*="' + "'" + location + "'" + '"]'); filter = true; }
	filter_selection.removeClass('hide');
}

function toggle_scenario_loc_tech(loc_tech_ids, add) {
	if (loc_tech_ids.length > 0) {
		$('.viz-spinner').show();
		var model_uuid = $('#header').data('model_uuid'),
			scenario_id = $("#scenario option:selected").data('id');
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/api/toggle_scenario_loc_tech/',
			type: 'POST',
			data: {
			  'model_uuid': model_uuid,
			  'scenario_id': scenario_id,
			  'loc_tech_ids': loc_tech_ids.join(','),
			  'add': +add,
			  'csrfmiddlewaretoken': getCookie('csrftoken'),
			},
			dataType: 'json',
			success: function (data) {
				active_lt_ids = data['active_lt_ids'];
				retrieve_map(false, scenario_id, undefined);
			}
		});
	};
}