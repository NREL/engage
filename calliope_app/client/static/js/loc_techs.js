var map_mode = 'loc_techs';
let template_data = {};
let template_edit = {};
let geoInputs = "GEOPHIRES Inputs";
let geoOutputs = "GEOPHIRES Outputs";

//import { getTemplateData } from 'templates.js';

$( document ).ready(function() {

	initiate_units();

    //------------Start Templates------------//
    $("#master-new").show();
    $("#master-new").html("Node Groups");
    $('#master-new').css({ "font-size:": '13px'});
    $('#master-new').attr('data-target','#templatesModal');
    $('#master-new').attr('data-toggle','modal');
    $('#master-new').on('click', function() {
		getTemplates();
	});

    $('#addTemplate').on('click', function() {
		addTemplateModal();
	});

    $('#editTemplate').on('click', function() {
		saveTemplate('#editTemplate');
	});

    $('#createTemplate').on('click', function() {
        var isValid = checkFormInputs(true); 
        if (!isValid) {
            return;
        }
		saveTemplate('#createTemplate');
	});

    $('#deleteTemplate').on('click', function() {
		deleteTemplateModal();
	});

    $('#confirmDeleteTemplate').on('click', function() {
		deleteTemplate();
	});

    $('#modelEditBack').on('click', function() {
		modelEditBack();
	});

    $('#modelDeleteBack').on('click', function() {
		modelDeleteBack();
	});

    $('#templateType').on('change', function() {
        appendTemplateCategories();
	});

    //On modal close
    $('#templatesModal').on('hidden.bs.modal', function () {
        closeTemplateModal(false);
    });
    //------------End Templates------------//

	$('#technology').on('change', function() {
		get_loc_techs();
	});

	get_loc_techs();

	// Save modified parameters
	$('#master-save').on('click', function() {

		if (validate_params()) {

			var form_data = filter_param_inputs($("#form_data :input")).serializeJSON();

			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/update_loc_tech_params/',
				type: 'POST',
				data: {
					'model_uuid': $('#header').data('model_uuid'),
					'loc_tech_id': $('tr.loc_tech_row.table-primary').data('loc_tech_id'),
					'form_data': JSON.stringify(form_data),
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

	$('#master-cancel').on('click', function() {
		window.onbeforeunload = null;
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/loc_techs/';
	});

	$('#master-bulk-up').removeClass('hide');
	$('#master-bulk-up').on('click', function(){
		var model_uuid = $('#header').data('model_uuid');
		//e.stopPropagation();
		var uploadForm = document.createElement('form');
		uploadForm.id = 'uploadForm';
		uploadForm.method='post';
		uploadForm.action='/' + LANGUAGE_CODE + '/api/upload_loctechs/';
		uploadForm.enctype = 'multipart/form-data';
		var modelInput = document.createElement('input');
		modelInput.name = 'model_uuid';
		modelInput.value = model_uuid;
		uploadForm.appendChild(modelInput);
		var csrfInput = document.createElement('input');
		csrfInput.name = 'csrfmiddlewaretoken';
		csrfInput.value = getCookie('csrftoken');
		uploadForm.appendChild(csrfInput);
    	var fileInput = document.createElement('input');
		var submit_outputs= document.createElement('input');
		submit_outputs.type = 'submit';
		submit_outputs.id = 'submit_outputs';
		uploadForm.appendChild(submit_outputs);

    	fileInput.type = 'file';
    	fileInput.name = 'myfile';
    	fileInput.multiple = false;
		fileInput.onchange = function(){

			$('#submit_outputs').click();
			uploadForm.remove();
		};

		uploadForm.appendChild(fileInput);
		$(document.body.append(uploadForm));
		fileInput.click();
	});

	$('#master-bulk-down').removeClass('hide');
	$('#master-bulk-down').attr("href", function() { return $(this).attr("href")+"&file_list=loc_techs"});

});

function renderTemplateModal() {
    $("#modalContent").show();
    $("#modalEdit").hide();
    $('#modalBody').empty();
    if (template_data.templates.length > 0) {
        $('#modalBody').append( "<h6>" + djangoTranslateExistingNodeGroups + "</h6>");
        for (var i = 0; i < template_data.templates.length; i++) {
            let id = "edit-" + template_data.templates[i].id;
            $('#modalBody').append( "<label><b>" + template_data.templates[i].name + "</b></label>");
            $('#modalBody').append( "<button type='button' id='" + id + "' class='btn btn-sm' style='padding-bottom:6px' name='" + template_data.templates[i].name + "'><i class='fas fa-edit'></i></button><br>");
            $('#' + id).on('click', function() {
                editTemplateModal(this);
            });
        }
    } else {
        $('#modalBody').append( "<h6>" + djangoTranslateExistingNodeGroupsMessage + "</h6>");
    }

    if ($("#primaryLocation").children('option').length === 0) {
        $("#primaryLocation").prepend( "<option selected value=''></option>");
        for (let i = 0; i < template_data.locations.length; i++) {
            if (template_edit.id == template_data.locations[i].id) {
                $("#primaryLocation").append( "<option selected value=" + template_data.locations[i].id + ">" + template_data.locations[i].pretty_name + "</option>");
            } else {
                $("#primaryLocation").append( "<option value=" + template_data.locations[i].id + ">" + template_data.locations[i].pretty_name + "</option>" );
            }
        }
    }

    if ($("#templateType").children('option').length === 0) {
        $("#templateType").append( "<option value=''></option>");
        for (let i = 0; i < template_data.template_types.length; i++) {
            if (template_edit.name == template_data.template_types[i]) {
                $("#templateType").append( "<option selected value=" + template_data.template_types[i].id + ">" + template_data.template_types[i].pretty_name + "</option>");
            } else {
                $("#templateType").append( "<option value=" + template_data.template_types[i].id + ">" + template_data.template_types[i].pretty_name + "</option>" );
            }
        }
    }
}

function getTemplates() {
    var model_uuid = $('#header').data('model_uuid');

    $.ajax({
        url: '/' + LANGUAGE_CODE + '/model/templates/',
        async: false,
        data: {
            'model_uuid': model_uuid,
            'csrfmiddlewaretoken': getCookie('csrftoken'),
        },
        dataType: 'json',
        success: function (data) {
            template_data = data;
            renderTemplateModal();
        }
    });
}

function deleteTemplateModal() {
    $("#modalEdit").hide();
    $("#modalDelete").show();
}

function editTemplateModal(el) {
    let id = parseInt(el.id.substr(5));
    template_edit = template_data.templates.find(temp => temp.id === id);
    // Set basic inputs
    $('#templateType').val(String(template_edit.template_type)).change();
    $('#templateType').attr("disabled", true);
    $('#primaryLocation').val(String(template_edit.location));
    $('#primaryLocation').attr("disabled", true);

    // Change modal view
    $("#modalContent").hide();
    $("#modalEdit").show();
    $("#createTemplate").hide();
    $("#editTemplate").show();
    $('#editTemplate').attr("disabled", false);
    $("#deleteTemplate").show();
    $("#templateName").val(template_edit.name);
    $("#editModalTitle").html(djangoTranslateUpdateNodeGroup + template_edit.name);
    appendTemplateCategories();
    $("#templateVars input").prop("disabled", true);
    var template_variables = template_data.template_variables.filter(temp => temp.template === id);
    template_variables.forEach(function (template_var) {
        $("#template_type_var_converted_" + template_var.template_type_variable).val(template_var.value);
        $("#template_type_var_" + template_var.template_type_variable).val(template_var.raw_value);
        $("#template_type_var_" + template_var.template_type_variable).attr('name', template_var.name);
    });
}

function addTemplateModal() {
    // Reset basic inputs
    $('#templateType').attr("disabled", false);
    $("#templateType").val([]);
    $('#primaryLocation').attr("disabled", false);
    $("#primaryLocation").val([]);
    $("#templateName").val("");

    // Change modal view
    $("#modalContent").hide();
    $("#modalEdit").show();
    $("#createTemplate").show();
    $("#editTemplate").hide();
    $("#editModalTitle").html(djangoTranslateAddNodeGroup);
    $("#deleteTemplate").hide();

    // Reset category inputs 
    $('#templateVars').empty();
}

function closeTemplateModal(reloadDialog) {
    $("#templateType").val([]);
    $("#primaryLocation").val([]);
    $("#templateName").val('');
    $("#templatesModal").modal('hide');
    $("#templateVars").empty();
    $("#modalDelete").hide();
    $("#editTemplate, #createTemplate").prop("disabled",true);
    template_edit = {};
    if (reloadDialog) {
        window.location.reload();
    }
}

function modelEditBack() {
    $("#modalContent").show();
    $("#modalEdit").hide();
}

function modelDeleteBack() {
    $("#modalContent").show();
    $("#modalDelete").hide();
}

function requestGeophires() {
    var isValid = checkFormInputs(false); 
    if (!isValid) {
        return;
    }
    $("#geophiresGraphs").attr("hidden", false);
    if ($('#runGeophires').is(':disabled')) {
        return;
    }
    $("#runGeophires").prop("disabled", true);
    var templateVarElements = $("#" + geoInputs.replace(/\s/g, '') + "-row :input:not(:button)");
    var templateVars = {};

    for (var i = 0; i < templateVarElements.length; i++) {
        var id = Number(templateVarElements[i].id.replace("template_type_var_", ""));
        let name = template_data.template_type_variables.filter(obj => {
            return obj.id === id
          })[0].name;
        let value = $("#template_type_var_converted_" + id).text() && toNumber($("#template_type_var_converted_" + id).text()) ? toNumber($("#template_type_var_converted_" + id).text()) : templateVarElements[i].value;
        if (!value) {
            resetGeophiresButton(true);
        }
        templateVars[name] = value;
    }

    $("#loadingGeophires").show();
    $('#geophiresError').attr("hidden", true);
    $.ajax({
        url: '/' + LANGUAGE_CODE + '/geophires/',
        type: 'POST',
        data: {
            'csrfmiddlewaretoken': getCookie('csrftoken'),
            'form_data': JSON.stringify(templateVars)
        },
        dataType: 'json',
        success: function (data) {
            var response = data;
            if (response.status == "SUCCESS" || response.status == "FAILURE") {
                renderGeophiresResponse(response.id, response.outputs);
            } else {
                checkGeophiresRunStatus(response.id);
            }
        },
        error: function (data) {
            resetGeophiresButton(true);
        }
    });
}

function renderGeophiresResponse(id, outputs) {
    var templateType = $('#templateType').val();
    var template_type_vars = template_data.template_type_variables.filter(obj => {
        return obj.template_type == parseInt(templateType) && obj.category == geoOutputs;
    });
    for (var i in template_type_vars) {
        if (outputs && outputs.output_params && outputs.output_params[template_type_vars[i].name]) {
            $("#template_type_var_" + template_type_vars[i].id).val(outputs.output_params[template_type_vars[i].name]);
        } else {
            console.log("Output variable not found: " + template_type_vars[i].name);
        }
    }
    resetGeophiresButton(false, id);
}

function checkGeophiresRunStatus(job_meta_id) {
    console.log("Getting geophires status");
    $.ajax({
        url: '/' + LANGUAGE_CODE + '/geophires/status/',
        type: 'POST',
        data: {
            'csrfmiddlewaretoken': getCookie('csrftoken'),
            'job_meta_id': job_meta_id
        },
        dataType: 'json',
        success: function (data) {
            if (data.status == 'SUCCESS' || data.status == 'FAILURE') {
                renderGeophiresResponse(job_meta_id, data.outputs);
                $("#runGeophires").prop("disabled",false);
            } else {
                setTimeout(function() {
                    checkGeophiresRunStatus(job_meta_id);
                }, 20000);
            }
        },
        error: function (data) {
            resetGeophiresButton(true);
        }
    });
}

function validateGeophiresParameters() {
    var templateVarElements = $("#" + geoInputs.replace(/\s/g, '') + "-row :input:not(:button)");
    for (var i = 0; i < templateVarElements.length; i++) {
        if (!templateVarElements[i].value) {
            return false;
        }
    }
    return true;
}

function validateTemplateParameters() {
    if (!$('#templateName').val() || $('#templateName').val().length == 0 ||
     !$('#templateType').val() || $('#templateType').val().length == 0 ||
      !$('#primaryLocation').val() || $('#primaryLocation').val().length == 0) {
        return false;
    }
    var templateVarElements = $("#templateVars :input:not(:button)");
    for (var i = 0; i < templateVarElements.length; i++) {
        if (!templateVarElements[i].value) {
            return false;
        }
    }
    return true;
}

function saveTemplate(buttonId) {
    if ($(buttonId).is(':disabled')) {
        return;
    }
    $("#editTemplate, #createTemplate").prop("disabled",true);
    var templateVars = [];
    if (!$('#templateName').val() || !$('#templateType').val() || !$('#primaryLocation').val()) {
        return ;
    }
    var templateVarElements = $("#templateVars :input:not(:button)");
    for (var i = 0; i < templateVarElements.length; i++) {
        if (!templateVarElements[i].value) {
            return;
        }
        var id = templateVarElements[i].id.replace("template_type_var_", "");

        let value = $("#template_type_var_converted_" + id).text() && toNumber($("#template_type_var_converted_" + id).text()) ? toNumber($("#template_type_var_converted_" + id).text()) : templateVarElements[i].value;
        templateVars.push({"id": id, "value": value, "raw_value": templateVarElements[i].value, "units": templateVarElements[i].units});
    }

    var data = {
        'model_uuid': $('#header').data('model_uuid'),
        'name': $('#templateName').val(),
        'template_type': $('#templateType').val(),
        'location': $('#primaryLocation').val(),
        'csrfmiddlewaretoken': getCookie('csrftoken'),
        'form_data': JSON.stringify({"templateVars": templateVars}),
    };

    if (template_edit) {
        data.template_id = template_edit.id;
    }

    $.ajax({
        url: '/' + LANGUAGE_CODE + '/model/templates/create/',
        type: 'POST',
        data: data,
        dataType: 'json',
        success: function (data) {
            closeTemplateModal(true);
            var response = data;
            $("#editTemplate, #createTemplate").prop("disabled",false);
        },
        error: function (data) {
            $("#editTemplate, #createTemplate").prop("disabled",false);
        }
    });
}

function deleteTemplate() {
    if ($('#confirmDeleteTemplate').is(':disabled')) {
        return;
    }
    //#modelDeleteBack

    var data = {
        'template_id': template_edit.id,
        'csrfmiddlewaretoken': getCookie('csrftoken'),
    };

    $.ajax({
        url: '/' + LANGUAGE_CODE + '/model/templates/delete/',
        type: 'POST',
        data: data,
        dataType: 'json',
        success: function (data) {
            closeTemplateModal(true);
            var response = data;
            //hide dialog
        },
        error: function (data) {
            //display error
        }
    });
}

function appendTemplateCategories() {
    $('#templateVars').empty();
    var templateType = $('#templateType').val();
    if (!templateType && templateType.length === 0) {
        return;
    }
    var template_type = template_data.template_types.find(o => o.id == parseInt(templateType))
    $('#templateVars').append( "<h4 style='padding-left:16px'>Node Group Parameters for " + template_type.pretty_name + "<h6>" );
    $('#templateVars').append( "<p style='padding-left:16px'>" + template_type.description + "<p>" );
    var template_type_vars = template_data.template_type_variables.filter(obj => {
        return obj.template_type == parseInt(templateType);
    });
    var uniqueCategories = [...new Set(template_type_vars.map(obj => obj.category))];
    if (uniqueCategories.includes(geoInputs)) {
        uniqueCategories = uniqueCategories.filter(item => item !== geoInputs);
        uniqueCategories.unshift(geoInputs);
    }
    if (uniqueCategories.includes(null)) {
        uniqueCategories = uniqueCategories.filter(item => item !== null);
        uniqueCategories.unshift(null);
    }
    for (var i = 0; i < uniqueCategories.length; i++) {
        var catCarrot = uniqueCategories[i] ? "<div style='float: right;'><i class='fas fa-caret-down'></i><i class='fas fa-caret-up hide'></i></div>" : "";
        var catId = uniqueCategories[i] ? uniqueCategories[i].replace(/\s/g, '') : "null-category";
        var catName = uniqueCategories[i] ? uniqueCategories[i] : "";
        var catClasses = uniqueCategories[i] ? "row hide" : "row";
        var catClass = uniqueCategories[i] ? "template-category hiding_rows" : "hiding_rows";
        $('#templateVars').append(
            "<div id='"+ catId + "' class='" + catClass + "'><a><h5>" + catName + catCarrot + "</h5></a></div><div id='" + catId + "-row' class='" + catClasses + "'></div>"
        );

        appendCategoryVariables(template_type_vars, uniqueCategories[i]);
        activateTemplateVariables();
    }

    var showAPIButtons = displayAPIButtons();
    setTemplateVarsClassLogic(showAPIButtons);
}

function activateTemplateVariables() {
    //set float-value class
    $('.tech-param-input.float-value').each(function() {
        autocomplete_units(this);
    });

    // Detection of unsaved changes
    $('.tech-param-input').unbind();
    $('.tech-param-input').on('focusout', function() {
        if ($(this).val() == '') { $(this).val( $(this).data('value') ) };
    });
    $('.tech-param-input').on('change keyup paste', function() {
        var row = $(this).parent('div'),
            value = row.find('.tech-param-input').val(),
            old_value = row.find('.tech-param-input').attr('value');

        // Convert to number if possible
        if (+value) { value = (+value).toFixed(8) };
        if (+old_value) { old_value = (+old_value).toFixed(8) };

        // Reset the formatting of row
        row.removeClass('table-warning');
        $(this).removeClass('invalid-value');

        // Update Row based on Input
        var update_val = (value != '') & (value != old_value);
        if (update_val & ($(this).hasClass('float-value') == true)) {
            var units = row.find('.parameter-units').text(),
                val = convert_units(value, units);
            if (typeof(val) == 'number') {
                $(this).attr('data-target_value', formatNumber(val, false));
                row.find('.tech-param-converted').html(formatNumber(val, true));
            } else {
                $(this).addClass('invalid-value');
                row.find('.tech-param-converted').html(row.find('.tech-param-converted').data('value'));
            }
            row.find('.tech-param-converted').show();
        } else {
            row.find('.tech-param-converted').html(row.find('.tech-param-converted').data('value'));
        }
    });
};

function appendCategoryVariables(template_type_vars, category) {
    var categoryVariables = template_type_vars.filter(obj => obj.category == category);
    categoryVariables.sort((a, b) => (a.pretty_name > b.pretty_name) ? 1 : -1);
    var categoryId = category ? category.replace(/\s/g, '') + "-row" : 'null-category-row';

    for (var i = 0; i < categoryVariables.length; i++) {
        var desc = categoryVariables[i].description;
        if (categoryVariables[i].min && categoryVariables[i].max) {
            desc += " " + categoryVariables[i].pretty_name + " has a minimum value of " + categoryVariables[i].min + " and a maximum value of " + categoryVariables[i].max + ".";  
        } else if (categoryVariables[i].max) { 
            desc += " " + categoryVariables[i].pretty_name + " has a maximum value of " + categoryVariables[i].max + ".";  
        } else if (categoryVariables[i].min) {
            desc += " " + categoryVariables[i].pretty_name + " has a minimum value of " + categoryVariables[i].min + ".";  
        }
        var units = "";
        var techParamsClass = ""; 
        if (categoryVariables[i].units && categoryVariables[i].units != "NA") {
            units = "<span style='width:80px;margin-left:.4em' class='text-sm parameter-units'>" + categoryVariables[i].units + "</span>";
            techParamsClass = "float-value";
        } else {
            units = "<span style='width:80px;margin-left:.4em' class='text-sm parameter-units'></span>";
        }
        let convertedValue = "<span id='template_type_var_converted_" + categoryVariables[i].id + "' class='tech-param-converted' style='display:none;' name='" + categoryVariables[i].pretty_name + "'>" + categoryVariables[i].default_value + "</span>";
        $('#'+ categoryId).append( "<div class='col-6 tech-params' data-toggle='tooltip' data-placement='bottom' title='" + desc +
            "' data-original-title='" + desc + "'><label class='template-label'><b>" + categoryVariables[i].pretty_name + "</b></label></div>"
        + "<div class='col-6 tech-params'><input id='template_type_var_" + categoryVariables[i].id + "' class='form-control tech-param-input " + techParamsClass + "' name='" + categoryVariables[i].pretty_name +"'></input>"
        + convertedValue + units + "</div>");

        if (categoryVariables[i].default_value) {
            $('#template_type_var_' + categoryVariables[i].id).val(categoryVariables[i].default_value);
            $('#template_type_var_' + categoryVariables[i].id).attr("value", categoryVariables[i].default_value);
        } else {
            $('#template_type_var_' + categoryVariables[i].id).val("");
        }

        if (categoryVariables[i].category == geoOutputs) {
            $('#template_type_var_' + categoryVariables[i].id).prop("disabled",true);
        }

        $('#template_type_var_' + categoryVariables[i].id).attr({
            "max" : categoryVariables[i].max,
            "min" : categoryVariables[i].min
        });

    }
}

function displayAPIButtons() {
    var showAPIButtons = document.getElementById(geoInputs.replace(/\s/g, '')) != null;
    if (showAPIButtons) {
        var geoId = "#" + geoInputs.replace(/\s/g, '')+"-row";
        $(geoId).append( "<div id='geophiresActions' class='col-12'></div>");
        $("#geophiresActions").append("<button id='runGeophires' class='btn btn-success' type='button' style='height:38px;'>" + djangoTranslateRun + " GEOPHIRES</button>");
        $(geoId).append( "<div class='col-12'><span style='font-size: .8em;margin-bottom:1em;float: right;'><i>" + djangoTranslateGEOPHIRESInfo + "<div data-toggle='tooltip' data-placement='bottom' title='" + djangoTranslateGEOPHIRESDesc + "' data-original-title='" + djangoTranslateGEOPHIRESDesc + "' style='display: inline-block;'><a target='_blank' href='https://www.osti.gov/biblio/1600135'>GEOPHIRES documentation</a></div>.</i><span>");
        //<button id='runGETEM' disabled class='btn btn-success' type='button'>Run GETEM</button>
        $(geoId).append( "<span id='geophiresError' class='center' hidden='true' style='color:red;margin-bottom:1em'>An error occured running Geophires! Please contact Support.</span>");
        $(geoId).append( "<span id='geophiresInputsError' class='center' hidden='true' style='color:red;margin-bottom:1em'></span>");
        $('#runGeophires').on('click', function() {
            requestGeophires();
        });
        $(geoId).append("<div id='loadingGeophires' class='center'><div class='spinner-border text-secondary' style='margin-left:50%' role='status'><span class='sr-only'>Loading...</span>"
            + "</div><br>" + djangoTranslateGEOPHIRESLoading + "</div>");
        $("#loadingGeophires").hide()
        $(geoId).append("<div id='geophiresGraphs' class='center'><a id='geoGraphButton' target='_blank' class='btn btn-success btn-sm' type='button' style='width:190px;height:38px;margin-bottom:1em;padding-top:6px;'>"
            + "GEOPHIRES Graphs<i class='fa-solid fa-up-right-from-square' style='margin-left: 1em;'></i></a></div>");
        $("#geophiresGraphs").hide()
    }
    $('.form-control').on('input', function() {
        var formFilledOut = validateTemplateParameters();
        if (formFilledOut) {
            $("#editTemplate, #createTemplate").prop("disabled",false);
        } else {
            $("#editTemplate, #createTemplate").prop("disabled",true);
        }
    
        if (showAPIButtons) {
            var geoFormFilledOut = validateGeophiresParameters();
            if (geoFormFilledOut) {
                $("#runGeophires").prop("disabled",false);
            } else {
                $("#runGeophires").prop("disabled",true);
            }
        }
    });
    return showAPIButtons;
}

function setTemplateVarsClassLogic(showAPIButtons) {
    $("[data-toggle='tooltip']").tooltip();
    $('.template-category').unbind();
    $('.template-category').on('click', function(){
        var rows = $(this).nextUntil('.template-category');
        if ($(this).hasClass('hiding_rows')) {
            rows.removeClass('hide');
            $(this).removeClass('hiding_rows');
            $(this).find('.fa-caret-up').removeClass('hide');
            $(this).find('.fa-caret-down').addClass('hide');
        } else {
            rows.addClass('hide');
            $(this).addClass('hiding_rows');
            $(this).find('.fa-caret-up').addClass('hide');
            $(this).find('.fa-caret-down').removeClass('hide');
        }
    });
    
}

function toNumber(string) {
    if (string && !isNaN(string.replace(/\,/g,""))) {
        return string.replace(/\,/g,"");
    } else {
        return false;
    }
}

function checkFormInputs(checkAll) {
    var errorMessageId = checkAll ? "#inputError" : "#geophiresInputsError";
    $("#geophiresGraphs").hide();
    $("#inputError").attr("hidden", true);
    $("#geophiresInputsError").attr("hidden", true);
    $("#templateVars :input:not(:button)").removeClass("input-error");
    var isValid = true;

    var templateVarElements = $("#templateVars :input:not(:button)");
    templateVarElements.map((i, templateVar) => {
        var id = Number(templateVar.id.replace("template_type_var_", ""));

        // Skip if we're only validating Geophires inputs and this one is not relvent 
        var isGeophiresInput = $("#" + geoInputs.replace(/\s/g, '') + "-row").parent($("#" + templateVar.id)).length > 1;
        if ((!checkAll && !isGeophiresInput) || !isValid) {
            return;
        }

        if ($("#" + templateVar.id).not("select")) {
            let value = $("#template_type_var_converted_" + id).text() && toNumber($("#template_type_var_converted_" + id).text()) ? toNumber($("#template_type_var_converted_" + id).text()) : templateVar.value;

            if (isNaN(value)) {
                $("#" + templateVar.id).addClass("input-error"); 
                $(errorMessageId).text(templateVar.name + " is expected to be a number, please update before submitting again.");
                $(errorMessageId).attr("hidden", false);
                isValid = false;
                return;
            } 
            value = parseFloat(value);
            if (templateVar.min && parseFloat(templateVar.min) > value) {
                $("#" + templateVar.id).addClass("input-error"); 
                $(errorMessageId).text(templateVar.name + " is below the accepted value of " + templateVar.min + ", please update before submitting again.");
                $(errorMessageId).attr("hidden", false);
                isValid = false;
                return;
            } else if (templateVar.max && parseFloat(templateVar.max) < value) {
                $("#" + templateVar.id).addClass("input-error"); 
                $(errorMessageId).text(templateVar.name + " is above the accepted value of " + templateVar.max + ", please update before submitting again.");
                $(errorMessageId).attr("hidden", false);
                isValid = false;
                return;
            }
        }
        
    });

    return isValid;
}

function resetGeophiresButton(showError, job_meta_id) {
    $("#runGeophires").prop("disabled",false);
    if (showError) {
        $('#geophiresError').attr("hidden", false);
        $("#geophiresGraphs").hide();
    } else {
        var rows = $("#" + geoOutputs.replace(/\s/g, '')).nextUntil('.template-category');
        if ($("#" + geoOutputs.replace(/\s/g, '')).hasClass('hiding_rows')) {
            rows.removeClass('hide');
            $(this).removeClass('hiding_rows');
            $(this).find('.fa-caret-up').removeClass('hide');
            $(this).find('.fa-caret-down').addClass('hide');
        }
        $("#geophiresGraphs").show();
        $("#geoGraphButton").attr("href", "/en/geophires/plotting/?id=" + job_meta_id);

        var formFilledOut = validateTemplateParameters();
        if (formFilledOut) {
            $("#editTemplate, #createTemplate").prop("disabled",false);
        } else {
            $("#editTemplate, #createTemplate").prop("disabled",true);
        }
    }
    $("#loadingGeophires").hide();  
}
