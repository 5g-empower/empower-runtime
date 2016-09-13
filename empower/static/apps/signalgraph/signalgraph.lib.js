jQuery(document).ready(function($){

loadVBSPsSelectBox(tenant_id);

/* SVG for D3 dimensions. */
var area_width  = 550,
    area_height = 680,
    colors = d3.scale.category10();

/* Nodes and links of the graph. */
var nodes = [],
    links = [];

var svg = d3.select('#graphRow')
    .append('svg')
    .attr('width', area_width)
    .attr('height', area_height);

/* Handles to link and node element groups. */
var paths = svg.append('svg:g'),
    enbs = svg.append('svg:g'),
    wtps = svg.append('svg:g'),
    ues = svg.append('svg:g');

/* Define 'div' for tooltips */
var div = d3.select('body')
    .append('div')
    .attr('class', 'tooltip')
    .style('opacity', 0);

/* Mouse event vars. */
var selected_node = null,
    mousedown_node = null;

fetchSignalData(tenant_id);

function fetchSignalData(tenant_id) {

    setTimeout(function () {

        $.getJSON("/api/v1/tenants/" + tenant_id + "/components/empower.apps.signalgraph.signalgraph", function(data) {
            /* Process the data here after receiving from app.*/
            if (data == null) {
                return;
            }

            /* Clean the nodes and link arrays. */
            nodes.splice(0, nodes.length);
            links.splice(0, links.length);

            var graph_data = data['graphData']

            Object.keys(graph_data).forEach(function(vbs) {

                var selected_vbsp = $("#vbsSelect :selected").val();

                if ((selected_vbsp !== "") && (selected_vbsp == vbs)) {

                    for (var i in graph_data[vbs].nodes) {
                        var n = graph_data[vbs].nodes[i];
                        var node = {
                                    id: n.id,
                                    node_id: n.node_id,
                                    entity: n.entity,
                                    tooltip: n.tooltip,
                                    x: n.x,
                                    y: (area_height - n.y),
                                    fixed: true
                                   };
                        nodes.push(node);
                    }

                    for (var i in graph_data[vbs].links) {
                        var l = graph_data[vbs].links[i];

                        var source, target;

                        for (var m in nodes) {
                            if (nodes[m].id == l.src) {
                                source = nodes[m];
                            }
                            if (nodes[m].id == l.dst) {
                                target = nodes[m];
                            }
                        }

                        var link = {
                            source: source,
                            target: target,
                            rsrp: l.rsrp,
                            rsrq: l.rsrq,
                            rssi: l.rssi,
                            color: l.color,
                            width: l.width,
                            entity: l.entity
                        }
                        links.push(link);
                    }
                }
            });
            updateSignalGraph();
            fetchSignalData(tenant_id);
        });

    }, 3000);

}


/* Update graph. */
function updateSignalGraph() {

    /* Setting SVG background color to white.*/
    d3.select('svg')
        .style('background-color', '#FFFFFF');

    /* Grouping of links. */
    var p = paths.selectAll('path').data(links);

    /* Adding new links. */
    p.enter().append('svg:path')
        .attr('class', 'link')
        .attr('d', function(d) {
            return 'M' + d.source.x + ',' + d.source.y +
                   'L' + d.target.x + ',' + d.target.y;
        })
        .style('stroke', function(d) { return d.color; })
        .style('stroke-width', function(d) { return d.width; })
        .classed('neigh_cell', function(d) { return (d.width == 4); })
        .on("mouseover", function(d) {
            div.transition()
                .duration(500)
                .style("opacity", 0);
            div.transition()
                .duration(200)
                .style("opacity", .9);
            if (d.entity === "lte") {
                div .html("<p>" + "RSRP: " + d.rsrp + "</br>" +
                          "RSRQ: " + d.rsrq + "</p>")
                    .style("left", (d3.event.pageX) + "px")
                    .style("top", (d3.event.pageY - 28) + "px");
            } else {
                div .html("RSSI: " + d.rssi)
                    .style("left", (d3.event.pageX) + "px")
                    .style("top", (d3.event.pageY - 28) + "px");
            }
        });

    /* Removing old links. */
    p.exit().remove();

    /* LTE base stations group. */
    var es = enbs
        .selectAll('g')
        .data(nodes.filter(function(d) { return d.entity === "enb"; }));

    /* Adding new base stations. */
    var gl = es.enter().append('svg:g');

    gl.attr('transform', function(d) {
        return 'translate(' + (d.x - 25) + ',' + (d.y - 25) + ')';
    });

    gl.append('svg:image')
        .attr('class', 'enb')
        .attr('xlink:href', "/static/apps/signalgraph/bs.png")
        .attr('width', 50)
        .attr('height', 50)
        .on("mouseover", function(d) {
            div.transition()
                .duration(500)
                .style("opacity", 0);
            div.transition()
                .duration(200)
                .style("opacity", .9);
            div .html(d.tooltip + ": " + d.node_id)
                .style("left", (d3.event.pageX) + "px")
                .style("top", (d3.event.pageY - 28) + "px");

            // enlarge target node
            d3.select(this).attr('transform', 'scale(1.2)');
        })
        .on('mouseout', function(d) {
            // unenlarge target node
            d3.select(this).attr('transform', '');
        });

    /* Remove old base stations. */
    es.exit().remove();

    /* WTPs group. */
    var ws = wtps
        .selectAll('g')
        .data(nodes.filter(function(d) { return d.entity === "wtp"; }));

    /* Adding new WTPs. */
    var gwt = ws.enter().append('svg:g');

    gwt.attr('transform', function(d) {
        return 'translate(' + (d.x - 20) + ',' + (d.y - 20) + ')';
    });

    gwt.append('svg:image')
        .attr('class', 'wtp')
        .attr('xlink:href', "/static/apps/signalgraph/wifi.png")
        .attr('width', 40)
        .attr('height', 40)
        .on("mouseover", function(d) {
            div.transition()
                .duration(500)
                .style("opacity", 0);
            div.transition()
                .duration(200)
                .style("opacity", .9);
            div .html(d.tooltip + ": " + d.node_id)
                .style("left", (d3.event.pageX) + "px")
                .style("top", (d3.event.pageY - 28) + "px");

            // enlarge target node
            d3.select(this).attr('transform', 'scale(1.2)');
        })
        .on('mouseout', function(d) {
            // unenlarge target node
            d3.select(this).attr('transform', '');
        });

    /* Remove old WTPs. */
    ws.exit().remove();

    /* UEs group. */
    var us = ues
        .selectAll('g')
        .data(nodes.filter(function(d) { return d.entity === "ue"; }));

    /* Update existing nodes (selected visual states)*/
    us.selectAll('circle')
        .style('fill', function(d) { return (d === selected_node) ? d3.rgb(colors(d.id)).brighter().toString() : colors(d.id); });

    /* Adding new UEs. */
    var gue = us.enter().append('svg:g');

    gue.attr('transform', function(d) {
        return 'translate(' + d.x + ',' + d.y + ')';
    });

    gue.append('svg:circle')
        .attr('class', 'ue')
        .attr('r', 13)
        .style('fill', function(d) { return (d === selected_node) ? d3.rgb(colors(d.id)).brighter().toString() : colors(d.id); })
        .style('stroke', function(d) { return d3.rgb(colors(d.id)).darker().toString(); })
        .style('stroke-width', '2.5px')
        .on("mouseover", function(d) {
            div.transition()
                .duration(500)
                .style("opacity", 0);
            div.transition()
                .duration(200)
                .style("opacity", .9);
            div .html(d.tooltip + ": " + d.node_id)
                .style("left", (d3.event.pageX) + "px")
                .style("top", (d3.event.pageY - 28) + "px");

            // enlarge target node
            d3.select(this).attr('transform', 'scale(1.2)');
        })
        .on('mouseout', function(d) {
            // unenlarge target node
            d3.select(this).attr('transform', '');
        })
        .on('mousedown', function(d) {
            // select node
            mousedown_node = d;

            if(mousedown_node === selected_node) {
                selected_node = null;
            }
            else {
                selected_node = mousedown_node;
            }
            updateSignalGraph();
        });

    /* Show UE IDs. */
    gue.append('svg:text')
        .attr('x', 0)
        .attr('y', 4)
        .attr('class', 'node_id')
        .text(function(d) {
            return "UE";
        });

    /* Remove old UEs. */
    us.exit().remove();
}

function loadVBSPsSelectBox(tenant_id) {

    setTimeout(function() {

        $.getJSON("/api/v1/tenants/" + tenant_id + "/vbses", function(data) {

            var selectVBSPMenu = $('#vbsSelect');

            var vbsp_values = [];

            $("#vbsSelect option").each(function() {
                vbsp_values.push($(this).val());
            });

            /* Check whether the selected vbsp still exists or not. */
            var selected_vbsp = $("#vbsSelect :selected").val();
            if (selected_vbsp !== "") {
                var vbsp_exist_flag = false;
                for (vbsp_index in data) {
                    if (selected_vbsp == data[vbsp_index].addr) {
                        vbsp_exist_flag = true;
                        break;
                    }
                }

                if (!vbsp_exist_flag){
                    $("#vbsSelect option").filter(function(index) {
                        return $(this).val() == selected_vbsp;
                    }).remove();
                    vbsp_values.splice(vbsp_values.indexOf(selected_vbsp),1);
                }
            }

            /* Check if all the vbsp in the options still exist or not. */
            $.each(vbsp_values, function(index, value) {
                if (value !== ""){
                    var exist_flag = false;
                    for (vbsp_index in data) {
                        if (value == data[vbsp_index].addr) {
                            exist_flag = true;
                            data.splice(vbsp_index,1);
                            break;
                        }
                    }
                    if (!exist_flag){
                        $("#vbsSelect option").filter(function(index) {
                            return $(this).val() == value;
                        }).remove();
                    }
                }
            });

            $.each(data, function(index, vbsp) {
                selectVBSPMenu.append("<option value= "+ vbsp.addr +">" + vbsp.label + " (" + vbsp.addr + ")" + "</option>");
            });
            loadVBSPsSelectBox(tenant_id);
        });
    }, 3000);
}

var signalChart = c3.generate({
    bindto: '#chartRow',
    data: {
        x: 'time',
        columns: [
            ['time', null]
        ]
    }
});

function updateSignalChart() {

    var prevStatType = "";

    setTimeout(function() {

        var selected_vbsp = $("#vbsSelect :selected").val();
        var statsType = $('#statsType input:radio:checked').val();

        if ((selected_vbsp === "") || (selected_vbsp === null) ||
                                                    (selected_node === null)) {
            signalChart.unload();
            prevStatType = "";
            updateSignalChart();
        } else {
            $.getJSON("/api/v1/vbses/" + selected_vbsp + "/ues/" + selected_node.node_id,

                function(data) {

                /* Clear chart if switching from different stats type. */
                if (prevStatType !== statsType) {
                    signalChart.unload();
                }
                prevStatType = statsType;

                var date_now = new Date();
                var time_now = date_now.getTime();

                /* We get {"message": "404: *****"} in case of unsuccessful req.
                 *
                */
                if ((!data.message) && (data != null) &&
                                                    (statsType !== 'rssi')) {

                    signalChart.load({
                                columns: [
                                    ['time', time_now]
                                ]
                    });

                    if (statsType === 'rsrp') {
                        signalChart.load({
                                    columns: [
                                        ['prsrp', data['primary_cell_rsrp']]
                                    ]
                        });
                    } else {
                        signalChart.load({
                                    columns: [
                                        ['prsrq', data['primary_cell_rsrq']]
                                    ]
                        });
                    }

                    var meas = data["rrc_meas"]

                    if (meas != null) {

                        Object.keys(meas).forEach(function(cell) {

                            var index = 'PCI:' + cell.toString();

                            if (statsType === 'rsrp') {
                                signalChart.load({
                                    columns: [
                                        [index, meas[cell].rsrp]
                                    ]
                                });
                            } else {
                                signalChart.load({
                                    columns: [
                                        [index, meas[cell].rsrq]
                                    ]
                                });
                            }
                        });
                    }
                }
                updateSignalChart();
            }).fail(function(jqXHR) {
                if (jqXHR.status == 404) {
                    updateSignalChart();
                } else {
                    updateSignalChart();
                }
            });
        }
    }, 3000);
}

updateSignalChart();

});