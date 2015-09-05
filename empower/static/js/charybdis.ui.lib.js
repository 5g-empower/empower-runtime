
wtps = {}
lvaps ={}

function loadWTPs(tenant_id) {
    if (tenant_id) {
        url = "/api/v1/tenants/" + tenant_id + "/wtps"
    } else {
        url = "/api/v1/wtps"
    }
    $.ajax({
        url: url,
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            var table = document.getElementById('wtps');
            var rowCount = table.rows.length - 1;
            while (rowCount--) {
                if (rowCount < 0) {
                    break
                }
                table.deleteRow(rowCount);
            }
            if (data.length == 0) {
                var table = document.getElementById('wtps');
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 3
                mac.style.textAlign = "center"
                mac.innerHTML = "Empty"
            }
            for (var stream in data) {
                value = data[stream].addr
                var table = document.getElementById('wtps');
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var c = 0
                var remove = row.insertCell(c++);
                remove.align = "center"
                remove.width = "24px"
                if (tenant_id) {
                    remove.innerHTML = "<img class=\"ctrl\" src=\"/static/images/remove.png\" onClick=\"removeWTP('" + value + "', '" + tenant_id + "')\" />"
                } else {
                    remove.innerHTML = "<img class=\"ctrl\" src=\"/static/images/remove.png\" onClick=\"removeWTP('" + value + "')\" />"
                }
                var flag = row.insertCell(c++);
                flag.align = "center"
                flag.width = "24px"
                if (data[stream]['connection']) {
                    flag.innerHTML = "<img class=\"ctrl\" src=\"/static/images/flag_green.png\"  />"
                } else {
                    flag.innerHTML = "<img class=\"ctrl\" src=\"/static/images/flag_red.png\"  />"
                }
                var mac = row.insertCell(c++);
                mac.innerHTML = data[stream]['label'] + " (" + value + ")"
                if (data[stream]['connection']) {
                    mac.innerHTML += "<div class=\"details\" id=\"wtp_" + stream + "\">"
                    mac.innerHTML += "Resource Blocks: "
                    for (var i in data[stream].supports) {
                        block = data[stream].supports[i]
                        mac.innerHTML += "(" + block.channel + ", " + block.band + ") "
                    }
                    mac.innerHTML +="at " + data[stream]['connection'][0] + ":" + data[stream]['connection'][1] + ", last seen: " + data[stream]['last_seen'] + "<br />"
                    mac.innerHTML += "</div>"
                } else {
                    mac.innerHTML += "<div class=\"details\" id=\"wtp_" + stream + "\">Disconnected</div>"
                }
            }
        },
    });
}

function removeWTP(mac, tenant_id) {
    if (tenant_id) {
        url = "/api/v1/tenants/" + tenant_id + "/wtps/" + mac
    } else {
        url = "/api/v1/wtps/" + mac
    }
    $.ajax({
        url: url,
        type: 'DELETE',
        dataType: 'json',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        success: function (data) {
            loadWTPs()
        },
        statusCode: {
            400: function () {
                alert('Invalid MAC Address');
            },
            400: function () {
                alert('Duplicate MAC Address');
            },
            500: function () {
                alert('Empty MAC Address');
            }
        }
    });
}

function registerWTP(tenant_id) {
    var mac = document.getElementById("wtp_mac").value;
    var label = document.getElementById("wtp_label").value;
    if (tenant_id) {
        url = "/api/v1/tenants/" + tenant_id + "/wtps"
    } else {
        url = "/api/v1/wtps"
    }
    data = '{  "version" : "1.0", "addr" : "' + mac + '", "label" : "' + label + '" }'
    $.ajax({
        url: url,
        type: 'POST',
        dataType: 'json',
        data: data,
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            201: function (data) {
                var table = document.getElementById('wtps');
                var rowCount = table.rows.length - 1;
                var row = table.deleteRow(rowCount);
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 3
                mac.align = "right"
                mac.innerHTML = "<a onClick=\"return addWTP()\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a></td>"
            },
            400: function () {
                alert('Invalid MAC Address');
            },
            409: function () {
                alert('Duplicate MAC Address');
            },
            500: function () {
                alert('Empty MAC Address');
            }
        }
    });
}

function addWTP() {
    var table = document.getElementById('wtps');
    var rowCount = table.rows.length - 1;
    var row = table.deleteRow(rowCount);
    var row = table.insertRow(rowCount);
    var mac = row.insertCell(0);
    tmp = "<ul><li><input onclick=\"this.value=''\" onblur=\" if (this.value == '') this.value='MAC Address' \" size=\"20\" autocapitalize=\"off\" autocorrect=\"off\" class=\"text-input\" id=\"wtp_mac\" type=\"text\" value=\"MAC Address\" />&nbsp;<input onclick=\"this.value=''\" onblur=\" if (this.value == '') this.value='Generic WTP' \" size=\"24\" autocapitalize=\"off\" autocorrect=\"off\" class=\"text-input\" id=\"wtp_label\" type=\"text\" value=\"Generic WTP\" /><div class=\"box\"><img width=\"24\" src=\"/static/images/accept.png\" onClick=\"registerWTP()\"/><img class=\"ctrl\" src=\"/static/images/reject.png\" onClick=\"removeWTPInputBox()\" /></div></li></ul>"
    mac.colSpan = 3
    mac.innerHTML = tmp
}

function removeWTPInputBox() {
    var table = document.getElementById('wtps');
    var rowCount = table.rows.length - 1;
    var row = table.deleteRow(rowCount);
    var row = table.insertRow(rowCount);
    var mac = row.insertCell(0);
    mac.colSpan = 3
    mac.align = "right"
    mac.innerHTML = "<a onClick=\"return addWTP()\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a></td>"
}

function removeMACInputBox(group) {
    var table = document.getElementById(group);
    var rowCount = table.rows.length - 1;
    var row = table.deleteRow(rowCount);
    var row = table.insertRow(rowCount);
    var mac = row.insertCell(0);
    if (group === 'wtps') {
        mac.colSpan = 3
    } else {
        mac.colSpan = 2
    }
    mac.align = "right"
    mac.innerHTML = "<a onClick=\"return addMAC('" + group + "')\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a></td>"
}

function removeMAC(group, mac) {
    $.ajax({
        url: "/api/v1/" + group + "/" + mac,
        type: 'DELETE',
        dataType: 'json',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        success: function (data) {},
        statusCode: {
            400: function () {
                alert('Invalid MAC Address');
            },
            400: function () {
                alert('Duplicate MAC Address');
            },
            500: function () {
                alert('Empty MAC Address');
            }
        }
    });
}


function registerMAC(group) {
    var mac = document.getElementById(group + "_mac").value;
    url = "/api/v1/" + group
    if (group == 'wtps') {
        data = '{  "version" : "1.0", "wtp" : "' + mac + '" }'
    } else {
        data = '{  "version" : "1.0", "sta" : "' + mac + '" }'
    }
    $.ajax({
        url: url,
        type: 'POST',
        dataType: 'json',
        data: data,
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            201: function (data) {
                var table = document.getElementById(group);
                var rowCount = table.rows.length - 1;
                var row = table.deleteRow(rowCount);
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 2
                mac.align = "right"
                mac.innerHTML = "<a onClick=\"return addMAC('" + group +
                    "')\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a></td>"
            },
            400: function () {
                alert('Invalid MAC Address');
            },
            409: function () {
                alert('Duplicate MAC Address');
            },
            500: function () {
                alert('Empty MAC Address');
            }
        }
    });
}

function addMAC(group) {
    var table = document.getElementById(group);
    var rowCount = table.rows.length - 1;
    var row = table.deleteRow(rowCount);
    var row = table.insertRow(rowCount);
    var mac = row.insertCell(0);
    mac.colSpan = 2
    mac.innerHTML = "<ul><li><input autocapitalize=\"off\" autocorrect=\"off\" class=\"text-input\" id=\"" + group + "_mac\" type=\"text\" value=\"\" /><div class=\"box\"><img width=\"24\" src=\"/static/images/accept.png\" onClick=\"registerMAC('" + group + "')\"/><img class=\"ctrl\" src=\"/static/images/reject.png\" onClick=\"removeMACInputBox('" + group + "')\" /></div></li></ul>"
}

function loadMACs(group) {
    $.ajax({
        url: "/api/v1/" + group,
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            var table = document.getElementById(group);
            var rowCount = table.rows.length - 1;
            while (rowCount--) {
                table.deleteRow(rowCount);
            }
            if (data.length == 0) {
                var table = document.getElementById(group);
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 2
                mac.style.textAlign = "center"
                mac.innerHTML = "Empty"
            }
            for (var stream in data) {
                value = data[stream]
                var table = document.getElementById(group);
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var c = 0
                var remove = row.insertCell(c++);
                remove.align = "center"
                remove.width = "24px"
                remove.innerHTML = "<img class=\"ctrl\" src=\"/static/images/remove.png\" onClick=\"removeMAC('" + group + "','" + value + "')\" />"
                if (group === 'wtps') {
                    var flag = row.insertCell(c++);
                    flag.align = "center"
                    flag.width = "24px"
                    if (data[stream]['connection']) {
                        flag.innerHTML = "<img class=\"ctrl\" src=\"/static/images/flag_green.png\"  />"
                    } else {
                        flag.innerHTML = "<img class=\"ctrl\" src=\"/static/images/flag_red.png\"  />"
                    }
                }
                var mac = row.insertCell(c++);
                mac.innerHTML = value
            }
        },
    });
}

function loadLVAPs(tenant) {
    if (tenant) {
        url = "/api/v1/tenants/" + tenant + "/lvaps"
    } else {
        url = "/api/v1/lvaps"
    }
    $.ajax({
        url: url,
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            var table = document.getElementById('lvaps');
            for (i = table.rows.length - 1; i > 0; i--) {
                table.deleteRow(i);
            }
            if (data.length == 0) {
                var table = document.getElementById('lvaps');
                var rowCount = table.rows.length;
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 6
                mac.style.textAlign = "center"
                mac.innerHTML = "No LVAPs available in this Tenant"
            }
            for (var stream in data) {
                var table = document.getElementById('lvaps');
                var row = table.insertRow(table.rows.length);
                var c = 0
                var sta = row.insertCell(c++);
                sta.innerHTML = data[stream].addr
                var ssid = row.insertCell(c++);
                ssid.innerHTML = data[stream].ssid
                var bssid = row.insertCell(c++);
                bssid.innerHTML = data[stream].bssid
                var wtpField = row.insertCell(c++);
                wtpField.innerHTML = data[stream].wtp.addr + " (" + data[stream].scheduled_on[0].channel + ", " + data[stream].scheduled_on[0].band + ")"
                wtpField.id = "field_" + data[stream].addr
                var wtpCtrl = row.insertCell(c++);
                wtpCtrl.id = "ctrl_" + data[stream].addr
                wtpCtrl.width = "24px"
                wtpCtrl.align = "center"
                if (tenant) {
                    wtpCtrl.innerHTML = "<a href=\"#\" onClick=\"listWTPs('" + data[stream].addr + "','" + data[stream].scheduled_on[0].addr + "', '" + tenant + "')\"><img width=\"24\" src=\"/static/images/edit.png\" /></a>"
                } else {
                    wtpCtrl.innerHTML = "<a href=\"#\" onClick=\"listWTPs('" + data[stream].addr + "','" + data[stream].scheduled_on[0].addr + "')\"><img width=\"24\" src=\"/static/images/edit.png\" /></a>"
                }
            }
        },
    });
}

function listWTPs(lvap, current, tenant) {
    clearInterval(lvapsInterval)
    if (tenant) {
        url = "/api/v1/tenants/" + tenant + "/wtps"
    } else {
        url = "/api/v1/wtps"
    }
    $.ajax({
        url: url,
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            var ctrl = document.getElementById('ctrl_' + lvap);
            if (tenant) {
                ctrl.innerHTML = "<a href=\"#\" onClick=\"setWTP('" + lvap + "', '" + tenant + "')\"><img width=\"24\" src=\"/static/images/accept.png\" /></a>"
            } else {
                ctrl.innerHTML = "<a href=\"#\" onClick=\"setWTP('" + lvap + "')\"><img width=\"24\" src=\"/static/images/accept.png\" /></a>"
            }
            var field = document.getElementById('field_' + lvap);
            var tmp = "<select id=\"select_" + lvap + "\">"
            for (var stream in data) {
                if (data[stream].connection) {
                    tmp += "<option>" + data[stream].addr + "</option>"
                }
            }
            tmp += "</select>"
            field.innerHTML = tmp
            var select = document.getElementById('select_' + lvap);
            select.value = current
        },
    });
}

function setWTP(lvap, tenant) {
    if (tenant) {
        url = "/api/v1/tenants/" + tenant + "/lvaps/" + lvap
    } else {
        url = "/api/v1/lvaps/" + lvap
    }
    var select = document.getElementById('select_' + lvap);
    $.ajax({
        url: url,
        type: 'PUT',
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        data: '{ "version" : "1.0", "wtp" : "' + select.value + '" }',
        dataType: 'json',
        cache: false,
        success: function (data) {
            if (tenant) {
                lvapsInterval = runLoader(loadLVAPs, tenant)
            } else {
                lvapsInterval = runLoader(loadLVAPs)
            }
        },
        error: function (data) {
            if (tenant) {
                lvapsInterval = runLoader(loadLVAPs, tenant)
            } else {
                lvapsInterval = runLoader(loadLVAPs)
            }
        },
    });
}

function refreshLVAPs() {

    $.getJSON("/api/v1/tenants/" + tenant_id + "/lvaps",
        function(data) {
            newLvaps = {}
            for (lvap in data) {
                var idLvap = data[lvap].addr
                newLvaps[idLvap] = data[lvap]
            }
            // remove old LVAPs
            for (idLvap in lvaps) {
                dl = JSON.stringify(newLvaps[idLvap].downlink) == JSON.stringify(lvaps[idLvap].downlink)
                ul = JSON.stringify(newLvaps[idLvap].uplink) == JSON.stringify(lvaps[idLvap].uplink)
                changed = !(dl && ul)
                if (!newLvaps[idLvap] || changed) {
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
                wtps[idWtp].connection = data[node].connection
                wtps[idWtp].feed = data[node].feed
            }
        });
}

function wtpUp(idWtp) {

}

function wtpDown(idWtp) {

}

function lvapUp(idLvap) {

}

function lvapDown(idLvap) {

}
