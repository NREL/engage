$(document).ready(function () {

	add_run_precheck();

	$('#master-cancel').removeClass('hide');
	$('#master-save').removeClass('hide');

	$('#master-cancel').on('click', function () {
		var model_uuid = $('#header').data('model_uuid');
		window.location = '/' + model_uuid + '/runs/';
	});

	$('#master-save').on('click', function () {
		var model_uuid = $('#header').data('model_uuid'),
			scenario_id = $("#scenario").data('scenario_id'),
			start_date = $('#start_date').val(),
			end_date = $('#end_date').val(),
			cluster = $('#cluster').is(":checked"),
			manual = $('#manual').is(":checked"),
			sd = new Date(start_date),
			ed = new Date(end_date),
			run_env = $('#run-environment option:selected').text();

		// fix timezone issues
		sd = new Date(sd.getTime() + sd.getTimezoneOffset() * 60000);
		ed = new Date(ed.getTime() + ed.getTimezoneOffset() * 60000);

		var validated = true;
		if (scenario_id == undefined) {
			alert('Must choose a Scenario')
			validated = false;
		} else if (!(sd & ed)) {
			alert('Must select a date range below.');
			validated = false;
		} else if (sd > ed) {
			alert('Start date can not be later then the end date.');
			validated = false;
		} else if (sd.getFullYear() != ed.getFullYear()) {
			alert('Start date and end date must occur within the same year')
			validated = false;
		};

		if (validated) {
			$('#master-save').prop('disabled', true);

			$.ajax({
				url: '/' + LANGUAGE_CODE + '/api/build/',
				data: {
					'model_uuid': model_uuid,
					'scenario_id': scenario_id,
					'start_date': start_date,
					'end_date': end_date,
					'cluster': cluster,
					'manual': manual,
					'run_env': run_env
				},
				dataType: 'json',
				success: function (data) {
					if (data['status'] == 'Success') {
						window.location = '/' + model_uuid + '/runs/';
					} else {
						$('#build-error').html(data['message']);
						$('#master-save').prop('disabled', false);
					};
				}
			});
		};
	});

	// Automatically deactivate clustering if manual is enabled.
	$('#manual').on('click', function () {
		if ($('#manual').is(":checked")) {
			$('#cluster').prop('checked', false);
		}
	});

});


function add_run_precheck() {
	var model_uuid = $('#header').data('model_uuid'),
		scenario_id = $("#scenario").data('scenario_id');
	$.ajax({
		url: '/' + LANGUAGE_CODE + '/component/add_run_precheck/',
		data: {
			'model_uuid': model_uuid,
			'scenario_id': scenario_id,
		},
		dataType: 'json',
		success: function (data) {
			$('#add_run_precheck').html(data['html']);
			render_gantt();
			activate_tiles();
		}
	});
};

function activate_tiles() {
	$('.selection_tile').on('click', function () {
		var start_date = $(this).data('start_date'),
			end_date = $(this).data('end_date');
		$('.selection_tile').removeClass('btn-outline-primary')
		$(this).addClass('btn-outline-primary')
		$('#start_date').val(start_date);
		$('#end_date').val(end_date);
	})
}

function render_gantt() {

	var data = $('#timeseries_gantt').data('timeseries');

	var margin = { top: 40, right: 40, bottom: 20, left: 40 },
		width = $('#timeseries_gantt').width() - margin.left - margin.right,
		bar_height = 16
	height = (bar_height + 4) * data.length;

	// Prep data
	var parseDate = d3.timeParse("%m/%d/%Y, %H:%M:%S");
	data.forEach(function (d) {
		d.node = d[0]
		d.parameter = d[1]
		d.start_date = parseDate(d[2]);
		d.end_date = parseDate(d[3]);
	});

	// X Axis
	var start_date = d3.min(data, function (d) { return d.start_date }),
		end_date = d3.max(data, function (d) { return d.end_date });
	var x = d3.scaleTime()
		.domain([start_date, end_date])
		.range([0, width]);
	var xAxis = d3.axisTop()
		.scale(x);

	// Y Axis
	var y = d3.scaleLinear()
		.domain([data.length, 0])
		.range([height, 0]);


	// Draw
	var svg = d3.select("#timeseries_gantt").append("svg")
		.attr("width", width + margin.left + margin.right)
		.attr("height", height + margin.top + margin.bottom)
		.append("g")
		.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	// Define the div for the tooltip
	var tooltip = d3.select("body").append("div")
		.attr("class", "tooltip")
		.style("background-color", "white")
		.style("border", "solid 3px black")
		.style("padding", "5px")
		.style("opacity", 0);

	svg.append("g")
		.attr("class", "x axis")
		.style("font-size", "1.2em")
		.call(xAxis)
	var g = svg.selectAll()
		.data(data).enter().append("g");

	g.append("rect")
		.attr("height", bar_height)
		.attr("width", function (d) { return x(end_date) - x(start_date); })
		.attr("x", function (d) { return x(start_date); })
		.attr("y", function (d, i) { return y(i) + (bar_height / 2); })
		.style("fill", "red")
		.style("opacity", "0.2");

	g.append("rect")
		.attr("height", bar_height)
		.attr("width", function (d) { return x(d.end_date) - x(d.start_date); })
		.attr("x", function (d) { return x(d.start_date); })
		.attr("y", function (d, i) { return y(i) + (bar_height / 2); })
		.style("fill", "green")
		.on("mouseover", function (d) {
			tooltip.transition()
				.duration(200)
				.style("opacity", 1);
			tooltip.html("<b>" + d.node + "</b><br/>" + d.parameter)
				.style("left", (d3.event.pageX - 100) + "px")
				.style("top", (d3.event.pageY - 50) + "px");
		})
		.on("mouseout", function (d) {
			tooltip.transition()
				.duration(500)
				.style("opacity", 0);
		});

};
