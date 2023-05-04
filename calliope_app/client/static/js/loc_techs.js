var map_mode = 'loc_techs';
let template_data = {};
let template_edit = {};
let geoInputs = "Geophires Inputs";
let geoOutputs = "Geophires Outputs";

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

    $('#createTemplate').on('click', function() {
		saveTemplate();
	});

    $('#modelEditBack').on('click', function() {
		modelEditBack();
	});

    $('#templateType').on('change', function() {
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

            appendCategoryVars(template_type_vars, uniqueCategories[i]);
        }

        var showAPIButtons = displayAPIButtons();
        setTemplateVarsClassLogic(showAPIButtons);

	});

    //On modal close
    $('#templatesModal').on('hidden.bs.modal', function () {
        closeTemplateModal();
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
        $('#modalBody').append( "<h6>Existing Node Groups:</h6>");
        for (var i = 0; i < template_data.templates.length; i++) {
            let id = "edit-" + template_data.templates[i].id;
            $('#modalBody').append( "<label><b>" + template_data.templates[i].name + "</b></label>");
            $('#modalBody').append( "<button type='button' id='" + id + "' class='btn btn-sm' style='padding-bottom:6px' name='" + template_data.templates[i].name + "'><i class='fas fa-edit'></i></button><br>");
            $('#' + id).on('click', function() {
                editTemplateModal(this);
            });
        }
    } else {
        $('#modalBody').append( "<h6>This model doesn't have any existing node groups yet.</h6>");
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

function editTemplateModal(el) {
    let id = parseInt(el.id.substr(5));//.replace(/-/g, ' ');
    template_edit = template_data.templates.find(temp => temp.id === id);
    $('#templateType').val(String(template_edit.template_type)).change();
    $('#templateType').attr("disabled", true);
    $('#primaryLocation').val(String(template_edit.location));
    $('#primaryLocation').attr("disabled", true);
    $("#modalContent").hide();
    $("#modalEdit").show();
    $("#createTemplate").hide();
    $("#editTemplate").show();
    $("#templateName").val(template_edit.name);
    $("#editModalTitle").html("Update Node Group: " + template_edit.name);

    //Set template type variarbles
}

function addTemplateModal() {
    $('#templateType').attr("disabled", false);
    $('#primaryLocation').attr("disabled", false);
    $("#modalContent").hide();
    $("#modalEdit").show();
    $("#createTemplate").show();
    $("#editTemplate").hide();
    $("#templateName").val("");
    $("#editModalTitle").html("Add Node Group to Model");
}

function closeTemplateModal() {
    $("#templateType").val([]);
    $("#primaryLocation").val([]);
    $("#templateName").val('');
    $("#templatesModal").modal('hide');
    $("#templateVars").empty();
    $("#editTemplate, #createTemplate").prop("disabled",true);
}

function modelEditBack() {
    $("#modalContent").show();
    $("#modalEdit").hide();
}

function requestGeophires() {
    $("#geophiresGraphs").hide();
    if ($('#runGeophires').is(':disabled')) {
        return;
    }
    $("#runGeophires").prop("disabled", true);
    var templateVarElements = $("#" + geoInputs.replace(/\s/g, '') + "-row :input:not(:button)");
    var templateVars = {};

    for (var i = 0; i < templateVarElements.length; i++) {
        if (!templateVarElements[i].value) {
            resetGeophiresButton(true);
        }
        var id = Number(templateVarElements[i].id.replace("template_type_var_", ""));
        var name = template_data.template_type_variables.filter(obj => {
            return obj.id === id
          })[0].name;
        var value = templateVarElements[i].value;
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
    resetGeophiresButton(false, id);
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
    //display button to graphs
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
    /*if (!$('#primaryLocation').val()) {
        return false;
    }*/
    var templateVarElements = $("#" + geoInputs.replace(/\s/g, '') + "-row :input:not(:button)");
    for (var i = 0; i < templateVarElements.length; i++) {
        if (!templateVarElements[i].value) {
            return false;
        }
    }
    return true;
}

function validateTemplateParameters() {
    if (!$('#templateName').val() || !$('#templateType').val() || !$('#primaryLocation').val()) {
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

function saveTemplate() {
    if ($('#editTemplate').is(':disabled') || $('#createTemplate').is(':disabled')) {
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
        var value = templateVarElements[i].value;
        templateVars.push({"id": id, "value": value});
    }

    $.ajax({
        url: '/' + LANGUAGE_CODE + '/model/templates/create/',
        type: 'POST',
        data: {
            'model_uuid': $('#header').data('model_uuid'),
            'name': $('#templateName').val(),
            'template_type': $('#templateType').val(),
            'location': $('#primaryLocation').val(),
            'csrfmiddlewaretoken': getCookie('csrftoken'),
            'form_data': JSON.stringify({"templateVars": templateVars})
        },
        dataType: 'json',
        success: function (data) {
            closeTemplateModal();
            var response = data;
            $("#editTemplate, #createTemplate").prop("disabled",false);
        },
        error: function (data) {
            $("#editTemplate, #createTemplate").prop("disabled",false);
        }
    });
}

function appendCategoryVars(template_type_vars, category) {
    var categoryVariables = template_type_vars.filter(obj => obj.category == category);
    categoryVariables.sort((a, b) => (a.pretty_name > b.pretty_name) ? 1 : -1);
    var categoryId = category ? category.replace(/\s/g, '') + "-row" : 'null-category-row';

    for (var i = 0; i < categoryVariables.length; i++) {
        var units = "";
        if (categoryVariables[i].units && categoryVariables[i].units != "NA") {
            units = "<span style='width:80px;margin-left:.4em' class='text-sm parameter-units'>" + categoryVariables[i].units + "</span>"
        } else {
            units = "<span style='width:80px;margin-left:.4em' class='text-sm parameter-units'></span>"
        }

        $('#'+ categoryId).append( "<div class='col-6 tech-params' data-toggle='tooltip' data-placement='bottom' title='" + categoryVariables[i].description +
            "' data-original-title='" + categoryVariables[i].description + "'><label class='template-label'><b>" + categoryVariables[i].pretty_name + "</b></label></div>"
        + "<div class='col-6 tech-params'><input id='template_type_var_" + categoryVariables[i].id + "' style='margin-bottom:1em;float:left;' class='form-control' value=''></input>"
        + units + "</div>");

        if (categoryVariables[i].default_value) {
            $('#template_type_var_' + categoryVariables[i].id).val(categoryVariables[i].default_value);
        }

        $('#template_type_var_' + categoryVariables[i].id).attr({
            "max" : categoryVariables[i].max,
            "min" : categoryVariables[i].min
        });

        $('#template_type_var_' + categoryVariables[i].id).on('input', function() {
            var min = parseInt($(this).attr('min'));
            var max = parseInt($(this).attr('max'));
            if (min || max) {
                var value = parseInt($(this).val());
                if (value < min) {
                    $(this).val(min);
                } else if (value > max) {
                    $(this).val(max);
                }
            }
        });
    }
}

function displayAPIButtons() {
    var showAPIButtons = document.getElementById(geoInputs.replace(/\s/g, '')) != null;
    if (showAPIButtons) {
        var geoId = "#" + geoInputs.replace(/\s/g, '')+"-row";
        $(geoId).append( "<div id='geophiresActions' class='col-12'></div>");
        $("#geophiresActions").append( "<button id='runGeophires' class='btn btn-success btn-sm' type='button' style='width:130px;height:38px;'>Run GEOPHIRES</button>");
        $(geoId).append( "<div class='col-12'><span style='font-size: .8em;margin-bottom:1em;float: right;'>For more information about Geophires please see the <a target='_blank' href='https://www.osti.gov/biblio/1600135'>Geophires abstract</a>.<span>");
        //<button id='runGETEM' disabled class='btn btn-success btn-sm' type='button'>Run GETEM</button>
        $(geoId).append( "<span id='geophiresError' class='center' hidden='true' style='color:red;margin-bottom:1em'>An error occured running Geophires! Please contact Support.</span>");
        $('#runGeophires').on('click', function() {
            requestGeophires();
        });
        $(geoId).append($("#loadingGeophires"));
        $("#loadingGeophires").hide()
        $(geoId).append($("#geophiresGraphs"));
        $("#geophiresGraphs").hide()
    }
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
}

function resetGeophiresButton(showError, job_meta_id) {
    $("#runGeophires").prop("disabled",false);
    if (showError) {
        $('#geophiresError').attr("hidden", false);
        $("#geophiresGraphs").hide();
    } else {
        var rows = $("#GeophiresOutputs").nextUntil('.template-category');
        if ($("#GeophiresOutputs").hasClass('hiding_rows')) {
            rows.removeClass('hide');
            $(this).removeClass('hiding_rows');
            $(this).find('.fa-caret-up').removeClass('hide');
            $(this).find('.fa-caret-down').addClass('hide');
        }
        $("#geophiresGraphs").show();
        $("#geoGraphButton").attr("href", "/en/geophires/plotting/?id=" + job_meta_id);
    }
    $("#loadingGeophires").hide();  
}
