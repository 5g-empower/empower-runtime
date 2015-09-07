
cpps = {}
lvnfs = {}

function loadCPPs(tenant_id) {
    if (tenant_id) {
        url = "/api/v1/tenants/" + tenant_id + "/cpps"
    } else {
        url = "/api/v1/cpps"
    }
    $.ajax({
        url: url,
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            var table = document.getElementById('cpps');
            var rowCount = table.rows.length - 1;
            while (rowCount--) {
                if (rowCount < 0) {
                    break
                }
                table.deleteRow(rowCount);
            }
            if (data.length == 0) {
                var table = document.getElementById('cpps');
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 3
                mac.style.textAlign = "center"
                mac.innerHTML = "Empty"
            }
            for (var stream in data) {
                value = data[stream].addr
                var table = document.getElementById('cpps');
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var c = 0
                var remove = row.insertCell(c++);
                remove.align = "center"
                remove.width = "24px"
                if (tenant_id) {
                    remove.innerHTML = "<img class=\"ctrl\" src=\"/static/images/remove.png\" onClick=\"removeCPP('" + value + "', '" + tenant_id + "')\" />"
                } else {
                    remove.innerHTML = "<img class=\"ctrl\" src=\"/static/images/remove.png\" onClick=\"removeCPP('" + value + "')\" />"
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
                    mac.innerHTML += "<div class=\"details\" id=\"cpp_" + stream + "\">at " + data[stream]['connection'] + ", last seen: " + data[stream]['last_seen'] + "</div>"
                } else {
                    mac.innerHTML += "<div class=\"details\" id=\"cpp_" + stream + "\">Disconnected</div>"
                }
            }
        },
    });
}

function removeCPP(mac, tenant_id) {
    if (tenant_id) {
        url = "/api/v1/tenants/" + tenant_id + "/cpps/" + mac
    } else {
        url = "/api/v1/cpps/" + mac
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
            loadCPPs()
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

function registerCPP(tenant_id) {
    var mac = document.getElementById("cpp_mac").value;
    var label = document.getElementById("cpp_label").value;
    if (tenant_id) {
        url = "/api/v1/tenants/" + tenant_id + "/cpps"
    } else {
        url = "/api/v1/cpps"
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
                var table = document.getElementById('cpps');
                var rowCount = table.rows.length - 1;
                var row = table.deleteRow(rowCount);
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 3
                mac.align = "right"
                mac.innerHTML = "<a onClick=\"return addCPP()\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a></td>"
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

function addCPP() {
    var table = document.getElementById('cpps');
    var rowCount = table.rows.length - 1;
    var row = table.deleteRow(rowCount);
    var row = table.insertRow(rowCount);
    var mac = row.insertCell(0);
    tmp = "<ul><li><input onclick=\"this.value=''\" onblur=\" if (this.value == '') this.value='MAC Address' \" size=\"20\" autocapitalize=\"off\" autocorrect=\"off\" class=\"text-input\" id=\"cpp_mac\" type=\"text\" value=\"MAC Address\" />&nbsp;<input onclick=\"this.value=''\" onblur=\" if (this.value == '') this.value='Generic CPP' \" size=\"24\" autocapitalize=\"off\" autocorrect=\"off\" class=\"text-input\" id=\"cpp_label\" type=\"text\" value=\"Generic CPP\" /><div class=\"box\"><img width=\"24\" src=\"/static/images/accept.png\" onClick=\"registerCPP()\"/><img class=\"ctrl\" src=\"/static/images/reject.png\" onClick=\"removeCPPInputBox()\" /></div></li></ul>"
    mac.colSpan = 3
    mac.innerHTML = tmp
}

function removeCPPInputBox() {
    var table = document.getElementById('cpps');
    var rowCount = table.rows.length - 1;
    var row = table.deleteRow(rowCount);
    var row = table.insertRow(rowCount);
    var mac = row.insertCell(0);
    mac.colSpan = 3
    mac.align = "right"
    mac.innerHTML = "<a onClick=\"return addCPP()\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a></td>"
}

function refreshLVNFs() {

    $.getJSON("/api/v1/tenants/" + tenant_id + "/lvnfs",
        function(data) {
            newLvnfs = {}
            for (lvnf in data) {
                var idLvnf = data[lvnf].lvnf_id
                newLvnfs[idLvnf] = data[lvnf]
            }
            // remove old LVNFs
            for (idLvnf in lvnfs) {
                if (!newLvnfs[idLvnf] || newLvnfs[idLvnf].cpp.addr != lvnfs[idLvnf].cpp.addr) {
                    var idCpp = lvnfs[idLvnf].cpp.addr
                    delete cpps[idCpp]['lvnfs'][idLvnf]
                    delete lvnfs[idLvnf]
                    lvnfDown(idLvnf, idCpp)
                }
            }
            // add new LVNFs
            for (lvnf in newLvnfs) {
                var idLvnf = newLvnfs[lvnf].lvnf_id
                var idCpp = newLvnfs[lvnf].cpp.addr
                if (!cpps[idCpp]) {
                    continue
                }
                if (!lvnfs[idLvnf]) {
                    lvnfs[idLvnf] = newLvnfs[lvnf]
                    cpps[idCpp]['lvnfs'][idLvnf] = newLvnfs[lvnf]
                    lvnfUp(idLvnf, idCpp)
                }
            }
        });
}

function refreshCPPs() {
    $.getJSON("/api/v1/tenants/" + tenant_id + "/cpps",
        function(data) {
            for (node in data) {
                var idCpp = data[node].addr
                if (!cpps[idCpp]) {
                    cpps[idCpp] = data[node]
                    cpps[idCpp]['lvnfs'] = {}
                    cpps[idCpp].connection = data[node].connection
                    cpps[idCpp].feed = data[node].feed
                    cppUp(idCpp)
                    continue
                }
                if (cpps[idCpp].connection && !data[node].connection) {
                    cppDown(idCpp)
                }
                if (!cpps[idCpp].connection && data[node].connection) {
                    cppUp(idCpp)
                }
                cpps[idCpp].connection = data[node].connection
                cpps[idCpp].feed = data[node].feed
            }
        });
}

function cppUp(idCpp) {

}

function cppDown(idCpp) {

}

function lvnfUp(idLvnf) {

}

function lvnfDown(idLvnf) {

}


function selectCPP() {

    $.getJSON("/api/v1/cpps",
        function(data) {

            tmp = "Select CPP: <select id=\"select_cpp\">"
            for (var stream in data) {
                tmp += "<option>" + data[stream].addr + "</option>"
            }
            tmp += "</select>"
            tmp += "<div class=\"box\"><img width=\"24\" src=\"/static/images/accept.png\" onClick=\"addCPPtoTenant()\"/><img class=\"ctrl\" src=\"/static/images/reject.png\" onClick=\"removeCPPSelectBox()\" /></div>"

            var table = document.getElementById("cpps");
            var rowCount = table.rows.length - 1;
            var row = table.deleteRow(rowCount);
            var row = table.insertRow(rowCount);
            var mac = row.insertCell(0);
            mac.colSpan = 3
            mac.innerHTML = tmp

        });

}

function removeCPPSelectBox() {
    var table = document.getElementById("cpps");
    var rowCount = table.rows.length - 1;
    var row = table.deleteRow(rowCount);
    var row = table.insertRow(rowCount);
    var mac = row.insertCell(0);
    mac.colSpan = 3
    mac.align = "right"
    mac.innerHTML = "<a onClick=\"return selectCPP()\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a>"
}

function addCPPtoTenant() {
    var select = document.getElementById('select_cpp');
    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/cpps/" + select.value,
        type: 'POST',
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        dataType: 'json',
        cache: false,
        success: function (data) {
            removeCPPSelectBox()
        },
        error: function (data) {
            removeCPPSelectBox()
        },
    });
}
