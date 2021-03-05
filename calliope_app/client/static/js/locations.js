var new_id = 0;
var map_mode = 'locations';

$( document ).ready(function() {
	
	$('#master-new').removeClass('hide');

	// https://stackoverflow.com/questions/7317273/warn-user-before-leaving-web-page-with-unsaved-changes
    window.addEventListener("beforeunload", function (e) {
		if ($('tr[data-dirty=true]').length == 0) return(undefined);
        var message = 'WARNING! Some locations are unsaved. If you leave this page, these changes will be lost.';
        (e || window.event).returnValue = message; //Gecko + IE
        return message; //Gecko + Webkit, Safari, Chrome etc.
    });
	
	$('#master-new').unbind();
	$('#master-new').on('click', function(e) {
		$('#master-cancel').removeClass('hide');
		e.stopPropagation();
		$('#create_location_notice').remove();
		add_location();
	});

	$('#master-cancel').on('click', function() {
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/locations/';
	});
	
	activate_location_elements();
	
	retrieve_map(true, undefined, undefined);
	
	if ($('#location_table tr[data-location_id]').length == 0) {
		$('#locations_dashboard').prepend('<div id="create_location_notice" class="col-12 text-center"><br/><br/><h4>Create a location (initially at the center of the map) by clicking the "+ New" button above!</h4></div>');
	}

});

function add_location(lng, lat, blink) {
	var add_row = $('.location-add-row').first().clone(),
		add_row_ds = $('.location-add-data_sources-row').first().clone(),
		rows = $('#location_table').find('tr').not('.tbl-header');
	new_id ++;
	var id = 'new_' + new_id;
	add_row.attr({
		'data-location_id': id,
		'data-new': true,
		'data-dirty': true
	});
	add_row_ds.attr('data-location_id', id);
	var center = map.getCenter();
	if (typeof lng === 'undefined') lng = center.lng;
	if (typeof lat === 'undefined') lat = center.lat;
	var coordinates = [lng, lat];
	var marker = add_marker('New Location', id, 'selected', true, coordinates);
	marker.togglePopup();
	locations.push({
		id: id,
		longitude: lng,
		latitude: lat,
		new: true,
	});
	blink_location(id, blink);
	add_row.find('.location-edit-long').attr('value', coordinates[0].toFixed(3)).trigger('change');
	add_row.find('.location-edit-lat').attr('value', coordinates[1].toFixed(3)).trigger('change');
	add_row.removeClass('location-add-row').addClass('location-meta-row').removeClass('hide');
	add_row_ds.removeClass('location-add-data_sources-row').addClass('location-data_sources-row').removeClass('hide');
	// add_row.find('.parameter-year-new').addClass('dynamic_year_input');
	// add_row.removeClass('add_param_row_min').addClass('table-warning');
	add_row.insertBefore(rows.first())
	add_row_ds.insertAfter(add_row)
	add_row.find('.location-edit-name').focus();
	// location-add-row
	activate_location_elements();
}

function toggle_location_edit(location_id, edit) {
	var rows = $('#location_table tr[data-location_id="' + location_id + '"]'),
		row = $(rows[0])
		toggle = true;
	
	if ((edit==true) & (row.hasClass('table-warning'))) {
		toggle = false;
	} else if ((edit==false) & (!row.hasClass('table-warning'))) {
		toggle = false;
	};
	
	if (toggle == true) {
		if (row.hasClass('table-warning')) {
			var id = row.data('location_id');
			
			if (row.data('new') == true) {
				var l = locations.findIndex(function(l) { return l.id == id } );
				if (l > -1) locations.splice(l, 1);
				var m = markers.findIndex(function(m) { return m.id == id } );
				if (m > -1) {
					markers[m].remove();
					markers.splice(m, 1);
				}
				row.remove();
				return;
			}
			
			row.find('input').each(function() {
				$(this).val($(this).attr('value'));
			});
			row.find('.location-edit').toggleClass('btn-danger bg-danger').html('<i class="fas fa-edit"></i> Edit');
			var marker = markers.find(function(m) { return m.id == id });
			var location = locations.find(function(l) { return l.id == id });
			marker.setLngLat([location.longitude, location.latitude]);
			row.attr('data-dirty', '');
		} else {
			row.attr('data-dirty', true);
			row.find('.location-edit').toggleClass('btn-danger bg-danger').html('<i class="fas fa-times"></i> Cancel');
		}
		row.toggleClass('table-warning');
		row.find('.location-save, .location-delete, .location-name, .location-lat, .location-long, .location-area, .location-description, .location-edit-name, .location-edit-lat, .location-edit-long, .location-edit-area, .location-edit-description').toggleClass('hide');
	}
};


function reset_location_values() {
	$('#location_table tr input').each(function() {
		$(this).val(this.defaultValue);
	});
}

function update_marker_from_row(tr) {
	var id = tr.data('location_id'),
		lat = tr.find('.location-edit-lat').val(),
		lng = tr.find('.location-edit-long').val(),
		name = tr.find('.location-edit-name').val(),
		description = '<h4>' + name + '</h4>',
		marker = markers.find(function(m) { return m.id == id });
	marker.description = description;
	marker.setLngLat([lng, lat]);
}

function activate_location_elements() {
	$('#location_table tr').unbind();
	$('#location_table tr').on('click', function() {
		var id = $(this).data('location_id');
		blink_location(id, 'marker', true);
	});
	
	reset_location_values();
	
	$('.location-edit-name, .location-edit-lat, .location-edit-long, .location-edit-area').unbind();
	$('.location-edit-name, .location-edit-lat, .location-edit-long, .location-edit-area').on('keyup change', function(e) {
		var tr = $(this).closest('tr');
		update_marker_from_row(tr);
		if (e.keyCode == 13) {
			$(this).trigger('change');
			tr.find('.location-save').click();
		} else if (e.keyCode == 27) {
			tr.find('.location-edit').click();
		}
	});
	
	$('.location-edit').unbind();
	$('.location-edit').on('click', function(e) {
		e.stopPropagation();
		var row = $(this).parents('tr'),
			location_id = row.attr('data-location_id');
		toggle_location_edit(location_id, null);
		if ($('.table-warning').length < 2) {
			$('#master-cancel').addClass('hide');
		} else {
			$('#master-cancel').removeClass('hide');
		}
		
		if ($('#location_table tr[data-location_id]').length == 0) {
			$('#locations_dashboard').prepend('<div id="create_location_notice" class="col-12 text-center"><br/><br/><h4>Create a location (initially at the center of the map) by clicking the "+ New" button above!</h4></div>');
		}
	});
	
	$('.location-save').unbind();
	$('.location-save').on('click', function(e) {
		if (typeof e !== 'undefined') e.stopPropagation();
		var row = $(this).parents('tr'),
			location_id = row.data('location_id'),
			rows = $('#location_table tr[data-location_id="' + location_id + '"]'),
			location_name = row.find('.location-edit-name').val(),
			location_lat = row.find('.location-edit-lat').val(),
			location_long = row.find('.location-edit-long').val(),
			location_area = row.find('.location-edit-area').val(),
			location_description = row.find('.location-edit-description').val();
		
		var marker = markers.find(function(m) {
			return m.id == location_id;
		});
		
		if (location_name) {
			if (row.data('new') == true) location_id = 0;
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/update_location/',
				type: 'POST',
				data: {
					'model_uuid': $('#header').data('model_uuid'),
					'location_id': location_id,
					'location_name': location_name,
					'location_lat': location_lat,
					'location_long': location_long,
					'location_area': location_area,
					'location_description': location_description,
					'csrfmiddlewaretoken': getCookie('csrftoken'),
				},
				dataType: 'json',
				success: function (data) {
					var id = data['location_id'];
					var i = locations.findIndex(function(l) { return l.id == id });
					var location = {
						'id': id,
						'latitude': data['location_lat'],
						'longitude': data['location_long'],
						'area': data['location_area'],
						'description': data['location_description'],
						'name': data['location_name'],
						'pretty_name': data['location_name'],
					};
					if (i == -1) {
						locations.push(location);
					} else {
						locations[i] = location;
					}
					row.attr('data-dirty', false);

					row.find('.location-name').text(data['location_name'])
					row.find('.location-edit-name')[0].defaultValue = data['location_name']
					row.find('.location-edit-name').val(data['location_name'])

					row.find('.location-lat').text(data['location_lat'])
					row.find('.location-edit-lat').val(data['location_lat'])
					row.find('.location-edit-lat')[0].defaultValue = data['location_lat']

					row.find('.location-long').text(data['location_long'])
					row.find('.location-edit-long').val(data['location_long'])
					row.find('.location-edit-long')[0].defaultValue = data['location_long']

					row.find('.location-area').text(data['location_area'])
					row.find('.location-edit-area').val(data['location_area'])
					row.find('.location-edit-area')[0].defaultValue = data['location_area']

					row.find('.location-description').text(data['location_description'])
					row.find('.location-edit-description').val(data['location_description'])
					row.find('.location-edit-description')[0].defaultValue = data['location_description']

					row.data('new', false);
					rows.each(function() {
						$(this).attr('data-location_id', id);
						$(this).data('location_id', id);
					})
					marker.id = id;
					toggle_location_edit(id, false);
					blink_location(id, 'marker');
					if ($('.table-warning').length < 2) {
						$('#master-cancel').addClass('hide');
					};
					// PVWatts & WTK
					var meta = get_loc_meta(id);
					request_pvwatts(id, meta[1], meta[2], 40, 180, update_availability);
					request_wtk(id, meta[1], meta[2], update_availability);
				}
			});
		} else {
			alert('Location name must not be blank')
		};
	});
	
	$('.location-delete').unbind();
	$('.location-delete').on('click', function(e) {
		e.stopPropagation();
		
		var row = $(this).parents('tr'),
			location_id = row.data('location_id');

		var confirmation = confirm('This will remove all parameter settings at this location. Are you sure you want to delete?');

		if (confirmation) {
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/delete_location/',
				type: 'POST',
				data: {
					'model_uuid': $('#header').data('model_uuid'),
					'location_id': location_id,
					'csrfmiddlewaretoken': getCookie('csrftoken'),
				},
				dataType: 'json',
				success: function (data) {
					$('#location_table tr[data-location_id='+location_id+']').remove();
					retrieve_map(true, undefined, undefined);
				}
			});
		};

	});

};