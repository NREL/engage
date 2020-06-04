
$( document ).ready(function() {

	// When the user clicks anywhere outside of the modal, close it
	window.onclick = function(event) {
	  if (event.target == $("#data-source-modal")[0]) {
	    $("#data-source-modal").css('display', "none");
	  }
	};

	// PVWatts
	$('tr.location-meta-row').each(function() {
		var location_id = +$(this).attr('data-location_id'),
			meta = get_loc_meta(location_id);
		request_pvwatts(location_id, meta[1], meta[2], 40, 180, update_availability);
	});
	$('.pvwatts').on('click', function() {
		$("#data-source-modal").css('display', "block");
		var location_id = +$(this).parents('tr').attr('data-location_id'),
			meta = get_loc_meta(location_id);
		pvwatts_form(meta[0], meta[1], meta[2])
	});
	$('#pvwatts_form #check_availability').on('click', function() {
		request_pvwatts(null,
						$('#pvwatts_lat').val(), $('#pvwatts_lon').val(),
						$('#pvwatts_tilt').val(), $('#pvwatts_azimuth').val(),
						update_availability);
	});
	$('#pvwatts_form #import_data').on('click', function() {
		request_pvwatts(null,
						$('#pvwatts_lat').val(), $('#pvwatts_lon').val(),
						$('#pvwatts_tilt').val(), $('#pvwatts_azimuth').val(),
						import_pvwatts);
	});

	$('#pvwatts_lat, #pvwatts_lon, #pvwatts_tilt, #pvwatts_azimuth').on('change keyup paste', function() { 
	    $('#import_data').attr('disabled', true);
		$('#available_src_data').hide();
		$('#not_available_src_data').hide();
	}); 

});

function pvwatts_form(name, lat, lon) {
	var default_name = 'Solar Resource: '+name+' ['+lat+','+lon+']'
	$('#pvwatts_name').val(default_name);
	$('#pvwatts_lat').val(lat);
	$('#pvwatts_lon').val(lon);
	$('#pvwatts_tilt').val(parseInt(Math.abs(lat)));
	if (lat < 0) {
		$('#pvwatts_azimuth').val(-180);
	} else {
		$('#pvwatts_azimuth').val(180);
	}
	request_pvwatts(null,
					$('#pvwatts_lat').val(), $('#pvwatts_lon').val(),
					$('#pvwatts_tilt').val(), $('#pvwatts_azimuth').val(),
					update_availability);
}

function get_loc_meta(location_id) {
	var row = $('tr.location-meta-row[data-location_id="' + location_id + '"]'),
		name = row.find('.location-name').text(),
		lat = +row.find('.location-lat').text(),
		lon = +row.find('.location-long').text();
	return [name, lat, lon]
}

function request_pvwatts(location_id, lat, lon, tilt, azimuth, response) {
	console.log('PVWatts')

	$('#checking_src_data').show();
	$('#available_src_data').hide();
	$('#not_available_src_data').hide();
	$('#import_data').attr('disabled', true);

	var data = {}
	data['api_key'] = pvwatts_api_key
	data['lat'] = lat
	data['lon'] = lon
	data['tilt'] = tilt
	data['azimuth'] = azimuth
	// data['dataset'] = 'intl'

	if (pvwatts_api_key != undefined) {
		$.ajax({
			url: 'https://developer.nrel.gov/api/pvwatts/v6.json?format=json&array_type=1&module_type=0&losses=10&system_capacity=1&timeframe=hourly',
			type: 'GET',
			data: data,
			dataType: 'json',
			success: function (data) {
				response(location_id, data);
			},
			error: function () {
				response(location_id, undefined);
			}
		});
	}
};

function update_availability(location_id, data) {
	if (data != undefined) {
		var row = $('tr.location-data_sources-row[data-location_id="' + location_id + '"]'),
			pvwatts = row.find('.pvwatts');
		pvwatts.removeClass('btn-outline-danger').addClass('btn-outline-success');
		pvwatts.css('font-weight', 'bold');
		$('#checking_src_data').hide();
		$('#available_src_data').show();
		$('#not_available_src_data').hide();
		$('#import_data').attr('disabled', false);
	} else {
		$('#checking_src_data').hide();
		$('#available_src_data').hide();
		$('#not_available_src_data').show();
	}
};

function import_pvwatts(location_id, data) {
	var timeseries = data['outputs']['ac'],
		model_uuid = $('#header').data('model_uuid'),
		name = $("#pvwatts_name").val().trim();

	if (name == '') {
		alert('Please provide a name for your new timeseries');
		return false;
	}
	$('#import_data').attr('disabled', true);

	for (var i=0; i<timeseries.length; i++) {
		timeseries[i] = timeseries[i] / 1000;
	}

	$.ajax({
		url: '/' + LANGUAGE_CODE + '/api/import_timeseries/',
		type: 'POST',
		data: {
			'model_uuid': model_uuid,
			'name': name,
			'timeseries': timeseries.toString(),
			'csrfmiddlewaretoken': getCookie('csrftoken'),
		},
		dataType: 'json',
		success: function (data) {
			$("#data-source-modal").css('display', "none");
		}
	});
};
