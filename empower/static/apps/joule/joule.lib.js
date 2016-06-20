google.load('visualization', '1', {
    packages: ['corechart']
});

var options = {
    width: 1000,
    height: 240,
    interpolateNulls: true,
    hAxis: {
        title: 'Time [s]',
        format: 'HH:mm:ss',
        titleTextStyle: {
            color: 'black',
            italic: 'false',
            fontSize: 16
        }
    },
    vAxis: {
        viewWindowMode: 'explicit',
        viewWindow: {
            max: 6.00,
            min: 0.00
        },
        title: 'Power [W] ',
        titleTextStyle: {
            color: 'black',
            italic: 'false',
            fontSize: 16
        }
    },
    legend: {
        position: 'top',
        textStyle: {
            color: 'black',
            fontSize: 16
        }
    }
};

displayWindow = 60000
wtps = {}
lvaps = {}

function initialize() {
    runLoader(refreshWTPs)
    runLoader(refreshLVAPs)
    runLoader(loop)
}

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
    $.getJSON("/api/v1/tenants/" + tenant_id + "/components/empower.apps.joule.joule",
        function (data) {
            for (node in data.feeds) {
                var idWtp = data.feeds[node].wtp
                if (!wtps[idWtp])
                    continue
                wtps[idWtp].vfeed = data.feeds[node]
            }
            drawGraphs()
        });
}

samples = {}

function drawGraphs() {

    console.log("Updating graphs")

    for (idWtp in wtps) {

        if (!wtps[idWtp].feed)
            continue

        if (!samples[idWtp]) {
            samples[idWtp] = []
            samples[idWtp].push(['Time', 'Real', 'Virtual'])
            samples[idWtp].push([new Date(), 0, 0])
        }

        var real_at

        for (datastream in wtps[idWtp].feed.datastreams) {

            if (wtps[idWtp].feed.datastreams[datastream].id != "power")
                continue

            var val = wtps[idWtp].feed.datastreams[datastream].current_value
            real_at = new Date(wtps[idWtp].feed.datastreams[datastream].at)
            samples[idWtp].push([real_at, val, null])

        }

        var virtual_at

        for (datastream in wtps[idWtp].vfeed.datastreams) {

            if (wtps[idWtp].vfeed.datastreams[datastream].id != "power")
                continue

            var val = wtps[idWtp].vfeed.datastreams[datastream].current_value
            virtual_at = new Date(wtps[idWtp].vfeed.datastreams[datastream].at)
            samples[idWtp].push([virtual_at, null, val])

        }

        var table = google.visualization.arrayToDataTable(samples[idWtp])

        var last = (real_at > virtual_at) ? real_at : virtual_at
        var min = new Date();
        min.setTime(last.getTime() - displayWindow);

        options.hAxis.viewWindow = {
            min: min,
            max: last
        }

        wtps[idWtp]['line'].draw(table, options);

    }

}

function lvapUp(idLvap, idWtp) {
    console.log("LVAP up event: " + idLvap)
    if (Object.keys(wtps[idWtp].lvaps).length == 1) {
        $("#chart_clients_" + idWtp.replace(/\:/g, '_') + " > div").html("")
    }
    $("#chart_clients_" + idWtp.replace(/\:/g, '_') + " > div").append(('<div id="chart_clients_lvap_' + idLvap.replace(/\:/g, '_') + '" style="display: table-cell;"><img width="70" src="/static/apps/joule/sta.png" title="' + newLvaps[lvap].addr + '"/></div>')).hide().fadeIn(500);
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
    if (!wtps[idWtp]['line']) {
        $('<tr><td><img id="ap_status_' + idWtp.replace(/\:/g, '_') + '" width="70" src="/static/apps/joule/ap_on.png" /><p>' + idWtp + '<br /></td><td><div id="chart_clients_' + idWtp.replace(/\:/g, '_') + '" style="width: 100%; display: table;"><div style="display: table-row">No Clients</div></div></div></td><td><div id="chart_' + idWtp.replace(/\:/g, '_') + '"></div></td></tr>').hide().appendTo('#feeds > tbody:last').fadeIn(500);
        wtps[idWtp]['line'] = new google.visualization.LineChart(document.getElementById("chart_" + idWtp.replace(/\:/g, '_')));
    }
    src = (!wtps[idWtp].connection) ? "/static/apps/joule/ap_off.png" : "/static/apps/joule/ap_on.png"
    $("#ap_status_" + idWtp.replace(/\:/g, '_')).attr("src", src)
}

function wtpDown(idWtp) {
    src = (!wtps[idWtp].connection) ? "/static/apps/joule/ap_off.png" : "/static/apps/joule/ap_on.png"
    $("#ap_status_" + idWtp.replace(/\:/g, '_')).attr("src", src)
}
