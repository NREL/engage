var bulk_confirmation = false,
    dialogInputId = null,
    dialogInputValue = null,
    dialogObj = {},
    disable_new_constraint = true,
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

    $("#new_constraint_name").on("input", function(){
        if ($('#new_constraint_name').val() && $('#new_constraint_name').val().trim().length > 0 ) {
            $('#new_constraint_btn').removeAttr("disabled");
        } else {
            $('#new_constraint_btn').attr("disabled", true);
        }
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
			}
		});
	} else {
		$('.viz-spinner').hide();
		$('#map').remove();
		$('#scenario_configuration').html('<div class="col-12 text-center"><br/><br/><h4>Select or create a scenario above!</h4></div>');
	};
};

function updateDialogConstraints() {
    $('#dialog-inputs').empty();
    Object.keys(dialogObj).forEach(constraint => {
        console.log(constraint, dialogObj[constraint]);
        $('#dialog-inputs').append( "<div id='" + constraint + "'>");
        $('#dialog-inputs').append( "<h5><b>Group Constraint Name: " + constraint +  "</b></h5>");

        //Display techs and locs first
        if (!dialogObj[constraint].techs) {
            dialogObj[constraint].techs = "";
        }
        $('#dialog-inputs').append( "<label><b>Technologies</b></label>");
        $('#dialog-inputs').append( "<p class='help-text'>Optionally enter a comma seperated list of technologies.</p>");
        $('#dialog-inputs').append( "<input id='" + constraint + "_techs' name='dialogObj[constraint].techs' class='form-control' placeholder='Technologies' value='" + dialogObj[constraint].techs + "'></input><br>" );
    
        if (!dialogObj[constraint].locs) {
            dialogObj[constraint].locs = "";
        }
        $('#dialog-inputs').append( "<label><b>Locations</b></label>");
        $('#dialog-inputs').append( "<p class='help-text'>Optionally enter a comma seperated list of locations.</p>");
        $('#dialog-inputs').append( "<input id='" + constraint + "_locs' name='dialogObj[constraint].locs' class='form-control' placeholder='Locations'  value='" + dialogObj[constraint].locs + "'></input><br>" );

        $('#dialog-inputs').append( "<label><b>Constraints</b></label>");
        $('#dialog-inputs').append( "<p class='help-text'>Enter a comma seperated list, formatted 'contraint name: constraint value,'. See Constraint column in Calliope documentation for value options.</p>");
        Object.keys(dialogObj[constraint]).forEach(fieldKey => {
            if (fieldKey !== "locs" && fieldKey !== "techs" ) {
                $('#dialog-inputs').append( "<label><b>" + fieldKey + "</b></label>");
                $('#dialog-inputs').append( "<input id='" + fieldKey + "_constraint' name='dialogObj[constraint][fieldKey]' class='form-control' placeholder='' value='" + dialogObj[constraint][fieldKey] + "'></input><br>" );
            }
        });
        $('#dialog-inputs').append( "</div>");
        $('#dialog-inputs').append( "<hr>" );
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

    // Group Constraints Modal
	//$('.scenario-settings:visible').attr('disabled', false);
	//$('.scenario-settings').unbind();
	$('.scenario-settings-dialog-btn').on('click', function() {

        // Get dialog data
        dialogInputId = this.name.slice(6);
        dialogInputValue = dialogInputId ? $('textarea[name="edit' + dialogInputId + '"]').text() : console.log("Dialog input id not found!");

        // display dialog
		$('#pvwatts_form').hide();
        $('#wtk_form').hide();
		$('#scenario_settings_json_form').show();
		$("#data-source-modal").css('display', "block");

        // Set dialog data
        dialogObj = JSON.parse(dialogInputValue ? dialogInputValue : {});

        Object.keys(dialogObj).forEach(constraint => {
            Object.keys(dialogObj[constraint]).forEach(fieldKey => {
                if (fieldKey === "techs") {
                    var newTechs = "";
                    if (dialogObj[constraint].techs && dialogObj[constraint].techs.length > 0) {
                        for (var tech in dialogObj[constraint].techs) {
                            newTechs += dialogObj[constraint].techs[tech];
                            if (Number(tech) !== dialogObj[constraint].techs.length-1) {
                                newTechs += ","
                            }
                        }
                    } 
                    dialogObj[constraint].techs = newTechs;
                }
                if (fieldKey === "locs") {
                    var newLocs = "";
                    if (dialogObj[constraint].locs && dialogObj[constraint].locs.length > 0) {
                        for (var loc in dialogObj[constraint].locs) {
                            newLocs += dialogObj[constraint].locs[loc];
                            if (Number(loc) !== dialogObj[constraint].locs.length-1) {
                                newLocs += ","
                            }
                        }
                    }
                    dialogObj[constraint].locs = newLocs;
                }
            });

        });

        updateDialogConstraints();

	});

    $('#settings_import_data').on('click', function() {
        Object.keys(dialogObj).forEach(constraint => {
            //Display techs and locs first
            var techsInput = $("#" + constraint + "_techs").val();
            if (techsInput && techsInput.length > 0) {
                dialogObj[constraint].techs = techsInput.split(',');
            } else {
                delete dialogObj[constraint].techs;
            }

            var locsInput = $("#" + constraint + "_locs").val();
            if (locsInput && locsInput.length > 0) {
                dialogObj[constraint].locs = locsInput.split(',');
            } else {
                delete dialogObj[constraint].locs;
            }
    
            //add constraints
            /*Object.keys(dialogObj[constraint]).forEach(fieldKey => {
                if (fieldKey !== "locs" && fieldKey !== "techs" ) {

                }
            });*/

        });
        $('textarea[name="edit' + dialogInputId + '"]').text(JSON.stringify(dialogObj));
        $('#data-source-modal').hide();
	});

    $('#group-constraints-close').on('click', function() {
        $('#data-source-modal').hide();
    });


    $('#new_constraint_btn').on('click', function() {
        var newGroupConstraint = $('#new_constraint_name').val().trim();
        if (newGroupConstraint.length > 0) {
            dialogObj[newGroupConstraint] = {};
            $('#new_constraint_name').val("");
            updateDialogConstraints();
        }
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



