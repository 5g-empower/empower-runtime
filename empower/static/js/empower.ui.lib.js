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
                if (data[stream]['ui']){
                    components.innerHTML = '<a href="'+data[stream]['ui']+'" target="_blank">'+stream+'</a>'
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
            createTenant(data.tenant_id, data.tenant_name, data.owner, data.desc)
        },
        error: function (data) {
        },
    });
}

function createTenant(tenant_id, tenant_name, owner, desc) {
    $.ajax({
        url: "/api/v1/tenants/" + tenant_id,
        type: 'POST',
        dataType: 'json',
        data: '{"version":"1.0", "owner":"'+owner+'", "desc":"'+desc+'", "tenant_name":"'+tenant_name+'" }',
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

    var request = {
        "version": "1.0",
        "tenant_name": tenant_name,
        "desc": desc
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
