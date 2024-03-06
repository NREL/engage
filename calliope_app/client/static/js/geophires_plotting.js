
var params = {'id': job_meta_id};

$.getJSON('/geophires/outputs/', params, function(data) {
  var template_type = data["template_type"];
  $("#template_name").text(template_type);
  var pwells = data["pwells"];
  var plottext = [];
  pwells.forEach((well, index) => {
    var tooltip = "Number of Production Wells: " + well;
    plottext.push(tooltip);
  });

  // Plot 1
  var data1 = [
    {
      x: data["plot1"]['x1'],
      y: data["plot1"]['y1'],
      mode: 'markers',
      type: 'scatter',
      name: 'Individual Geophires Solutions',
      marker: {
        color: pwells, //'green'
      },
      text: plottext,
      hovertemplate: '%{text}<br>Avg. Thermal Capacity: %{x:.2f}(KWth)<br>Subsurface Total Cost: %{y:.2f}($M)',
    },
    {
      x: data["plot1"]['x1_line'],
      y: data["plot1"]['lower_b1_line'],
      mode: 'lines',
      name: data["plot1"]['label_b1'] + '<span style="font-size: 9px">for subsurface cost-to-thermal capacity relation</span>',
      line: {
        dash: 'dashdot',
        width: 4,
        color: 'red'
      }
    }
  ];
  var layout1 = {
    'title': 'Surface Cost-to-Electric Capacity',
    'xaxis': {
      'title': 'Avg. Electric capacity (KWe)'
    },
    'yaxis': {
      'title': 'Subsurface Total Cost ($M)'
    }
  }
  Plotly.plot('plot1', data1, layout1);

  // Plot 2
  var data2 = [
    {
      x: data["plot2"]['x2'],
      y: data["plot2"]['y2'],
      mode: 'markers',
      type: 'scatter',
      name: 'Individual Geophires Solutions',
      marker: {
        color: pwells, //'blue'
      },
      text: plottext,
      hovertemplate: '%{text}<br>Avg. Electric Capacity:%{x:.2f}(KWe)<br>Surface Total Cost: %{y:.2f}($M)',
    },
    {
      x: data["plot2"]['x2_line'],
      y: data["plot2"]['lower_b2_line'],
      mode: 'lines',
      name: data["plot2"]['label_b2'] + '<span style="font-size: 9px">for surface cost-to-electric capacity relation</span>',
      line: {
        dash: 'dashdot',
        width: 4,
        color: 'red'
      }
    }
  ];
  var layout2 = {
    'title': 'Surface O&M Cost-to-Electric Capacity',
    'xaxis': {
      'title': 'Avg. Electric Capacity (KWe)'
    },
    'yaxis': {
      'title': 'Surface O&M Total Cost ($M)'
    }
  }
  Plotly.plot('plot2', data2, layout2);

  // Plot 3
  var data3 = [
    {
      x: data["plot3"]['x3'],
      y: data["plot3"]['y3'],
      mode: 'markers',
      type: 'scatter',
      name: 'Individual Geophires Solutions',
      marker: {
        color: pwells, //'purple'
      },
      text: plottext,
      hovertemplate: '%{text}<br>Avg. Thermal Capacity:%{x:.2f}(KWth)<br>Subsurface Total O&M Cost: %{y:.2f}($M)',
    },
    {
      x: data["plot3"]['x3_line'],
      y: data["plot3"]['lower_b3_line'],
      mode: 'lines',
      name: data["plot3"]['label_b3'] + '<span style="font-size: 9px">for subsurface O&M cost-to-thermal capacity relation</span>',
      line: {
        dash: 'dashdot',
        width: 4,
        color: 'red'
      }
    },
  ];
  var layout3 = {
    'title': ' Reservoir Cost-to-Thermal Capacity',
    'xaxis': {
      'title': 'Avg. Thermal capacity (KWth)'
    },
    'yaxis': {
      'title': 'Reservoir Total Cost ($M)'
    }
  }
  Plotly.plot('plot3', data3, layout3);

  // Plot 4
  var data4 = [
    {
      x: data["plot4"]['x4'],
      y: data["plot4"]['y4'],
      mode: 'markers',
      type: 'scatter',
      name: 'Individual Geophires Solutions',
      marker: {
        color: pwells, //'orange'
      },
      text: plottext,
      hovertemplate: '%{text}<br>Avg. Electric Capacity: %{x:.2f}(KWe)<br>Surface O&M Total Cost: %{y:.2f}($M)',
    },
    {
      x: data["plot4"]['x4_line'],
      y: data["plot4"]['lower_b4_line'],
      mode: 'lines',
      name: data["plot4"]['label_b4'] + '<span style="font-size: 9px">for surface O&M cost-to-electric capacity relation</span>',
      line: {
        dash: 'dashdot',
        width: 4,
        color: 'red'
      }
    }
  ];
  var layout4 = {
    'title': ' Reservoir O&M Cost-to-Thermal Capacity',
    'xaxis': {
      'title': 'Avg. Thermal capacity (KWe)'
    },
    'yaxis': {
      'title': 'Reservoir O&M Total Cost ($M)'
    }
  }
  Plotly.plot('plot4', data4, layout4);
});
