var map_mode = 'loc_techs';
//import { getTemplateData } from 'templates.js';

$( document ).ready(function() {

	initiate_units();

    //Templates
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
    //End Templates

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

var modelTemplates = ["Platte River Hydropower Plant", "Valley View Hotsprings Geothermal"];
//var edittingTemplate = false;
function getTemplates() {
    $("#modalContent").show();
    $("#modalEdit").hide();
    $('#modalBody').empty();
    for (var i = 0; i <  modelTemplates.length; i++) {
        let id = "edit-" + modelTemplates[i].replace(/\s+/g, '-');
        $('#modalBody').append( "<label><b>" + modelTemplates[i] + "</b></label>");
        $('#modalBody').append( "<button type='button' id='" + id + "' class='btn btn-sm' style='padding-bottom:6px' name='" + modelTemplates[i] + "'><i class='fas fa-edit'></i></button><br>");
        //$('#modalBody').append("<div class='form-group col-md-8'><input id='edit-" + modelTemplates[i] + "' type='submit' class='btn btn-sm btn-success' name='' value='+ Constraint'></div>");
        $('#' + id).on('click', function() {
            console.log("hi");
            editTemplate(this);
        });
    }
}

function editTemplate(el) {
    console.log(el.id);
    let name = el.id.substr(5).replace(/-/g, ' ');
    $("#modalContent").hide();
    $("#modalEdit").show();
    $("#templateName").val(name);
    $("#editModalTitle").html("Edit Tamplate: " + name);
}

function addTemplate() {
    $("#modalContent").hide();
    $("#modalEdit").show();
    $("#templateName").val("");
    $("#editModalTitle").html("Add Tamplate");
}

