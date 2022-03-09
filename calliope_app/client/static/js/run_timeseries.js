
function render_timeseries(input_data) {

    // Build Plotly Layers
    var layers = [],
        legend_items = [];
    metrics.slice().reverse().forEach((metric, i) => {
      console.log(metric);
      console.log(i);
      if (input_data[metric] == undefined) { return };
      if (input_data[metric]['timeseries'] == undefined) { return };
      var data = input_data[metric]['timeseries'],
          ts = data.base.x.slice(0, 8760);
      data.layers.forEach(function(layer) {
          var trace = {
              x: ts, y: layer.y, yaxis: 'y' + (i + 1),
              name: layer.name,
              stackgroup: layer.group,
              showlegend: !legend_items.includes(layer.name),
              legendgroup: layer.name,
              fillcolor: layer.color,
              line: { width: 1, color: 'black' },
              hovertemplate: '<b>%{y}</b> ' + units[units.length - 1 - i] + '&nbsp;&nbsp;&nbsp;&nbsp;%{x}<br>' + layer.name + '<extra></extra>',
          };
          layers.push(trace);
          legend_items.push(layer.name);
      });
      if (data.overlay != undefined) {
          var trace = {
              x: ts, y: data.overlay.y, yaxis: 'y' + (i + 1),
              name: data.overlay.name,
              stackgroup: "Secondary", legendgroup: "Secondary", showlegend: true,
              fillcolor: "transparent", line: { width: 4, color: "white", dash: "dashdot" },
              hovertemplate: '<b>%{y}</b> ' + units[units.length - 1 - i] + '&nbsp;&nbsp;&nbsp;&nbsp;%{x}<br>' + data.overlay.name + '<extra></extra>',
          };
          layers.push(trace);
      };
    });

    // Layout
    var layout = {plot_bgcolor: 'transparent',
                  paper_bgcolor: 'transparent',
                  hovermode: 'x',
                  xaxis:  { anchor: 'y4', side: "top", gridcolor: "#3b3b3b", gridwidth: 1, type: 'date' },
                  yaxis:  { title: { text: metrics[7] }, domain: [0.03, 0.13], gridcolor: "#3b3b3b", gridwidth: 1, autorange: true, type: 'linear' },
                  yaxis2: { title: { text: metrics[6] }, domain: [0.15, 0.25], gridcolor: "#3b3b3b", gridwidth: 1, autorange: true, type: 'linear' },
                  yaxis3: { title: { text: metrics[5] }, domain: [0.27, 0.37], gridcolor: "#3b3b3b", gridwidth: 1, autorange: true, type: 'linear' },
                  yaxis4: { title: { text: metrics[4] }, domain: [0.39, 0.49], gridcolor: "#3b3b3b", gridwidth: 1, autorange: true, type: 'linear' },
                  yaxis5: { title: { text: metrics[3] }, domain: [0.51, 0.61], gridcolor: "#3b3b3b", gridwidth: 1, autorange: true, type: 'linear' },
                  yaxis6: { title: { text: metrics[2] }, domain: [0.63, 0.73], gridcolor: "#3b3b3b", gridwidth: 1, autorange: true, type: 'linear' },
                  yaxis7: { title: { text: metrics[1] }, domain: [0.75, 0.86], gridcolor: "#3b3b3b", gridwidth: 1, autorange: true, type: 'linear' },
                  yaxis8: { title: { text: metrics[0] }, domain: [0.85, 0.97], gridcolor: "#3b3b3b", gridwidth: 1, autorange: true, type: 'linear' },
                  showlegend: true,
                  legend: { traceorder: 'reversed', bgcolor: '#1a1b1bde', bordercolor: '#FFFFFF', borderwidth: 1 },
                  margin: { l: 60, r: 30, t: 40, b: 10 },
                  font: { color: 'white' }};

    var config = {responsive: true};
    console.log(layers);
    Plotly.newPlot('viz_outputs_timeseries', layers, layout, config);

};
