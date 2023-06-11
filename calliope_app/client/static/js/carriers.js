
$( document ).ready(function(){
    $('#master-bulk-down').addClass('hide');
    $('#master-bulk-up').addClass('hide');

    $('.carrier-field, .carrier-new').unbind();
    $('.carrier-field, .carrier-new').on('focusout', function() {
        if ($(this).val() == '') { $(this).val( $(this).data('value') ) };
    });
    $('.carrier-field, .carrier-new').on('change keyup paste', function() {
        var row = $(this).parents('tr'),
        name = row.find('#carrier-name').val(),
        rate = row.find('#carrier-rate').val(),
        quantity = row.find('#carrier-quantity').val(),
        carrier_id = $(this).parents('tr').data('carrier_id');

        console.log(row);
        row.addClass('table-warning');
        $('.master-btn').addClass('hide');
        if ($('.table-warning, .table-danger').length != 0) {
            $('#master-save').removeClass('hide');
            $('#master-cancel').removeClass('hide');
            window.onbeforeunload = function() {
                return true;
            };
        };
    });

    $('#master-save').on('click', function(){
        var form_data = filter_carrier_inputs($("#carrier_form :input")).serializeJSON();
        $.ajax({
            url: '/' + LANGUAGE_CODE + '/api/update_carriers/',
            type: 'POST',
            data: {
                'model_uuid': $('#header').data('model_uuid'),
                'form_data': JSON.stringify(form_data),
                'csrfmiddlewaretoken': getCookie('csrftoken'),
            },
            dataType: 'json',
            success: function (data) {
                console.log(data['message']);
                if (data['message'] != "Success."){
                    alert(data['message']);
                }
                window.onbeforeunload = null;
                location.reload();
            }
        });
    });

    $('#master-cancel').on('click', function() {
		window.onbeforeunload = null;
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/carriers/';
	});

    $('.carrier-delete').unbind();
	$('.carrier-delete').on('click', function() {
		var row = $(this).parents('tr');
		if (row.hasClass('table-danger')) {
			row.find('.check_delete').prop("checked", false)
			row.removeClass('table-danger');
			row.find('.carrier-field, .carrier-new, .carrier-readonly').prop('disabled', false);
		} else {
			row.find('.check_delete').prop("checked", true)
			row.addClass('table-danger');
			row.find('.carrier-field, .carrier-new, .carrier-readonly').prop('disabled', true);
		}
        $('.master-btn').addClass('hide');
        if ($('.table-warning, .table-danger').length != 0) {
            $('#master-save').removeClass('hide');
            $('#master-cancel').removeClass('hide');
            window.onbeforeunload = function() {
                return true;
            };
        };
	});
});

function filter_carrier_inputs(query) {

	return query.filter(function(index, element) {
		var has_value = !['','New Carrier'].includes($(element).val()),
			is_modified = $(element).parents('tr').hasClass('table-warning'),
			is_delete = $(element).parents('tr').hasClass('table-danger');
		if (is_modified && has_value) {
			$(element).css('background-color', '#28a745');
		};
		return ((is_modified) || is_delete);
	});

}
