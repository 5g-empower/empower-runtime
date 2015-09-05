google.load('visualization', '1', {
    packages: ['gauge']
});

var options = {
    width: 155,
    height: 155,
    redFrom: 9,
    redTo: 10,
    yellowFrom: 7.5,
    yellowTo: 9,
    min: 0,
    max: 10,
};

wtps = {}
lvaps = {}

function refreshLVAPs(data) {
    $.getJSON("/api/v1/tenants/" + tenant_id + "/lvaps",
        function(data) {
            newLvaps = {}
            for (lvap in data) {
                var idLvap = data[lvap].addr
                newLvaps[idLvap] = data[lvap]
            }
            // remove old LVAPs
            for (idLvap in lvaps) {
                if (!newLvaps[idLvap] ||
                    newLvaps[idLvap].wtp.addr != lvaps[idLvap].wtp.addr) {
                    var idWtp = lvaps[idLvap].wtp.addr
                    delete wtps[idWtp]['lvaps'][idLvap]
                    delete lvaps[idLvap]
                    lvapDown(idLvap, idWtp)
                }
            }
            // add new LVAPs
            for (lvap in newLvaps) {
                var idLvap = newLvaps[lvap].addr
                var idWtp = newLvaps[lvap].wtp.addr
                if (!wtps[idWtp]) {
                    continue
                }
                if (!lvaps[idLvap]) {
                    lvaps[idLvap] = newLvaps[lvap]
                    wtps[idWtp]['lvaps'][idLvap] = newLvaps[lvap]
                    lvapUp(idLvap, idWtp)
                }
            }
        });
}

function refreshWTPs(data) {
    $.getJSON("/api/v1/tenants/" + tenant_id + "/wtps",
        function(data) {
            for (node in data) {
                var idWtp = data[node].addr
                if (!wtps[idWtp]) {
                    wtps[idWtp] = data[node]
                    wtps[idWtp]['lvaps'] = {}
                    wtps[idWtp].feed = data[node].feed
                    wtps[idWtp].connection = data[node].connection
                    wtpUp(idWtp)
                }
                if (wtps[idWtp].connection != data[node].connection) {
                    wtps[idWtp].connection = data[node].connection
                    if (wtps[idWtp].connection) {
                        wtpUp(idWtp)
                    } else {
                        wtpDown(idWtp)
                    }
                }
                wtps[idWtp].feed = data[node].feed
            }
        });
}

function loop() {
    console.log("Updating gauges")
    for (idWtp in wtps) {
        if (wtps[idWtp].feed) {
            for (datastream in wtps[idWtp].feed.datastreams) {
                if (wtps[idWtp].feed.datastreams[datastream].id == "power") {
                    var value = wtps[idWtp].feed.datastreams[datastream].current_value
                    var table = google.visualization.arrayToDataTable([
                        ['Label', 'Value'],
                        ['Power [W]', value]
                    ]);
                    wtps[idWtp]['gauge'].draw(table, options);
                }
            }
        }
    }
}

function lvapUp(idLvap, idWtp) {
    console.log("LVAP up event: " + idLvap)
    if (Object.keys(wtps[idWtp].lvaps).length == 1) {
        $("#chart_clients_" + idWtp.replace(/\:/g, '_') + " > div").html("")
    }
    $("#chart_clients_" + idWtp.replace(/\:/g, '_') + " > div").append(('<div id="chart_clients_lvap_' + idLvap.replace(/\:/g, '_') + '" style="display: table-cell;"><img width="70" src="/static/apps/thor/sta.png"/><br />' + newLvaps[lvap].addr + '</div>')).hide().fadeIn(500);
}

function lvapDown(idLvap, idWtp) {
    console.log("LVAP down event: " + idLvap)
    $("#chart_clients_lvap_" + idLvap.replace(/\:/g, '_')).fadeOut(500)
    if (Object.keys(wtps[idWtp].lvaps).length == 0) {
        $("#chart_clients_" + idWtp.replace(/\:/g, '_') + " > div")
            .html("No Clients")
    }
}

function wtpUp(idWtp) {
    if (!wtps[idWtp].feed) {
        return
    }
    if (!wtps[idWtp]['gauge']) {
        $('<tr><td><img id="ap_status_' + idWtp.replace(/\:/g, '_') + '" width="70" src="/static/apps/thor/ap_on.png" /><p>' + idWtp + '<br /></td><td><div class="charts" id="chart_' + idWtp.replace(/\:/g, '_') + '"></div></td><td><div id="chart_clients_' + idWtp.replace(/\:/g, '_') + '" style="width: 100%; display: table;"><div style="display: table-row">No Clients</div></div></div></td></tr>').hide().appendTo('#feeds > tbody:last').fadeIn(500);
        var table = google.visualization.arrayToDataTable([
            ['Label', 'Value'],
            ['[W]', 0.0]
        ]);
        var gauge = new google.visualization.Gauge(document.getElementById("chart_" + idWtp.replace(/\:/g, '_')));
        wtps[idWtp]['gauge'] = gauge
        wtps[idWtp]['gauge'].draw(table, options);
    }
    src = (!wtps[idWtp].connection) ? "/static/apps/thor/ap_off.png" : "/static/apps/thor/ap_on.png"
    $("#ap_status_" + idWtp.replace(/\:/g, '_')).attr("src", src)
}

function wtpDown(idWtp) {
    src = (!wtps[idWtp].connection) ? "/static/apps/thor/ap_off.png" : "/static/apps/thor/ap_on.png"
    $("#ap_status_" + idWtp.replace(/\:/g, '_')).attr("src", src)
}
