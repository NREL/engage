
function render_timeseries(data, units) {

    var ts = data.base.x.slice(0, 8760),
        layers = [];

    data.layers.forEach(function(layer) {
        var trace = {
            x: ts,
            y: layer.y,
            name: layer.name,
            stackgroup: layer.group,
            fillcolor: layer.color,
            line: {
              width: 2,
              color: layer.color,
            },
            hovertemplate: '<b>%{y}</b> ' + units + '<br>' + layer.name + '<extra></extra>',
        };
        layers.push(trace);
    });
    if (data.overlay != undefined) {
        layers.push({
            x: ts,
            y: data.overlay.y,
            name: data.overlay.name,
            stackgroup: "Secondary",
            fillcolor: "transparent",
            line: {
              width: 3,
              color: "white",
              dash: "dashdot"
            },
            hovertemplate: '<b>%{y}</b> ' + units + '  ' + data.overlay.name + '<extra></extra>',
        });
    };

    var layout = {
                  plot_bgcolor: 'transparent',
                  paper_bgcolor: 'transparent',
                  // hovermode: 'closest',
                  xaxis: {
                    gridcolor: "#3b3b3b",
                    gridwidth: 1,
                    type: 'date'
                  },
                  yaxis: {
                    gridcolor: "#3b3b3b",
                    gridwidth: 1,
                    autorange: true,
                    type: 'linear'
                  },
                  showlegend: true,
                  legend: {
                    // orientation: 'h',
                    traceorder: 'reversed',
                    bgcolor: '#1a1b1bde',
                    bordercolor: '#FFFFFF',
                    borderwidth: 1
                  },
                  margin: {
                    l: 60,
                    r: 30,
                    t: 10,
                    b: 40
                  },
                  font: {
                    color: 'white'
                  }};

    var config = {responsive: true};
    Plotly.newPlot('viz_outputs_timeseries', layers, layout, config);

};
