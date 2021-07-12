
function render_barcharts(input_data) {

    // Build Plotly Layers
    var layers = [];
    metrics.slice().reverse().forEach((metric, i) => {
      if (input_data[metric] == undefined) { return };
      if (input_data[metric]['barchart'] == undefined) { return };
      var data = input_data[metric]['barchart'];
      data.layers_ctx.forEach(function(layer) {
          var trace = {
              x: [layer.name], y: layer.y, xaxis: 'x' + (i + 1), yaxis: 'y' + (i + 1),
              name: layer.name,
              type: 'bar',
              marker: { opacity: 0.5, color: layer.color + '33', line: { color: layer.color, width: 2 } },
              hovertemplate: '<b>%{y}</b> ' + units[3 - i] + ' (Maximum Constraint) <br>' + layer.name + '<extra></extra>',
          };
          layers.push(trace);
      })
      data.layers.forEach(function(layer) {
          var trace = {
              x: [layer.name], y: layer.y, xaxis: 'x' + (i + 1), yaxis: 'y' + (i + 1),
              name: layer.name,
              type: 'bar',
              marker: { color: layer.color, line: { color: 'transparent', width: 1 } },
              hovertemplate: '<b>%{y}</b> ' + units[3 - i] + '<br>' + layer.name + '<extra></extra>',
          };
          layers.push(trace);
      })
    });

    // Layout
    var layout = {plot_bgcolor: 'transparent',
                  paper_bgcolor: 'transparent',
                  hovermode: 'closest',
                  xaxis:  { visible: false },
                  xaxis2: { visible: false },
                  xaxis3: { visible: false },
                  xaxis4: { visible: false },
                  xaxis5: { visible: false },
                  yaxis:  { title: { text: labels[3] }, domain: [0.03, 0.22], gridcolor: "#3b3b3b", gridwidth: 1, type: 'log' },
                  yaxis2: { title: { text: labels[2] }, domain: [0.28, 0.47], gridcolor: "#3b3b3b", gridwidth: 1, type: 'log' },
                  yaxis3: { title: { text: labels[1] }, domain: [0.53, 0.72], gridcolor: "#3b3b3b", gridwidth: 1, type: 'log' },
                  yaxis4: { title: { text: labels[0] }, domain: [0.75, 0.97], gridcolor: "#3b3b3b", gridwidth: 1, type: 'log' },
                  bargap: 0,
                  barmode: 'overlay',
                  // barmode: 'relative',
                  // showlegend: (data.layers.length > 1),
                  showlegend: false,
                  legend: { traceorder: 'reversed', bgcolor: '#1a1b1bde', bordercolor: '#FFFFFF', borderwidth: 1 },
                  margin: { l: 80, r: 30, t: 40, b: 10},
                  font: { color: 'white' }};

    var config = {responsive: true}

    Plotly.newPlot('viz_outputs_barchart', layers, layout, config);

}
