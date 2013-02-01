function draw_force_graph(json_file_name)
{
var width = 960,
    height = 500;

var color = d3.scale.category20();

var force = d3.layout.force()
    .charge(-350)
    .linkDistance(40)
    .size([width, height])
    .gravity(0.2)
    .friction(0.2)
    .theta(1)
    .linkStrength(function(l) {return l.value; });


var svg = d3.select("#chart").append("svg")
    .attr("width", width)
    .attr("height", height);

d3.json(json_file_name, function(json) {
  force
      .nodes(json.nodes)
      .links(json.links)
      .start();

  var link = svg.selectAll("line.link")
      .data(json.links)
    .enter().append("line")
      .attr("class", "link")
      .style("stroke-width", function(d) { return Math.floor(3*d.value)+1; });

  var node = svg.selectAll("circle.node")
      .data(json.nodes)
    .enter().append("circle")
      .attr("class", "node")
      .attr("r", 5)
      .style("fill", function(d) { return color(d.group); })
      .call(force.drag);

  node.append("title")
      .text(function(d) { return d.name; });

  node.attr("data-legend", function(d) { return d.datalegend; });

  force.on("tick", function() {
    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node.attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
  });
});


function try_to_draw_legend() {
    if (svg.selectAll("[data-legend]")[0].length<2){
        setTimeout(try_to_draw_legend,1000)
    }else{
        var legend = svg.append("g")
          .attr("class","legend")
          .attr("transform","translate(50,30)")
          .style("font-size","12px")
          .call(d3.legend);
    }
}
try_to_draw_legend();
}
