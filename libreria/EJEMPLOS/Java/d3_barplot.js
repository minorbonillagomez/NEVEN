// Simple D3 bar chart for RJ2XCL
var barHeight = Math.ceil(height / data.length);

svg.selectAll('rect')
  .data(data)
  .enter().append('rect')
    .attr('width', function(d) { return d * width; })
    .attr('height', barHeight - 1)
    .attr('y', function(d, i) { return i * barHeight; })
    .attr('fill', function(d, i) { 
      var colors = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b'];
      return colors[i % colors.length]; 
    })
    .on('mouseover', function(d) {
      d3.select(this).attr('opacity', 0.7);
    })
    .on('mouseout', function(d) {
      d3.select(this).attr('opacity', 1);
    });

svg.selectAll('text')
  .data(data)
  .enter().append('text')
    .attr('x', function(d) { return d * width + 5; })
    .attr('y', function(d, i) { return i * barHeight + barHeight/2 + 4; })
    .text(function(d) { return (d * 100).toFixed(0) + '%'; })
    .attr('fill', 'white')
    .attr('font-size', '12px');
