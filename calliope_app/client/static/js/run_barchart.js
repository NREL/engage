
function render_barchart(data, units, redraw) {

    if (data == undefined) { $('#viz_outputs_barchart').html(""); return };

    var layers = [];

    data.layers.forEach(function(layer) {
        var trace = {
            x: data.base.x,
            y: layer.y,
            name: layer.name,
            type: 'bar',
            marker: {
              color: layer.color,
              line: {
                color: 'transparent',
                width: 1
              }
            },
            hovertemplate: '<b>%{y}</b> ' + units + '<br>' + layer.name + '<extra></extra>',
        };
        layers.push(trace);
    })

    var layout = {plot_bgcolor: 'transparent',
                  paper_bgcolor: 'transparent',
                  hovermode: 'closest',
                  xaxis: {
                    gridcolor: "#3b3b3b",
                    gridwidth: 1,
                    type: 'category'
                  },
                  yaxis: {
                    gridcolor: "#3b3b3b",
                    gridwidth: 1,
                    type: 'log'
                  },
                  bargap: 0,
                  // barmode: 'relative',
                  // showlegend: (data.layers.length > 1),
                  showlegend: false,
                  legend: {
                    traceorder: 'reversed',
                    bgcolor: '#1a1b1bde',
                    bordercolor: '#FFFFFF',
                    borderwidth: 1
                  },
                  margin: {
                    l: 80,
                    r: 30,
                    t: 10,
                    b: 40
                  },
                  font: {
                    color: 'white'
                  }};

    var config = {responsive: true}

    Plotly.newPlot('viz_outputs_barchart', layers, layout, config);

}
