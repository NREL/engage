'use strict';

var total_radius = 40,
    buffer_radius = 10,
    calc_zoom_scale = function(current_zoom) {
        var nodes_scale = 1 / Math.sqrt(nodes.length + 1);
        var map_scale = 2 * Math.pow(1.2 + nodes_scale, current_zoom - initial_map_zoom);
        var scale = nodes_scale * map_scale;
        return scale;
    },
    radius_multiplier = function(d) {
        return 1 + Math.log10(link_counts[d.loc])
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
    stroke_multiplier = 10,
    lat_buffer = 0.02,
    lon_buffer = 0.5,
    techs = [],
    colors = {},
    names = {},
    parents = {},
    tech_groups = {},
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
    timestamps = [],
    max_prod = 100000,
    initial_map_zoom = 1,
    map_bounds = null,
    zoom_scale = 1,
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
    data_loaded = false;

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
    console.log("Setting map style...")
    map_style = $('#map-style').val();
    localStorage.setItem("mapstyle", map_style);
    map.setStyle('mapbox://styles/' + map_style);
}

//---------------- LOAD DATA

function load_data(model_uuid, run_id) {
    console.log('loading data...', model_uuid, run_id);

    // load Mapbox
    $('#viz_outputs_map').html('')
    var center_lat = (min_lat + max_lat) / 2,
        center_lon = (min_lon + max_lon) / 2;
    map = new mapboxgl.Map({
        container: 'viz_outputs_map',
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


    $.ajax({
        url: '/' + LANGUAGE_CODE + '/component/map_outputs/',
        type: 'POST',
        data: {
            'model_uuid': model_uuid,
            'run_id': run_id,
            'csrfmiddlewaretoken': document.getElementsByName('csrfmiddlewaretoken')[0].value
        },
        dataType: 'json',
        complete: function (data) {
            if (data.status != 200) {
                alert('There was a problem getting the map data.');
                return;
            }
            
            if (data_loaded == false) {
                console.log(data.responseJSON);

                // load colors & techs
                data.responseJSON['inputs_colors'].split('\n').slice(0, -1).map(function(line) {
                    var d = line.split(',');
                    colors[d[0]] = d[1];
                    techs.push(d[0]);
                });
                
                // load names
                data.responseJSON['inputs_names'].split('\n').slice(0, -1).map(function(line) {
                    var d = line.split(',');
                    names[d[0]] = d[1];
                });
                
                // load parents & groups
                data.responseJSON['inputs_inheritance'].split('\n').slice(0, -1).map(function(line) {
                    var d = line.split(',');
                    parents[d[0]] = d[1];
                    if (Object.keys(tech_groups).indexOf(d[1]) == -1) {
                        tech_groups[d[1]] = [d[0]];
                    } else {
                        tech_groups[d[1]].push(d[0]);
                    }
                });
                
                // load coordinates
                var lats = [], lons = [];
                data.responseJSON['inputs_loc_coordinates'].split('\n').slice(0, -1).map(function(line) {
                    var d = line.split(',');
                    assign(coordinates, [d[1], d[0]], +d[2]);
                    if (d[0] == 'lat') {
                        lats.push(+d[2])
                    };
                    if (d[0] == 'lon') {
                        lons.push(+d[2])
                    };
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
                data.responseJSON['results_energy_cap'].split('\n').slice(0, -1).map(function(line) {
                    var d = line.split(',');
                    if (techs.includes(d[1])) {
                        nodes.push({
                            'loc': d[0],
                            'tech': d[1],
                            'capacity': +d[2]
                        });
                        locations[d[0]].push(d[1]);
                        assign(capacities, [d[0], d[1]], +d[2]);
                    } else {
                        links.push({
                            'loc1': d[0],
                            'loc2': d[1].split(':')[1],
                            'tech': d[1].split(':')[0],
                            'capacity': +d[2]
                        });
                        
                        // Cache # of links from each node:
                        link_counts[d[0]] ++;
                        
                        assign(trans_capacities, [d[0], d[1].split(':')[0], d[1].split(':')[1]], +d[2]);
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
            data.responseJSON['results_carrier_con'].split('\n').slice(0, -1).map(function(line) {
                var d = line.split(',');
                if (techs.includes(d[1])) {
                    if (!carriers.includes(d[2])) {
                        carriers.push(d[2])
                    }
                    if (!timestamps.includes(d[3])) {
                        timestamps.push(d[3])
                        production[d[3]] = []
                    }
                    production[d[3]].push({
                        'loc': d[0],
                        'tech': d[1],
                        'carrier': d[2],
                        'production': +d[4]
                    });
                } else {
                    if (trans_production[d[3]] == undefined) {
                        trans_production[d[3]] = []
                    };
                    trans_production[d[3]].push({
                        'loc1': d[0],
                        'loc2': d[1].split(':')[1],
                        'tech': d[1].split(':')[0],
                        'carrier': d[2],
                        'production': -d[4]
                    });
                }
            });
            
            // load production
            max_prod = 0;
            var max_prods = {};
            data.responseJSON['results_carrier_prod'].split('\n').slice(0, -1).map(function(line) {
                var d = line.split(',');
                if (!carriers.includes(d[2])) {
                    carriers.push(d[2])
                }
                if (techs.includes(d[1])) {
                    max_prods[d[3]] = (max_prods[d[3]] || 0) + +d[4];
                    production[d[3]].push({
                        'loc': d[0],
                        'tech': d[1],
                        'carrier': d[2],
                        'production': +d[4]
                    });
                } else {
                    // NOTE: USING CONSUMPTION DATA INSTEAD (ABOVE)
                    // trans_production[d[3]].push({
                    //     'loc1': d[0],
                    //     'loc2': d[1].split(':')[1],
                    //     'tech': d[1].split(':')[0],
                    //     'carrier': d[2],
                    //     'production': +d[4]
                    // });
                };
            });
            max_prod = Math.max.apply(Math, Object.values(max_prods));

            data_loaded = true;
            console.log(data);
            main();
        }
    });
}

//---------------- BUILD VISUALIZATION

function main() {
    changeMapStyle();
    zoom_scale = calc_zoom_scale(initial_map_zoom);
    viz = initiate_viz();
    build_viz();
}

function initiate_viz() {
    console.log('1. initiate_viz')
    d3.selectAll("svg").remove();
	
    //---- Initiate the SVG Canvas
    var width = $('#viz_outputs_map').width();
    var height = $('#viz_outputs_map').height();
	
    var svg_main = d3.select(container).append("svg")
        .attr("width", "100%")
        .attr("height", "100%")
        // .call(d3zoom)
        .append("g");

    // Initiate Hatch Fill for Consumption
    svg_main
        .append('defs')
        .append('pattern')
        .attr('id', 'diagonalHatch')
        .attr('patternUnits', 'userSpaceOnUse')
        .attr('width', 8)
        .attr('height', 8)
        .append('path')
        .attr('d', 'M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2')
        .attr('transform', 'scale(2)')
        .attr('stroke', '#fff')
        .attr('stroke-width', 1);

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
        tsScale: tsScale,
        width: width,
        height: height
    };
}

function build_viz() {
    console.log('2. build_viz')
    //---- Draw Static Transmission
    // draw trans_capacities
    d3.selectAll(".trans_capacities").remove();
    viz.main.selectAll(".trans_capacities")
        .data(links)
        .enter().append("line")
        .attr("class", "trans_capacities")
        .attr("stroke-width", 1 + stroke_multiplier * zoom_scale)
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
        .style("stroke", "gray")
        .style("opacity", 0.2)
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
        .attr("fill", "white")
        .attr("stroke", "black")
        .attr("stroke-width", 0.5)
        .attr("d", static_arc)
        .style("opacity", 0.7)
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
	
	// draw capacity datums
    d3.selectAll(".capacity-datum").remove();
    viz.main.selectAll(".capacity-datum")
        .data(nodes)
        .enter().append("line")
        .attr("class", "capacity-datum")
        .attr("transform", function(d) {
            return translate(coordinates[d.loc])
        })
        .attr("x1", 0).attr("y1", function(d) {
            return -get_iRadius(d);
        })
        .attr("x2", 0).attr("y2", function(d) {
            return -get_oRadius(d);
        })
        .attr("stroke-width", 1 + stroke_multiplier * zoom_scale)
        .attr("stroke", function(d) {
            return colors[d.tech]
        })
        .attr("d", static_arc)
        .moveToFront();

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
    .attr("stroke", "black")
    .attr("stroke-width", 0.5)
    .attr("d", dynamic_arc)
        .each(function(d) {
            this._current = d;
        });

    // Draw initial consumption (hatch fill)
    d3.selectAll(".consumption").remove();
    viz.main.selectAll(".consumption")
        .data(production[timestamps[0]])
        .enter().append("path")
        .attr("class", function(d) {
            return "consumption carrier carrier-" + d.carrier
        })
        .attr("transform", function(d) {
            return translate(coordinates[d.loc])
        })
        .attr("fill", "url(#diagonalHatch)")
        .attr("opacity", function(d) {
            if (d.production >= 0) {
                return 0
            } else {
                return 1
            };
        })
        .attr("d", dynamic_arc);

}

//---------------- SUPPORTING FUNCTIONS

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
