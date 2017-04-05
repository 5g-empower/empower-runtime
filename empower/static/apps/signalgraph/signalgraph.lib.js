jQuery(document).ready(function($){

function send_rrc_req() {

    var selected_ue = $("#ueSelect :selected").val();
    var sel_ue_text = $("#ueSelect :selected").text();

    if (selected_ue !== "" && sel_ue_text.indexOf("LTE") !== -1) {

        var url = "/api/v1/tenants/" + tenant_id + "/vbs_rrc_stats";

        var data = '{\
            "version": "1.0",\
            "vbs": "00:00:00:00:0E:21",\
            "ue":' + selected_ue + ',\
            "meas_req": {\
            "rat_type": "EUTRA",\
            "cell_to_measure": [],\
            "blacklist_cells": [],\
            "bandwidth": 50,\
            "carrier_freq": 6400,\
            "report_type": "periodical_ref_signal",\
            "threshold1" : {\
                              "type": "RSRP",\
                              "value": 20\
                          },\
             "threshold2" : {\
                              "type": "RSRP",\
                              "value": 50\
                          },\
            "report_interval": 10,\
            "trigger_quantity": "RSRP",\
            "num_of_reports": "infinite",\
            "max_report_cells": 3,\
            "a3_offset": 5\
            }\
        }'

        $.ajax({
            url: url,
            type: 'POST',
            dataType: 'json',
            data: data,
            cache: false,
            beforeSend: function (request) {
                request.setRequestHeader("Authorization", "Basic Zm9vOmZvbw==");
            },
            statusCode: {
                201: function (data) {
                },
                400: function (data) {
                    alert(data.responseJSON.message);
                },
                404: function (data) {
                    alert('Component not found');
                },
                500: function (data) {
                    alert('Internal error');
                }
            }
        });
    }
}

$("#ueSelect").on("click", send_rrc_req);

/* SVG for D3 dimensions. */
var area_width  = 550,
    area_height = 760,
    colors = d3.scale.category20();

/* Nodes and links of the graph. */
var nodes = [],
    links = [];

var svg = d3.select('#graphRow')
    .append('svg')
    .attr('class', 'nw_graph')
    .attr('width', area_width)
    .attr('height', area_height);

var p, gl, gwt, gue, gsta;

/* Handles to link and node element groups. */
var nw_paths = svg.append('svg:g').selectAll('.link'),
    nw_enbs = svg.append('svg:g').selectAll('.enb'),
    nw_wtps = svg.append('svg:g').selectAll('.wtp'),
    nw_ues = svg.append('svg:g').selectAll('.ue'),
    nw_sta = svg.append('svg:g').selectAll('.sta');

/* Introduce force layout in the graph. */
var force = d3.layout.force()
    .size([area_width, area_height])
    .charge(-400)
    .linkDistance(60)
    .on("tick", tick);

/* Introduce drag event. */
var drag = force.drag()
    .on("dragstart", dragstart);

/* Define 'div' for tooltips */
var tp_div = d3.select('body')
    .append('div')
    .attr('class', 'tooltip')
    .style('opacity', 0);

var signalChart = c3.generate({
    bindto: '#chartRow',
    data: {
        columns: [
        ],
        type: 'spline'
    },
    legend: {
        show: false
    }
});

fetchSignalData(tenant_id);

function fetchSignalData(tenant_id) {

    setTimeout(function () {

        $.getJSON("/api/v1/tenants/" + tenant_id + "/components/empower.apps.signalgraph.signalgraph", function(data) {
            /* Process the data here after receiving from app.*/
            if (data == null) {
                return;
            }

            var graph_data = data['graphData']

            var existing_nodes = nodes.slice(0);

            links.splice(0, links.length);
            nodes.splice(0, nodes.length);

            /* Iterate through already existing nodes. */
            for (var k in existing_nodes) {
                /* Existing node. */
                var en = existing_nodes[k];

                for (var i in graph_data.nodes) {
                    /* Node from API JSON result. */
                    var n = graph_data.nodes[i];

                    if (en.node_id === n.node_id && en.entity === n.entity) {
                        var node = {
                            id: n.id,
                            node_id: n.node_id,
                            entity: n.entity,
                            tooltip: n.tooltip,
                            mac: n.mac,
                            x: en.x,
                            y: en.y,
                            fixed: en.fixed
                           };
                        nodes.push(node);
                        graph_data.nodes.splice(i, 1);
                        break;
                    }
                }
            }

            /* Whatever nodes remains in graph_data should be added to nodes. */
            for (var i in graph_data.nodes) {
                var n = graph_data.nodes[i];
                var node = {
                            id: n.id,
                            node_id: n.node_id,
                            entity: n.entity,
                            tooltip: n.tooltip,
                            mac: n.mac,
                            x: n.x,
                            y: (area_height - n.y),
                            fixed: false
                           };
                nodes.push(node);
            }

            /* Add links from graph_data. */
            for (var i in graph_data.links) {
                var l = graph_data.links[i];

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

            updateSignalGraph();
            loadUEsSelectBox();
            fetchSignalData(tenant_id);
        });

    }, 5000);

}

/* Update graph. */
function updateSignalGraph() {

    var g_nodes = nodes.slice(0);
    var g_links = links.slice(0);

    /* Setting SVG background color to white.*/
    d3.select('svg')
        .style('background-color', '#FFFFFF');

    force
    .nodes(g_nodes)
    .links(g_links);

    nw_paths = nw_paths.data(g_links)

    nw_paths.enter().append('line')
            .attr('class', 'link')
            .style('stroke', function(d) { return d.color; })
            .style('stroke-width', function(d) { return d.width; })
            .classed('neigh_cell', function(d) { return (d.width == 4); });

    nw_paths.on("mouseover", function(d) {
                tp_div.transition()
                    .duration(500)
                    .style("opacity", 0);
                tp_div.transition()
                    .duration(200)
                    .style("opacity", .9);
                if (d.entity === "lte") {
                    tp_div .html("<p>" + "RSRP: " + d.rsrp + "</br>" +
                              "RSRQ: " + d.rsrq + "</p>")
                        .style("left", (d3.event.pageX) + "px")
                        .style("top", (d3.event.pageY - 28) + "px");
                } else {
                    tp_div .html("RSSI: " + d.rssi)
                        .style("left", (d3.event.pageX) + "px")
                        .style("top", (d3.event.pageY - 28) + "px");
                }
            });

    nw_paths.style('stroke', function(d) { return d.color; })
            .style('stroke-width', function(d) { return d.width; })
            .classed('neigh_cell', function(d) { return (d.width == 4); });

    nw_paths.exit().remove();

    nw_enbs = nw_enbs.data(g_nodes.filter(function(d) {
                                            return d.entity === "enb";
                                        }),
                                        function(d) {
                                            return d.id;
                                        });

    nw_enbs.enter()
            .append('svg:image')
            .attr('class', 'enb')
            .attr('xlink:href', "/static/apps/signalgraph/bs.png")
            .attr('width', 50)
            .attr('height', 50)
            .on("dblclick", dblclick)
            .call(drag);

    nw_enbs.on("mouseover", function(d) {
                tp_div.transition()
                    .duration(500)
                    .style("opacity", 0);
                tp_div.transition()
                    .duration(200)
                    .style("opacity", .9);
                tp_div .html(d.tooltip + ": " + d.node_id)
                    .style("left", (d3.event.pageX) + "px")
                    .style("top", (d3.event.pageY - 28) + "px");
            });

    nw_enbs.attr('xlink:href', "/static/apps/signalgraph/bs.png")
            .attr('width', 50)
            .attr('height', 50);

    nw_enbs.exit().remove();

    nw_wtps = nw_wtps.data(g_nodes.filter(function(d) {
                                            return d.entity === "wtp";
                                        }),
                                        function(d) {
                                            return d.id;
                                        });

    nw_wtps.enter()
            .append('svg:image')
            .attr('class', 'wtp')
            .attr('xlink:href', "/static/apps/signalgraph/wifi.png")
            .attr('width', 40)
            .attr('height', 40)
            .on("dblclick", dblclick)
            .call(drag);

    nw_wtps.on("mouseover", function(d) {
                tp_div.transition()
                    .duration(500)
                    .style("opacity", 0);
                tp_div.transition()
                    .duration(200)
                    .style("opacity", .9);
                tp_div .html(d.tooltip + ": " + d.node_id)
                    .style("left", (d3.event.pageX) + "px")
                    .style("top", (d3.event.pageY - 28) + "px");
            });

    nw_wtps.attr('xlink:href', "/static/apps/signalgraph/wifi.png")
            .attr('width', 40)
            .attr('height', 40);

    nw_wtps.exit().remove();

    nw_ues = nw_ues.data(g_nodes.filter(function(d) {
                                        return d.entity === "ue";
                        }),
                        function(d) {
                                    return d.id;
                        });

    gue = nw_ues.enter()
        .append('svg:g')
        .attr('class', 'ue');

    gue.append('svg:circle')
        .attr('r', 13)
        .style('fill', function(d) { return colors(d.id); })
        .style('stroke', function(d) { return d3.rgb(colors(d.id)).darker().toString(); })
        .style('stroke-width', '2.5px');

    gue.append('svg:text')
        .attr('x', 0)
        .attr('y', 4)
        .attr('class', 'node_id')
        .text(function(d) {
            return "UE";
        });

    gue.on("mouseover", function(d) {
            tp_div.transition()
                .duration(500)
                .style("opacity", 0);
            tp_div.transition()
                .duration(200)
                .style("opacity", .9);
            tp_div .html(d.tooltip + ": " + d.node_id + "(" + d.mac + ")")
                .style("left", (d3.event.pageX) + "px")
                .style("top", (d3.event.pageY - 28) + "px");
        });

    gue.on("dblclick", dblclick)
        .call(drag);

    gue.selectAll('circle')
        .style('fill', function(d) { return colors(d.id); })
        .style('stroke', function(d) { return d3.rgb(colors(d.id)).darker().toString(); })
        .style('stroke-width', '2.5px');

    nw_ues.exit().remove();

    nw_sta = nw_sta.data(g_nodes.filter(function(d) {
                                        return d.entity === "sta";
                        }),
                        function(d) {
                                    return d.id;
                        });

    gsta = nw_sta.enter()
        .append('svg:g')
        .attr('class', 'sta');

    gsta.append('svg:circle')
        .attr('r', 13)
        .style('fill', function(d) { return colors(d.id); })
        .style('stroke', function(d) { return d3.rgb(colors(d.id)).darker().toString(); })
        .style('stroke-width', '2.5px');

    gsta.append('svg:text')
        .attr('x', 0)
        .attr('y', 4)
        .attr('class', 'node_id')
        .text(function(d) {
            return "STA";
        });

    gsta.on("mouseover", function(d) {
            tp_div.transition()
                .duration(500)
                .style("opacity", 0);
            tp_div.transition()
                .duration(200)
                .style("opacity", .9);
            tp_div .html(d.tooltip + ": " + d.node_id)
                .style("left", (d3.event.pageX) + "px")
                .style("top", (d3.event.pageY - 28) + "px");
        });

    gsta.on("dblclick", dblclick)
        .call(drag);

    gsta.selectAll('circle')
        .style('fill', function(d) { return colors(d.id); })
        .style('stroke', function(d) { return d3.rgb(colors(d.id)).darker().toString(); })
        .style('stroke-width', '2.5px');

    nw_sta.exit().remove();

    force.start();
}

function tick() {

    nw_paths.attr("x1", function(d) {
                    return d.source.x;
            })
            .attr("y1", function(d) {
                    return d.source.y;
            })
            .attr("x2", function(d) {
                    return d.target.x;
            })
            .attr("y2", function(d) {
                    return d.target.y;
            });

    nw_enbs.attr('transform', function(d) {
        return 'translate(' + (d.x - 25) + ',' + (d.y - 25) + ')';
    });

    nw_wtps.attr('transform', function(d) {
        return 'translate(' + (d.x - 20) + ',' + (d.y - 20) + ')';
    });

    nw_ues.attr('transform', function(d) {
        return 'translate(' + d.x + ',' + d.y + ')';
    });

    nw_sta.attr('transform', function(d) {
        return 'translate(' + d.x + ',' + d.y + ')';
    });
}

function dblclick(d) {
    d3.select(this).classed("fixed", d.fixed = false);
}

function dragstart(d, i) {
    d3.select(this).classed("fixed", d.fixed = true);
}

function loadUEsSelectBox() {

    if ((nodes !== null) && (nodes !== undefined) && (nodes !== [])) {

        var ue_data = []

        for (var id in nodes) {
            var n = nodes[id];
            if (n["entity"] === 'ue' || n["entity"] === 'sta') {
                var node = {
                                id: n.id,
                                node_id: n.node_id,
                                entity: n.entity,
                                tooltip: n.tooltip,
                                mac: n.mac,
                                x: n.x,
                                y: n.y,
                                fixed: true
                           };
                ue_data.push(node);
            }
        }

        var selectUEMenu = $('#ueSelect');

        var ue_values = [];

        $("#ueSelect option").each(function() {
            ue_values.push($(this).val());
        });

        /* Check whether the selected ue still exists or not. */
        var selected_ue = $("#ueSelect :selected").val();
        if (selected_ue !== "") {
            var ue_exist_flag = false;
            for (ue_index in ue_data) {
                if (selected_ue == ue_data[ue_index].node_id) {
                    ue_exist_flag = true;
                    break;
                }
            }

            if (!ue_exist_flag) {
                $("#ueSelect option").filter(function(index) {
                    return $(this).val() == selected_ue;
                }).remove();
                ue_values.splice(ue_values.indexOf(selected_ue), 1);
            }
        }

        /* Check if all the ues in the options still exist or not. */
        $.each(ue_values, function(index, value) {
            if (value !== ""){
                var exist_flag = false;
                for (ue_index in ue_data) {
                    if (value == ue_data[ue_index].node_id) {
                        exist_flag = true;
                        ue_data.splice(ue_index, 1);
                        break;
                    }
                }
                if (!exist_flag){
                    $("#ueSelect option").filter(function(index) {
                        return $(this).val() == value;
                    }).remove();
                }
            }
        });

        $.each(ue_data, function(index, ue) {
            if (ue.entity === 'ue') {
                selectUEMenu.append("<option value= "+ ue.node_id +">" + ue.node_id + " (LTE UE)" + "</option>");
            } else {
                selectUEMenu.append("<option value= "+ ue.node_id +">" + ue.node_id + " (Wifi station)" + "</option>");
            }
        });
    }
}

var data_set = {};
var prevStatType = "";
var prevSelected_ue = "";

function updateSignalChart() {

    setTimeout(function() {

        var statsType = $('#statsType input:radio:checked').val();
        var selected_ue = $("#ueSelect :selected").val();

        if ((links === null) || (links === undefined) ||
            (selected_ue === null) || (selected_ue === "") ||
            (statsType === "") || (statsType === null) ||
            (prevStatType !== statsType && prevStatType !== "") ||
            (prevSelected_ue !== selected_ue && prevSelected_ue !== "")) {

            signalChart.unload();
            prevStatType = "";
            prevSelected_ue = "";
            data_set = {};

        } else {

            var ls_copy = links.slice(0);
            var ls = [];

            prevSelected_ue = selected_ue;
            prevStatType = statsType;

            if (statsType !== 'rssi') {

                for (var id in ls_copy) {
                    var li = ls_copy[id];
                    if (li["entity"] === "lte" &&
                        ((li["source"].node_id == selected_ue)
                                || (li["target"].node_id == selected_ue))) {
                        ls.push(li);
                    }
                }

                for (var i in ls) {

                    var l = ls[i];

                    if (l["rsrp"] === null) {
                        continue;
                    }

                    if (l["rsrq"] === null) {
                        continue;
                    }

                    var index = null;

                    if (l["source"].node_id == selected_ue) {
                        index = l["target"].tooltip + ":" + l["target"].node_id.toString();
                    } else {
                        index = l["source"].tooltip + ":" + l["source"].node_id.toString();
                    }
                    if (statsType === 'rsrp') {

                        if (!(index in data_set)) {
                            data_set[index] = [index, l["rsrp"]];
                        } else {
                            data_set[index].push(l["rsrp"]);
                            if (data_set[index].length > 30) {
                                /* Remove first object*/
                                data_set[index].splice(1, 1);
                            }
                        }

                        signalChart.load({
                            columns: [
                                data_set[index]
                            ]
                        });
                    } else {

                        if (!(index in data_set)) {
                            data_set[index] = [index, l["rsrq"]];
                        } else {
                            data_set[index].push(l["rsrq"]);
                            if (data_set[index].length > 30) {
                                /* Remove first object*/
                                data_set[index].splice(1, 1);
                            }
                        }

                        signalChart.load({
                            columns: [
                                data_set[index]
                            ]
                        });
                    }
                }
            } else if ((links != null) && (statsType === 'rssi')) {

                for (var id in ls_copy) {
                    var li = ls_copy[id];

                    if (li["entity"] === "wifi" &&
                        ((li["source"].node_id == selected_ue)
                                || (li["target"].node_id == selected_ue))) {
                        ls.push(li);
                    }
                }

                for (var i in ls) {

                    var l = ls[i];

                    if (l["rssi"] === null) {
                        continue;
                    }

                    var index = null;

                    if (l["source"].node_id == selected_ue) {
                        index = l["target"].tooltip + ":" + l["target"].node_id.toString();
                    } else {
                        index = l["source"].tooltip + ":" + l["source"].node_id.toString();
                    }

                    if (!(index in data_set)) {
                        data_set[index] = [index, l["rssi"]];
                    } else {
                        data_set[index].push(l["rssi"]);
                        if (data_set[index].length > 30) {
                            /* Remove first object*/
                            data_set[index].splice(1, 1);
                        }
                    }

                    signalChart.load({
                        columns: [
                            data_set[index]
                        ]
                    });
                }
            }
        }
        updateSignalChart();
    }, 3000);
}

updateSignalChart();

});
