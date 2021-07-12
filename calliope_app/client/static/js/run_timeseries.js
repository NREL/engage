
function render_timeseries(input_data) {

    // Build Plotly Layers
    var layers = [],
        legend_items = [];
    metrics.slice().reverse().forEach((metric, i) => {
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
              line: { width: 2, color: layer.color },
              hovertemplate: '<b>%{y}</b> ' + units[3 - i] + '<br>' + layer.name + '<extra></extra>',
          };
          layers.push(trace);
          legend_items.push(layer.name);
      });
      if (data.overlay != undefined) {
          var trace = {
              x: ts, y: data.overlay.y, yaxis: 'y' + (i + 1),
              name: data.overlay.name,
              stackgroup: "Secondary1", legendgroup: "Secondary", showlegend: false,
              fillcolor: "transparent", line: { width: 3, color: "black" },
              hovertemplate: '<b>%{y}</b> ' + units[3 - i] + '  ' + data.overlay.name + '<extra></extra>',
          };
          layers.push(trace);
          var trace = {...trace};
          trace.line = { width: 3, color: "white", dash: "dash" };
          trace.stackgroup = "Secondary2";
          trace.legendgroup = "Secondary";
          trace.showlegend = true;
          layers.push(trace);
      };
    });

    // Layout
    var layout = {plot_bgcolor: 'transparent',
                  paper_bgcolor: 'transparent',
                  // hovermode: 'closest',
                  xaxis:  { anchor: 'y4', side: "top", gridcolor: "#3b3b3b", gridwidth: 1, type: 'date' },
                  yaxis:  { title: { text: metrics[3] }, domain: [0.03, 0.22], gridcolor: "#3b3b3b", gridwidth: 1, autorange: true, type: 'linear' },
                  yaxis2: { title: { text: metrics[2] }, domain: [0.28, 0.47], gridcolor: "#3b3b3b", gridwidth: 1, autorange: true, type: 'linear' },
                  yaxis3: { title: { text: metrics[1] }, domain: [0.53, 0.75], gridcolor: "#3b3b3b", gridwidth: 1, autorange: true, type: 'linear' },
                  yaxis4: { title: { text: metrics[0] }, domain: [0.75, 0.97], gridcolor: "#3b3b3b", gridwidth: 1, autorange: true, type: 'linear' },
                  showlegend: true,
                  legend: { traceorder: 'reversed', bgcolor: '#1a1b1bde', bordercolor: '#FFFFFF', borderwidth: 1 },
                  margin: { l: 60, r: 30, t: 40, b: 10 },
                  font: { color: 'white' }};

    var config = {responsive: true};
    Plotly.newPlot('viz_outputs_timeseries', layers, layout, config);

};
