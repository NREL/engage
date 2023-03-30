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
        $('#templateVars').append( "<hr><h6>Template Type Variables for " + template_type.pretty_name + "<h6>" );
        $('#templateVars').append( "<p>" + template_type.description + "<p>" );
        var template_type_vars = template_data.template_type_variables.filter(obj => {
            return obj.template_type == parseInt(templateType);
        });
        for (var i = 0; i < template_type_vars.length; i++) {
            $('#templateVars').append( "<label><b>" + template_type_vars[i].name + "</b></label>");
            $('#templateVars').append( "<p class='help-text'>" + template_type_vars[i].description + ".</p>");
            $('#templateVars').append( "<div><input id='template_type_var_" + template_type_vars[i].id + "' style='margin-bottom:1em;float:left;' class='form-control' value=''></input><span style='width:80px;margin-left:.4em' class='text-sm parameter-units'>" + template_type_vars[i].units + "</span></div><br>");
            if (template_type_vars[i].default_value) {
                $('#template_type_var_' + template_type_vars[i].id).val(template_type_vars[i].default_value);
            }
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

//var edittingTemplate = false;
function getTemplates() {
    getTemplatesAdmin();
    $("#modalContent").show();
    $("#modalEdit").hide();
    $('#modalBody').empty();
    for (var i = 0; i < template_data.templates.length; i++) {
        let id = "edit-" + template_data.templates[i].id;
        $('#modalBody').append( "<label><b>" + template_data.templates[i].name + "</b></label>");
        $('#modalBody').append( "<button type='button' id='" + id + "' class='btn btn-sm' style='padding-bottom:6px' name='" + template_data.templates[i].name + "'><i class='fas fa-edit'></i></button><br>");
        $('#' + id).on('click', function() {
            editTemplate(this);
        });
    }

    if ($("#primaryLocation").children('option').length === 0) {
        $("#primaryLocation").prepend( "<option selected value=''></option>");
        for (let i = 0; i < locations.length; i++) {
            if (template_edit.id == locations[i].id) {
                $("#primaryLocation").append( "<option selected value=" + locations[i].id + ">" + locations[i].pretty_name + "</option>");
            } else {
                $("#primaryLocation").append( "<option value=" + locations[i].id + ">" +locations[i].pretty_name + "</option>" );
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

function getTemplatesAdmin() {
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

function saveTemplate() {
    var templateVarElements = $("#templateVars :input");
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
