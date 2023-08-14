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
        url: '/' + LANGUAGE_CODE + '/component/group_constraint_options/',
        async: false,
        data: {
            'model_uuid': model_uuid,
        },
        dataType: 'json',
        success: function (data) {
            carriers = data.carriers ? data.carriers.map(obj => obj.name) : [];
            locations = data.locations;
            technologies = data.technologies;
        }
    });
}

function updateDialogConstraints(onlyUpdateConstraints) {
    $('#dialog-inputs').empty();
    if (dialogObj.length > 0) {
        $('#dialog-inputs').append( "<h5><b>Group Constraints</b></h5>");
    }
    Object.keys(dialogObj).forEach(constraint => {
         
        $('#dialog-inputs').append( "<div id='" + constraint + "' style='padding-top:1.5em'>");
        let constraintId = "#" + constraint;
        $(constraintId).append( "<div><h5 class='constraint-name'><b>" + constraint +  "</b></h5><button id='delete_group_constraint_btn_" + constraint + "' type='button' class='btn btn-sm btn-outline-danger constraint-delete' title='Delete constraint'><i class='fas fa-trash'></i></button></div>");

        //Display techs and locs first
        dialogObj[constraint].techs = dialogObj[constraint].techs ? dialogObj[constraint].techs : "";
        $(constraintId).append("<div><label class='amsify-label' data-toggle='tooltip' data-placement='bottom' data-original-title='Optionally enter technologies.'><b>Technologies</b></label><br>" + 
        "<select id='" + constraint + "_techs' name='Technologies' multiple searchable></select></div>");
        for (var t in technologies) {
            $('#' + constraint + '_techs').append('<option value="'+ technologies[t].name + '" '+ (dialogObj[constraint].techs.includes(technologies[t].name) ? ' selected' : '') +'>' + technologies[t].pretty_name + '</option>');
        }

        dialogObj[constraint].techs_lhs = dialogObj[constraint].techs_lhs ? dialogObj[constraint].techs_lhs : "";
        $(constraintId).append("<div><label class='amsify-label' data-toggle='tooltip' data-placement='bottom' data-original-title='Optionally enter left hand-side technologies.'><b>Technologies Left Hand-side</b></label><br>" + 
        "<select id='" + constraint + "_techs_lhs' name='Technologies Left Hand-side' multiple searchable></select></div>");
        for (var t in technologies) {
            $('#' + constraint + '_techs_lhs').append('<option value="'+ technologies[t].name + '" '+ (dialogObj[constraint].techs_lhs.includes(technologies[t].name) ? ' selected' : '') +'>' + technologies[t].pretty_name + '</option>');
        }

        dialogObj[constraint].techs_rhs = dialogObj[constraint].techs_rhs ? dialogObj[constraint].techs_rhs : "";
        $(constraintId).append("<div><label class='amsify-label' data-toggle='tooltip' data-placement='bottom' data-original-title='Optionally enter right hand-side technologies.'><b>Technologies Right Hand-side</b></label><br>" + 
        "<select id='" + constraint + "_techs_rhs' name='Technologies Right Hand-side' multiple searchable></select></div>");
        for (var t in technologies) {
            $('#' + constraint + '_techs_rhs').append('<option value="'+ technologies[t].name + '" '+ (dialogObj[constraint].techs_rhs.includes(technologies[t].name) ? ' selected' : '') +'>' + technologies[t].pretty_name + '</option>');
        }

        dialogObj[constraint].locs = dialogObj[constraint].locs ? dialogObj[constraint].locs : "";
        $(constraintId).append("<div><label class='amsify-label' data-toggle='tooltip' data-placement='bottom' data-original-title='Optionally enter locations.'><b>Locations</b></label><br>" + 
        "<select id='" + constraint + "_locs' name='Locations' multiple searchable></select></div>");
        for (var l in locations) {
            $('#' + constraint + '_locs').append('<option value="'+ locations[l].name + '" '+ (dialogObj[constraint].locs.includes(locations[l].name) ? ' selected' : '') +'>' + locations[l].pretty_name + '</option>');
        }

        dialogObj[constraint].locs_lhs = dialogObj[constraint].locs_lhs ? dialogObj[constraint].locs_lhs : "";
        $(constraintId).append("<div><label class='amsify-label' data-toggle='tooltip' data-placement='bottom' data-original-title='Optionally enter left hand-side locations.'><b>Locations Left Hand-side</b></label><br>" + 
        "<select id='" + constraint + "_locs_lhs' name='Locations Left Hand-side' multiple searchable></select></div>");
        for (var l in locations) {
            $('#' + constraint + '_locs_lhs').append('<option value="'+ locations[l].name + '" '+ (dialogObj[constraint].locs_lhs.includes(locations[l].name) ? ' selected' : '') +'>' + locations[l].pretty_name + '</option>');
        }

        dialogObj[constraint].locs_rhs = dialogObj[constraint].locs_rhs ? dialogObj[constraint].locs_rhs : "";
        $(constraintId).append("<div><label class='amsify-label' data-toggle='tooltip' data-placement='bottom' data-original-title='Optionally enter right hand-side locations.'><b>Locations Right Hand-side</b></label><br>" + 
        "<select id='" + constraint + "_locs_rhs' name='Locations Right Hand-side' multiple searchable></select></div>");
        for (var l in locations) {
            $('#' + constraint + '_locs_rhs').append('<option value="'+ locations[l].name + '" '+ (dialogObj[constraint].locs_rhs.includes(locations[l].name) ? ' selected' : '') +'>' + locations[l].pretty_name + '</option>');
        }

        $('#' + constraint + '_locs, #' + constraint + '_locs_lhs, #' + constraint + '_locs_rhs, #' + constraint + '_techs, #' + constraint + '_techs_lhs, #' + constraint + '_techs_rhs').amsifySelect({
            type : 'amsify',
            defaultLabel : 'test'
        });

        $(constraintId).append( "<label id='constraints-label' data-toggle='tooltip' data-placement='bottom' data-original-title='Multiple constraints can be added to a single group constraint. Cost and carriers are a key and value pair whereas all other types are a value. See Constraint column in Calliope documentation for value options.'><b>Constraints</b></label><br>");
        Object.keys(dialogObj[constraint]).forEach(fieldKey => {
            if (fieldKey !== "locs" && fieldKey !== "techs" && fieldKey !== "techs_lhs" && fieldKey !== "techs_rhs" && fieldKey !== "locs_lhs" && fieldKey !== "locs_rhs") {

                $(constraintId).append( "<label style='padding-left:20px'><b>Constraint Type </b></label><div style='float:right;'><span style='margin-right: 10px'>" + fieldKey + "</span><button id='delete_constraint_btn_" + constraint + "-" + fieldKey + "' type='button' class='btn btn-sm btn-outline-danger constraint-delete' title='Delete constraint'><i class='fas fa-trash'></i></button></div><br>");
                $("#delete_constraint_btn_" + constraint + "-" + fieldKey).on('click', function() {
                    let con = this.id.replace("delete_constraint_btn_", "").split("-");
                    delete dialogObj[con[0]][con[1]];
                    updateDialogConstraints();
                });
                let constraintFields = "#fields-" + constraint + fieldKey;
                $(constraintId).append("<div id='fields-" + constraint + fieldKey + "' class='constraint-key-value' ></div>");
                if (constraints.indexOf(fieldKey) <= 30) {
                    if (!dialogObj[constraint][fieldKey] || typeof dialogObj[constraint][fieldKey] !== 'object') {
                        dialogObj[constraint][fieldKey] = {};
                    }
                    const key = Object.keys(dialogObj[constraint][fieldKey]).length !== 0 ? Object.keys(dialogObj[constraint][fieldKey])[0] : "";
                    const val = key ? dialogObj[constraint][fieldKey][Object.keys(dialogObj[constraint][fieldKey])[0]] : "";
                    $(constraintFields).append( "<label><b>Key </b></label>");
                    let dropdownArray = constraints.indexOf(fieldKey) <= 21 ? carriers : ["co2", "ch4", "co2e", "n2o", "monetary"];
                    if (dropdownArray.indexOf(key) === -1) {
                        dropdownArray.push(key);
                    }
                    $(constraintFields).append( "<select style='margin-bottom:1em' class='form-control smol' id='" + constraint + fieldKey + "-key' name='dialogObj[constraint][fieldKey].name' data-toggle='tooltip' data-placement='left'></select><br><br>" );
                    for (let i = 0; i < dropdownArray.length; i++) {
                        if (key == dropdownArray[i]) {
                            $('#' + constraint + fieldKey + '-key').append( "<option selected value=" + dropdownArray[i] + ">" + dropdownArray[i] + "</option>" );
                        } else {
                            $('#' + constraint + fieldKey + '-key').append( "<option value=" + dropdownArray[i] + ">" + dropdownArray[i] + "</option>" );
                        }
                    }

                    $(constraintFields).append( "<label><b>Value </b></label>");
                    $(constraintFields).append( "<input id='" + constraint + fieldKey + "-val' name='dialogObj[constraint][fieldKey].value' class='form-control smol' placeholder='' value='" + val + "'></input><br><br>" );
                } else {
                    $(constraintFields).append( "<label><b>Value </b></label>");
                    $(constraintFields).append( "<input id='" + constraint + fieldKey + "-val' name='dialogObj[constraint][fieldKey]' class='form-control smol' placeholder='' value='" + dialogObj[constraint][fieldKey] + "'></input><br><br>" );
                }
            }
        });

        $(constraintId).append( "<br><label><b>New Constraint Type </b></label>");
        $(constraintId).append( "<select style='margin-bottom:1em' class='form-control smol' id='new-constraint-dropdown-" + constraint + "' data-toggle='tooltip' data-placement='left'></select>" );
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

        $("#delete_group_constraint_btn_" + constraint).on('click', function() {
            let con = this.id.replace("delete_constraint_btn_", "");
            delete dialogObj[con];
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
        $(document).ready(function() {
            $('[data-toggle="tooltip"]').tooltip();
          });
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
	$('.scenario-constraints-dialog-btn').on('click', function() {

        // Get dialog data
        dialogInputId = this.name.slice(6);
        dialogInputValue = dialogInputId ? $('textarea[name="edit' + dialogInputId + '"]').text() : console.log("Dialog input id not found!");

        // display dialog
		$('#pvwatts_form').hide();
        $('#wtk_form').hide();
		$('#scenario_constraints_form').show();
		$("#data-source-modal").css('display', "block");

        // Set dialog data
        dialogObj = dialogInputValue && JSON.parse(dialogInputValue) ? JSON.parse(dialogInputValue) : {};

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
        updateDialogConstraints();

        $('#tabs li a:not(:first)').addClass('inactive');
        $('.tab-container').hide();
        $('.tab-container:first').show();
            
        $('#tabs li a').click(function(){
            var t = $(this).attr('id');
            if($(this).hasClass('inactive')){ 
                $('#tabs li a').addClass('inactive');           
                $(this).removeClass('inactive');
                
                $('.tab-container').hide();
                $('#'+ t + 'C').fadeIn('slow');
            }
        });

        $('#tab2').click(function(){
            updateDialogObject();
            $('#JSONPreview').text(JSON.stringify(dialogObj, undefined, 2));
        });

	});

    $('#settings_import_data').on('click', function() {
        updateDialogObject();
        $('textarea[name="edit' + dialogInputId + '"]').text(JSON.stringify(dialogObj));
        $('#data-source-modal').hide();
	});

    function updateDialogObject() {
        Object.keys(dialogObj).forEach(constraint => {

            //Technologies
            var techsInput = $("#" + constraint + "_techs").val();
            if (techsInput && techsInput.length > 0) {
                dialogObj[constraint].techs = techsInput;
            } else {
                delete dialogObj[constraint].techs;
            }

            techsInput = $("#" + constraint + "_techs_lhs").val();
            if (techsInput && techsInput.length > 0) {
                dialogObj[constraint].techs_lhs = techsInput;
            } else {
                delete dialogObj[constraint].techs_lhs;
            }

            techsInput = $("#" + constraint + "_techs_rhs").val();
            if (techsInput && techsInput.length > 0) {
                dialogObj[constraint].techs_rhs = techsInput;
            } else {
                delete dialogObj[constraint].techs_rhs;
            }
            
            // Locations
            var locsInput = $("#" + constraint + "_locs").val();
            if (locsInput && locsInput.length > 0) {
                dialogObj[constraint].locs = locsInput;
            } else {
                delete dialogObj[constraint].locs;
            }

            locsInput = $("#" + constraint + "_locs_lhs").val();
            if (locsInput && locsInput.length > 0) {
                dialogObj[constraint].locs_lhs = locsInput;
            } else {
                delete dialogObj[constraint].locs_lhs;
            }

            locsInput = $("#" + constraint + "_locs_rhs").val();
            if (locsInput && locsInput.length > 0) {
                dialogObj[constraint].locs_rhs = locsInput;
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
    }

    $('.group-constraints-close').on('click', function() {
        $('#data-source-modal').hide();
    });


    $('#new_group_constraint_btn').on('click', function() {
        var newGroupConstraint = $('#new_group_constraint_name').val().trim();
        if (newGroupConstraint.length > 0) {
            dialogObj[newGroupConstraint] = {};
            $('#new_group_constraint_name').val("");
            updateDialogConstraints();
            $('#new_group_constraint_btn').attr("disabled", true);
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