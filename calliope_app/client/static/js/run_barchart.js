
function render_barcharts(input_data) {

    // Build Plotly Layers
    var layers = [];
    metrics.slice().reverse().forEach((metric, i) => {
      if (input_data[metric] == undefined) { return };
      if (input_data[metric]['barchart'] == undefined) { return };
      var data = input_data[metric]['barchart'];
      var c_units = input_data[metric]['units'];
      data.layers_ctx.forEach(function(layer) {
          var trace = {
              x: [layer.name], y: layer.y, xaxis: 'x' + (i + 1), yaxis: 'y' + (i + 1),
              name: layer.name,
              type: 'bar',
              marker: { opacity: 0.5, color: layer.color + '33', line: { color: layer.color, width: 2 } },
              hovertemplate: '<b>%{y}</b> ' + units[units.length - 1 - i].replace('[[rate]]',c_units['rate']).replace('[[quantity]]',c_units['quantity'])
                                 + ' (Maximum Constraint) <br>' + layer.name + '<extra></extra>',
          };
          layers.push(trace);
      })
      data.layers.forEach(function(layer) {
          var trace = {
              x: [layer.name], y: layer.y, xaxis: 'x' + (i + 1), yaxis: 'y' + (i + 1),
              name: layer.name,
              type: 'bar',
              marker: { color: layer.color, line: { color: 'silver', width: 1 } },
              hovertemplate: '<b>%{y}</b> ' + units[units.length - 1 - i].replace('[[rate]]',c_units['rate']).replace('[[quantity]]',c_units['quantity'])
                                 + '<br>' + layer.name + '<extra></extra>',
          };
          layers.push(trace);
      })
    });

    // Layout
    var layout = {plot_bgcolor: 'transparent',
                  paper_bgcolor: 'transparent',
                  hovermode: 'x',
                  xaxis:  { visible: false },
                  xaxis2: { visible: false },
                  xaxis3: { visible: false },
                  xaxis4: { visible: false },
                  xaxis5: { visible: false },
                  xaxis6: { visible: false },
                  xaxis7: { visible: false },
                  xaxis8: { visible: false },
                  yaxis:  { title: { text: labels[7] }, domain: [0.03, 0.13], gridcolor: "#3b3b3b", gridwidth: 1, type: 'log' },
                  yaxis2: { title: { text: labels[6] }, domain: [0.15, 0.25], gridcolor: "#3b3b3b", gridwidth: 1, type: 'log' },
                  yaxis3: { title: { text: labels[5] }, domain: [0.27, 0.37], gridcolor: "#3b3b3b", gridwidth: 1, type: 'log' },
                  yaxis4: { title: { text: labels[4] }, domain: [0.39, 0.49], gridcolor: "#3b3b3b", gridwidth: 1, type: 'log' },
                  yaxis5: { title: { text: labels[3] }, domain: [0.51, 0.61], gridcolor: "#3b3b3b", gridwidth: 1, type: 'log' },
                  yaxis6: { title: { text: labels[2] }, domain: [0.63, 0.73], gridcolor: "#3b3b3b", gridwidth: 1, type: 'log' },
                  yaxis7: { title: { text: labels[1] }, domain: [0.75, 0.85], gridcolor: "#3b3b3b", gridwidth: 1, type: 'log' },
                  yaxis8: { title: { text: labels[0] }, domain: [0.87, 0.97], gridcolor: "#3b3b3b", gridwidth: 1, type: 'log' },
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
