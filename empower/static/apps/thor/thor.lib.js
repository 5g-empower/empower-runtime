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

function loop() {
    console.log("Updating gauges")
    for (idWtp in wtps) {
        src = (!wtps[idWtp].connection) ? "/static/apps/thor/ap_off.png" : "/static/apps/thor/ap_on.png"
        $("#ap_status_" + idWtp.replace(/\:/g, '_')).attr("src", src)
        if (wtps[idWtp].feed) {
            for (datastream in wtps[idWtp].feed.datastreams) {
                if (wtps[idWtp].feed.datastreams[datastream].id == "power") {
                    var value = wtps[idWtp].feed.datastreams[datastream].current_value
                    var table = google.visualization.arrayToDataTable([
                        ['Label', 'Value'],
                        ['Power [W]', value]
                    ]);
                    if (wtps[idWtp]['gauge']) {
                        wtps[idWtp]['gauge'].draw(table, options);
                    }
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

        idGaugeElm = "chart_" + idWtp.replace(/\:/g, '_')

        $('<tr><td><img id="ap_status_' + idWtp.replace(/\:/g, '_') + '" width="70" src="/static/apps/thor/ap_on.png" /><p>' + idWtp + '<br /></td><td><div class="charts" id="' + idGaugeElm + '"></div></td><td><div id="chart_clients_' + idWtp.replace(/\:/g, '_') + '" style="width: 100%; display: table;"><div style="display: table-row">No Clients</div></div></div></td></tr>').hide().appendTo('#feeds > tbody:last').fadeIn(500);

        var table = google.visualization.arrayToDataTable([
            ['Label', 'Value'],
            ['[W]', 0.0]
        ]);

        gaugeElm = document.getElementById(idGaugeElm)
        wtps[idWtp]['gauge'] = new google.visualization.Gauge(gaugeElm);
        wtps[idWtp]['gauge'].draw(table, options);

    }

}

function wtpDown(idWtp) {
}
