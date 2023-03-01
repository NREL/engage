var bulk_confirmation = false,
    dialogInputId = null,
    dialogInputValue = null,
    dialogObj = {},
    disable_new_constraint = true,
	map_mode = 'scenarios',
    carriers = null,
    constraints = ["demand_share_min", "demand_share_max", "demand_share_equals",
     "demand_share_per_timestep_min", "demand_share_per_timestep_max", "demand_share_per_timestep_equals",
      "demand_share_per_timestep_decision", "carrier_prod_share_min", "carrier_prod_share_max",
       "carrier_prod_share_equals", "carrier_prod_share_per_timestep_min", "carrier_prod_share_per_timestep_max",
        "carrier_prod_share_per_timestep_equals", "net_import_share_min", "net_import_share_max",
         "net_import_share_equals", "carrier_prod_min", "carrier_prod_max", "carrier_prod_equals", 
         "carrier_con_min", "carrier_con_max", "carrier_con_equals", "cost_max", "cost_min",
       "cost_equals", "cost_var_max", "cost_var_min", "cost_var_equals", "cost_investment_max",
    "cost_investment_min", "cost_investment_equals", "energy_cap_share_min", "energy_cap_share_max",
"energy_cap_share_equals", "energy_cap_min", "energy_cap_max", "energy_cap_equals", "resource_area_min",
"resource_area_max", "resource_area_equals", "storage_cap_min", "storage_cap_max", "storage_cap_equals"];

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

    $("#new_group_constraint_name").on("input", function(){
        if ($('#new_group_constraint_name').val() && $('#new_group_constraint_name').val().trim().length > 0 ) {
            $('#new_group_constraint_btn').removeAttr("disabled");
        } else {
            $('#new_group_constraint_btn').attr("disabled", true);
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

function getModelCarriers() {
    var model_uuid = $('#header').data('model_uuid');
    
    $.ajax({
        url: '/' + LANGUAGE_CODE + '/component/model_carriers/',
        async: false,
        data: {
            'model_uuid': model_uuid,
        },
        dataType: 'json',
        success: function (data) {
            carriers = data.carriers;
        }
    });
}

function updateDialogConstraints() {
    $('#dialog-inputs').empty();
    $('#dialog-inputs').append( "<h5><b>Group Constraints</b></h5>");
    Object.keys(dialogObj).forEach(constraint => {
         
        $('#dialog-inputs').append( "<div id='" + constraint + "' style='padding-top:1.5em'>");
        let constraintId = "#" + constraint;
        $(constraintId).append( "<h5 style='color:#007bff;'>" + constraint +  "</h5>");

        //Display techs and locs first
        dialogObj[constraint].techs = dialogObj[constraint].techs ? dialogObj[constraint].techs : "";
        $(constraintId).append( "<label><b>Technologies</b></label>");
        $(constraintId).append( "<p class='help-text'>Optionally enter a comma seperated list of technologies.</p>");
        $(constraintId).append( "<input id='" + constraint + "_techs' name='dialogObj[constraint].techs' class='form-control' placeholder='Technologies' value='" + dialogObj[constraint].techs + "'></input><br>" );
    
        dialogObj[constraint].techs_lhs = dialogObj[constraint].techs_lhs ? dialogObj[constraint].techs_lhs : "";
        $(constraintId).append( "<label><b>Technologies Left Hand-side</b></label>");
        $(constraintId).append( "<p class='help-text'>Optionally enter a comma seperated list of left hand-side technologies.</p>");
        $(constraintId).append( "<input id='" + constraint + "_techs_lhs' name='dialogObj[constraint].techs_lhs' class='form-control' placeholder='Technologies Left' value='" + dialogObj[constraint].techs_lhs + "'></input><br>" );
    
        dialogObj[constraint].techs_rhs = dialogObj[constraint].techs_rhs ? dialogObj[constraint].techs_rhs : "";
        $(constraintId).append( "<label><b>Technologies Right Hand-side</b></label>");
        $(constraintId).append( "<p class='help-text'>Optionally enter a comma seperated list of right hand-side technologies.</p>");
        $(constraintId).append( "<input id='" + constraint + "_techs_rhs' name='dialogObj[constraint].techs_rhs' class='form-control' placeholder='Technologies Right' value='" + dialogObj[constraint].techs_rhs + "'></input><br>" );
    
        dialogObj[constraint].locs = dialogObj[constraint].locs ? dialogObj[constraint].locs : "";
        $(constraintId).append( "<label><b>Locations</b></label>");
        $(constraintId).append( "<p class='help-text'>Optionally enter a comma seperated list of locations.</p>");
        $(constraintId).append( "<input id='" + constraint + "_locs' name='dialogObj[constraint].locs' class='form-control' placeholder='Locations'  value='" + dialogObj[constraint].locs + "'></input><br>" );

        dialogObj[constraint].locs_lhs = dialogObj[constraint].locs_lhs ? dialogObj[constraint].locs_lhs : "";
        $(constraintId).append( "<label><b>Locations Left Hand-side</b></label>");
        $(constraintId).append( "<p class='help-text'>Optionally enter a comma seperated list of left hand-side locations.</p>");
        $(constraintId).append( "<input id='" + constraint + "_locs_lhs' name='dialogObj[constraint].locs_lhs' class='form-control' placeholder='Locations Left'  value='" + dialogObj[constraint].locs_lhs + "'></input><br>" );

        dialogObj[constraint].locs_rhs = dialogObj[constraint].locs_rhs ? dialogObj[constraint].locs_rhs : "";
        $(constraintId).append( "<label><b>Locations Right Hand-side</b></label>");
        $(constraintId).append( "<p class='help-text'>Optionally enter a comma seperated list of right hand-side locations.</p>");
        $(constraintId).append( "<input id='" + constraint + "_locs_rhs' name='dialogObj[constraint].locs_rhs' class='form-control' placeholder='Locations Right'  value='" + dialogObj[constraint].locs_lhs + "'></input><br>" );

        $(constraintId).append( "<label><b>Constraints</b></label>");
        $(constraintId).append( "<p class='help-text'>Multiple constraints can be added to a single group constraint. Cost and carriers are a key and value pair whereas all other types are a value. See Constraint column in Calliope documentation for value options.</p>");
        Object.keys(dialogObj[constraint]).forEach(fieldKey => {
            if (fieldKey !== "locs" && fieldKey !== "techs" && fieldKey !== "techs_lhs" && fieldKey !== "techs_rhs" && fieldKey !== "locs_lhs" && fieldKey !== "locs_rhs") {

                $(constraintId).append( "<label><b>Constraint Type </b></label><span style='float:right'>" + fieldKey + "</span><br>");
                let constraintFields = "#fields-" + constraint + fieldKey;
                $(constraintId).append("<div id='fields-" + constraint + fieldKey + "' style='padding-left:5em'></div>");
                if (constraints.indexOf(fieldKey) <= 30) {
                    if (!dialogObj[constraint][fieldKey] || typeof dialogObj[constraint][fieldKey] !== 'object') {
                        dialogObj[constraint][fieldKey] = {};
                    }
                    const key = Object.keys(dialogObj[constraint][fieldKey]).length !== 0 ? Object.keys(dialogObj[constraint][fieldKey])[0] : "";
                    const val = key ? dialogObj[constraint][fieldKey][Object.keys(dialogObj[constraint][fieldKey])[0]] : "";
                    $(constraintFields).append( "<div class='input-field'><label><b>Key </b></label>");
                    let dropdownArray = constraints.indexOf(fieldKey) <= 21 ? carriers : ["co2", "ch4", "co2e", "n20"];
                    if (dropdownArray.indexOf(key) === -1) {
                        dropdownArray.push(key);
                    }
                    $(constraintFields).append( "<select style='margin-bottom:1em' class='form-control' id='" + constraint + fieldKey + "-key' name='dialogObj[constraint][fieldKey].name' data-toggle='tooltip' data-placement='left'></select>" );
                    for (let i = 0; i < dropdownArray.length; i++) {
                        if (key == dropdownArray[i]) {
                            $('#' + constraint + fieldKey + '-key').append( "<option selected value=" + dropdownArray[i] + ">" + dropdownArray[i] + "</option>" );
                        } else {
                            $('#' + constraint + fieldKey + '-key').append( "<option value=" + dropdownArray[i] + ">" + dropdownArray[i] + "</option>" );
                        }
                    }

                    $(constraintFields).append( "<div class='input-field'><label><b>Value </b></label>");
                    $(constraintFields).append( "<input id='" + constraint + fieldKey + "-val' name='dialogObj[constraint][fieldKey].value' class='form-control' placeholder='' value='" + val + "'></input><br></div>" );
                } else {
                    $(constraintFields).append( "<div class='input-field'><label><b>Value </b></label>");
                    $(constraintFields).append( "<input id='" + constraint + fieldKey + "-val' name='dialogObj[constraint][fieldKey]' class='form-control' placeholder='' value='" + dialogObj[constraint][fieldKey] + "'></input><br></div>" );
                }
            }
        });

        $(constraintId).append( "<br><label><b>New Constraint Type </b></label>");
        $(constraintId).append( "<select style='margin-bottom:1em' class='form-control' id='new-constraint-dropdown-" + constraint + "' data-toggle='tooltip' data-placement='left'></select>" );
        $('#new-constraint-dropdown-' + constraint ).append( "<option></option>" );
        for (let i = 0; i < constraints.length; i++) {
            $('#new-constraint-dropdown-' + constraint ).append( "<option value=" + constraints[i] + ">" + constraints[i] + "</option>" );
        }

        $(constraintId).append("<div class='form-group col-md-8'><input disabled id='new_constraint_btn_" + constraint + "' type='submit' class='btn btn-sm btn-success' name='' value='+ Constraint'></div>");
        $("#new_constraint_btn_" + constraint).on('click', function() {
            let con = this.id.replace("new_constraint_btn_", "");
            let newConstraint = $("#new-constraint-dropdown-" + con).val();
            if (newConstraint && newConstraint.length > 0) {
                dialogObj[con][newConstraint] = "";
            }
            updateDialogConstraints();
        });

        $("#new-constraint-dropdown-" + constraint).change(function () {
            let con = this.id.replace("new-constraint-dropdown-", "");
            if (this.value && this.value.length > 0 ) {
                $("#new_constraint_btn_" + con).removeAttr("disabled");
            } else {
                $('#new_constraint_btn_' + con).attr("disabled", true);
            }
        });
        $(constraintId).append( "<hr>" );
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
                // Technologies
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
                if (fieldKey === "techs_lhs") {
                    var newTechs = "";
                    if (dialogObj[constraint].techs_lhs && dialogObj[constraint].techs_lhs.length > 0) {
                        for (var tech in dialogObj[constraint].techs_lhs) {
                            newTechs += dialogObj[constraint].techs_lhs[tech];
                            if (Number(tech) !== dialogObj[constraint].techs_lhs.length-1) {
                                newTechs += ","
                            }
                        }
                    } 
                    dialogObj[constraint].techs_lhs = newTechs;
                }
                if (fieldKey === "techs_rhs") {
                    var newTechs = "";
                    if (dialogObj[constraint].techs_rhs && dialogObj[constraint].techs_rhs.length > 0) {
                        for (var tech in dialogObj[constraint].techs_rhs) {
                            newTechs += dialogObj[constraint].techs_rhs[tech];
                            if (Number(tech) !== dialogObj[constraint].techs_rhs.length-1) {
                                newTechs += ","
                            }
                        }
                    } 
                    dialogObj[constraint].techs_rhs = newTechs;
                }

                // Locations
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
                if (fieldKey === "locs_lhs") {
                    var newLocs = "";
                    if (dialogObj[constraint].locs_lhs && dialogObj[constraint].locs_lhs.length > 0) {
                        for (var loc in dialogObj[constraint].locs_lhs) {
                            newLocs += dialogObj[constraint].locs_lhs[loc];
                            if (Number(loc) !== dialogObj[constraint].locs_lhs.length-1) {
                                newLocs += ","
                            }
                        }
                    }
                    dialogObj[constraint].locs_lhs = newLocs;
                }
                if (fieldKey === "locs_rhs") {
                    var newLocs = "";
                    if (dialogObj[constraint].locs_rhs && dialogObj[constraint].locs_rhs.length > 0) {
                        for (var loc in dialogObj[constraint].locs_rhs) {
                            newLocs += dialogObj[constraint].locs_rhs[loc];
                            if (Number(loc) !== dialogObj[constraint].locs_rhs.length-1) {
                                newLocs += ","
                            }
                        }
                    }
                    dialogObj[constraint].locs_rhs = newLocs;
                }
            });

        });

        getModelCarriers();
        if (carriers) {
            updateDialogConstraints();
        }

	});

    $('#settings_import_data').on('click', function() {
        Object.keys(dialogObj).forEach(constraint => {

            //Technologies
            var techsInput = $("#" + constraint + "_techs").val();
            if (techsInput && techsInput.length > 0) {
                dialogObj[constraint].techs = techsInput.split(',');
            } else {
                delete dialogObj[constraint].techs;
            }

            techsInput = $("#" + constraint + "_techs_lhs").val();
            if (techsInput && techsInput.length > 0) {
                dialogObj[constraint].techs_lhs = techsInput.split(',');
            } else {
                delete dialogObj[constraint].techs_lhs;
            }

            techsInput = $("#" + constraint + "_techs_rhs").val();
            if (techsInput && techsInput.length > 0) {
                dialogObj[constraint].techs_rhs = techsInput.split(',');
            } else {
                delete dialogObj[constraint].techs_rhs;
            }
            
            // Locations
            var locsInput = $("#" + constraint + "_locs").val();
            if (locsInput && locsInput.length > 0) {
                dialogObj[constraint].locs = locsInput.split(',');
            } else {
                delete dialogObj[constraint].locs;
            }

            locsInput = $("#" + constraint + "_locs_lhs").val();
            if (locsInput && locsInput.length > 0) {
                dialogObj[constraint].locs_lhs = locsInput.split(',');
            } else {
                delete dialogObj[constraint].locs_lhs;
            }

            locsInput = $("#" + constraint + "_locs_rhs").val();
            if (locsInput && locsInput.length > 0) {
                dialogObj[constraint].locs_rhs = locsInput.split(',');
            } else {
                delete dialogObj[constraint].locs_rhs;
            }
    
            //add constraints
            Object.keys(dialogObj[constraint]).forEach(fieldKey => {
                if (fieldKey !== "locs" && fieldKey !== "techs" && fieldKey !== "techs_lhs" && fieldKey !== "techs_rhs" && fieldKey !== "locs_lhs" && fieldKey !== "locs_rhs") {
                    let value = $("#" + constraint + fieldKey + "-val").val();
                    if (constraints.indexOf(fieldKey) <= 30) {
                        let key = $("#" + constraint + fieldKey + "-key").val();
                        dialogObj[constraint][fieldKey] = {};
                        if (key) {
                            dialogObj[constraint][fieldKey][key] = value;
                        }
                    } else {
                        dialogObj[constraint][fieldKey] = value;
                    } 
                }
            });
        });
        $('textarea[name="edit' + dialogInputId + '"]').text(JSON.stringify(dialogObj));
        $('#data-source-modal').hide();
	});

    $('.group-constraints-close').on('click', function() {
        $('#data-source-modal').hide();
    });


    $('#new_group_constraint_btn').on('click', function() {
        var newGroupConstraint = $('#new_group_constraint_name').val().trim();
        if (newGroupConstraint.length > 0) {
            dialogObj[newGroupConstraint] = {};
            $('#new_group_constraint_name').val("");
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



