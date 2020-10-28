
$( document ).ready(function() {

	// When the user clicks anywhere outside of the modal, close it
	window.onclick = function(event) {
	  if (event.target == $("#data-source-modal")[0]) {
	    $("#data-source-modal").css('display', "none");
	  }
	};

	// PVWatts & WTK
	$('tr.location-meta-row').each(function() {
		var location_id = +$(this).attr('data-location_id'),
			meta = get_loc_meta(location_id);
		request_pvwatts(location_id, meta[1], meta[2], 40, 180, update_availability);
		request_wtk(location_id, meta[1], meta[2], update_availability);
	});

	// PVWatts
	$('.pvwatts').on('click', function() {
		$('#pvwatts_form').show();
		$('#wtk_form').hide();
		$("#data-source-modal").css('display', "block");
		var location_id = +$(this).parents('tr').attr('data-location_id'),
			meta = get_loc_meta(location_id);
		pvwatts_form(meta[0], meta[1], meta[2])
	});
	$('#pvwatts_check_availability').on('click', function() {
		request_pvwatts(null,
						$('#pvwatts_lat').val(), $('#pvwatts_lon').val(),
						$('#pvwatts_tilt').val(), $('#pvwatts_azimuth').val(),
						update_availability);
	});
	$('#pvwatts_import_data').on('click', function() {
		request_pvwatts(null,
						$('#pvwatts_lat').val(), $('#pvwatts_lon').val(),
						$('#pvwatts_tilt').val(), $('#pvwatts_azimuth').val(),
						import_pvwatts);
	});
	$('#pvwatts_lat, #pvwatts_lon, #pvwatts_tilt, #pvwatts_azimuth').on('change keyup paste', function() { 
	    $('#pvwatts_import_data').attr('disabled', true);
		$('#pvwatts_available_src_data').hide();
		$('#pvwatts_not_available_src_data').hide();
	});

	// WTK
	$('.wtk').on('click', function() {
		$('#pvwatts_form').hide();
		$('#wtk_form').show();
		$("#data-source-modal").css('display', "block");
		var location_id = +$(this).parents('tr').attr('data-location_id'),
			meta = get_loc_meta(location_id);
		wtk_form(meta[0], meta[1], meta[2])
	});
	$('#wtk_check_availability').on('click', function() {
		request_wtk(null,
					$('#wtk_lat').val(), $('#wtk_lon').val(),
					update_availability);
	});
	$('#wtk_import_data').on('click', function() {
		request_wtk(null,
					$('#wtk_lat').val(), $('#wtk_lon').val(),
					import_wtk);
	});
	$('#wtk_lat, #wtk_lon').on('change keyup paste', function() { 
	    $('#wtk_import_data').attr('disabled', true);
		$('#wtk_available_src_data').hide();
		$('#wtk_not_available_src_data').hide();
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

function wtk_form(name, lat, lon) {
	var default_name = 'Wind Resource: '+name+' ['+lat+','+lon+']'
	$('#wtk_name').val(default_name);
	$('#wtk_lat').val(lat);
	$('#wtk_lon').val(lon);
	request_wtk(null,
				$('#wtk_lat').val(), $('#wtk_lon').val(),
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

	$('#pvwatts_checking_src_data').show();
	$('#pvwatts_available_src_data').hide();
	$('#pvwatts_not_available_src_data').hide();
	$('#pvwatts_import_data').attr('disabled', true);

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
				response(location_id, data, 'pvwatts');
			},
			error: function () {
				response(location_id, undefined, 'pvwatts');
			}
		});
	}
};

function request_wtk(location_id, lat, lon, response) {
	console.log('WTK')

	$('#wtk_checking_src_data').show();
	$('#wtk_available_src_data').hide();
	$('#wtk_not_available_src_data').hide();
	$('#wtk_import_data').attr('disabled', true);

	var data = {};
	data['lat'] = lat;
	data['lon'] = lon;
	data['csrfmiddlewaretoken'] = getCookie('csrftoken');

	$.ajax({
		url: '/' + LANGUAGE_CODE + '/api/wtk_timeseries/',
		type: 'POST',
		data: data,
		dataType: 'json',
		success: function (data) {
			response(location_id, data['cf_profile'], 'wtk');
		},
		error: function () {
			response(location_id, undefined, 'wtk');
		}
	});
};

function update_availability(location_id, data, source) {
	if (data != undefined) {
		var row = $('tr.location-data_sources-row[data-location_id="' + location_id + '"]'),
			pvwatts = row.find('.' + source);
		pvwatts.removeClass('btn-outline-danger').addClass('btn-outline-success');
		pvwatts.css('font-weight', 'bold');
		$('#' + source + '_checking_src_data').hide();
		$('#' + source + '_available_src_data').show();
		$('#' + source + '_not_available_src_data').hide();
		$('#' + source + '_import_data').attr('disabled', false);
	} else {
		$('#' + source + '_checking_src_data').hide();
		$('#' + source + '_available_src_data').hide();
		$('#' + source + '_not_available_src_data').show();
	}
};

function import_pvwatts(location_id, data) {
	var timeseries = data['outputs']['ac'],
		name = $("#pvwatts_name").val().trim();

	if (name == '') {
		alert('Please provide a name for your new timeseries');
		return false;
	}
	$('#pvwatts_import_data').attr('disabled', true);

	for (var i=0; i<timeseries.length; i++) {
		timeseries[i] = timeseries[i] / 1000;
	}

	import_timeseries(name, timeseries);
};

function import_wtk(location_id, data) {
	console.log(data)
	var name = $("#wtk_name").val().trim();

	if (name == '') {
		alert('Please provide a name for your new timeseries');
		return false;
	}
	$('#wtk_import_data').attr('disabled', true);

	import_timeseries(name, data);
};

function import_timeseries(name, timeseries) {
	var model_uuid = $('#header').data('model_uuid');

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