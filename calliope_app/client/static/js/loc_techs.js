var map_mode = 'loc_techs';
let template_data = {};
let template_edit = {};
//import { getTemplateData } from 'templates.js';

$( document ).ready(function() {

	initiate_units();

    //------------Start Templates------------//
    $("#master-new").show();
    $("#master-new").html("Templates");
    $('#master-new').attr('data-target','#templatesModal');
    $('#master-new').attr('data-toggle','modal');
    $('#master-new').on('click', function() {
		getTemplates();
	});

    $('#addTemplate').on('click', function() {
		addTemplate();
	});

    $('#saveTemplate').on('click', function() {
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
        $('#templateVars').append( "<hr><h4>Template Type Parameters for " + template_type.pretty_name + "<h6>" );
        $('#templateVars').append( "<p>" + template_type.description + "<p>" );
        var template_type_vars = template_data.template_type_variables.filter(obj => {
            return obj.template_type == parseInt(templateType);
        });
        var uniqueCategories = [...new Set(template_type_vars.map(obj => obj.category))];
        if (uniqueCategories.includes("Geotechnical tool input parameters")) {
            uniqueCategories = uniqueCategories.filter(item => item !== "Geotechnical tool input parameters");
            uniqueCategories.unshift("Geotechnical tool input parameters");
        }
        for (var i = 0; i < uniqueCategories.length; i++) {
            if (uniqueCategories[i]) {
                $('#templateVars').append(
                    "<div id='"+ uniqueCategories[i].replace(/\s/g, '') + "'><h5>" + uniqueCategories[i] + "</h5></div>"
                );
            }
        }
        for (var i = 0; i < template_type_vars.length; i++) {
            var categoryId = template_type_vars[i].category ? template_type_vars[i].category.replace(/\s/g, '') : 'templateVars';
            $('#'+ categoryId).append( "<p class='help-text'>" + template_type_vars[i].description + "</p>");
            if (template_type_vars[i].units && template_type_vars[i].units != "NA") {
                $('#'+ categoryId).append( "<div><label><b>" + template_type_vars[i].pretty_name + "</b></label><input id='template_type_var_" + template_type_vars[i].id + "' style='margin-bottom:1em;float:left;' class='form-control' value=''></input><span style='width:80px;margin-left:.4em' class='text-sm parameter-units'>" + template_type_vars[i].units + "</span></div><br>");
            } else {
                $('#'+ categoryId).append( "<div><label><b>" + template_type_vars[i].pretty_name + "</b></label><input id='template_type_var_" + template_type_vars[i].id + "' style='margin-bottom:1em;float:left;' class='form-control' value=''></input><span style='width:80px;margin-left:.4em' class='text-sm parameter-units'></span></div><br>");
            }
            if (template_type_vars[i].default_value) {
                $('#template_type_var_' + template_type_vars[i].id).val(template_type_vars[i].default_value);
            }
        }

        var showAPIButtons = document.getElementById("Geotechnical tool input parameters".replace(/\s/g, '')) != null;
        if (showAPIButtons) {
            $("#Geotechnical tool input parameters".replace(/\s/g, '')).append( "<div style='padding: 1rem;border-top: 1px solid white;'><button id='runGeophires' class='btn btn-success btn-sm' type='button' style='width:130px;height:38px;'>Run GEOPHIRES</button><button id='runGETEM' disabled class='btn btn-success btn-sm' type='button' style='width:100px;height:38px;margin-left:1em'>Run GETEM</button></div>");
            $("#Geotechnical tool input parameters".replace(/\s/g, '')).append( "<span id='geophiresError' hidden='true' style='color:red;margin-bottom:1em'>Please fill out all Geotechincal input parameters and a primary location.</span>");
            $('#runGeophires').on('click', function() {
                requestGeophires();
            });
        }
	});

    //On modal close
    $('#templatesModal').on('hidden.bs.modal', function () {
        $('#templateError').hide();
        $("#templateType").val([]);
        $("#primaryLocation").val([]);
        $("#templateName").val('');
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
        $('#modalBody').append( "<h6>Existing Templates:</h6>");
        for (var i = 0; i < template_data.templates.length; i++) {
            let id = "edit-" + template_data.templates[i].id;
            $('#modalBody').append( "<label><b>" + template_data.templates[i].name + "</b></label>");
            $('#modalBody').append( "<button type='button' id='" + id + "' class='btn btn-sm' style='padding-bottom:6px' name='" + template_data.templates[i].name + "'><i class='fas fa-edit'></i></button><br>");
            $('#' + id).on('click', function() {
                editTemplate(this);
            });
        }
    } else {
        $('#modalBody').append( "<h6>This model doesn't have an existing templates yet.</h6>");
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

function editTemplate(el) {
    let id = parseInt(el.id.substr(5));//.replace(/-/g, ' ');
    template_edit = template_data.templates.find(temp => temp.id === id);
    $('#templateType').val(String(template_edit.template_type)).change();
    $('#templateType').attr("disabled", true);
    $('#primaryLocation').val(String(template_edit.location));
    $('#primaryLocation').attr("disabled", true);
    $("#modalContent").hide();
    $("#modalEdit").show();
    $("#templateName").val(template_edit.name);
    $("#editModalTitle").html("Edit Template: " + template_edit.name);

    //Set template type variarbles
}

function addTemplate() {
    $('#templateType').attr("disabled", false);
    $('#primaryLocation').attr("disabled", false);
    $("#modalContent").hide();
    $("#modalEdit").show();
    $("#templateName").val("");
    $("#editModalTitle").html("Add Template");
}

function closeTemplateModal() {
    $('#templateError').hide();
    $("#templateType").val([]);
    $("#primaryLocation").val([]);
    $("#templateName").val('');
    $("#templatesModal").modal('hide');
}

function modelEditBack() {
    $("#modalContent").show();
    $("#modalEdit").hide();
}

function requestGeophires() {
    var templateVarElements = $("#Geotechnicaltoolinputparameters :input:not(:button)");
    var templateVars = {};
    if (!$('#primaryLocation').val()) {
        $('#geophiresError').attr("hidden", false);
        return;
    }

    for (var i = 0; i < templateVarElements.length; i++) {
        if (!templateVarElements[i].value) {
            $('#geophiresError').attr("hidden", false);
            return;
        }
        var id = Number(templateVarElements[i].id.replace("template_type_var_", ""));
        var name = template_data.template_type_variables.filter(obj => {
            return obj.id === id
          })[0].name;
        var value = templateVarElements[i].value;
        templateVars[name] = value;
    }

    $('#geophiresError').attr("hidden", true);
    $.ajax({
        url: '/' + LANGUAGE_CODE + '/geophires/',
        type: 'POST',
        data: {
            'csrfmiddlewaretoken': getCookie('csrftoken'),
            'location': $('#primaryLocation').val(),
            'form_data': JSON.stringify(templateVars)
        },
        dataType: 'json',
        success: function (data) {
            //fill in output parameters
            var response = data;
        }
    });
}

function saveTemplate() {
    var templateVarElements = $("#templateVars :input:not(:button)");
    var templateVars = [];
    if (!$('#templateName').val() || !$('#templateType').val() || !$('#primaryLocation').val()) {
        $('#templateError').attr("hidden", false);
        return;
    }
    for (var i = 0; i < templateVarElements.length; i++) {
        if (!templateVarElements[i].value) {
            $('#templateError').attr("hidden", false);
            return;
        }
        var id = templateVarElements[i].id.replace("template_type_var_", "");
        var value = templateVarElements[i].value;
        templateVars.push({"id": id, "value": value});
    }

    $('#templateError').attr("hidden", true);
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
        }
    });
}
