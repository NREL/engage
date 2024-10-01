'use strict';

var total_radius = 40,
    buffer_radius = 10,
    calc_zoom_scale = function(current_zoom) {
        return 0.3;
        var nodes_scale = 1 / Math.sqrt(nodes.length + 1);
        var map_scale = 2 * Math.pow(1.2 + nodes_scale, current_zoom - initial_map_zoom);
        var scale = nodes_scale * map_scale;
        return scale;
    },
    radius_multiplier = function(d) {
        return 1 + 1.5 * Math.log10(n_loc_techs(d)) + 0.5 * Math.log10(link_counts[d.loc])
    },
    mapbox_styles = {
        'Streets': 'mapbox/streets-v11',
        'Satellite': 'mapbox/satellite-v9',
        'Satellite + Streets': 'mapbox/satellite-streets-v9',
        'Outdoors': 'mapbox/outdoors-v11',
        'Light': 'mapbox/light-v10',
        'Dark': 'mapbox/dark-v10'
    },
    map_style = localStorage.getItem("mapstyle") || Object.values(mapbox_styles)[0],
    buffer_divisor = 5,
    stroke_multiplier = 12,
    inactive_opacity = 0.1,
    active_opacity = function() {
        return 1;
        // return selected_tech === null ? 1 : Math.floor(ts_ind % 10 > 1);
    },
    abstract_techs = {
        supply: {
            description: 'Supplies energy to a carrier, has a positive resource.',
            icon: '<i class="fas fa-bolt"></i>',
            pretty_name: 'Supply'
        },
        supply_plus: {
            description: 'Supplies energy to a carrier, has a positive resource. Additional possible constraints, including efficiencies and storage, distinguish this from supply.',
            icon: '<i class="fas fa-battery-three-quarters"></i> <i class="fas fa-bolt"></i>',
            pretty_name: 'Supply + Storage'
        },
        demand: {
            description: 'Demands energy from a carrier, has a negative resource.',
            icon: '<i class="far fa-building"></i>',
            pretty_name: 'Demand'
        },
        storage: {
            description: 'Stores energy.',
            icon: '<i class="fas fa-battery-three-quarters"></i>',
            pretty_name: 'Storage'
        },
        transmission: {
            description: 'Transmits energy from one location to another.',
            icon: '<i class="fas fa-exchange-alt"></i>',
            pretty_name: 'Transmission'
        },
        conversion: {
            description: 'Converts energy from one carrier to another.',
            icon: '<i class=\"fa-solid fa-shuffle\"></i>',
            pretty_name: 'Conversion'
        },
        conversion_plus: {
            description: 'Converts energy from one carrier to another.',
            icon: '<i class=\"fa-solid fa-shuffle\"></i> <i class="fas fa-plus"></i>',
            pretty_name: 'Conversion Plus'
        }
    },
    lat_buffer = 0.02,
    lon_buffer = 0.5,
    techs = [],
    colors = {},
    names = {},
    parents = {},
    base_techs = {},
    locations = {},
    coordinates = {},
    max_lat = 0,
    min_lat = 0,
    max_lon = 0,
    min_lon = 0,
    nodes = [],
    links = [],
    link_counts = {},
    capacities = {},
    trans_capacities = {},
    carriers = [],
    production = {},
    trans_production = {},
    selected_tech = null,
    selected_carrier = 'all',
    animation_speed = 600,
    animation_interval = null,
    wait_d3_interval = null,
    wait_mapbox_interval = null,
    wait_setup_interval = null,
    timeline_redraw_timer = null,
    timestamps = [],
    ts = null,
    ts_ind = 0,
    min_date = null,
    min_date_str = null,
    max_date = null,
    max_date_str = null,
    min_index = 0,
    max_index = 0,
    max_prod = 100000,
    initial_map_zoom = 1,
    map_bounds = null,
    zoom_scale = 1,
    dragging_timeline = false,
    viz = {},
    map = null,
    container = null,
    model_uuid = null,
    run_id = null,
    popup = null,
    popup_content = "",
    last_popup_content = "",
    static_arc = function() {},
    dynamic_arc = function() {},
    d3_loaded = false,
    map_loaded = false,
    data_loaded = false;

if (LANGUAGE_CODE === "fr") {
    abstract_techs = {
        supply: {
            description: "Fournit de l'énergie à un transporteur, a une ressource positive.",
            icon: '<i class="fas fa-bolt"></i>',
            pretty_name: "Supply"
        },
        supply_plus: {
            description: "Fournit de l'énergie à un transporteur, a une ressource positive. D'autres contraintes possibles, notamment l'efficacité et le stockage, distinguent cela de l'approvisionnement.",
            icon: '<i class="fas fa-battery-three-quarters"></i> <i class="fas fa-bolt"></i>',
            pretty_name: "D'approvisionnement + Stockage"
        },
        demand: {
            description: "Demande de l'énergie à un transporteur, a une ressource négative.",
            icon: '<i class="far fa-building"></i>',
            pretty_name: 'Demand'
        },
        storage: {
            description: "Stocke l'énergie.",
            icon: '<i class="fas fa-battery-three-quarters"></i>',
            pretty_name: 'Storage'
        },
        transmission: {
            description: "Transmet l'énergie d'un endroit à un autre.",
            icon: '<i class="fas fa-exchange-alt"></i>',
            pretty_name: 'Transmission'
        },
        conversion: {
            description: "Convertit l'énergie d'un transporteur à un autre.",
            icon: '<i class=\"fa-solid fa-shuffle\"></i>',
            pretty_name: 'Conversion'
        },
        conversion_plus: {
            description: "Convertit l'énergie d'un transporteur à un autre.",
            icon: '<i class=\"fa-solid fa-shuffle\"></i> <i class="fas fa-plus"></i>',
            pretty_name: 'Conversion Plus'
        }
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
};

MapStyleControl.prototype.onRemove = function() {
	this._container.parentNode.removeChild(this._container);
	this._map = undefined;
};

function changeMapStyle() {
    // console.log("Setting map style...")
    map_style = $('#map-style').val();
    localStorage.setItem("mapstyle", map_style);
    map.setStyle('mapbox://styles/' + map_style);
}

function getDates() {
    var date_field = $('#map-start-date'),
        val = date_field.val();
    if (val == "") {
        date_field.val(date_field.attr('min'));
    }
    
    min_date = new Date(val);
    max_date = new Date(min_date);
    max_date.setDate(min_date.getDate() + 7);
    
    min_date_str = min_date.toISOString().substr(0, 10);
    max_date_str = max_date.toISOString().substr(0, 10);
}

function changeStartDate() {

    min_index = timestamps.findIndex(function(x) {
        return x.substr(0, 10) >= min_date_str;
    });
    
    var max_date_index = timestamps.slice().reverse().findIndex(function(x) {
        return x.substr(0, 10) < max_date_str;
    });
    max_index = timestamps.length - 1;
    if (max_date_index > -1) {
        max_index -= max_date_index;
    }
    
    ts_ind = min_index;
    
    redraw_timeline();
}

function fix_height() {
    $('#viz-legend').outerHeight($(window).innerHeight() - $('#viz-container').offset().top);
    $('#viz-container').outerHeight($(window).innerHeight() - $('#viz-container').offset().top);
}

$(document).ready(function() {
    load_data();
    
    fix_height();
    
    $('#map-start-date').change(load_data);
    
    wait_d3_interval = setInterval(function() {
        if (typeof d3 == 'undefined' || typeof d3.selection == 'undefined') return;
        clearInterval(wait_d3_interval);
        wait_d3_interval = null;
        // console.log('D3 loaded!');
        
        //---------------- D3 FUNCTIONS
        
        d3.selection.prototype.moveToFront = function() {
            return this.each(function() {
                this.parentNode.appendChild(this);
            });
        };
        
        static_arc = d3.arc()
            // .innerRadius((d) => get_iRadius(d))
            .innerRadius(0)
            .outerRadius((d) => get_oRadius(d))
            .startAngle(0)
            .endAngle(2 * Math.PI);
        
        dynamic_arc = d3.arc()
            .innerRadius((d) => get_iRadius(d))
            .outerRadius((d) => get_oRadius(d))
            .startAngle(0)
            .endAngle((d) => get_utilization(d) * 2 * Math.PI);
            
        d3_loaded = true;
    }, 100);
    
    wait_mapbox_interval = setInterval(function() {
        if (Object.keys(coordinates).length == 0 || typeof mapboxgl == 'undefined' || typeof mapboxgl.Map == 'undefined') return;
        clearInterval(wait_mapbox_interval);
        wait_mapbox_interval = null;
        // console.log('Setting up Mapbox...');
        
        // load Mapbox
        $('#viz-main').html('')
        var center_lat = (min_lat + max_lat) / 2,
            center_lon = (min_lon + max_lon) / 2;
        map = new mapboxgl.Map({
            container: 'viz-main',
            style: 'mapbox://styles/' + map_style,
            center: [center_lon, center_lat],
            attributionControl: false,
            bounds: [
                [min_lon, min_lat],
                [max_lon, max_lat]
            ]
            })
            .addControl(new mapboxgl.AttributionControl({
                compact: true
            }))
            .addControl(new MapStyleControl())
            .addControl(new mapboxgl.NavigationControl());
        initial_map_zoom = map.getZoom();
        map_bounds = map.getBounds();
        container = map.getCanvasContainer();
        map_loaded = true;
    }, 100);
    
    wait_setup_interval = setInterval(function() {
        if (data_loaded == false || map_loaded == false || d3_loaded == false) return;
        clearInterval(wait_setup_interval);
        // console.log('Setup done! Initiating viz...');
        main();
    }, 150);
});

//---------------- LOAD DATA

function load_data() {
    getDates();
    // console.log('loading data...');
    model_uuid = $('#viz-container').data('model_uuid');
    run_id = $('#viz-main').data('run_id');
    $.ajax({
        url: '/' + LANGUAGE_CODE + '/component/map_outputs/',
        type: 'POST',
        data: {
            'model_uuid': model_uuid,
            'run_id': run_id,
            'start_date': min_date_str,
            'end_date': max_date_str,
            'csrfmiddlewaretoken': document.getElementsByName('csrfmiddlewaretoken')[0].value
        },
        dataType: 'json',
        complete: function (data) {
            if (data.status != 200) {
                alert('There was a problem getting the map data.');
                return;
            }
            
            if (data_loaded == false) {

                // load colors & techs
                var [headers, lines] = parse_data(data, 'inputs_color');
                lines.map(function(d) {
                    colors[d[headers.techs]] = d[headers.color];
                    techs.push(d[headers.techs]);
                });
                
                // load names
                var [headers, lines] = parse_data(data, 'inputs_name');
                lines.map(function(d) {
                    names[d[headers.techs]] = d[headers.name];
                });
                
                // load parents & groups
                var [headers, lines] = parse_data(data, 'inputs_base_tech');
                lines.map(function(d) {
                    parents[d[headers.techs]] = d[headers.base_tech];
                    if (Object.keys(base_techs).indexOf(d[headers.base_tech]) == -1) {
                        base_techs[d[headers.base_tech]] = [d[headers.techs]];
                    } else {
                        base_techs[d[headers.base_tech]].push(d[headers.techs]);
                    }
                });
                
                // load coordinates
                var lats = [], lons = [];

                var [latHeaders, latLines] = parse_data(data, 'inputs_latitude');
                latLines.map(function(d) {
                    assign(coordinates, [d[latHeaders.nodes], 'latitude'], +d[latHeaders.latitude]);
                    lats.push(+d[latHeaders.latitude]);
                });

                var [lonHeaders, lonLines] = parse_data(data, 'inputs_longitude');
                lonLines.map(function(d) {
                    assign(coordinates, [d[lonHeaders.nodes], 'longitude'], +d[lonHeaders.longitude]);
                    lons.push(+d[lonHeaders.longitude]);
                });
                
                lat_buffer = (Math.max.apply(Math, lats) - Math.min.apply(Math, lats)) / buffer_divisor;
                lon_buffer = (Math.max.apply(Math, lons) - Math.min.apply(Math, lons)) / buffer_divisor;
                max_lat = Math.max.apply(Math, lats) + lat_buffer;
                min_lat = Math.min.apply(Math, lats) - lat_buffer;
                max_lon = Math.max.apply(Math, lons) + lon_buffer;
                min_lon = Math.min.apply(Math, lons) - lon_buffer;
                for (var key in coordinates) {
                    locations[key] = [];
                    link_counts[key] = 0;
                }
                
                // load capacities
                var [headers, lines] = parse_data(data, 'results_flow_cap');
                lines.map(function(d) {
                    if (!d[headers.nodes2]) {
                        nodes.push({
                            'loc': d[headers.nodes],
                            'tech': d[headers.techs],
                            'capacity': +d[headers.flow_cap]
                        });
                        locations[d[headers.nodes]].push(d[headers.techs]);
                        assign(capacities, [d[headers.nodes], d[headers.techs]], +d[headers.flow_cap]);
                    } else {
                        links.push({
                            'loc1': d[headers.nodes],
                            'loc2': d[headers.nodes2],
                            'tech': d[headers.techs],
                            'capacity': +d[headers.flow_cap]
                        });
                        
                        // Cache # of links from each node:
                        link_counts[d[headers.nodes]] ++;
                        
                        assign(trans_capacities, [d[headers.nodes], d[headers.techs].split(':')[0], d[headers.techs].split(':')[1]], +d[headers.flow_cap]);
                    };
                });
            } else {
                // Clear variables for new timeseries data
                carriers = []
                timestamps = []
                production = {}
                trans_production = {}
            }

            // load consumption
            var [headers, lines] = parse_data(data, 'results_flow_in');
            lines.map(function(d) {
                if (!d[headers.nodes2]) {
                    if (!carriers.includes(d[headers.carriers])) {
                        carriers.push(d[headers.carriers])
                    }
                    if (!timestamps.includes(d[headers.timesteps])) {
                        timestamps.push(d[headers.timesteps])
                        production[d[headers.timesteps]] = []
                    }
                    production[d[headers.timesteps]].push({
                        'loc': d[headers.nodes],
                        'tech': d[headers.techs],
                        'carrier': d[headers.carriers],
                        'production': +d[headers.flow_in]
                    });
                } else {
                    if (trans_production[d[headers.timesteps]] == undefined) {
                        trans_production[d[headers.timesteps]] = []
                    };
                    trans_production[d[headers.timesteps]].push({
                        'loc1': d[headers.nodes],
                        'loc2': d[headers.nodes2],
                        'tech': d[headers.techs],
                        'carrier': d[headers.carriers],
                        'production': -d[headers.flow_in]
                    });
                }
            });
            
            // load production
            max_prod = 0;
            var max_prods = {};
            var [headers, lines] = parse_data(data, 'results_flow_out');
            lines.map(function(d) {
                if (!carriers.includes(d[headers.carriers])) {
                    carriers.push(d[headers.carriers])
                }
                if (!d[headers.nodes2]) {
                    max_prods[d[headers.timesteps]] = (max_prods[d[headers.timesteps]] || 0) + +d[headers.flow_out];
                    production[d[headers.timesteps]].push({
                        'loc': d[headers.nodes],
                        'tech': d[headers.techs],
                        'carrier': d[headers.carriers],
                        'production': +d[headers.flow_out]
                    });
                } else {
                    // NOTE: USING CONSUMPTION DATA INSTEAD (ABOVE)
                    // trans_production[d[headers.timesteps]].push({
                    //     'loc1': d[headers.nodes],
                    //     'loc2': d[headers.techs].split(':')[1],
                    //     'tech': d[headers.techs].split(':')[0],
                    //     'carrier': d[headers.carriers],
                    //     'production': +d[headers.flow_out]
                    // });
                };
            });
            max_prod = Math.max.apply(Math, Object.values(max_prods));

            data_loaded = true;
            changeStartDate();
        }
    });
}

function parse_data(data, key) {
    var lines = data.responseJSON[key].split('\n'),
        headers = lines[0].split(',');
    headers = headers.reduce(function(a, b, i) { return (a[b] = i, a) }, {});
    lines = lines.slice(1, -1).map(function(a) { return a.split(',') });
    return [headers, lines];
};

//---------------- BUILD VISUALIZATION

function main() {
    changeMapStyle();
    
    $(window).resize(redraw_timeline);
    $(window).focus(start_animation);
    window.onblur = function(e) {
		// console.log('window.onblur');
		stop_animation();
	};
    
    zoom_scale = calc_zoom_scale(initial_map_zoom);
    viz = initiate_viz();
    build_viz();
    start_animation();
}

function animate_now(immediate) {
    if (typeof immediate !== 'boolean') immediate = false;
    ts = timestamps[ts_ind];
	
    update_viz(ts, immediate);
    ts_ind ++;
    if (ts_ind >= max_index) {
        ts_ind = min_index
        // stop_animation();
    }
}

function start_animation() {
    if (dragging_timeline) {
        animate_now(true);
        return;
    }
	
    if (animation_interval === null) {
        animation_interval = setInterval(animate_now, animation_speed);
    }
}

function stop_animation() {
    if (animation_interval !== null) {
        clearInterval(animation_interval);
        animation_interval = null;
    }
}

function timeline_drag_start() {
    dragging_timeline = true;
    stop_animation();
}

function timeline_drag_end() {
    dragging_timeline = false;
    start_animation();
}

function timeline_drag_move() {
    if (!dragging_timeline) return;
    // log the mouse x position
    var pos = d3.mouse(this)[0] / $(this).width();
    ts_ind = -1 + min_index + Math.round(pos * (1 + max_index - min_index));
    animate_now(true);
}

function initiate_viz() {
    // console.log('1. initiate_viz')
    d3.selectAll("svg").remove();
	
    //---- Initiate the SVG Canvas
    var width = $('#viz-main').width();
    var height = $('#viz-main').height();
	
    // Setup z scale
    var zScale = d3.scaleLinear()
        .domain([0, max_prod])
        .range([0, $('#viz-timeline').height() / 2]); // value -> display
	
    // Setup ts scale
    var tsScale = d3.scaleLinear()
        .domain([0, (max_index - min_index)])
        .range([0, $('#viz-timeline').width()]); // value -> display
	
    var svg_main = d3.select(container).append("svg")
        .attr("width", "100%")
        .attr("height", "100%")
        // .call(d3zoom)
        .append("g");
	
    var div_legend = d3.select("#viz-legend-content").append("g"),
        legend_header = d3.select("#viz-legend-header").append("g");
    
    //---- Draw clock
    d3.selectAll(".clock").remove();
    legend_header.append("div")
        .attr("class", "clock flex-wrap d-inline-flex justify-content-center align-items-center")
        .style("font-family", "monospace")
        .style("font-size", "20px");
    
    // Add the timeline canvas to the body of the webpage
    var svg_timeline = d3.select("#viz-timeline").append("svg")
        .attr("class", "timeline")
        .attr("width", "100%")
        .attr("height", "100%")
        .on('touchstart', timeline_drag_start)
        .on('mousedown', timeline_drag_start)
        .on('touchend', timeline_drag_end)
        .on('mouseup', timeline_drag_end)
        .on('mouseleave', timeline_drag_end)
        .on('touchmove', timeline_drag_move)
        .on('mousemove', timeline_drag_move)
        .append("g");
    
    //---- Build Legend
    
    // Add Carriers
    if (carriers.length > 1) {
        
        // Add Carriers header
        var group = div_legend.append("div")
            .attr("class", "group row")
            .style("margin-bottom", "30px");
        var title = group.append("div")
            .attr("class", "col-12")
            .style("font-size", "20px")
            .style("font-weight", "500")
            .style("text-align", "center")
            .attr("title", "Carriers")
            .attr("data-toggle", "tooltip")
            .style("background-color", "silver")
            .html("Carriers");
        
        for (var i = 0; i <= carriers.length; i ++) {
            var carrier;
            if (i == carriers.length) {
                carrier = 'all';
            } else {
                carrier = carriers[i];
            }
            group.append("div")
                .attr("class", "col-12 carrier " + (function(len) {
                    if (len > 20) return '';
                    else if (len > 8) return 'col-lg-6';
                    else return 'col-lg-4 col-md-6';
                })(carrier.length))
                .append("a")
                .attr("class", "p-2 rounded d-inline-block")
                .attr("data-carrier", carrier)
                .style("cursor", "pointer")
                .html(carrier.titleCase())
                .on("click", function() {
                    var bbox = new mapboxgl.LngLatBounds();
                    d3.selectAll(".production")
                        .each(function(d) {
                            if (selected_carrier != 'all' && d.carrier != selected_carrier) return;
                            var coords = new mapboxgl.LngLat(coordinates[d.loc].lon, coordinates[d.loc].lat);
                            bbox.extend(coords);
                        });
                    d3.selectAll(".consumption")
                        .each(function(d) {
                            if (selected_carrier != 'all' && d.carrier != selected_carrier) return;
                            var coords = new mapboxgl.LngLat(coordinates[d.loc].lon, coordinates[d.loc].lat);
                            bbox.extend(coords);
                        });
                    d3.selectAll(".trans_production")
                        .each(function(d) {
                            if (selected_carrier != 'all' && d.carrier != selected_carrier) return;
                            var coords1 = new mapboxgl.LngLat(coordinates[d.loc1].lon, coordinates[d.loc1].lat);
                            var coords2 = new mapboxgl.LngLat(coordinates[d.loc2].lon, coordinates[d.loc2].lat);
                            bbox.extend(coords1);
                            bbox.extend(coords2);
                        });
                    var min_width = (max_lon - min_lon) / 10;
                    var min_height = (max_lat - min_lat) / 10;
                    bbox.setNorthEast(new mapboxgl.LngLat(bbox._ne.lng + min_width/2, bbox._ne.lat + min_height/2));
                    bbox.setSouthWest(new mapboxgl.LngLat(bbox._sw.lng - min_width/2, bbox._sw.lat - min_height/2));
                    map.fitBounds(bbox.toArray());
                })
                .on("mouseover", function() {
                    selected_carrier = $(this).data("carrier");
                    $(this).css("background-color", "#000");
                    $(this).css("color", "#fff");
                })
                .on("mouseout", function() {
                    selected_carrier = 'all';
                    $(this).css("background-color", "transparent");
                    $(this).css("color", "#000");

                    viz.main.selectAll(".trans_production")
                        .data(trans_production[ts])
                        .style("opacity", function(d) {
                            return active_opacity();
                        })
                    viz.main.selectAll(".production")
                        .data(production[ts])
                        .style("opacity", function(d) {
                            return active_opacity();
                        })
                    viz.main.selectAll(".consumption")
                        .data(production[ts])
                        .attr("opacity", function(d) {
                            if (d.production >= 0) {
                                return 0
                            } else {
                                return active_opacity();
                            };
                        });
                });
        }
    }
    
    Object.keys(base_techs).sort().forEach(function(g) {
        var group = div_legend.append("div")
            .attr("class", "group row")
            .style("margin-bottom", "30px");
        
        var title = group.append("div")
            .attr("class", "col-12")
            .style("background-color", "silver")
            .style("font-size", "20px")
            .style("font-weight", "500")
            .style("text-align", "center")
            .attr("title", abstract_techs[g].description)
            .attr("data-toggle", "tooltip")
            .html(
                abstract_techs[g].icon + " &nbsp;" + abstract_techs[g].pretty_name
            );
        
            base_techs[g].sort().forEach(function(tech) {
            var gd = group.append("div")
                .attr("class", "tech col-12")
                .style("text-align", "left");
            
            var link = gd.append("a")
                .attr("class", "px-1 rounded d-inline-block")
                .attr("data-tech", tech)
                .style("color", "#000")
                .style("cursor", "pointer")
                .style("padding", "3px")
                .on("click", function() {
                    var bbox = new mapboxgl.LngLatBounds();
                    d3.selectAll(".capacity")
                        .each(function(d) {
                            if (d.tech != selected_tech) return;
                            var coords = new mapboxgl.LngLat(coordinates[d.loc].lon, coordinates[d.loc].lat);
                            bbox.extend(coords);
                        });
                    d3.selectAll(".trans_capacities")
                        .each(function(d) {
                            if (d.tech != selected_tech) return;
                            var coords1 = new mapboxgl.LngLat(coordinates[d.loc1].lon, coordinates[d.loc1].lat);
                            var coords2 = new mapboxgl.LngLat(coordinates[d.loc2].lon, coordinates[d.loc2].lat);
                            bbox.extend(coords1).extend(coords2);
                        });
                    var min_width = (max_lon - min_lon) / 10;
                    var min_height = (max_lat - min_lat) / 10;
                    bbox.setSouthWest(new mapboxgl.LngLat(bbox._sw.lng - min_width/2, bbox._sw.lat - min_height/2));
                    bbox.setNorthEast(new mapboxgl.LngLat(bbox._ne.lng + min_width/2, bbox._ne.lat + min_height/2));
                    // console.log(bbox);
                    map.fitBounds(bbox.toArray());
                })
                .on("mouseover", function() {
                    selected_tech = $(this).data("tech");
                    $(this).css("background-color", colors[selected_tech]);
                    if (brightnessByColor(colors[selected_tech]) > 127) {
                        $(this).css("color", "#000");
                    } else {
                        $(this).css("color", "#fff");
                    }
                    $(this).find(".symbol").css("background-color", "#fff");
                })
                .on("mouseout", function() {
                    selected_tech = null;
                    
                    $(this).css("color", "#000");
                    $(this).css("background-color", "transparent");
                    $(this).find(".symbol").css("background-color", colors[$(this).data("tech")]);
                    viz.main.selectAll(".trans_production")
                        .data(trans_production[ts])
                        .style("opacity", function(d) {
                            return active_opacity();
                        })
                    viz.main.selectAll(".production")
                        .data(production[ts])
                        .style("opacity", function(d) {
                            return active_opacity();
                        })
                    viz.main.selectAll(".consumption")
                        .data(production[ts])
                        .attr("opacity", function(d) {
                            if (d.production >= 0) {
                                return 0
                            } else {
                                return active_opacity();
                            };
                        });
                });
                
                var symbol = link.append("span")
                    .attr("class", "symbol")
                    .style("background-color", colors[tech])
                    .style("display", "inline-block")
                    .style("margin-right", "4px");
                
                if (g == "transmission") {
                    symbol.style("width", "32px")
                        .style("height", "6px")
                        .style("border-radius", "6px")
                        .style("margin-bottom", "2px");
                } else {
                    symbol.style("width", "24px")
                        .style("height", "12px")
                        .style("border-radius", "24px 24px 0 0");
                }
                
                link.append("span")
                    .html(tech.titleCase());
        });
    });
    
    map.on('error', function(e) {
        var message;
        if (typeof e.error !== 'undefined' && typeof e.error.message !== 'undefined') {
            message = e.error.message;
        }
        if (message.indexOf('NetworkError') == 0) {
            console.log("Caught MapBox NetworkError (user aborted?)");
        } else {
            console.log("Caught MapBox Error:");
            console.log(e);
        }
    });
    
    map.on('load', function() {
        fix_height();
        map.addSource('mapbox-dem', {
            'type': 'raster-dem',
            'url': 'mapbox://mapbox.mapbox-terrain-dem-v1',
            'tileSize': 512,
            'maxzoom': 14
        });
        map.setTerrain({ 'source': 'mapbox-dem', 'exaggeration': 1.5 });
        map.addLayer({
            'id': 'sky',
            'type': 'sky',
            'paint': {
                'sky-type': 'atmosphere',
                'sky-atmosphere-sun': [0.0, 0.0],
                'sky-atmosphere-sun-intensity': 15
            }
        });
    });
    
    map.on('move', function() {
        ts = timestamps[ts_ind];
        update_viz(ts, true);
    });
    
    
    map.on("mousemove", function(e) {
        if (popup_content != last_popup_content) {
            last_popup_content = popup_content;
            if (popup_content.length == 0) {
                if (popup !== null) {
                    popup.remove();
                    popup = null;
                }
            } else {
                if (popup === null) {
                    popup = new mapboxgl.Popup({ closeButton: false })
                        .setHTML(popup_content)
                        .setMaxWidth('auto')
                        .addTo(map);
                }
            }
        }
        
        if (popup !== null) popup.setLngLat(e.lngLat);
    })
    
    
    return {
        main: svg_main,
        legend: div_legend,
        timeline: svg_timeline,
        zScale: zScale,
        tsScale: tsScale,
        width: width,
        height: height
    };
}

function redraw_timeline() {
    if (typeof viz.timeline === 'undefined') return;
    
    fix_height();
    
    if (timeline_redraw_timer !== null) {
        clearTimeout(timeline_redraw_timer);
    }
    
    timeline_redraw_timer = setTimeout(function() {
        viz.timeline.selectAll(".stacked-bar").remove();
        viz.timeline.selectAll("line").remove();
        viz.timeline.selectAll("text").remove();
        
        viz.zScale = d3.scaleLinear()
            .domain([0, max_prod])
            .range([0, $('#viz-timeline').height() / 2]); // value -> display
        
        viz.tsScale = d3.scaleLinear()
            .domain([0, (max_index - min_index)])
            .range([0, $('#viz-timeline').width()]); // value -> display
            
        var bar_width = 1 + Math.round(viz.tsScale.range()[1] / (1 + max_index - min_index));
        var zHeight = $('#viz-timeline').height() / 2;
        var td = null, display_date = null, last_year = null, last_month = null, last_day = null;
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        for (var i = min_index; i < max_index; ++i) {
            var prods = production[timestamps[i]];
            var total_prod = 0;
            var total_con = 0;
            for (var j = 0; j < prods.length; ++j) {
                var prod = prods[j].production
                var bar_height = viz.zScale(Math.abs(prod))
                if (prod >= 0) {
                    var bar_base = zHeight - total_prod - bar_height;
                    total_prod += bar_height;
                } else {
                    var bar_base = zHeight + total_con;
                    total_con += bar_height;
                };
                viz.timeline.append("rect")
                    .style("fill", colors[prods[j].tech])
                    .attr("class", "stacked-bar carrier carrier-" + prods[j].carrier)
                    .attr("x", viz.tsScale(i - min_index))
                    .attr("y", bar_base)
                    .attr("width", bar_width)
                    .attr("height", bar_height);
            };
        }
        
        viz.timeline.selectAll('.tick').remove();
        
        for (var i = min_index; i < max_index; ++i) {
            td = new Date(timestamps[i].substr(0, 10));
            if (td.getUTCDate() != last_day) {
                last_day = td.getUTCDate();
                display_date = last_day.toString();
                if (td.getUTCMonth() != last_month) {
                    last_month = td.getUTCMonth();
                    display_date = months[td.getUTCMonth()] + ' ' + display_date;
                    if (td.getUTCFullYear() != last_year) {
                        last_year = td.getUTCFullYear();
                        display_date += ', ' + last_year.toString();
                    }
                }
                // console.log(display_date);
                var tick_group = viz.timeline.append("g")
                    .attr("class", "tick");
                
                tick_group.append("rect")
                    .style("fill", "#000")
                    .attr("width", 8 + 5.7 * display_date.length)
                    .attr("rx", 7)
                    .attr("height", 14)
                    .attr("transform", function(d) {
                        return 'translate( ' + (-3 + viz.tsScale(i - min_index)) + ' , ' + (-5 + zHeight) + '), rotate(-45)';
                    })
                    .moveToFront();
                tick_group.append("text")
                    .style("fill", "#fff")
                    .style("font-size", "8pt")
                    .style("font-weight", "600")
                    .style("pointer-events", "none")
                    .text(display_date)
                    .attr("transform", function(d) {
                        return 'translate( ' + (7 + viz.tsScale(i - min_index)) + ' , ' + zHeight + '), rotate(-45)';
                    })
                    .moveToFront();
                if (i > min_index) {
                    tick_group.append("line")
                        .style("stroke", "#fff")
                        .style("stroke-dasharray", ("3, 3"))
                        .style("mix-blend-mode", "difference")
                        .attr("x1", viz.tsScale(i - min_index))
                        .attr("x2", viz.tsScale(i - min_index))
                        .attr("y1", 0)
                        .attr("y2", zHeight * 2)
                        .moveToFront();
                }
                
            }
        }
        //---- Draw slider
        viz.timeline.selectAll(".slider").remove();
        viz.timeline.append("line")
            .attr("class", "slider")
            .style("stroke", "yellow")
            .attr("stroke-width", "6px")
            .style("mix-blend-mode", "difference")
            .attr("x1", viz.tsScale(ts_ind - min_index))
            .attr("y1", 0)
            .attr("x2", viz.tsScale(ts_ind - min_index))
            .attr("y2", $('#viz-timeline').height())
            .moveToFront();
        
        timeline_redraw_timer = null;
    }, 200);
}

function build_viz() {
    // console.log('2. build_viz')
    //---- Draw Static Transmission
    
    // draw trans_capacities
    d3.selectAll(".trans_capacities").remove();
    viz.main.selectAll(".trans_capacities")
        .data(links)
        .enter().append("line")
        .attr("class", "trans_capacities")
        .attr("stroke-width", (1 + stroke_multiplier * zoom_scale) * 0.4)
        .attr("x1", function(d) {
            return project(coordinates[d.loc1]).x;
        })
        .attr("x2", function(d) {
            return project(coordinates[d.loc2]).x;
        })
        .attr("y1", function(d) {
            return project(coordinates[d.loc1]).y;
        })
        .attr("y2", function(d) {
            return project(coordinates[d.loc2]).y;
        })
        .style("stroke", "silver")
        .style("opacity", 0.4)
        .style("stroke-linecap", "round")
        .attr("cursor", "crosshair")
        .attr("pointer-events", "visible")
        .on("mouseenter", function(d) {
            popup_content = '<h4>Transmission</h4>' +
                 '<h5>' + d.loc1.titleCase() + ' &harr; ' + d.loc2.titleCase() + '</h5>';
        })
        .on("mouseleave", function(d) {
            popup_content = '';
        });

    
    d3.selectAll(".trans_production").remove();
    viz.main.selectAll(".trans_production")
        .data(trans_production[timestamps[0]])
        .enter().append("line")
        .attr("class", "trans_production")
        .attr("x1", function(d) {
            return project(coordinates[d.loc1]).x;
        })
        .attr("x2", function(d) {
            return project(coordinates[d.loc2]).x;
        })
        .attr("y1", function(d) {
            return project(coordinates[d.loc1]).y;
        })
        .attr("y2", function(d) {
            return project(coordinates[d.loc2]).y;
        })
        .style("stroke", function(d) {
            return colors[d.tech];
        })
        .attr("stroke-width", 1 + stroke_multiplier * zoom_scale)
        .style("stroke-linecap", "round")
        .attr("x1", function(d) {
            return project(coordinates[d.loc2]).x;
        })
        .attr("x2", function(d) {
            var lx1 = project(coordinates[d.loc1]).x,
                lx2 = project(coordinates[d.loc2]).x;
            return d3.interpolate(lx2, lx1)(get_trans_utilization(d));
        })
        .attr("y1", function(d) {
            return project(coordinates[d.loc2]).y;
        })
        .attr("y2", function(d) {
            var ly1 = project(coordinates[d.loc1]).y,
                ly2 = project(coordinates[d.loc2]).y;
            return d3.interpolate(ly2, ly1)(get_trans_utilization(d));
        })

    //---- Draw Static Nodes

    // draw capacities
    d3.selectAll(".capacity").remove();
    viz.main.selectAll(".capacity")
        .data(nodes)
        .enter().append("path")
        .attr("class", "capacity")
        .attr("transform", function(d) {
            return translate(coordinates[d.loc])
        })
        .attr("stroke", "silver")
        .attr("stroke-width", 1)
        .attr("d", static_arc)
        .style("opacity", 0.4)
        .style("fill", "gray")
        .style("fill-opacity", 0.8)
        .attr("cursor", "crosshair")
        .attr("pointer-events", "visible")
        .on("mouseenter", function(d) {
            popup_content = '<h4>' + d.loc.titleCase() + '</h4><table>' +
                '<tr><th class="h6">Technology</th><th class="h6">Capacity</th></tr>';
            var techs = Object.keys(capacities[d.loc]);
            for (var i = 0; i < techs.length; i ++) {
                popup_content += '<tr><th>' + techs[i].titleCase() + '</th>' +
                    '<td>' + capacities[d.loc][techs[i]] + '</td></tr>';
            }
            popup_content += '</table>';
        })
        .on("mouseleave", function(d) {
            popup_content = '';
        });

    // draw initial production
    d3.selectAll(".production").remove();
    viz.main.selectAll(".production")
        .data(production[timestamps[0]])
        .enter().append("path")
        .attr("class", function(d) {
            return "production tech-" + d.tech + " carrier carrier-" + d.carrier
        })
        .attr("transform", function(d) {
            return translate(coordinates[d.loc])
        })
        .attr("fill", function(d) {
            return colors[d.tech];
        })
    .attr("stroke", "transparent")
    // .attr("stroke", "black")
    .attr("stroke-width", 1)
    .attr("d", dynamic_arc)
        .each(function(d) {
            this._current = d;
        });

    // Draw initial consumption
    // d3.selectAll(".consumption").remove();
    // viz.main.selectAll(".consumption")
    //     .data(production[timestamps[0]])
    //     .enter().append("path")
    //     .attr("class", function(d) {
    //         return "consumption carrier carrier-" + d.carrier
    //     })
    //     .attr("transform", function(d) {
    //         return translate(coordinates[d.loc])
    //     })
    //     .attr("fill", function(d) {
    //         return colors[d.tech];
    //     })
    //     .attr("opacity", function(d) {
    //         if (d.production >= 0) {
    //             return 0
    //         } else {
    //             return 1
    //         };
    //     })
    //     .attr("d", dynamic_arc);

    //---- Draw timeline initially
    redraw_timeline();
}


function update_viz(ts, immediate) {
    // if ($('#viz-main').length == 0 || typeof viz.main == 'undefined' || !d3_loaded || !map_loaded || !data_loaded) {
    //     stop_animation();
    //     return;
    // }
    if (typeof timestamps === 'undefined') return;
    if (typeof ts === 'undefined') ts = timestamps[0];
    if (typeof immediate !== 'boolean') immediate = false;
	
    var duration = animation_speed;
    if (immediate) duration = 0;
	
	var current_bounds = map.getBounds();
	
    // check if map bounds, zoom, pan/tilt, etc. have changed:
    if (map_bounds._ne.lat != current_bounds._ne.lat |
		map_bounds._ne.lng != current_bounds._ne.lng |
		map_bounds._sw.lat != current_bounds._sw.lat |
		map_bounds._sw.lng != current_bounds._sw.lng) {
        
		// duration = 0;
        map_bounds = map.getBounds();
        zoom_scale = calc_zoom_scale(map.getZoom());

        // update static transmission lines
        viz.main.selectAll(".trans_capacities")
            .data(links)
            .transition().duration(duration)
            .attr("stroke-width", (1 + stroke_multiplier * zoom_scale) * 0.4)
            .attr("x1", function(d) {
                return project(coordinates[d.loc1]).x;
            })
            .attr("x2", function(d) {
                return project(coordinates[d.loc2]).x;
            })
            .attr("y1", function(d) {
                return project(coordinates[d.loc1]).y;
            })
            .attr("y2", function(d) {
                return project(coordinates[d.loc2]).y;
            });

        // update capacities
		viz.main.selectAll(".capacity")
            .data(nodes)
            .transition().duration(duration)
            .attr("transform", function(d) {
                return translate(coordinates[d.loc])
            })
            .attr("d", static_arc);
        
        // workaround for rendering bug when
        // zooming/panning in Safari:
        viz.main
            .transition().duration(1000)
            .style("opacity", .99)
            .transition().duration(1000)
            .style("opacity", 1);
    }
    
    if (selected_tech !== null) {
        viz.main.selectAll(".trans_production")
            .data(trans_production[ts])
            .style("opacity", function(d) {
                return (selected_tech == d.tech ? active_opacity() : inactive_opacity);
            });
        viz.main.selectAll(".production")
            .data(production[ts])
            .style("opacity", function(d) {
                return (selected_tech == d.tech ? active_opacity() : inactive_opacity);
            });
        viz.main.selectAll(".consumption")
            .data(production[ts])
            .attr("opacity", function(d) {
                if (d.production >= 0) {
                    return 0
                } else {
                    return (selected_tech == d.tech ? active_opacity() : inactive_opacity);
                };
            });
    }
    
    if (selected_carrier !== 'all') {
        viz.main.selectAll(".trans_production")
            .data(trans_production[ts])
            .style("opacity", function(d) {
                return (selected_carrier == d.carrier ? active_opacity() : inactive_opacity);
            });
        viz.main.selectAll(".production")
            .data(production[ts])
            .style("opacity", function(d) {
                return (selected_carrier == d.carrier ? active_opacity() : inactive_opacity);
            });
        viz.main.selectAll(".consumption")
            .data(production[ts])
            .attr("opacity", function(d) {
                if (d.production >= 0) {
                    return 0
                } else {
                    return (selected_carrier == d.carrier ? active_opacity() : inactive_opacity);
                };
            });
    }
    
    // draw trans_production
    viz.main.selectAll(".trans_production")
        .data(trans_production[ts])
        .transition().duration(duration)
        .attr("stroke-width", stroke_multiplier * zoom_scale)
        .style("stroke-linecap", "round")
        .style("stroke", function(d) {
            return colors[d.tech];
        })
        .attr("x1", function(d) {
            return project(coordinates[d.loc1]).x;
        })
        .attr("x2", function(d) {
            var lx1 = project(coordinates[d.loc1]).x,
                lx2 = project(coordinates[d.loc2]).x;
            return d3.interpolate(lx1, lx2)(get_trans_utilization(d));
        })
        .attr("y1", function(d) {
            return project(coordinates[d.loc1]).y;
        })
        .attr("y2", function(d) {
            var ly1 = project(coordinates[d.loc1]).y,
                ly2 = project(coordinates[d.loc2]).y;
            return d3.interpolate(ly1, ly2)(get_trans_utilization(d));
        })

    // Draw production / consumption

    // update production
    viz.main.selectAll(".production")
        .data(production[ts])
        .transition().duration(duration)
        .attrTween("d", arcTween)
        .attr("transform", function(d) {
            return translate(coordinates[d.loc]);
        });

    // update consumption
    // viz.main.selectAll(".consumption")
    //     .data(production[ts])
    //     .transition().duration(duration)
    //     .attrTween("d", arcTween)
    //     .attr("transform", function(d) {
    //         return translate(coordinates[d.loc])
    //     });
        
    // Update the Clock
    var print_ts;
    if (ts.lastIndexOf(':') > ts.indexOf(':')) {
        print_ts = ts.substr(0, ts.lastIndexOf(':'));
    } else {
        print_ts = ts;
    }
    d3.select(".clock")
        .text(print_ts);
    
    // Update the slider position
    viz.timeline.select(".slider")
        .attr("x1", viz.tsScale(ts_ind - min_index))
        .attr("x2", viz.tsScale(ts_ind - min_index));
};

//---------------- SUPPORTING FUNCTIONS

// Transition between arcs
function arcTween(a) {
    var i = d3.interpolate(this._current, a);
    this._current = i(0);
    return function(t) {
        return dynamic_arc(i(t));
    };
}

function get_utilization(d) {
    if (typeof locations[d.loc] !== 'undefined') return (d.production + 0.000001) / (capacities[d.loc][d.tech] + 0.001);
    else return 0;
}

function get_trans_utilization(d) {
    if (typeof locations[d.loc1] !== 'undefined') return (d.production + 0.000001) / (trans_capacities[d.loc1][d.tech][d.loc2] + 0.001);
    else return 0;
}

function get_iRadius(d) {
    return radius_multiplier(d) * (buffer_radius + tech_index(d) * (total_radius / n_loc_techs(d))) * zoom_scale
}

function get_oRadius(d) {
    return radius_multiplier(d) * (buffer_radius + (tech_index(d) + 1) * (total_radius / n_loc_techs(d))) * zoom_scale
}

function n_loc_techs(d) {
    if (typeof locations[d.loc] !== 'undefined') return locations[d.loc].length;
    else return -1;
}

function tech_index(d) {
    if (typeof locations[d.loc] !== 'undefined') return locations[d.loc].sort().indexOf(d.tech);
    else return -1;
}

function assign(obj, keyPath, value) {
    var lastKeyIndex = keyPath.length - 1;
    for (var i = 0; i < lastKeyIndex; ++i) {
        var key = keyPath[i];
        if (!(key in obj)) {
            obj[key] = {}
        }
        obj = obj[key];
    }
    if (obj[keyPath[lastKeyIndex]] == undefined) {
        obj[keyPath[lastKeyIndex]] = value;
    } else {
        obj[keyPath[lastKeyIndex]] += value;
    }

}

function toLngLat(x) {
    try {
        var ll = new mapboxgl.LngLat(x.lon, x.lat);
    } catch (err) {
        console.log(x, err);
    }
    return ll;
}

function project(x) {
    return map.project(toLngLat(x));
}

function translate(x) {
    var p = project(x),
        str = p.x.toString() + ', ' + p.y.toString();
    return ('translate(' + str + ')');
}

// array utils:

Array.prototype.contains = function(v) {
  for (var i = 0; i < this.length; i++) {
    if (this[i] === v) return true;
  }
  return false;
};

Array.prototype.unique = function() {
  var arr = [];
  for (var i = 0; i < this.length; i++) {
    if (!arr.contains(this[i])) {
      arr.push(this[i]);
    }
  }
  return arr;
}

String.prototype.titleCase = function() {
    return this.replace(/_/g, " ").replace(
        /\w\S*/g, function(txt) {
            if (txt.length < 3) {
                return txt.toUpperCase();
            } else {
                return txt.charAt(0).toUpperCase() + txt.substr(1);
            }
        }
    );
}


/**
 * Calculate brightness value by RGB or HEX color.
 * @param color (String) The color value in RGB or HEX (for example: #000000 || #000 || rgb(0,0,0) || rgba(0,0,0,0))
 * @returns (Number) The brightness value (dark) 0 ... 255 (light)
 * https://gist.github.com/w3core/e3d9b5b6d69a3ba8671cc84714cca8a4
 */
function brightnessByColor(color) {
  var color = "" + color, isHEX = color.indexOf("#") == 0, isRGB = color.indexOf("rgb") == 0;
  if (isHEX) {
    color = color.substr(1);
    if (color.length == 3) color = color[0]+color[0] + color[1]+color[1] + color[2]+color[2];
    var m = color.match(color.length == 6 ? /(\S{2})/g : /(\S{1})/g);
    if (m) var r = parseInt(m[0], 16), g = parseInt(m[1], 16), b = parseInt(m[2], 16);
  }
  if (isRGB) {
    var m = color.match(/(\d+){3}/g);
    if (m) var r = m[0], g = m[1], b = m[2];
  }
  if (typeof r != "undefined") return ((r*299)+(g*587)+(b*114))/1000;
}
