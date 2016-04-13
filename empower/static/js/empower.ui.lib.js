POLLING_PERIOD = 2000

$(document).ready(function() {
    console.log("Initializing...")
    console.log("Loop interval: " + POLLING_PERIOD + "ms")
    initialize()
});

function initialize() {

}

function runLoader(func, param) {
    func(param);
    return setInterval(function () {
        func(param);
    }, POLLING_PERIOD);
}

function refreshTab(tab) {
}

function initTab() {

    var tabsSelector = ".tabs .tab";
    var panelsSelector = ".tabPanels .tabPanel";
    var tabs = $(tabsSelector);
    var panels = $(panelsSelector);

    $(tabs[0]).addClass("selected");
    $(panels[0]).addClass("selected");
    refreshTab(tabs[0])

    tabs.each(function (index) {
        $(this).bind("click", function () {
            var i = 0,
                len = tabs.length;
            var panelToHide = null;
            while (i < len) {
                $(tabs[i]).removeClass("selected");
                $(panels[i]).removeClass("selected");
                if (this == tabs[i]) {
                    panelToHide = i;
                }
                i++
            }
            $(this).addClass("selected");
            $(panels[panelToHide]).addClass("selected");
            refreshTab(this)
        });
    });
}

function addGauge(entry, power, current, voltage) {
    maxBars = 20
    macPower = 10
    green = 12
    yellow = 16
    bars = Math.round(power * (maxBars / macPower))
    linear = "<table style=\"border-collapse: collapse; border: 1px solid white; text-align: center; \">"
    linear += "<tr><td colspan=\"20\" style=\"border: 1px solid white; font-size: 10pt\">" + power + "W - " + voltage + "V - " + current + "A</td></tr>"
    linear += "<tr>"
    for (i = 0; i < maxBars; i++) {
        if (i < green)
            color = "0f0"
        else if (i < yellow)
            color = "ff0"
        else
            color = "f00"
        if (i >= bars)
            color = "eeeeee"
        linear += "<td style=\"background-color: #" + color + "; border: 1px solid white; font-size: 8pt\">&nbsp;</td>"
    }
    linear += "</tr>"
    linear += "<table>"
    entry.innerHTML = linear
}

function loadFeeds() {
    $.ajax({
        url: "/api/v1/feeds",
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            var table = document.getElementById('feeds');
            for (i = table.rows.length - 2; i > 0; i--) {
                table.deleteRow(i);
            }
            if (data.length == 0) {
                var table = document.getElementById('feeds');
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 9
                mac.style.textAlign = "center"
                mac.innerHTML = "Empty"
            }
            for (var stream in data) {
                var table = document.getElementById('feeds');
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var c = 0
                var remove = row.insertCell(c++);
                remove.align = "center"
                remove.innerHTML = "<a onClick=\"return removeFeed(" + data[stream].id + ")\"><img class=\"ctrl\" src=\"/static/images/remove.png\" /></a>"
                var flag = row.insertCell(c++);
                flag.align = "center"
                if (data[stream].status == 'live') {
                    flag.innerHTML = "<img class=\"ctrl\" src=\"/static/images/flag_green.png\" />"
                } else {
                    flag.innerHTML = "<img class=\"ctrl\" src=\"/static/images/flag_red.png\" />"
                }
                var id = row.insertCell(c++);
                id.align = "center"
                id.innerHTML = data[stream].id;
                var entry = row.insertCell(c++);
                entry.align = "center"
                power = 0.0
                voltage = 0.0
                current = 0.0
                for (var sensor in data[stream]['datastreams']) {
                    sensor_id = data[stream]['datastreams'][sensor]['id']
                    value = data[stream]['datastreams'][sensor]['current_value']
                    if (sensor_id == 'voltage') {
                        voltage = value;
                    } else if (sensor_id == 'current') {
                        current = value;
                    } else if (sensor_id == 'power') {
                        power = value;
                    }
                }
                addGauge(entry, power, current, voltage)
                var mac = row.insertCell(c++);
                if (data[stream]['datastreams'].length > 0) {
                    mac.innerHTML += data[stream].updated
                }
                var dev = row.insertCell(c++);
                if (data[stream].wtp) {
                    dev.innerHTML += data[stream].wtp
                } else if (data[stream].cpp) {
                    dev.innerHTML += data[stream].cpp
                } else {
                    dev.innerHTML += "None"
                }
                var set = row.insertCell(c++);
                set.align = "center"
                for (var sensor in data[stream]['datastreams']) {
                    if (data[stream]['datastreams'][sensor].id == 'switch') {
                        if (data[stream]['datastreams'][sensor].current_value == 0)
                            set.innerHTML += "<a href=\"#\" onClick=\"toggleSwitch('" + data[stream].id + "', 1)\"><img id=\"toggle_" + data[stream].id + "\" class=\"ctrl\" src=\"/static/images/enabled.png\" /></a>"
                        else
                            set.innerHTML += "<a href=\"#\" onClick=\"toggleSwitch('" + data[stream].id + "', 0)\"><img id=\"toggle_" + data[stream].id + "\" class=\"ctrl\" src=\"/static/images/disabled.png\" /></a>"
                    }
                }
            }
        },
    });
}

function loadComponents() {
    $.ajax({
        url: "/api/v1/components",
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            var table = document.getElementById('components');
            for (i = table.rows.length - 2; i > 0; i--) {
                table.deleteRow(i);
            }
            if (data.length == 0) {
                var table = document.getElementById('components');
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 3
                mac.style.textAlign = "center"
                mac.innerHTML = "Empty"
            }
            for (var stream in data) {
                var table = document.getElementById('components');
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var c = 0
                var components = row.insertCell(c++);
                if (data[stream]['ui_url']){
                    components.innerHTML = '<a href="'+data[stream]['ui_url']+'" target="_blank">'+stream+'</a>'
                    } else {
                    components.innerHTML = stream
                }
                var ctrl = row.insertCell(c++);
                ctrl.innerHTML += "<img class=\"ctrl\" onClick=\"unregisterComponent('" + stream + "')\" src=\"/static/images/remove.png\"  />"
                ctrl.align = "center"
            }
        },
    });
}

function addComponent() {
    var table = document.getElementById('components');
    var rowCount = table.rows.length - 1;
    var row = table.deleteRow(rowCount);
    var row = table.insertRow(rowCount);
    var mac = row.insertCell(0);
    mac.colSpan = 3
    mac.innerHTML = "<ul><li> \
<input onclick=\"this.value=''\" onblur=\" if (this.value == '') this.value='e.g. empower.energino.energinoserver' \" size=\"60\" autocapitalize=\"off\" autocorrect=\"off\" class=\"text-input\" id=\"component\" type=\"text\" value=\"e.g. empower.energino.energinoserver\" /> \
<div class=\"box\"><img width=\"24\" src=\"/static/images/accept.png\" onClick=\"registerComponent()\"/> \
<img class=\"ctrl\" src=\"/static/images/reject.png\" onClick=\"removeRegisterComponentInputBox()\" /> \
</div></li></ul>"
}

function removeRegisterComponentInputBox() {
    var table = document.getElementById('components');
    var rowCount = table.rows.length - 1;
    var row = table.deleteRow(rowCount);
    var row = table.insertRow(rowCount);
    var mac = row.insertCell(0);
    mac.colSpan = 3
    mac.align = "right"
    mac.innerHTML = "<a onClick=\"return addComponent()\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a></td>"
}

function registerComponent() {
    var args = document.getElementById("component").value;
    var label = document.getElementById("component").value;
    url = "/api/v1/components"
    data = '{"version" : "1.0", "argv" : "' + args + '"}'
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
                var table = document.getElementById('components');
                var rowCount = table.rows.length - 1;
                var row = table.deleteRow(rowCount);
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 3
                mac.align = "right"
                mac.innerHTML = "<a onClick=\"return addComponent()\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a></td>"
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

function removeLVNF(lvnf_id, tenant) {
    $.ajax({
        url: '/api/v1/tenants/' + tenant + '/lvnfs/' + lvnf_id,
        type: 'DELETE',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            400: function () {
                alert('Invalid args');
            },
            404: function () {
                alert('Component not found');
            },
            405: function () {
                alert('Module cannot be unloaded');
            },
            500: function () {
                alert('Internal error');
            }
        }
    });
}

function unregisterComponent(component) {
    $.ajax({
        url: '/api/v1/components/' + component,
        type: 'DELETE',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            400: function () {
                alert('Invalid args');
            },
            404: function () {
                alert('Component not found');
            },
            405: function () {
                alert('Module cannot be unloaded');
            },
            500: function () {
                alert('Internal error');
            }
        }
    });
}

function loadPendingTenantsAdmin(username) {
    loadPendingTenants(username, true)
}

function loadPendingTenantsUser(username) {
    loadPendingTenants(username, false)
}

function loadPendingTenants(username, admin) {

    if (admin) {
        url = '/api/v1/pending'
    } else {
        url = '/api/v1/pending?user=' + username
    }

    $.ajax({
        url: url,
        type: 'GET',
        dataType: 'json',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        success: function (data) {
            var table = document.getElementById('pending');
            for (i = table.rows.length - 1; i > 0; i--) {
                table.deleteRow(i);
            }
            var nb_pending = document.getElementById('nb_pending');
            nb_pending.innerHTML = "Requests: " + data.length
            if (data.length == 0) {
                var table = document.getElementById('pending');
                var rowCount = table.rows.length;
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 4
                mac.style.textAlign = "center"
                mac.innerHTML = "No requests"
            }
            for (var stream in data) {
                var table = document.getElementById("pending");
                var row = table.insertRow(1);
                var checkbox = row.insertCell(0);
                if (admin) {
                    checkbox.style.textAlign = "center"
                    checkbox.innerHTML = "<img class=\"ctrl\" src=\"/static/images/add.png\" onClick=\"acceptTenant('" + data[stream].tenant_id + "')\" />"
                }
                var tenant_id = row.insertCell(1);
                tenant_id.innerHTML = data[stream].tenant_id
                var tenant_name = row.insertCell(2);
                tenant_name.innerHTML = data[stream].tenant_name
                var status = row.insertCell(3);
                status.innerHTML = data[stream].owner
                var bssid_type = row.insertCell(4);
                bssid_type.innerHTML = data[stream].bssid_type
            }
        },
    });
}

function acceptTenant(tenant_id) {
    $.ajax({
        url: "/api/v1/pending/" + tenant_id,
        type: 'GET',
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        cache: false,
        success: function (data) {
            createTenant(data.tenant_id, data.tenant_name, data.owner, data.desc, data.bssid_type)
        },
        error: function (data) {
        },
    });
}

function createTenant(tenant_id, tenant_name, owner, desc, bssid_type) {
    $.ajax({
        url: "/api/v1/tenants/" + tenant_id,
        type: 'POST',
        dataType: 'json',
        data: '{"version":"1.0", "owner":"'+owner+'", "desc":"'+desc+'", "tenant_name":"'+tenant_name+'", "bssid_type":"'+bssid_type+'" }',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            201: function (data) {
                removeTenantRequest(tenant_id)
            }
        }
    });
}

function requestTenant(pending) {

    desc = document.getElementById('desc').value;
    tenant_name = document.getElementById('tenant_name').value;
    var bssid_values = document.getElementsByName('bssid_type');
    for (var i = 0; i < bssid_values.length; i++)
    {
        if (bssid_values[i].checked)
        {
            bssid_type = bssid_values[i].value;
            break;
        }
    }

    var request = {
        "version": "1.0",
        "tenant_name": tenant_name,
        "desc": desc,
        "bssid_type": bssid_type
    }

    $.ajax({
        url: "/api/v1/pending",
        type: 'POST',
        dataType: 'json',
        data: JSON.stringify(request),
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            201: function (data) {
                window.location.replace("/");
            }
        }
    });

}

function removeTenantRequest(tenant_id) {
    url = "/api/v1/pending/" + tenant_id
    $.ajax({
        url: url,
        type: 'DELETE',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            204: function (data) {}
        }
    });
}

function loadApps(username) {

    $.ajax({
        url: url = '/api/v1/components?user=' + username,
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            var table = document.getElementById('apps');
            var rows = table.rows.length
            while (rows--) {
                table.deleteRow(rows);
            }
            r = 0
            a = 0
            var table = document.getElementById("apps");
            var row = table.insertRow(r);
            for (var stream in data) {
                if (a % 3 == 0) {
                    r++
                    var row = table.insertRow(r);
                }
                url = "/apps/" + stream.split(":")[0]  + "/" + stream.split(":")[1] + "/index.html"
                appicon = "/apps/" + stream.split(":")[0]  + "/static/appicon.png"
                var icon = row.insertCell(a);
                icon.style.textAlign = "center"
                icon.innerHTML = "<a target=\"_blank\" href=\"" + url + "\"><img class=\"appicon\" src=\"" + appicon + "\" /></a><br />"
                label = stream.split(":")[0].replace("empower.apps.", "")
                n = label.split('.')
                if (n.length >= 2) {
                    if (n[n.length-1] == n[n.length-2]) {
                        n.splice(-1, 1);
                    }
                    label = n.join(".")
                }
                icon.innerHTML += label + "<br />" + stream.split(":")[1]
                a++
            }
        },
    });
}

function loadTenantsAdmin(username) {
    loadTenants(username, true)
}

function loadTenantsUser(username) {
    loadTenants(username, false)
}

function loadTenants(username, admin) {

    if (admin) {
        url = '/api/v1/tenants'
    } else {
        url = '/api/v1/tenants?user=' + username
    }

    $.ajax({
        url: url,
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            var table = document.getElementById('tenants');
            for (i = table.rows.length - 2; i > 0; i--) {
                table.deleteRow(i);
            }
            for (var stream in data) {
                var table = document.getElementById("tenants");
                var row = table.insertRow(1);
                var checkbox = row.insertCell(0);
                checkbox.style.textAlign = "center"
                checkbox.innerHTML = "<img class=\"ctrl\" src=\"/static/images/remove.png\" onClick=\"removeTenant('" + data[stream].tenant_id + "')\" />"
                var tenant_id = row.insertCell(1);
                if ((data[stream].owner == username)) {
                    tenant_id.innerHTML = "<a href=\"/manage_tenant?tenant_id=" + data[stream].tenant_id + "\">" + data[stream].tenant_id + "</a>"
                } else {
                    tenant_id.innerHTML = data[stream].tenant_id
                }
                var tenant = row.insertCell(2);
                tenant.innerHTML = data[stream].tenant_name
                var devs = row.insertCell(3);
                for (cpp in data[stream].cpps) {
                    devs.innerHTML += data[stream].cpps[cpp].addr + "<br />"
                }
                for (wtp in data[stream].wtps) {
                    devs.innerHTML += data[stream].wtps[wtp].addr + "<br />"
                }
                var status = row.insertCell(4);
                status.innerHTML = data[stream].owner
                var bssid_type = row.insertCell(5);
                bssid_type.innerHTML = data[stream].bssid_type
            }
        },
    });
}

function removeTenant(tenant_id) {
    $.ajax({
        url: '/api/v1/tenants/' + tenant_id,
        type: 'DELETE',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
    });
}

function removeFeed(idFeed) {
    url = "/api/v1/feeds/" + idFeed
    $.ajax({
        url: url,
        type: 'DELETE',
        dataType: 'json',
        data: '{  "version" : "1.0" }',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            201: function (data) {},
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

function addFeed() {
    url = "/api/v1/feeds"
    $.ajax({
        url: url,
        type: 'POST',
        dataType: 'json',
        data: '{  "version" : "1.0" }',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            201: function (data) {},
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

function loadUsers() {
    $.ajax({
        url: "/api/v1/accounts",
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            var table = document.getElementById("users");
            var rowCount = table.rows.length - 1;
            while (rowCount-- > 1) {
                table.deleteRow(rowCount);
            }
            if (data.length == 0) {
                var table = document.getElementById("users");
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var user = row.insertCell(0);
                user.colSpan = 6
                user.style.textAlign = "center"
                user.innerHTML = "Empty"
            }
            for (var stream in data) {
                value = data[stream]
                var table = document.getElementById("users");
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var c = 0
                var remove = row.insertCell(c++);
                remove.align = "center"
                remove.width = "24px"
                remove.innerHTML = "<img class=\"ctrl\" src=\"/static/images/remove.png\" onClick=\"removeUser('" + value.username + "')\" />"
                var username = row.insertCell(c++);
                username.innerHTML = value.username
                var name = row.insertCell(c++);
                name.innerHTML = value.name
                var surname = row.insertCell(c++);
                surname.innerHTML = value.surname
                var role = row.insertCell(c++);
                role.innerHTML = value.role
                var email = row.insertCell(c++);
                email.innerHTML = value.email
            }
        },
    });
}

function removeUser(user) {
    $.ajax({
        url: "/api/v1/accounts/" + user,
        type: 'DELETE',
        dataType: 'json',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        success: function (data) {
        },
        statusCode: {
            400: function () {
                alert('Invalid username');
            },
            500: function () {
                alert('Error');
            }
        }
    });
}

function toggleSwitch(idFeed, value) {
    loadFeeds();
    $.ajax({
        url: '/api/v1/feeds/' + idFeed,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        type: 'PUT',
        dataType: 'json',
        data: '{  "version" : "1.0", "value" : ' + value + '}',
        cache: false,
    });
}


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
                    mac.innerHTML +="at " + data[stream]['connection'][0] + ", last seen: " + data[stream]['last_seen'] + "<br />"
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
    mac.innerHTML = "<a onClick=\"return addWTP()\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a>"
}

function removeMACInputBox(group) {
    var table = document.getElementById(group);
    var rowCount = table.rows.length - 1;
    var row = table.deleteRow(rowCount);
    var row = table.insertRow(rowCount);
    var mac = row.insertCell(0);
    mac.colSpan = 2
    mac.align = "right"
    mac.innerHTML = "<a onClick=\"return addMAC('" + group + "')\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a>"
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
    var label = document.getElementById(group + "_label").value;
    url = "/api/v1/" + group
    data = '{"version":"1.0","sta":"'+mac+'","label":"'+label+'"}'
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
    mac.innerHTML = "<ul><li><input autocapitalize=\"off\" autocorrect=\"off\" class=\"text-input\" id=\"" + group + "_mac\" type=\"text\" value=\"\" />&nbsp;<input autocapitalize=\"off\" autocorrect=\"off\" class=\"text-input\" id=\"" + group + "_label\" type=\"text\" value=\"\" /><div class=\"box\"><img width=\"24\" src=\"/static/images/accept.png\" onClick=\"registerMAC('" + group + "')\"/><img class=\"ctrl\" src=\"/static/images/reject.png\" onClick=\"removeMACInputBox('" + group + "')\" /></div></li></ul>"
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
                remove.innerHTML = "<img class=\"ctrl\" src=\"/static/images/remove.png\" onClick=\"removeMAC('" + group + "','" + value.addr + "')\" />"
                var mac = row.insertCell(c++);
                mac.innerHTML = value.addr + " " + value.label
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
                var net_bssid = row.insertCell(c++);
                net_bssid.innerHTML = data[stream].net_bssid
                var lvap_bssid = row.insertCell(c++);
                lvap_bssid.innerHTML = data[stream].lvap_bssid
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

function loadLVNFs(tenant) {
    url = "/api/v1/tenants/" + tenant + "/lvnfs"
    $.ajax({
        url: url,
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            var table = document.getElementById('lvnfs');
            for (i = table.rows.length - 1; i > 0; i--) {
                table.deleteRow(i);
            }
            if (data.length == 0) {
                var table = document.getElementById('lvnfs');
                var rowCount = table.rows.length;
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 6
                mac.style.textAlign = "center"
                mac.innerHTML = "No LVNFs available in this Tenant"
            }
            for (var stream in data) {
                var table = document.getElementById('lvnfs');
                var row = table.insertRow(table.rows.length);
                var c = 0

                var lvnf_id = row.insertCell(c++);
                lvnf_id.innerHTML = data[stream].lvnf_id

                var image = row.insertCell(c++);
                image.innerHTML = data[stream].image.vnf

                var status = row.insertCell(c++);
                status.innerHTML = data[stream].process

                var cpp = row.insertCell(c++);
                cpp.innerHTML = data[stream].cpp.addr

                var cppCtrl = row.insertCell(c++);
                cppCtrl.id = "ctrl_" + data[stream].lvnf_id
                cppCtrl.width = "24px"
                cppCtrl.align = "center"
                cppCtrl.innerHTML = "<a href=\"#\" onClick=\"removeLVNF('" + data[stream].lvnf_id + "','"+tenant+"')\"><img width=\"24\" src=\"/static/images/remove.png\" /></a>"

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

function selectWTP() {

    $.getJSON("/api/v1/wtps",
        function(data) {

            tmp = "Select WTP: <select id=\"select_wtp\">"
            for (var stream in data) {
                tmp += "<option>" + data[stream].addr + "</option>"
            }
            tmp += "</select>"
            tmp += "<div class=\"box\"><img width=\"24\" src=\"/static/images/accept.png\" onClick=\"addWTPtoTenant()\"/><img class=\"ctrl\" src=\"/static/images/reject.png\" onClick=\"removeWTPSelectBox()\" /></div>"

            var table = document.getElementById("wtps");
            var rowCount = table.rows.length - 1;
            var row = table.deleteRow(rowCount);
            var row = table.insertRow(rowCount);
            var mac = row.insertCell(0);
            mac.colSpan = 3
            mac.innerHTML = tmp

        });

}

function removeWTPSelectBox() {
    var table = document.getElementById("wtps");
    var rowCount = table.rows.length - 1;
    var row = table.deleteRow(rowCount);
    var row = table.insertRow(rowCount);
    var mac = row.insertCell(0);
    mac.colSpan = 3
    mac.align = "right"
    mac.innerHTML = "<a onClick=\"return selectWTP()\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a>"
}

function addWTPtoTenant() {
    var select = document.getElementById('select_wtp');
    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/wtps/" + select.value,
        type: 'POST',
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        dataType: 'json',
        cache: false,
        success: function (data) {
            removeWTPSelectBox()
        },
        error: function (data) {
            removeWTPSelectBox()
        },
    });
}

oains = {}

function loadOAINs(tenant_id) {
    if (tenant_id) {
        url = "/api/v1/tenants/" + tenant_id + "/oains"
    } else {
        url = "/api/v1/oains"
    }
    $.ajax({
        url: url,
        type: 'GET',
        dataType: 'json',
        cache: false,
        success: function (data) {
            var table = document.getElementById('oains');
            var rowCount = table.rows.length - 1;
            while (rowCount--) {
                if (rowCount < 0) {
                    break
                }
                table.deleteRow(rowCount);
            }
            if (data.length == 0) {
                var table = document.getElementById('oains');
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 3
                mac.style.textAlign = "center"
                mac.innerHTML = "Empty"
            }
            for (var stream in data) {
                value = data[stream].addr
                var table = document.getElementById('oains');
                var rowCount = table.rows.length - 1;
                var row = table.insertRow(rowCount);
                var c = 0
                var remove = row.insertCell(c++);
                remove.align = "center"
                remove.width = "24px"
                if (tenant_id) {
                    remove.innerHTML = "<img class=\"ctrl\" src=\"/static/images/remove.png\" onClick=\"removeOAIN('" + value + "', '" + tenant_id + "')\" />"
                } else {
                    remove.innerHTML = "<img class=\"ctrl\" src=\"/static/images/remove.png\" onClick=\"removeOAIN('" + value + "')\" />"
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
                    mac.innerHTML += "<div class=\"details\" id=\"oain_" + stream + "\">at " + data[stream]['connection'] + ", last seen: " + data[stream]['last_seen'] + "</div>"
                } else {
                    mac.innerHTML += "<div class=\"details\" id=\"oain_" + stream + "\">Disconnected</div>"
                }
            }
        },
    });
}

function removeOAIN(mac, tenant_id) {
    if (tenant_id) {
        url = "/api/v1/tenants/" + tenant_id + "/oains/" + mac
    } else {
        url = "/api/v1/oains/" + mac
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
            loadOAINs()
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

function registerOAIN(tenant_id) {
    var mac = document.getElementById("oain_mac").value;
    var label = document.getElementById("oain_label").value;
    if (tenant_id) {
        url = "/api/v1/tenants/" + tenant_id + "/oains"
    } else {
        url = "/api/v1/oains"
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
                var table = document.getElementById('oains');
                var rowCount = table.rows.length - 1;
                var row = table.deleteRow(rowCount);
                var row = table.insertRow(rowCount);
                var mac = row.insertCell(0);
                mac.colSpan = 3
                mac.align = "right"
                mac.innerHTML = "<a onClick=\"return addOAIN()\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a></td>"
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

function addOAIN() {
    var table = document.getElementById('oains');
    var rowCount = table.rows.length - 1;
    var row = table.deleteRow(rowCount);
    var row = table.insertRow(rowCount);
    var mac = row.insertCell(0);
    tmp = "<ul><li><input onclick=\"this.value=''\" onblur=\" if (this.value == '') this.value='MAC Address' \" size=\"20\" autocapitalize=\"off\" autocorrect=\"off\" class=\"text-input\" id=\"oain_mac\" type=\"text\" value=\"MAC Address\" />&nbsp;<input onclick=\"this.value=''\" onblur=\" if (this.value == '') this.value='Generic OAI Node' \" size=\"24\" autocapitalize=\"off\" autocorrect=\"off\" class=\"text-input\" id=\"oain_label\" type=\"text\" value=\"Generic OAI Node\" /><div class=\"box\"><img width=\"24\" src=\"/static/images/accept.png\" onClick=\"registerOAIN()\"/><img class=\"ctrl\" src=\"/static/images/reject.png\" onClick=\"removeOAINInputBox()\" /></div></li></ul>"
    mac.colSpan = 3
    mac.innerHTML = tmp
}

function removeOAINInputBox() {
    var table = document.getElementById('oains');
    var rowCount = table.rows.length - 1;
    var row = table.deleteRow(rowCount);
    var row = table.insertRow(rowCount);
    var mac = row.insertCell(0);
    mac.colSpan = 3
    mac.align = "right"
    mac.innerHTML = "<a onClick=\"return addOAIN()\"><img class=\"ctrl\" src=\"/static/images/add.png\" /></a></td>"
}
