var marker_clicked = false,
	set_loc_clicked = 1, // toggle between 1 and 2 -- when loc clicked on map, set this loc dropdown
	map = null,
	active_lt_ids = [],
	loc_techs = [],
	markers = [],
	placeholder_text;

$(function() {
		$(".alert-info,.alert-success").fadeTo(3000, 500).slideUp(500, function() {
			$(this).slideUp(500);
		});
});

function activate_table() {

	$('.parameter-value.float-value').each(function() {
		autocomplete_units(this);
	});

	// Detection of unsaved changes
	$('.parameter-value-new, .parameter-value-existing, .parameter-year-existing').unbind();
	$('.parameter-value-new, .parameter-value-existing, .parameter-year-existing').on('focusout', function() {
		if ($(this).val() == '') { $(this).val( $(this).data('value') ) };
	});
	$('.parameter-value-new, .parameter-value-existing, .parameter-year-existing').on('change keyup paste', function() {
		var row = $(this).parents('tr'),
			year = row.find('.parameter-year').val(),
			old_year = row.find('.parameter-year').data('value'),
			value = row.find('.parameter-value').val(),
			old_value = row.find('.parameter-value').data('value'),
			param_id = $(this).parents('tr').data('param_id'),
			ts_id = row.find('.parameter-value.timeseries').val();
		// Convert to number if possible
		if (+value) { value = +value };
		if (+old_value) { old_value = +old_value };
		// If it is a timeseries: render the charts
		if (ts_id) {
			activate_charts(param_id, ts_id)
		};
		// Reset the formatting of row
		row.find('.parameter-reset').addClass('hide')
		row.find('.parameter-delete, .parameter-value-delete').removeClass('hide')
		row.removeClass('table-warning');
		$(this).removeClass('invalid-value');

		// Update Row based on Input
		var update_val = (value != '') & (value != old_value),
			update_year = (year != '') & (year != old_year);
		if (update_val & ($(this).hasClass('float-value') == true)) {
			var units = row.find('.parameter-units').data('value'),
				val = convert_units(value, units);
			if (typeof(val) == 'number') {
				$(this).attr('data-target_value', formatNumber(val, false));
				row.find('.parameter-target-value').html(formatNumber(val, true));
				row.find('.parameter-reset').removeClass('hide')
				row.find('.parameter-delete, .parameter-value-delete').addClass('hide')
				row.addClass('table-warning');
			} else {
				$(this).addClass('invalid-value');
				row.find('.parameter-target-value').html(row.find('.parameter-target-value').data('value'));
			}
		} else if (update_val || update_year) {
			row.find('.parameter-reset').removeClass('hide')
			row.find('.parameter-delete, .parameter-value-delete').addClass('hide')
			row.addClass('table-warning');
		} else {
			row.find('.parameter-target-value').html(row.find('.parameter-target-value').data('value'));
		}
		check_unsaved();
	});
	// Paste multiple values
	activate_paste('.dynamic_value_input');
	activate_paste('.dynamic_year_input');

	$('#tech_name, #tech_tag, #tech_description, #tech_color, #tech_is_linear, #tech_is_expansion, .tech_carrier, .tech_carrier_ratio').on('change keyup paste', function() {
		$(this).addClass('table-warning');
		$(this).siblings('.sp-replacer').addClass('btn-warning');
		check_unsaved();
	});

	$("#tech_color").spectrum({showInput: true, allowEmpty:true, showInitial:true, preferredFormat: "hex"});

	// Reset parameter to saved value in database
	$('.parameter-reset').unbind();
	$('.parameter-reset').on('click', function() {
		var row = $(this).parents('tr'),
			value_field = row.find('.parameter-value'),
			old_value = value_field.data('value'),
			year_field = row.find('.parameter-year'),
			old_year = year_field.data('value'),
			param_id = $(this).parents('tr').data('param_id'),
			ts = row.find('.parameter-value-existing.timeseries'),
			ts_id = ts.data('ts_id');
		if (ts_id != undefined) {
			// Timeseries Fields
			ts.val(+ts_id);
			activate_charts(param_id, +ts_id)
		} else {
			// Input Fields
			value_field.val(old_value);
			year_field.val(old_year);
		};
		value_field.change();
		check_unsaved();
	});

	// Delete parameter from database
	$('.parameter-delete').unbind();
	$('.parameter-delete').on('click', function() {
		var row = $(this).parents('tr'),
			param_id = row.data('param_id'),
			rows = $('tr[data-param_id='+param_id+']');
		if (row.hasClass('table-danger')) {
			rows.find('.check_delete').prop("checked", false)
			rows.removeClass('table-danger');
			rows.find('.parameter-value, .parameter-year').prop('disabled', false);
			change_timeseries_color(param_id, true);
		} else {
			rows.find('.check_delete').prop("checked", true)
			rows.addClass('table-danger');
			rows.find('.parameter-value, .parameter-year').prop('disabled', true)
			change_timeseries_color(param_id, false);
		}
		check_unsaved();
	});
	$('.parameter-value-delete').unbind();
	$('.parameter-value-delete').on('click', function() {
		var row = $(this).parents('tr');
		if (row.hasClass('table-danger')) {
			row.find('.check_delete').prop("checked", false)
			row.removeClass('table-danger');
			row.find('.parameter-value, .parameter-year').prop('disabled', false);
		} else {
			row.find('.check_delete').prop("checked", true)
			row.addClass('table-danger');
			row.find('.parameter-value, .parameter-year').prop('disabled', true)
		};
		check_unsaved();
	});

	// Timeseries
	$('.convert-to-timeseries').on('click', function() {
		var confirmation = confirm('Converting parameter to timeseries...\nAny unsaved changes will be lost.\nContinue?');
		if (confirmation) {
			var model_uuid = $('#header').data('model_uuid'),
				row = $(this).parents('tr'),
				param_id = row.data('param_id'),
				technology_id = $("#technology option:selected").data('id'),
				loc_tech_id = $('tr.loc_tech_row.table-primary').data('loc_tech_id');
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/convert_to_timeseries/',
				data: {
				  'model_uuid': model_uuid,
				  'param_id': +param_id,
				  'technology_id': +technology_id,
				  'loc_tech_id': +loc_tech_id,
				},
				dataType: 'json',
				success: function (data) {
					window.onbeforeunload = null;
					location.reload();
				}
			});
		}
	});

	// Model favorites
	$('.fa-star').unbind();
	$('.fa-star').on('click', function() {
		if ($(this).is("[disabled]") == false) {
			toggle_favorite($(this), true);
		};
	});

	// Allow 'return' key to tab through input cells
	activate_return('.static_inputs');
	activate_return('.dynamic_year_input');
	activate_return('.dynamic_value_input');
	
	// Show and Hide the parameter rows
	$('.param_row_toggle').unbind();
	$('.param_row_toggle').on('click', function() {
		var param_id = $(this).parents('tr').data('param_id');
		param_row_toggle(param_id, false);
	});
	// Show parameter rows and append another row
	$('.parameter-value-add').unbind();
	$('.parameter-value-add').on('click', function() {
		$(this).parents('tr').find('.parameter-target-value').html('');
		add_row($(this));
	});
	// Drop parameter row
	$('.parameter-value-remove').unbind();
	$('.parameter-value-remove').on('click', function() {
		var row = $(this).parents('tr');
		row.remove();
		check_unsaved();
	});

	// Select all on text input focus
	$("input:text").focus(function() { 
		$(this).select(); 
	});

	$('.tbl-header').unbind();
	$('.tbl-header').on('click', function(){
		var rows = $(this).nextUntil('.tbl-header');
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

	$(function () {
	  $('[data-toggle="tooltip"]').tooltip()
	});

};


function collapse_parameter_library() {
	var rows = ($('.tbl-header').first()).nextAll().not('.tbl-header');
	$('.tbl-header').addClass('hiding_rows')
	rows.addClass('hide')
}


function param_row_toggle(param_id, expand_only) {
	var row = $('tr[data-param_id='+param_id+']');
	if (expand_only || $('.param_row_'+param_id).hasClass('param_row_min')) {
		$('.param_row_'+param_id).removeClass('param_row_min');
		row.find('.view_rows').addClass('hide');
		row.find('.hide_rows').removeClass('hide');
		activate_charts(param_id, row.find('.parameter-value-existing.timeseries').val());
	} else {
		$('.param_row_'+param_id).addClass('param_row_min');
		row.find('.view_rows').removeClass('hide');
		row.find('.hide_rows').addClass('hide');
	};
};


function get_tech_parameters() {
	var model_uuid = $('#header').data('model_uuid'),
		technology_id = $("#technology option:selected").data('id');

	if (technology_id != undefined) {
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/component/all_tech_params/',
			data: {
			  'model_uuid': model_uuid,
			  'technology_id': technology_id,
			},
			dataType: 'json',
			success: function (data) {
				$('#tech_essentials').html(data['html_essentials']);
				$('#tech_parameters').html(data['html_parameters']);
				$('#tech_parameters').data('favorites', data['favorites']);
				$('#tech_essentials').data('technology_id', data['technology_id']);
				activate_tech_delete();
				activate_table();
				activate_favorites();
				collapse_parameter_library();
				check_unsaved();
				activate_essentials();
			}
		});
	} else {
		$('#tech_essentials').html("");
		$('#tech_parameters').html("");
	};
};

function activate_tech_delete() {
	$('#technology-delete').on('click', function() {
		var confirmation = confirm('This will remove all parameter settings for this technology. Are you sure you want to delete?');
		if (confirmation) {
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/delete_technology/',
				type: 'POST',
				data: {
					'model_uuid': $('#header').data('model_uuid'),
					'technology_id': $("#technology option:selected").data('id'),
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
};

function get_loc_techs() {
	var model_uuid = $('#header').data('model_uuid'),
		technology_id = $("#technology option:selected").data('id');

	if (technology_id != undefined) {
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/component/all_loc_techs/',
			data: {
			  'model_uuid': model_uuid,
			  'technology_id': technology_id,
			},
			dataType: 'json',
			success: function (data) {
				if (map) map = null;

				loc_techs = data['loc_techs'];
				
				$('#tech_essentials').html(data['html_essentials']);
				$('#tech_essentials').data('technology_id', data['technology_id']);
				$('.loc_tech_row').on('click', function() {
					$('.loc_tech_row').removeClass('table-primary')
					$(this).addClass('table-primary')
					get_loc_tech_parameters();
				});
				
				$('#loc_tech-add-1, #loc_tech-add-2').on('change', function() {
					var id = $(this).val();
					blink_location(id, 'marker', true);
				});
				
				$('.loc_tech-add').on('click', function() {
					var loc_1_id = $('#loc_tech-add-1').val(),
						loc_2_id = $('#loc_tech-add-2').val();
					if (loc_1_id != loc_2_id) {
						$.ajax({
							url: '/' + LANGUAGE_CODE + '/api/add_loc_tech/',
							type: 'POST',
							data: {
								'model_uuid': $('#header').data('model_uuid'),
								'technology_id': $("#technology option:selected").data('id'),
								'location_1_id': $('#loc_tech-add-1').val(),
								'location_2_id': $('#loc_tech-add-2').val(),
								'csrfmiddlewaretoken': getCookie('csrftoken'),
							},
							dataType: 'json',
							success: function (data) {
								window.onbeforeunload = null;
								location.reload();
							}
						});
					} else {
						alert('Please select the location(s) to add.');
					};
				});
				$('.loc_tech-delete').on('click', function() {
					var model_uuid = $('#header').data('model_uuid'),
						loc_tech_id = $(this).parents('tr.loc_tech_row').data('loc_tech_id');
					var confirmation = confirm('This will remove all parameter settings for this node.\nAre you sure you want to delete?');
					if (confirmation) {
						$.ajax({
							url: '/' + LANGUAGE_CODE + '/api/delete_loc_tech/',
							type: 'POST',
							data: {
								'model_uuid': model_uuid,
								'loc_tech_id': loc_tech_id,
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
				var list_position = $('tr.loc_tech_row.table-primary').position();
				if (list_position) {
					$('.location-list').animate( { scrollTop: list_position.top }, 500 )
				};
				get_loc_tech_parameters();
			}
		});
	} else {
		$('#tech_essentials').html("");
		get_loc_tech_parameters();
	};
};

function get_loc_tech_parameters() {
	var model_uuid = $('#header').data('model_uuid'),
		loc_tech_id = $('tr.loc_tech_row.table-primary').data('loc_tech_id'),
		technology_id = $("#technology option:selected").data('id');

	if (loc_tech_id != undefined) {
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/component/all_loc_tech_params/',
			data: {
			  'model_uuid': model_uuid,
			  'loc_tech_id': loc_tech_id,
			},
			dataType: 'json',
			success: function (data) {
				$('#tech_parameters').html(data['html_parameters']);
				$('#tech_parameters').data('favorites', data['favorites']);
				activate_table();
				activate_favorites();
				collapse_parameter_library();
				check_unsaved();
				retrieve_map(false, undefined, technology_id, loc_tech_id);
			}
		});
	} else {
		var msg = '<div class="col-12 centered"><br><br><h4>Please select or create a node.</h4></div>'
		$('#tech_parameters').html(msg);
		retrieve_map(false, undefined, technology_id);
	};
};


function activate_charts(param_id, ts_id) {

	var model_uuid = $('#header').data('model_uuid'),
		div_id = 'chart-'+param_id;

	if (ts_id > 0) {
		if ($('#'+div_id).length > 0) {
			
			draw_charts(div_id, ['2019-07-24'], [0]);
			
			$('#' + div_id).attr('model_uuid', model_uuid);
			$('#' + div_id).attr('ts_id', ts_id);
			$('#' + div_id).attr('param_id', param_id);
			
			$('#' + div_id + ' .loader-container').show();
			
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/component/timeseries_view/',
				data: {
					'model_uuid': model_uuid,
					'ts_id': ts_id,
				},
				dataType: 'json',
				success: function (data) {
					draw_charts(div_id, data['timestamps'], data['values']);
					$('#timeseries-placeholder').hide();
				}
			});
		};
	};
}

function draw_charts(div_id, x, y) {

	var data = [{
		type: "scatter",
		mode: "lines",
		x: x,
		y: y,
		fill: 'tozeroy',
	}]
	
	var layout = {
		xaxis: {
			autorange: true,
			type: 'date'
		},
		yaxis: {
			autorange: true,
			type: 'linear',
		},
		dragmode: $('#' + div_id).attr('dragmode'),
		height: 280,
		margin: {l:60,r:25,t:10,b:40,pad:10},
		showlegend: false,
	};

	var config = {};

	Plotly.newPlot( div_id, data, layout, config);
	
	
	if ($('#' + div_id).find('.loader').length < 1) {
		$('#' + div_id).append('<div class="loader-container"><div class="loader"></div></div>');
	}
	
	
	$('#' + div_id + ' .loader-container').hide();
	
	var start_date = x[0].substring(0, 10);
	var end_date = x[x.length - 1].substring(0, 10);
	if (end_date < start_date) {
		var tmp_date = start_date;
		start_date = end_date;
		end_date = tmp_date;
	}
	$('#' + div_id).attr('start_date', start_date);
	$('#' + div_id).attr('end_date', end_date);
	
	$('#' + div_id + ' a.modebar-btn[data-attr=zoom][data-val=auto]').on('click', function(data) {
		// var model_uuid = $('#' + div_id).attr('model_uuid');
		var ts_id = $('#' + div_id).attr('ts_id');
		var param_id = $('#' + div_id).attr('param_id');
		activate_charts(param_id, ts_id);
	});
	
	$('#' + div_id).on('plotly_relayout', function(data) {
		
		var range = data.target.layout.xaxis.range;
		var dragmode = data.target.layout.dragmode;
		var start_date = range[0].substring(0, 10);
		var end_date = range[1].substring(0, 10);
		if (end_date < start_date) {
			var tmp_date = start_date;
			start_date = end_date;
			end_date = tmp_date;
		}
		if (start_date != $(this).attr('start_date') || end_date != $(this).attr('end_date')) {
			
			$('#' + div_id + ' .loader-container').show();
			
			$(this).attr('start_date', start_date);
			$(this).attr('end_date', end_date);
			$(this).attr('dragmode', dragmode);
			var model_uuid = $(this).attr('model_uuid');
			var ts_id = $(this).attr('ts_id');
			
			$.ajax({
				url: '/' + LANGUAGE_CODE + '/component/timeseries_view/',
				data: {
					'model_uuid': model_uuid,
					'ts_id': ts_id,
					'start_date': start_date,
					'end_date': end_date,
					// 'start_date': start_date.getFullYear() + '-' + (start_date.getMonth() + 1).toString().padStart(2, '0') + '-' + start_date.getDate(),
					// 'end_date': end_date.getFullYear() + '-' + (end_date.getMonth() + 1).toString().padStart(2, '0') + '-' + end_date.getDate(),
				},
				dataType: 'json',
				success: function (data) {
					draw_charts(div_id, data['timestamps'], data['values'])
				}
			});
		}
	});

}

function change_timeseries_color(param_id, mark_delete) {
	if (mark_delete == true) {
		var update = {
		    'marker.color': ['#1f77b4']
		};
	} else {
		var update = {
		    'marker.color': ['#f5c6cb']
		};
	}
	var div_id = 'chart-'+param_id;
	if ($('#'+div_id).length > 0) {
		if (!$('#'+div_id).is(':empty')) {
			Plotly.restyle(div_id, update, [0])
		};
	};
}

function retrieve_map(draggable, scenario_id, technology_id, loc_tech_id) {
	if ($('#map').length) {
		var model_uuid = $('#header').data('model_uuid');
		
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/component/location_coordinates/',
			data: {
				'model_uuid': model_uuid,
				'scenario_id': scenario_id,
				'technology_id': technology_id,
				'loc_tech_id': loc_tech_id,
			},
			dataType: 'json',
			success: function (data) {
				// assign locations to global variable:
				locations = data['locations'];
				render_map(locations, data['transmissions'], draggable, loc_tech_id);
			}
		});
	};

}

function blink_element(ele, n) {
	if (typeof n !== 'number') n = 2;
	var delay = 70;
	for (var i = 0; i < n; i ++) {
		ele.delay(delay).animate({ opacity: 0 }, 0)
			.delay(delay).animate({ opacity: 1.0 }, 0);
	}
}

function set_location(id) {
	var select = $('#loc_tech-add-' + set_loc_clicked.toString());
	if (select.length == 1) {
		select.val(id);
		blink_element(select);
	}
}

function blink_location(id, what_to_blink, pan_to_marker) {
	setTimeout(function() {
		if (typeof what_to_blink === 'undefined') what_to_blink = 'both';
		if (typeof pan_to_marker === 'undefined') pan_to_marker = false;
		var marker = markers.find(function(m) {
			return m.id == id;
		});
		var ele = marker.getElement();
		
		if (what_to_blink == 'marker' || what_to_blink == 'both') {
			blink_element($(ele));
			if (pan_to_marker) {
				map.once('moveend', function() {
					blink_element($(ele));
				});
				map.flyTo({
					center: marker.getLngLat(),
					zoom: map.getZoom(),
					duration: 750
				});
			}
		}
		
		if (what_to_blink == 'row' || what_to_blink == 'both') {
			var row = $('#location_table tr[data-location_id="' + id + '"]');
			$('#locations_dashboard').animate({
				scrollTop: row.position().top
			}, {
				duration: 500,
				complete: function() {
					blink_element(row);
				}
			});
		}
	}, 10);
}

function add_marker(name, id, type, draggable, coordinates) {
	var description = '<h4>' + name + '</h4>';
	if (typeof loc_techs !== 'undefined') {
		var has_techs = false;
		var has_trans = false;
		var techs_html = '';
		var trans_html = '<hr>';
		for (var i = 0; i < loc_techs.length; i ++) {
			if (!active_lt_ids.includes(loc_techs[i].id)) { continue };
			if (name == loc_techs[i].location_1 || name == loc_techs[i].location_2) {
				if (loc_techs[i].location_2 == null) {
					has_techs = true;
					techs_html += '<br><span style="color: ' + loc_techs[i].color + '; padding-right: 10px;">' + loc_techs[i].icon + '</span>' + loc_techs[i].technology;
				} else {
					has_trans = true;
					if (loc_techs[i].location_2 == name) { var loc = loc_techs[i].location_1 } else { var loc = loc_techs[i].location_2 };
					trans_html += '<span style="color: ' + loc_techs[i].color + '; padding-right: 10px;">' + loc_techs[i].icon + '</span>' + loc_techs[i].technology + '&nbsp;&rarr;&nbsp;' + loc + '<br>';
				}
			}
		}
		if (has_techs || has_trans) {
			description += techs_html;
			if (has_trans) description += trans_html;
		}
	}
	var el = document.createElement('div');
	el.className = 'marker ' + type;
	if (map_style == "mapbox/dark-v10") {
		el.className += ' dark';
	}
	var marker = new mapboxgl.Marker(el)
		.setDraggable(draggable)
		.setLngLat(coordinates)
		.addTo(map);
	marker.id = id;
	marker.el = el;
	marker.lat = coordinates[0];
	marker.lon = coordinates[1];
	marker.description = description;
	marker._element._marker = marker;
	marker._element.addEventListener('mouseenter', function(e) {
		var m = e.target._marker;
		$('#map-legend').html(m.description);
	});
	marker._element.addEventListener('mouseleave', function(e) {
		$('#map-legend').html("");
	});
	marker._element.addEventListener('mouseup', function(e) {
		// if (!draggable) e.stopPropagation();
		var m = e.target._marker;
		setTimeout(function() {
			set_location(m.id);
			blink_location(m.id, 'row');
			if ($('#loc_tech-add-2').length == 1 && set_loc_clicked == 1) {
				set_loc_clicked = 2;
			} else {
				set_loc_clicked = 1;
			}
		}, 20);
	});
	markers.push(marker);
	if (draggable) {
		marker.on('up', false);
		marker.on('dragstart', function(e) {
			this.old_pos = this._pos;
			var lnglat = this.getLngLat();
			this.lat = lnglat.lat;
			this.lon = lnglat.lng;
		});
		marker.on('dragend', function(e) {
			$('#map canvas').css('cursor', '');
			marker_clicked = true;
			
			var that = this;
			var marker = e.target;
			var new_lnglat = marker.getLngLat();
			var new_pos = marker._pos;
			var old_pos = marker.old_pos;
			var dist = Math.sqrt((new_pos.x - old_pos.x)**2 + (new_pos.y - old_pos.y)**2);
			
			if (dist < 4) {
				setTimeout(function() {
					blink_location(marker.id, 'row');
					marker.setLngLat([marker.lon, marker.lat]);
				}, 20);
			} else {
				blink_location(marker.id);
				toggle_location_edit(marker.id, true);
				var row = $("tr[data-location_id='" + marker.id + "']");
				row.find('.location-edit-lat').val(new_lnglat.lat.toFixed(5))
				row.find('.location-edit-long').val(new_lnglat.lng.toFixed(5))
				marker.lat = new_lnglat.lat;
				marker.lon = new_lnglat.lng;
			}
			
			setTimeout(function() {
				// $('#map canvas').css('cursor', 'crosshair');
				marker_clicked = false;
			}, 500);
		});
	};
	return marker;
}

var mapbox_styles = {
	'Dark': 'mapbox/dark-v10',
	'Light': 'mapbox/light-v10',
	'Streets': 'mapbox/streets-v11',
	'Satellite': 'mapbox/satellite-v9',
	'Satellite + Streets': 'mapbox/satellite-streets-v9'
}

var map_style = localStorage.getItem("mapstyle") || Object.values(mapbox_styles)[0];

function changeMapStyle() {
    map_style = $('#map-style').val();
    localStorage.setItem("mapstyle", map_style);
    map.setStyle('mapbox://styles/' + map_style);
	if (map_style == "mapbox/dark-v10") {
		$('.marker').addClass('dark');
	} else {
		$('.marker').removeClass('dark');
	}
}

function MapStyleControl() { }

MapStyleControl.prototype.onAdd = function(map) {
	this._map = map;
	this._container = document.createElement('div');
	this._container.className = 'mapboxgl-ctrl';
	
	var label = document.createElement('label');
	label.setAttribute('for', 'map-style');
	label.textContent = 'Base map style:';
	label.className = 'm-0 font-weight-bold';
	
	var select = document.createElement('select');
	select.style.backgroundColor = '#d9ebff';
	select.id = 'map-style';
	
	var mapbox_style_keys = Object.keys(mapbox_styles),
		mapbox_style_values = Object.values(mapbox_styles);
	for (var i = 0; i < mapbox_style_keys.length; i ++) {
		$(select).append($('<option/>')
			  .val(mapbox_style_values[i])
			  .text(mapbox_style_keys[i]));
	}
	$(select).val(map_style);
	$(select).change(changeMapStyle);
	
	this._container.append(label);
	this._container.append(document.createElement('br'));
	this._container.append(select);
	
	return this._container;
}

MapStyleControl.prototype.onRemove = function() {
	this._container.parentNode.removeChild(this._container);
	this._map = undefined;
}


function load_map(locations, transmissions, draggable, loc_tech_id) {
	// Locations
	if (typeof markers !== 'undefined') {
		markers.forEach(function(m) { m.remove() });
	}
	
	markers = [];
	
	for (var i = 0; i < locations.length; i++) {
		var coordinates = [locations[i]['longitude'], locations[i]['latitude']];
		var type = locations[i]['type'];
		if (typeof map_mode !== 'undefined' && map_mode == 'locations') type = '';
		
		add_marker(locations[i].pretty_name, locations[i]['id'], type, draggable, coordinates);
	};
	
	var active_trans = [], inactive_trans = [];
	if (transmissions.length == 0) {
		loc_techs.filter(function(lt) {
				return lt.location_2_id != null;
			}).map(function(lt) {
				var loc_1 = locations.find(function(l) {
					return l.id == lt.location_1_id;
				});
				var loc_2 = locations.find(function(l) {
					return l.id == lt.location_2_id;
				});
				
				var coords = [
					[loc_1.longitude, loc_1.latitude],
					[loc_2.longitude, loc_2.latitude]
				];
				
				if (lt.id == loc_tech_id) {
					active_trans.push(coords);
				} else {
					inactive_trans.push(coords);
				}
			});
	} else {
		active_trans = transmissions.map(function(t) {
			return [[t.lon1, t.lat1], [t.lon2, t.lat2]];
		});
	}
	
	var trans_data = {
		"type": "FeatureCollection",
		"features": [
			{
				"type": "Feature",
				"properties": {
					"color": "blue",
					"width": 4
				},
				"geometry": {
					"type": "MultiLineString",
					"coordinates": active_trans
				}
			}
		]
	};
	
	if (inactive_trans.length > 0) {
		trans_data["features"].push({
			"type": "Feature",
			"properties": {
				"color": "black",
				"width": 2
			},
			"geometry": {
				"type": "MultiLineString",
				"coordinates": inactive_trans
			}
		});
	}
	
	if (typeof map.getSource('transmission') === 'undefined') {
		map.addLayer({
			id: "transmission",
			source: {
				type: "geojson",
				data: trans_data
			},
			type: "line",
			paint: {
				'line-width': ['get', 'width'],
				'line-color': ['get', 'color']
			}
		});
	} else {
		map.getSource('transmission').setData(trans_data);
	}
	
}


function render_map(locations, transmissions, draggable, loc_tech_id) {

	// Bounds
	var lvar = ('Bounds: ' + document.title).split(' | ')[1],
		bounds = JSON.parse(window.localStorage.getItem(lvar));
	if ((bounds == null) || (lvar == 'Home')) {
		var coords = [];
		if (locations.length == 0) {
			// Center on global extent by default
			coords = [[-180, -90], [180, 90]];
		} else {
			coords = locations.map(function(l) {
				return [l.longitude, l.latitude];
			});
		}
		bounds = coords.reduce(
			function(bounds, coord) {
				return bounds.extend(coord);
			}, new mapboxgl.LngLatBounds(coords[0], coords[0]))
	} else {
		var sw = new mapboxgl.LngLat(bounds['_sw']['lng'], bounds['_sw']['lat']),
			ne = new mapboxgl.LngLat(bounds['_ne']['lng'], bounds['_ne']['lat']);
		bounds = new mapboxgl.LngLatBounds(sw, ne);
	}
	
	// Map
	if (map === null) {
		map = new mapboxgl.Map({
				container: 'map',
				style: 'mapbox://styles/' + map_style,
				attributionControl: false,
				bounds: bounds
			})
			.addControl(new mapboxgl.AttributionControl({
				compact: true
			}))
			.addControl(new MapStyleControl())
			.addControl(new mapboxgl.NavigationControl());
		
		map.on('load', function() {
			load_map(locations, transmissions, draggable, loc_tech_id);
			var camera = map.cameraForBounds(bounds, {
				padding: 50,
				maxZoom: 15
			});
			map.jumpTo(camera);
		});
		map.on('moveend', function() {
			var lvar = ('Bounds: ' + document.title).split(' | ')[1];
			window.localStorage.setItem(lvar, JSON.stringify(map.getBounds()));
		});
	} else {
		load_map(locations, transmissions, draggable, loc_tech_id);
	}

	$('.viz-spinner').hide();
}

function toggle_favorite($this, update_favorite) {
	var model_uuid = $('#header').data('model_uuid'),
		row = $this.parents('tr'),
		param_id = row.data('param_id');
	if ($this.hasClass('favorite')) {
		$this.removeClass('favorite');
		var add_favorite = false;
	} else {
		$this.addClass('favorite');
		var rows = $('tr[data-param_id='+param_id+']'),
			header = row.prevAll('.tbl-header').last();
		rows.insertBefore( header );
		var add_favorite = true;
	};
	if (update_favorite) {
		$.ajax({
			url: '/' + LANGUAGE_CODE + '/api/update_favorite/',
			data: {
				'model_uuid': model_uuid,
				'add_favorite': +add_favorite,
				'param_id': +param_id,
			},
			dataType: 'json'
		});
	};
}

function activate_favorites() {
	$($("tr").get().reverse()).each(function() {
		$this = $(this);
		var param_id = $(this).data('param_id'),
			favorites = $('#tech_parameters').data('favorites');
		if (favorites.includes(param_id)) {
			toggle_favorite($this.find('.fa-star'), false)
		};
	})
}

function activate_essentials() {
	$('.carrier-value-add').on('click', function() {
		var container = $(this).parent().parent().find('.new_carrier_form').last();
		new_container = container.clone().removeClass('hide');
		new_container.find('input').addClass('table-warning');
		new_container.insertBefore(container);
		check_unsaved();
	});
	$('.tech_carrier').on('focus', function() {
		$(this).val('');
		$(this).change();
	});
	$('#tech_description').on('input click', function() {
		this.style.height = this.scrollHeight + 10 + "px";
	});
}

function activate_paste(class_name) {
	$(class_name).bind('paste', null, function(e) {
		var values = e.originalEvent.clipboardData.getData('Text').split(/\s+/),
			$txt = $(this),
			row = $txt.parents('tr'),
			param_id = row.data('param_id'),
			inputs = $('tr[data-param_id='+param_id+'] ' + class_name),
			index = inputs.index($txt);
		setTimeout(function () {
			for (var i = 0; i < values.length; i++) {
				var next = inputs.eq(index + i)
				if (next.length == 0) {
					var new_row = add_row($txt);
					next = new_row.find(class_name);
				} else {
					var next_row = next.parents('tr')
					next_row.addClass('table-warning');
					next_row.find('.parameter-reset').removeClass('hide')
					next_row.find('.parameter-delete, .parameter-value-delete').addClass('hide')
				};
				next.val(values[i]);
				next.trigger('change');
				next.focus();
			};
		}, 0);
	});
}

function activate_return(class_name) {
	$(class_name).keydown(function (e) {
		if ((e.which === 13) && ($('.autocomplete-active').length == 0)) {
			if (e.shiftKey) {
				var shift = -1;
			} else {
				var shift = +1;
			};
			var index = $(class_name).index(this) + shift;
			$(class_name).eq(index).focus();
		}
	});
}

function add_row($this) {
	var row = $this.parents('tr'),
		param_id = row.data('param_id');
	row.addClass('param_header');
	$('.param_row_'+param_id).removeClass('param_row_min');
	head_value_cell = row.find('.head_value');
	head_value_cell.removeClass('head_value').addClass('param_row_toggle');
	head_value_cell.find('.static_inputs').remove();
	row.find('.param_row_toggle').find('.hide_rows').removeClass('hide');
	row.find('.param_row_toggle').find('.view_rows').addClass('hide');
	var add_row = $('.add_param_row_'+param_id).last().clone();
	add_row.find('.parameter-value-new').addClass('dynamic_value_input');
	add_row.find('.parameter-year-new').addClass('dynamic_year_input');
	add_row.removeClass('add_param_row_min').addClass('table-warning');
	add_row.insertBefore($('.add_param_row_'+param_id).last());
	add_row.find('.parameter-target-value').html('');
	add_row.find('.parameter-target-value').attr('data-value', '');
	activate_table();
	check_unsaved();
	return add_row;
}

function check_unsaved() {
	// Set warning on parameter headers if sub rows have modifications
	$('.param_header').removeClass('table-warning')
	$('.tbl-header').removeClass('table-warning')
	$('.table-warning, .table-danger').each(function() {
		var param_id = $(this).data('param_id');
		$('.param_header[data-param_id='+param_id+']').addClass('table-warning');
		$(this).prevAll('.tbl-header').first().addClass('table-warning');
	});
	// If modifications exist, activate the SAVE button
	$('.master-btn').addClass('hide');
	if ($('.table-warning, .table-danger').length == 0) {
		$('#master-new').removeClass('hide');
		window.onbeforeunload = null;
	} else {
		$('#master-save').removeClass('hide');
		$('#master-cancel').removeClass('hide');
		window.onbeforeunload = function() {
			return true;
		};
	};
}

function filter_param_inputs(query) {

	return query.filter(function(index, element) {
		var val = $(element).val(),
			tval = $(element).attr('data-target_value');
		if ((tval != undefined) & (tval != val)) {
			$(element).val(tval + '||' + val);

		};
		var has_value = $(element).val() != '',
			is_modified = $(element).parents('tr').hasClass('table-warning'),
			is_delete = $(element).parents('tr').hasClass('table-danger');
		if (is_modified && has_value) {
			$(element).css('background-color', '#28a745');
		};
		return ((is_modified && has_value) || is_delete);
	})

}

function validate_params() {
	var validated = true;
	$('.param_row').each(function() {
		var year_input = $(this).find('.parameter-year-new.dynamic_year_input'),
			value_input = $(this).find('.parameter-value-new.dynamic_value_input');
		if (year_input.length > 0) {
			if (!year_input.val()) {
				var param_id = $(this).data('param_id');
				param_row_toggle(param_id, true);
				year_input.focus();
				setTimeout(function(){alert('Oops! One or more year fields were left blank')}, 10);
				validated = false;
				return false;
			} else {
				if ((!(year_input.val() <= 9999)) | (!(year_input.val() >= 0))) {
					var param_id = $(this).data('param_id');
					param_row_toggle(param_id, true);
					year_input.focus();
					setTimeout(function(){alert('Oops! One or more year fields are invalid')}, 10);
					validated = false;
					return false;
				}
			};
			if (!value_input.val()) {
				var param_id = $(this).data('param_id');
				param_row_toggle(param_id, true);
				value_input.focus();
				setTimeout(function(){alert('Oops! One or more value fields were left blank')}, 10);
				validated = false;
				return false;
			};
		};
	});
	return validated;
}

function placeholder_blinker() {

	if (placeholder_text == undefined) {
		placeholder_text = $('input.nav-dropdown[type=text]').attr('placeholder')
	}
	if ($('input.nav-dropdown[type=text]').attr('placeholder')) {
		$('input.nav-dropdown[type=text]').attr('placeholder', '');
	} else {
		$('input.nav-dropdown[type=text]').attr('placeholder', placeholder_text);
	}

	setTimeout(placeholder_blinker, 1000);

}

function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function formatNumber(x, commas) {

    var parts = x.toString().split(".");
    if (commas == true) {
    	parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    };
    if (parts.length > 1) {
    	if (parts[1].length > 3) { parts[1] = parts[1].slice(0, 3) };
    };
    return parts.join(".");

}

var maximize_label = 'Open Dashboard&nbsp;&nbsp;<i class="fas fa-chevron-up"></i>',
	minimize_label = 'Minimize Dashboard&nbsp;&nbsp;<i class="fas fa-chevron-down"></i>',
	minimize_threshold = 0.1;

function splitter_resize(upper, lower){
	$('#splitter').unbind('mousedown')
	$('#splitter').on('mousedown', function(e) {
		e.stopPropagation();
		var md = {e, upperHeight: upper.outerHeight(),
			      lowerHeight: lower.outerHeight()};
		$(document).unbind('mousemove');
		$(document).on('mousemove', function (e) {
			var delta = Math.min(Math.max((e.clientY - md.e.clientY), -md.upperHeight), md.lowerHeight),
				totalHeight = md.upperHeight + md.lowerHeight,
				upperHeight = (100 * (md.upperHeight + delta) / totalHeight);
			upper.css('height', (upperHeight) + '%');
			lower.css('height', (100 - upperHeight) + '%');
			if (lower.height() / totalHeight > minimize_threshold){
				$('#splitter_btn').html(minimize_label);
			} else {
				$('#splitter_btn').html(maximize_label);
			}
		});
		$(document).unbind('mouseup')
		$(document).on('mouseup', function () {
			$(this).unbind('mousemove mouseup');
			if (map != undefined) { map.resize() };
		});
	});
	$('#splitter_btn').unbind('mousedown')
	$('#splitter_btn').on('mousedown', function(e) { e.stopPropagation() });
	$('#splitter_btn').unbind('click')
	$('#splitter_btn').on('click', function() {
		splitter_toggle(upper, lower);
	});
}

function splitter_toggle(upper, lower){
	if ((lower.height() / (lower.height() + upper.height())) > minimize_threshold){
		// Minimize Lower Row
		upper.css('height', '99%');
		lower.css('height', '1%');
		$('#splitter_btn').html(maximize_label);
	} else{
		// Expand Lower Row
		upper.css('height', '50%');
		lower.css('height', '50%');
		$('#splitter_btn').html(minimize_label);
	}
	if (map != undefined) { map.resize() };
}
