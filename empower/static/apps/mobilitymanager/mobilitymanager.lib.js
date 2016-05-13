function refreshWTPs() {
    $.getJSON("/api/v1/tenants/" + tenant_id + "/wtps",
        function(data) {
            for (node in data) {
                var idWtp = data[node].addr
                if (!wtps[idWtp]) {
                    wtps[idWtp] = data[node]
                    wtps[idWtp]['lvaps'] = {}
                    wtps[idWtp].connection = data[node].connection
                    wtps[idWtp].feed = data[node].feed
                    wtpUp(idWtp)
                    continue
                }
                if (wtps[idWtp].connection && !data[node].connection) {
                    wtpDown(idWtp)
                }
                if (!wtps[idWtp].connection && data[node].connection) {
                    wtpUp(idWtp)
                }
                wtps[idWtp].supports = data[node]. supports

            }
        });
}

function refreshLVAPs() {
    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvaps",
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            console.log("Refreshing LVAPs")
            var table = document.getElementById('stations');
            for (i = table.rows.length - 1; i > 0; i--) {
                table.deleteRow(i);
            }
            if (data.length == 0) {
                var table = document.getElementById('stations');
                var rowCount = table.rows.length;
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 2
                mac.style.textAlign = "center"
                mac.innerHTML = "No LVAPs available in this Tenant"
            }
            for (var stream in data) {
                var table = document.getElementById('stations');
                var row = table.insertRow(table.rows.length);
                var c = 0
                var sta = row.insertCell(c++);
                var lvap_addr = data[stream].addr
                sta.innerHTML = "<img src='/static/apps/mobilitymanager/sta.png' width='100' /><br />" + data[stream].addr + "<br />RB: (" + data[stream].scheduled_on[0].addr + ", " + data[stream].scheduled_on[0].channel + ", " + data[stream].scheduled_on[0].band + ")"
                var aps = row.insertCell(c++);
                var apLogo = ""
                tmp = "<table width='100%'><tr>"
                for (wtp in wtps) {
                    if (wtps[wtp].addr == data[stream].wtp.addr) {
                        apLogo="ap_on.png"
                    } else {
                        apLogo="ap_off.png"
                    }
                    tmp += "<td><img src='/static/apps/mobilitymanager/" + apLogo + "' width='100' /><br />" + wtps[wtp].addr + "<br />RBs: "
                    for (block in wtps[wtp].supports) {
                        tmp += "("+wtps[wtp].supports[block].channel+", "+wtps[wtp].supports[block].band+") "
                        ucqm = wtps[wtp].supports[block].ucqm[lvap_addr]
                        if (ucqm) {
                            var rssi = ucqm.sma_rssi
                        }
                    }
                    tmp += "<br />RSSI: " + rssi
                    tmp += "</td>"
                }
                tmp += "</tr></table>"
                aps.innerHTML = tmp
            }
        },
    });
}
