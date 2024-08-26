var bulk_confirmation = false,
    dialogInputId = null,
    dialogInputValue = null,
    dialogObj = {},
    disable_new_constraint = true,
	map_mode = 'scenarios',
    carriers = null,
    admin_group_constraints = null,
    initialDialogOpen = true,
    constraints = {
        "demand_share_min":"carriers", "demand_share_max":"carriers", "demand_share_equals":"carriers",
        "demand_share_per_timestep_min":"carriers", "demand_share_per_timestep_max":"carriers", "demand_share_per_timestep_equals":"carriers",
        "demand_share_per_timestep_decision":"carriers", "carrier_prod_share_min":"carriers", "carrier_prod_share_max":"carriers",
        "carrier_prod_share_equals":"carriers", "carrier_prod_share_per_timestep_min":"carriers", "carrier_prod_share_per_timestep_max":"carriers",
        "carrier_prod_share_per_timestep_equals":"carriers", "net_import_share_min":"carriers", "net_import_share_max":"carriers",
        "net_import_share_equals":"carriers", "carrier_prod_min":"carriers", "carrier_prod_max":"carriers", "carrier_prod_equals":"carriers",
        "carrier_con_min":"carriers", "carrier_con_max":"carriers", "carrier_con_equals":"carriers", "cost_max":"costs", "cost_min":"costs",
        "cost_equals":"costs", "cost_var_max":"costs", "cost_var_min":"costs", "cost_var_equals":"costs", "cost_investment_max":"costs",
        "cost_investment_min":"costs", "cost_investment_equals":"costs", "energy_cap_share_min":"none", "energy_cap_share_max":"none",
        "energy_cap_share_equals":"none", "energy_cap_min":"none", "energy_cap_max":"none", "energy_cap_equals":"none", "resource_area_min":"none",
        "resource_area_max":"none", "resource_area_equals":"none", "storage_cap_min":"none", "storage_cap_max":"none", "storage_cap_equals":"none",
        "target_reserve_share_equals":"carriers", "target_reserve_share_max":"carriers", "target_reserve_share_min":"carriers",
        "target_reserve_adder_equals":"carriers", "target_reserve_adder_max":"carriers", "target_reserve_adder_min":"carriers",
        "target_reserve_abs_equals":"carriers", "target_reserve_abs_max":"carriers", "target_reserve_abs_min":"carriers",
        "target_reserve_share_operating_equals":"carriers", "target_reserve_share_operating_max":"carriers",
        "target_reserve_share_operating_min":"carriers", "target_reserve_abs_operating_equals":"carriers",
        "target_reserve_abs_operating_max":"carriers", "target_reserve_abs_operating_min":"carriers",
        "target_reserve_adder_operating_equals":"carriers", "target_reserve_adder_operating_max":"carriers", "target_reserve_adder_operating_min":"carriers"
    };

$( document ).ready(function() {

	// Resize Dashboard
	splitter_resize();

	$('#map-legend').css("display", "none");
	$('#master-new').removeClass('hide');

	$('#scenario').on('change', function() {
		get_scenario_configuration();
	});

    $('#scenario-settings').on('click', function() {
		$('#pvwatts_form').hide();
        $('#wtk_form').hide();
		$('#scenario_constraints_json_form').hide();
        $('#scenario_weights_json_form').hide();
        $('#modal_scenario_settings').show();
		$("#data-source-modal").css('display', "block");
	});

	$('#master-save').on('click', function() {
        $('.master-btn').addClass('hide')
        $('#master-settings').removeClass('hide');
        $('#form_scenario_settings').addClass('hide');
        $('#scenario_configuration').removeClass('hide')
        save_scenario_settings();
	});

	$('#modal-save').on('click', function() {
        $('.master-btn').addClass('hide')
        $('#master-settings').removeClass('hide');
        $('#form_scenario_settings').addClass('hide');
        $('#scenario_configuration').removeClass('hide')
        save_modal_scenario_settings();
	});

	$('#master-new').on('click', function() {
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/add_scenarios/';
	});

	$('#master-cancel').on('click', function() {
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/scenarios/';
	});

	$('#modal-cancel').on('click', function() {
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/scenarios/';
	});

    $("#new_group_constraint_name").on("input", function() {
        handleInputOrDropdownChange();
    });

	get_scenario_configuration();
});

function handleInputOrDropdownChange() {
    if (isCalliopeVersionSeven(calliope_version)) {
        if ($('#new_group_constraint_name').val() && $('#new_group_constraint_name').val().trim().length > 0 &&
        $('#new_group_constraint_dropdown').val()) {
            $('#new_group_constraint_btn').removeAttr("disabled");
        } else {
            $('#new_group_constraint_btn').attr("disabled", true);
        }
    } else {
        if ($('#new_group_constraint_name').val() && $('#new_group_constraint_name').val().trim().length > 0 ) {
            $('#new_group_constraint_btn').removeAttr("disabled");
        } else {
            $('#new_group_constraint_btn').attr("disabled", true);
        }
    }
}

function save_scenario_settings() {

	var model_uuid = $('#header').data('model_uuid'),
		scenario_id = $("#scenario option:selected").data('id')
		form_data = $("#form_scenario_settings :input").serializeJSON();
	$.ajax({
		url: '/' + LANGUAGE_CODE + '/api/update_scenario/',
		type: 'POST',
		data: {
			'model_uuid': model_uuid,
			'scenario_id': scenario_id,
			'description' : $('#scenario_description').val(),
            'name' :$('#scenario_name').val(),
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

function save_modal_scenario_settings() {

	var model_uuid = $('#header').data('model_uuid'),
		scenario_id = $("#scenario option:selected").data('id')
		form_data = $("#scenario_settings :input").serializeJSON();
	$.ajax({
		url: '/' + LANGUAGE_CODE + '/api/update_scenario/',
		type: 'POST',
		data: {
			'model_uuid': model_uuid,
			'scenario_id': scenario_id,
			'description' : $('#scenario_description').val(),
            'name' :$('#scenario_name').val(),
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
        $('#scenario_details').html(data['scenario_details']);
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
                    // Here is tto change

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
		// $('#scenario_configuration').html('<div class="col-12 text-center"><br/><br/><h4>Select or create a scenario above!</h4></div>');
	};
};

function convertToJSON() {
    let tempDialogObj = structuredClone(dialogObj);
    Object.keys(dialogObj).forEach(constraint => {
        let constraintId = safeHTMLId(constraint);

        if (isCalliopeVersionSeven(calliope_version)) {
            let groupConstraintId = constraint.split("||")[0];
            let adminGroupConstraint = admin_group_constraints.find(obj => obj.id === Number(groupConstraintId));
            let tempEquations = adminGroupConstraint.equations[0].expression;

            // Remove values not inputted 
            Object.entries(tempDialogObj[constraint].sub_expression).forEach(([key, value]) => {
                if (tempDialogObj[constraint].sub_expression[key][0].expression == [] || tempDialogObj[constraint].sub_expression[key][0].expression == "") {
                    delete tempDialogObj[constraint].sub_expression[key];
                } 
            });

            Object.entries(tempDialogObj[constraint].slices).forEach(([key, value]) => {
                if (tempDialogObj[constraint].slices[key][0].expression == [] || tempDialogObj[constraint].slices[key][0].expression == "") {
                    delete tempDialogObj[constraint].slices[key];
                    let toDelete = `||${key}||`
                    tempEquations = tempEquations.replace(toDelete, "");
                }
            });

            // Throw error if values are not filled out and at least one dropdown?

            // Update equation
            tempEquations = tempEquations.replaceAll("||||", ",");
            tempEquations = tempEquations.replaceAll("||", "");
            tempEquations = tempEquations.replace("[]", "");
            tempDialogObj[constraint].equations[0].expression = tempEquations;

            delete tempDialogObj[constraint].id;
        } else {
            var techsInput = $("#" + constraintId + "_techs").val();
            if (techsInput && techsInput.length > 0) {
                dialogObj[constraint].techs = techsInput;
            } else {
                delete dialogObj[constraint].techs;
            }

            var techsInputLhs = $("#" + constraintId + "_techs_lhs").val();
            if (techsInputLhs && techsInputLhs.length > 0) {
                dialogObj[constraint].techs_lhs = techsInputLhs;
            } else {
                delete dialogObj[constraint].techs_lhs;
            }

            var techsInputRhs = $("#" + constraintId + "_techs_rhs").val();
            if (techsInputRhs && techsInputRhs.length > 0) {
                dialogObj[constraint].techs_rhs = techsInputRhs;
            } else {
                delete dialogObj[constraint].techs_rhs;
            }

            // Locations
            var locsInput = $("#" + constraintId + "_locs").val();
            if (locsInput && locsInput.length > 0) {
                dialogObj[constraint].locs = locsInput;
            } else {
                delete dialogObj[constraint].locs;
            }

            var locsInputLhs = $("#" + constraintId + "_locs_lhs").val();
            if (locsInputLhs && locsInputLhs.length > 0) {
                dialogObj[constraint].locs_lhs = locsInputLhs;
            } else {
                delete dialogObj[constraint].locs_lhs;
            }

            var locsInputRhs = $("#" + constraintId + "_locs_rhs").val();
            if (locsInputRhs && locsInputRhs.length > 0) {
                dialogObj[constraint].locs_rhs = locsInputRhs;
            } else {
                delete dialogObj[constraint].locs_rhs;
            }

            // Add constraints
            Object.keys(dialogObj[constraint]).forEach(fieldKey => {
                if (fieldKey !== "locs" && fieldKey !== "techs" && fieldKey !== "techs_lhs" && fieldKey !== "techs_rhs" && fieldKey !== "locs_lhs" && fieldKey !== "locs_rhs") {
                    let value = $("#" + constraintId + fieldKey + "-val").val();
                    if (value) {
                        value = parseFloat(value, 10);
                    } else {
                        value = 0;
                    }

                    if (constraints[fieldKey] !== "none") {
                        let key = $("#" + constraintId + fieldKey + "-key").val() ? $("#" + constraintId + fieldKey + "-key").val() : "";
                        dialogObj[constraint][fieldKey] = {};
                        if (key) {
                            dialogObj[constraint][fieldKey][key] = value;
                        }
                    } else {
                        dialogObj[constraint][fieldKey] = value;
                    }
                }
            });
        }
    });

    return isCalliopeVersionSeven(calliope_version) ? tempDialogObj : dialogObj;

}

function updateDialogGroupConstraints(initialLoad) {
    $('#dialog-inputs').empty();
    if (dialogObj.length > 0) {
        $('#dialog-inputs').append("<h3><b>Constraint Groups</b></h3>");
    }

    Object.keys(dialogObj).forEach(constraint => {
        let groupConstraintPrettyName = constraint.split("||")[1] ? constraint.split("||")[1] : "Error: Misformatted string";
        let constraintId = safeHTMLId(constraint);
        let adminGroupConstraint = admin_group_constraints.find(obj => obj.id === Number(dialogObj[constraint].id));
        $('#dialog-inputs').append( "<div id='" + constraintId + "' style='padding-top:1.5em'></div>");
        $("#" + constraintId).append( "<div class='cateogry-expander'><a><h5 class='constraint-name'><div style='float: right;'><i class='fas fa-caret-down'></i><i class='fas fa-caret-up' style='display: none;'></i>" + groupConstraintPrettyName
        + "</div></h5></a></div>");

        $(`#${constraintId}`).append(`<div id="${constraintId}-content" name="${constraint}" class=""></div>`);
        let constraintContent = "#" + constraintId + "-content";
        $(constraintContent).append(`
            <button id="delete_group_constraint_btn_${constraintId}" 
                    name="${constraint}" 
                    type="button" 
                    class="btn btn-sm btn-outline-danger group-constraint-delete" 
                    title="Delete constraint">
                <i class="fas fa-trash"></i>
            </button>
        `);
        $("#delete_group_constraint_btn_" + constraintId).on('click', function() {
            delete dialogObj[$(this).attr('name')];
            updateDialogGroupConstraints();
        });

        renderGroupConstraintDropdowns(constraint, constraintId, constraintContent, adminGroupConstraint);

        if (isCalliopeVersionSeven(calliope_version)) {
            renderSubExpressions(constraint, constraintId, constraintContent, adminGroupConstraint);
        }
        
        if (!isCalliopeVersionSeven(calliope_version) ) {
            updateConstraintTypes(constraint, constraintId, constraintContent);
        }

        $(constraintContent).append( "<hr>" );
        $(document).ready(function() {
            $('[data-toggle="tooltip"]').tooltip();
        });
    });
    

    if (initialLoad) {
        var rows = $('.cateogry-expander').next();
        rows.addClass('hide');
        $('.cateogry-expander').addClass('hiding_rows');
        $('.cateogry-expander').find('.fa-caret-down').addClass('hide');
        $('.cateogry-expander').find('.fa-caret-up').removeClass('hide');
    }
    setGroupConstraintClassLogic();
    
}

function renderSubExpressions(constraint, constraintId, constraintContent, adminGroupConstraint) {
    Object.entries(adminGroupConstraint.sub_expression).forEach(([key, value]) => {
        if (value.show) {
            $(constraintContent).append(`<label><b>${key}</b></label>`);
            const input = $(`<input type='number' id='${constraintId}${key}-val' name='${constraint}' data-key=${key} class='form-control smol' placeholder='' value='${dialogObj[constraint].sub_expression[key][0]?.expression || ""}' step='1'></input><br><br>`);
            $(constraintContent).append(input);

            $(`#${constraintId}${key}-val`).on('input', function() {
                dialogObj[$(this).attr('name')].sub_expression[$(this).attr('data-key')][0].expression = $(this).val();
            });
        }
    });
}

function renderGroupConstraintDropdowns(constraint, constraintId, constraintContent, adminGroupConstraint) {

    if (isCalliopeVersionSeven(calliope_version)) {
        Object.entries(dialogObj[constraint].slices).forEach(([key, value]) => {
            if (isCalliopeVersionSeven(calliope_version)) {
                let sliceDim = adminGroupConstraint.slices[key].dim;
                let sliceOptions = [];
                if (sliceDim == "techs") {
                    sliceOptions = technologies;
                } else if (sliceDim == "locs") {
                    sliceOptions = locations;
                } else if (sliceDim == "carriers") {
                    sliceOptions = carriers;
                } else if (sliceDim == "costs") {
                    sliceOptions = ["co2", "ch4", "co2e", "n2o", "monetary"];
                }
                createDropdown(
                    `${constraintId}_${key}`,
                    constraint,
                    key,
                    sliceOptions,
                    dialogObj[constraint].slices[key][0]?.expression,
                    constraintContent,
                    Array.isArray(dialogObj[constraint].slices[key][0]?.expression)
                );
            }
        });
    } else {
        // Calliope 6

        // Initialize techs dropdown
        dialogObj[constraint].techs = dialogObj[constraint].techs || "";
        createDropdown(
            `${constraintId}_techs`,
            constraint,
            djangoTranslateTechnologies,
            technologies,
            dialogObj[constraint].techs,
            constraintContent,
            true
        );

        // Initialize techs_lhs dropdown
        dialogObj[constraint].techs_lhs = dialogObj[constraint].techs_lhs || "";
        createDropdown(
            `${constraintId}_techs_lhs`,
            constraint,
            `${djangoTranslateTechnologies} ${djangoTranslateLeftHand}`,
            technologies,
            dialogObj[constraint].techs_lhs,
            constraintContent,
            true
        );
        
        // Initialize techs_rhs dropdown
        dialogObj[constraint].techs_rhs = dialogObj[constraint].techs_rhs || "";
        createDropdown(
            `${constraintId}_techs_rhs`,
            constraint,
            `${djangoTranslateTechnologies} ${djangoTranslateRightHand}`,
            technologies,
            dialogObj[constraint].techs_rhs,
            constraintContent,
            true
        );
        

        // Show or hide techs dropdowns based on conditions
        if (!(dialogObj[constraint].techs_rhs && dialogObj[constraint].techs_lhs && dialogObj[constraint].techs)) {
            $(constraintContent).append(`<br><span>${djangoTranslateShowLeftRight} ${djangoTranslateTechnologies} </span>
                <label class="switch">
                    <input id="${constraintId}_toggle_techs" type="checkbox"><span class="slider round"></span>
                </label><br>`
            );
            $(`#${constraintId}_toggle_techs`).click(function() {
                $(`#${constraintId}_techs_container`).toggle();
                $(`#${constraintId}_techs_lhs_container`).toggle();
                $(`#${constraintId}_techs_rhs_container`).toggle();
            });
        }

        // Initialize locs dropdown
        dialogObj[constraint].locs = dialogObj[constraint].locs || "";
        createDropdown(
            `${constraintId}_locs`,
            constraint,
            djangoTranslateLocations,
            locations,
            dialogObj[constraint].loc,
            constraintContent,
            true
        );
        

        // Initialize locs_lhs dropdown
        dialogObj[constraint].locs_lhs = dialogObj[constraint].locs_lhs || "";
        createDropdown(
            `${constraintId}_locs_lhs`,
            constraint,
            `${djangoTranslateLocations} ${djangoTranslateLeftHand}`,
            locations,
            dialogObj[constraint].locs_lhs,
            constraintContent,
            true
        );
        
        
        // Initialize locs_rhs dropdown
        dialogObj[constraint].locs_rhs = dialogObj[constraint].locs_rhs || "";
        createDropdown(
            `${constraintId}_locs_rhs`,
            constraint,
            `${djangoTranslateLocations} ${djangoTranslateRightHand}`,
            locations,
            dialogObj[constraint].locs_rhs,
            constraintContent,
            true
        );
        

        // Show or hide locs dropdowns based on conditions specified
        if (!(dialogObj[constraint].locs_rhs && dialogObj[constraint].locs_lhs && dialogObj[constraint].locs)) {
            $(constraintContent).append(`<br><span>${djangoTranslateShowLeftRight} ${djangoTranslateLocations} </span>
                <label class="switch">
                    <input id="${constraintId}_toggle_locs" type="checkbox"><span class="slider round"></span>
                </label><br>`
            );
            $(`#${constraintId}_toggle_locs`).click(function() {
                $(`#${constraintId}_locs_container`).toggle();
                $(`#${constraintId}_locs_lhs_container`).toggle();
                $(`#${constraintId}_locs_rhs_container`).toggle();
            });
        }

        // Initial visibility for techs dropdowns
        if (!dialogObj[constraint].techs_rhs && !dialogObj[constraint].techs_lhs) {
            $(`#${constraintId}_techs_lhs_container`).hide();
            $(`#${constraintId}_techs_rhs_container`).hide();
        }

        // Initial visibility for locs dropdowns
        if (!dialogObj[constraint].locs_rhs && !dialogObj[constraint].locs_lhs) {
            $(`#${constraintId}_locs_lhs_container`).hide();
            $(`#${constraintId}_locs_rhs_container`).hide();
        }
    }
    
}

function createDropdown(id, constraint, label, options, selectedValues, constraintContent, isMultiSelect) {
    let dropdownHtml = `
        <div id="${id}_container" class="input-wrapper single">
            <label data-toggle="tooltip" data-placement="bottom" data-original-title="Optionally enter ${label}."><b>${label}</b></label><br>
            <select id="${id}" name="${constraint}"></select>
        </div>
    `;

    if (isMultiSelect) { 
        dropdownHtml = `
            <div id="${id}_container" class="input-wrapper">
                <label data-toggle="tooltip" data-placement="bottom" data-original-title="Optionally enter ${label}."><b>${label}</b></label><br>
                <select id="${id}" name="${constraint}" data-label="${label}" multiple searchable></select>
            </div>
        `;
    }

    if (!isMultiSelect) { 
        $(`#${id}`).append(selectedValues && selectedValues.length > 0 ? `<option value=""></option>` : `<option selected value=""></option>`);
    }

    $(constraintContent).append(dropdownHtml);

    options.forEach(option => {
        optionValue = option;
        optionText = option;

        if (isMultiSelect) { 
            optionValue = option.tag ? `${option.name}-${option.tag}` : option.name;
            optionText = option.tag ? `${option.pretty_name} [${option.pretty_tag}]` : option.pretty_name;
        } 
        isSelected = selectedValues.includes(optionValue) ? ' selected' : '';
        
        $(`#${id}`).append(`<option value="${optionValue}"${isSelected}>${optionText}</option>`);
    });

    if (!isCalliopeVersionSeven(calliope_version)) {
        $(`#${id}`).on('change', function () {
            convertToJSON();
        });
    } else {
        $(`#${id}`).on('change', function () {
           dialogObj[$(this).attr('name')].slices[$(this).attr('data-label')][0].expression = $(this).val();
        });
    }

    if (isMultiSelect) { 
        $(`#${id}`).multiselect({
            includeSelectAllOption: false,
            enableFiltering: true,
            enableCaseInsensitiveFiltering: true,
            buttonWidth: '550px'
        });
    }

}

function updateConstraintTypes(constraint, constraintId, constraintContent) {
    $(constraintContent).append( "<label id='constraints-label' data-toggle='tooltip' data-placement='bottom' data-original-title='Multiple constraints can be added to a single constraint group. Cost and carriers are a key and value pair whereas all other types are a value. See Constraint column in Calliope documentation for value options.'><b>" + djangoTranslateConstraints + "</b></label><br>");

    Object.keys(dialogObj[constraint]).forEach(fieldKey => {
        if (fieldKey !== "locs" && fieldKey !== "techs" && fieldKey !== "techs_lhs" && fieldKey !== "techs_rhs" && fieldKey !== "locs_lhs" && fieldKey !== "locs_rhs") {

            $(constraintContent).append( "<label style='padding-left:20px'><b>" + djangoTranslateConstraint + "</b></label><div style='float:right;'><span style='margin-right: 10px'>" + fieldKey + "</span><button id='delete_constraint_btn_" + constraintId + "-" + fieldKey + "' type='button' class='btn btn-sm btn-outline-danger constraint-delete' title='Delete constraint'><i class='fas fa-trash'></i></button></div><br>");
            $("#delete_constraint_btn_" + constraintId + "-" + fieldKey).on('click', function() {
                let con = this.id.replace("delete_constraint_btn_", '').split("-");
                delete dialogObj[constraint][con[1]];
                updateDialogGroupConstraints();
            });
            let constraintFields = "#fields-" + constraintId + fieldKey;
            $(constraintContent).append("<div id='fields-" + constraintId + fieldKey + "' class='constraint-key-value' ></div>");
            if (constraints[fieldKey] != 'none') {
                if (!dialogObj[constraint][fieldKey] || typeof dialogObj[constraint][fieldKey] !== 'object') {
                    dialogObj[constraint][fieldKey] = {};
                }
                const key = Object.keys(dialogObj[constraint][fieldKey]).length !== 0 ? Object.keys(dialogObj[constraint][fieldKey])[0] : "";
                const val = key ? dialogObj[constraint][fieldKey][Object.keys(dialogObj[constraint][fieldKey])[0]] : "";
                $(constraintFields).append( "<label><b>" + djangoTranslateKey + "</b></label>");
                let dropdownArray = constraints[fieldKey] == 'carriers' ? carriers : ["co2", "ch4", "co2e", "n2o", "monetary"];
                if (key.length > 0 && dropdownArray.indexOf(key) === -1) {
                    dropdownArray.push(key);
                }
                $(constraintFields).append( "<select style='margin-bottom:1em' class='form-control smol' id='" + constraintId + fieldKey + "-key' name='dialogObj[constraint][fieldKey].name' data-toggle='tooltip' data-placement='left'></select><br><br>" );
                for (let i = 0; i < dropdownArray.length; i++) {
                    if (key == dropdownArray[i]) {
                        $('#' + constraintId + fieldKey + '-key').append( "<option selected value=" + dropdownArray[i] + ">" + dropdownArray[i] + "</option>" );
                    } else {
                        $('#' + constraintId + fieldKey + '-key').append( "<option value=" + dropdownArray[i] + ">" + dropdownArray[i] + "</option>" );
                    }
                }

                $("#" + constraintId + fieldKey + "-key").on('change', function () {
                    convertToJSON();
                });

                $(constraintFields).append( "<label><b>" + djangoTranslateValue + " </b></label>");
                $(constraintFields).append("<input type='number' id='" + constraintId + fieldKey + "-val' name='dialogObj[constraint][" + fieldKey + "].value' class='form-control smol' placeholder='' value='" + val + "' step='1'></input><br><br>");
            } else {
                $(constraintFields).append( "<label><b>" + djangoTranslateValue + "</b></label>");
                $(constraintFields).append( "<input id='" + constraintId + fieldKey + "-val' name='dialogObj[constraint][fieldKey]' class='form-control smol' placeholder='' value='" + dialogObj[constraint][fieldKey] + "'></input><br><br>" );
            }
            $("#" + constraintId + fieldKey + "-val").on('change', function () {
                convertToJSON();
            });
        }
    });

    $(constraintContent).append( "<br><label><b>" + djangoTranslateNew + ' ' + djangoTranslateConstraint + "</b></label>");
    $(constraintContent).append( "<select style='margin-bottom:1em' class='form-control smol' id='new-constraint-dropdown-" + constraintId + "' data-toggle='tooltip' data-placement='left'></select>" );
    $('#new-constraint-dropdown-' + constraintId ).append( "<option></option>" );
    i = 0;
    for (const [fieldKey,fieldValue] of Object.entries(constraints)) {
        i=i+1;
        $('#new-constraint-dropdown-' + constraintId ).append( "<option value=" + fieldKey + ">" + fieldKey + "</option>" );
    }

    $(constraintContent).append("<div class='form-group col-md-8'><input disabled id='new_constraint_btn_" + constraintId + "' type='submit' class='btn btn-sm btn-success' name='" + constraint + "' value='+ " + djangoTranslateConstraint + "'></div>");
    $("#new_constraint_btn_" + constraintId).on('click', function() {
        let con = this.id.replace("new_constraint_btn_", "");
        let newConstraint = $("#new-constraint-dropdown-" + con).val();
        if (newConstraint && newConstraint.length > 0) {
            dialogObj[this.name][newConstraint] = "";
        }
        updateDialogGroupConstraints();
    });

    $("#new-constraint-dropdown-" + constraintId).on('change', function(e) {
        let con = this.id.replace("new-constraint-dropdown-", "");
        if (this.value && this.value.length > 0 ) {
            $("#new_constraint_btn_" + con).removeAttr("disabled");
        } else {
            $('#new_constraint_btn_' + con).attr("disabled", true);
        }
    });

}

function safeHTMLId(id) {
    return id.replace(/([^A-Za-z0-9[\]{}_:-])\s?/g, '');
}

function setGroupConstraintClassLogic() {
    $('.cateogry-expander').unbind();
    $('.cateogry-expander').on('click', function(){
        var rows = $(this).next();
        if ($(this).hasClass('hiding_rows')) {
            rows.removeClass('hide');
            $(this).removeClass('hiding_rows');
            $(this).find('.fa-caret-up').css('display', 'inline');
            $(this).find('.fa-caret-down').css('display', 'none');
        } else {
            rows.addClass('hide');
            $(this).addClass('hiding_rows');
            $(this).find('.fa-caret-up').css('display', 'none');
            $(this).find('.fa-caret-down').css('display', 'inline');
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

    const parseJSON = (inputString, fallback) => {
        if (inputString && inputString.length > 0) {
          try {
            return JSON.parse(inputString);
          } catch (e) {
            return fallback;
          }
        }
        return fallback;
    };

    // Wieght of cost classes Modal
    $('.scenario-weight-dialog-btn').on('click', function() {
        // display dialog
		$('#pvwatts_form').hide();
        $('#wtk_form').hide();
		$('#scenario_constraints_json_form').hide();
        $('#modal_scenario_settings').hide();
        $('#scenario_weights_json_form').show();
		$("#data-source-modal").css('display', "block");

        dialogInputId = this.name.slice(6);
        dialogInputValue = dialogInputId ? $('textarea[name="edit' + dialogInputId + '"]').text() : console.log("Dialog input id not found!");
        dialogInputValue = dialogInputValue.replace(/'/g, '"');
        dialogObj = parseJSON(dialogInputValue, {});

        $('#monetary').val(dialogObj["monetary"]);
        $('#co2').val(dialogObj["co2"]);
        $('#ch4').val(dialogObj["ch4"]);
        $('#n2o').val(dialogObj["n2o"]);
        $('#co2e').val(dialogObj["co2e"]);
    });

    // Constraint Group Modal
	$('.scenario-constraints-dialog-btn').on('click', function() {
        
        // display dialog
		$('#pvwatts_form').hide();
        $('#wtk_form').hide();
        $('#scenario_weights_json_form').hide();
        $('#modal_scenario_settings').hide();
		$('#scenario_constraints_json_form').show();
		$("#data-source-modal").css('display', "block");

        // Get dialog data
        dialogInputId = this.name.slice(6);
        dialogInputValue = dialogInputId ? $('textarea[name="edit' + dialogInputId + '"]').text() : console.log("Dialog input id not found!");
        dialogInputValue = dialogInputValue.replace(/'/g, '"');
        dialogObj = parseJSON(dialogInputValue, {}); 

        processDialogObj(dialogObj).then(() => {
            getModelCarriers();
            if (isCalliopeVersionSeven(calliope_version)) {
                getAdminGroupConstraints();
            
                if (initialDialogOpen) {
                    $('#new_group_constraint_btn').val('+ Group Constraint');
                    $('#new_group_constraint_name').attr('placeholder', 'Group Constraint Name');
                    var dropdownHtml = `
                        <div class="constraint-key-value">
                            <label><b>Group Constraint</b></label>
                            <select class="form-control smol" id="new_group_constraint_dropdown">
                            </select>
                        </div>
                        <br>
                    `;

                    $('#name-input').after(dropdownHtml);

                    $('#new_group_constraint_dropdown').append('<option selected value=""></option>');
                    for (var gc in admin_group_constraints) {
                        $('#new_group_constraint_dropdown').append('<option value="' + admin_group_constraints[gc].id + '">' + admin_group_constraints[gc].pretty_name + '</option>');
                    }
                }
                initialDialogOpen = false;

                $("#new_group_constraint_dropdown").on("change", function() {
                    handleInputOrDropdownChange();
                });
            }
            updateDialogGroupConstraints(true);
        }).catch(error => {
            console.error("Error processing dialogObj:", error);
        });

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
            let tempDialogObj = convertToJSON();
            $('#JSONPreview').text(JSON.stringify(tempDialogObj, undefined, 2));
        });

	});

    function processDialogObj(dialogObj) {
        if (isCalliopeVersionSeven(calliope_version) ) {
            //Take example of final product and convert to json format
            Object.keys(dialogObj).forEach(constraint => {
                // Change "[]" to a reall array for each slice expression

                // Split name||id to just name with an id subobject
            });
            return Promise.resolve({});
        } else {    
            return new Promise((resolve, reject) => {
                try {
                    Object.keys(dialogObj).forEach(constraint => {
                        Object.keys(dialogObj[constraint]).forEach(fieldKey => {
                            // Technologies
                            if (fieldKey === "techs") {
                                var newTechs = "";
                                if (dialogObj[constraint].techs && dialogObj[constraint].techs.length > 0) {
                                    for (var tech in dialogObj[constraint].techs) {
                                        newTechs += dialogObj[constraint].techs[tech];
                                        if (Number(tech) !== dialogObj[constraint].techs.length - 1) {
                                            newTechs += ",";
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
                                        if (Number(tech) !== dialogObj[constraint].techs_lhs.length - 1) {
                                            newTechs += ",";
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
                                        if (Number(tech) !== dialogObj[constraint].techs_rhs.length - 1) {
                                            newTechs += ",";
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
                                        if (Number(loc) !== dialogObj[constraint].locs.length - 1) {
                                            newLocs += ",";
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
                                        if (Number(loc) !== dialogObj[constraint].locs_lhs.length - 1) {
                                            newLocs += ",";
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
                                        if (Number(loc) !== dialogObj[constraint].locs_rhs.length - 1) {
                                            newLocs += ",";
                                        }
                                    }
                                }
                                dialogObj[constraint].locs_rhs = newLocs;
                            }
                        });
                    });
                    resolve();
                } catch (error) {
                    reject(error);
                }
            });
        }
    }

    $('#settings_import_data').on('click', function() {
        let tempDialogObj = convertToJSON();
        $('textarea[name="edit' + dialogInputId + '"]').text(JSON.stringify(tempDialogObj, undefined, 2));
        $('#scenario_constraints_json_form').hide();
        $('#modal_scenario_settings').show();
	});

    $('#settings_import_cancel').on('click', function() {
        $('#scenario_constraints_json_form').hide();
        $('#modal_scenario_settings').show();
	});

    $('#settings_weights_import_data').on('click', function() {
        dialogObj["monetary"] = $("#monetary").val();
        dialogObj["co2"] = $("#co2").val();
        dialogObj["ch4"] = $("#ch4").val();
        dialogObj["n2o"] = $("#n2o").val();
        dialogObj["co2e"] = $("#co2e").val();

        $('textarea[name="edit' + dialogInputId + '"]').text(JSON.stringify(dialogObj, undefined, 2));
        $('#scenario_weights_json_form').hide();
        $('#modal_scenario_settings').show();

        // $('#data-source-modal').hide();
	});

    $('.group-constraints-close, .weights-close').on('click', function() {
        $('#data-source-modal').hide();
    });


    $('#new_group_constraint_btn').on('click', function() {
        var newGroupConstraint = $('#new_group_constraint_name').val().trim();

        let groupConstraintId;
        if (isCalliopeVersionSeven(calliope_version)) {
            if (!$('#new_group_constraint_dropdown').val() || $('#new_group_constraint_dropdown').val().length <= 0) {
                return;
            }
            groupConstraintId = $('#new_group_constraint_dropdown').val();
            newGroupConstraint = groupConstraintId + '||' + newGroupConstraint
        }

        if (newGroupConstraint.length > 0) {
            dialogObj[newGroupConstraint] = {};

            if (isCalliopeVersionSeven(calliope_version)) {
                let adminGroupConstraint = admin_group_constraints.find(obj => obj.id === Number(groupConstraintId));

                // Construct object
                dialogObj[newGroupConstraint].id = groupConstraintId;

                if (adminGroupConstraint.where) {
                    dialogObj[newGroupConstraint].where = adminGroupConstraint.where;
                }
                dialogObj[newGroupConstraint].description = adminGroupConstraint.description;
                dialogObj[newGroupConstraint].equations = structuredClone(adminGroupConstraint.equations);
                dialogObj[newGroupConstraint].slices = dialogObj[newGroupConstraint].slices ? dialogObj[newGroupConstraint].slices : {};
                Object.entries(adminGroupConstraint.slices).forEach(([key, value]) => {
                    dialogObj[newGroupConstraint].slices[key] = structuredClone(value.yaml);
                });
                dialogObj[newGroupConstraint].sub_expression = dialogObj[newGroupConstraint].sub_expression ? dialogObj[newGroupConstraint].sub_expression : {};
                Object.entries(adminGroupConstraint.sub_expression).forEach(([key, value]) => {
                    if (value.show) {
                        dialogObj[newGroupConstraint].sub_expression[key] = structuredClone(value.yaml);
                    }
                });
                if (adminGroupConstraint.for_each) {
                    dialogObj[newGroupConstraint].for_each = structuredClone(adminGroupConstraint.for_each);
                }
   
                $('#new_group_constraint_dropdown').val("");
            }

            $('#new_group_constraint_name').val("");
            $('#new_group_constraint_btn').attr("disabled", true);
            updateDialogGroupConstraints();
        }

    });
}

function getAdminGroupConstraints() {
    $.ajax({
        url: '/' + LANGUAGE_CODE + '/admin/group_constraints/',
        async: false,
        data: {
        },
        dataType: 'json',
        success: function (data) {
            admin_group_constraints = data.admin_group_constraints ? data.admin_group_constraints : [];
        }
    });
}

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


