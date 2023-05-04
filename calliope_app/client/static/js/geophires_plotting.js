
var params = {'id': job_meta_id};

$.getJSON('/geophires/outputs/', params, function(data) {
  // Plot 1
  var data1 = [
    {
      x: data["plot1"]['x1'],
      y: data["plot1"]['y1'],
      mode: 'markers',
      type: 'scatter',
      name: 'Raw Data',
      marker: {
        color: 'green'
      }
    },
    {
      x: data["plot1"]['x1_line'],
      y: data["plot1"]['lower_b1_line'],
      mode: 'lines',
      name: data["plot1"]['label_b1'],
      line: {
        dash: 'dashdot',
        width: 4,
        color: 'red'
      }
    }
  ];
  var layout1 = {
    'title': plant + ' subsurface cost-to-thermal capacity relation',
    'xaxis': {
      'title': 'Avg. Thermal capacity (MWth)'
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
      name: 'Raw Data',
      marker: {
        color: 'blue'
      }
    },
    {
      x: data["plot2"]['x2_line'],
      y: data["plot2"]['lower_b2_line'],
      mode: 'lines',
      name: data["plot2"]['label_b2'],
      line: {
        dash: 'dashdot',
        width: 4,
        color: 'red'
      }
    }
  ];
  var layout2 = {
    'title': plant + ' surface cost-to-electric capacity relation',
    'xaxis': {
      'title': 'Avg. Electric capacity (MWe)'
    },
    'yaxis': {
      'title': 'Surface Total Cost ($M)'
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
      name: 'Raw Data',
      marker: {
        color: 'purple'
      }
    },
    {
      x: data["plot3"]['x3_line'],
      y: data["plot3"]['lower_b3_line'],
      mode: 'lines',
      name: data["plot3"]['label_b3'],
      line: {
        dash: 'dashdot',
        width: 4,
        color: 'red'
      }
    },
  ];
  var layout3 = {
    'title': plant + ' subsurface O&M cost-to-thermal capacity relation',
    'xaxis': {
      'title': 'Avg. Thermal capacity (MWth)'
    },
    'yaxis': {
      'title': 'Subsurface Total O&M Cost ($M)'
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
      name: 'Raw Data',
      marker: {
        color: 'orange'
      }
    },
    {
      x: data["plot4"]['x4_line'],
      y: data["plot4"]['lower_b4_line'],
      mode: 'lines',
      name: data["plot4"]['label_b4'],
      line: {
        dash: 'dashdot',
        width: 4,
        color: 'red'
      }
    }
  ];
  var layout4 = {
    'title': plant + ' surface O&M cost-to-electric capacity relation',
    'xaxis': {
      'title': 'Avg. Electric capacity (MWe)'
    },
    'yaxis': {
      'title': 'Surface O&M Total Cost ($M)'
    }
  }
  Plotly.plot('plot4', data4, layout4);
});
