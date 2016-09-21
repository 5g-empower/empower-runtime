jQuery(document).ready(function($){

function send_rrc_req() {

var selected_ue = $("#ueSelect :selected").val();

    if (selected_ue !== "") {

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
            "carrier_freq": 6300,\
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

            /* Clean the nodes and link arrays. */
            nodes.splice(0, nodes.length);
            links.splice(0, links.length);

            updateSignalGraph();

            var graph_data = data['graphData']

            // Object.keys(graph_data).forEach(function(vbs) {
            if ("nodes" in graph_data) {
                for (var i in graph_data.nodes) {
                    var n = graph_data.nodes[i];
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
            }

            // });

            updateSignalGraph();
            loadUEsSelectBox();
            // updateSignalChart();
            fetchSignalData(tenant_id);
        });

    }, 5000);

}

/* Update graph. */
function updateSignalGraph() {

    /* Setting SVG background color to white.*/
    d3.select('svg')
        .style('background-color', '#FFFFFF');

    /* Grouping of links. */
    var p = paths.selectAll('path').data(links, function(d) { return d.source.id + "-" + d.target.id; });

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
        // .classed('inactive_wtp', function(d) {
        //     return (d.entity === "wifi" && d.width == 4);
        // })
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
        .data(nodes, function(d) { return ((d.node_id).toString() + d.entity); });

    /* Adding new base stations. */
    var gl = es.enter()
                .append('svg:g')
                .filter(function(d) { return d.entity === "enb"; });

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
            // d3.select(this).attr('transform', 'scale(1.2)');
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
        .data(nodes, function(d) { return ((d.node_id).toString() + d.entity); });

    /* Adding new WTPs. */
    var gwt = ws.enter()
                .append('svg:g')
                .filter(function(d) { return d.entity === "wtp"; });

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
            // d3.select(this).attr('transform', 'scale(1.2)');
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
        .data(nodes, function(d) { return ((d.node_id).toString() + d.entity); });

    /* Update existing nodes (selected visual states)*/
    us.selectAll('circle')
        .style('fill', function(d) { return colors(d.id); });

    /* Adding new UEs. */
    var gue = us.enter()
                .append('svg:g')
                .filter(function(d) { return d.entity === "ue"; });

    gue.attr('transform', function(d) {
        return 'translate(' + d.x + ',' + d.y + ')';
    });

    gue.append('svg:circle')
        .attr('class', 'ue')
        .attr('r', 13)
        .style('fill', function(d) { return colors(d.id); })
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
            // d3.select(this).attr('transform', 'scale(1.2)');
        })
        .on('mouseout', function(d) {
            // unenlarge target node
            d3.select(this).attr('transform', '');
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


var UE_MAC_ADDR1 = "A0:39:F7:4C:AB:87"

function loadUEsSelectBox() {

    if ((nodes !== null) && (nodes !== undefined) && (nodes !== [])) {

        var ue_data = []

        for (var id in nodes) {
            var n = nodes[id];
            if (n["entity"] === 'ue') {
                var node = {
                                id: n.id,
                                node_id: n.node_id,
                                entity: n.entity,
                                tooltip: n.tooltip,
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
                ue_values.splice(ue_values.indexOf(selected_ue),1);
            }
        }

        /* Check if all the ues in the options still exist or not. */
        $.each(ue_values, function(index, value) {
            if (value !== ""){
                var exist_flag = false;
                for (ue_index in ue_data) {
                    if (value == ue_data[ue_index].node_id) {
                        exist_flag = true;
                        ue_data.splice(ue_index,1);
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
            selectUEMenu.append("<option value= "+ ue.node_id +">" + ue.node_id + "</option>");
        });
    }
}

var data_set = {};
var prevStatType = "";

function updateSignalChart() {

    setTimeout(function() {

        var statsType = $('#statsType input:radio:checked').val();
        var selected_ue = $("#ueSelect :selected").val();

        if ((links === null) || (links === undefined) ||
                (selected_ue === null) || (selected_ue === "") ||
                    (statsType === "") || (statsType === null) ||
                        (prevStatType !== statsType && prevStatType !== "")) {

            signalChart.unload();
            prevStatType = "";
            data_set = {};

        } else {

            var ls = links.slice(0);

            prevStatType = statsType;

            if (statsType !== 'rssi') {

                for (var id in links) {
                    var li = links[id];
                    if (li["entity"] !== "lte" &&
                        ((li["source"].node_id === selected_ue)
                                    && (li["target"].node_id === selected_ue))) {
                        ls.splice(id, 1);
                    }
                }

                for (var i in ls) {

                    var l = ls[i];

                    var index = null;

                    if (l["source"].node_id === selected_ue) {
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

                for (var id in links) {
                    var li = links[id];
                    if (li["entity"] !== "wifi" &&
                        ((li["source"].node_id === selected_ue)
                                    && (li["target"].node_id === selected_ue))) {
                        ls.splice(id, 1);
                    }
                }

                for (var i in ls) {

                    var l = ls[i];

                    var index = null;

                    if (l["source"].node_id === selected_ue) {
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
