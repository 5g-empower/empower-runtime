
imageId = "49313ecb-9d00-4b7d-b873-b55d3d9acbbb"

selectedLvap = "00:18:DE:CC:D3:40"
lvap = null

selectedLvnf = "20c7ecf7-be9e-4643-8f98-8ac582b4bc03"
lvnf = null

AVERAGING_PERIOD=4000
READ_HANDLERS_PERIOD=1000
RENDERING_PERIOD=1000

var inputGraph2D
var inputDataset = new vis.DataSet();
var inputPrev = 0

var outputGraph2D
var outputDataset = new vis.DataSet();
var outputPrev = 0

var tenant_id="{{tenant_id}}"

function initialize() {

    lvapDown(selectedLvap)
    lvnfDown(selectedLvnf)

    var inputDiv = document.getElementById('incoming');
    inputGraph2D = new vis.Graph2d(inputDiv, inputDataset, options);
    renderStep(inputGraph2D);

    var outputDiv = document.getElementById('outgoing');
    outputGraph2D = new vis.Graph2d(outputDiv, outputDataset, options);
    renderStep(outputGraph2D);

    runLoader(refreshLVNFs)
    runLoader(refreshLVAPs)
    runLoader(refreshWTPs)
    runLoader(refreshCPPs)

    runLoader(loop)

}

var options = {
    start: vis.moment().add(-60, 'seconds'), // changed so its faster
    end: vis.moment(),
    /*dataAxis: {
      left: {
        range: {
          min:0, max: 5
        }
      }
    },*/
    drawPoints: {
        style: 'circle' // square, circle
    },
    shaded: {
        orientation: 'bottom' // top, bottom
    }
};

function loop() {

    if (lvaps[selectedLvap]) {

        // render wtps
        $("#wtps").html("")
        for (var i in wtps) {
            // look for downlink
            found = false
            for (var j in lvaps[selectedLvap].downlink) {
                sched_on = lvaps[selectedLvap].downlink[j]
                if (sched_on.addr == wtps[i].addr) {
                    found = true
                }
            }
            if (found) {
                html = "<img title='" + wtps[i].addr + "' src='/static/apps/scylla/ap_dl_ul.png' width='90'>"
                $("#wtps").append(html)
                continue
            }
            // look for uplinks
            found = false
            for (var j in lvaps[selectedLvap].uplink) {
                sched_on = lvaps[selectedLvap].uplink[j]
                if (sched_on.addr == wtps[i].addr) {
                    found = true
                }
            }
            if (found) {
                html = "<img title='" + wtps[i].addr + "' src='/static/apps/scylla/ap_ul_on.png' onclick='disableMultipleUplinks()' width='90'>"
                $("#wtps").append(html)
            } else {
                html = "<img title='" + wtps[i].addr + "' src='/static/apps/scylla/ap_ul_off.png' onclick='enableMultipleUplinks()' width='90'>"
                $("#wtps").append(html)
            }
        }

        // render next
        $.getJSON("/api/v1/tenants/" + tenant_id + "/lvaps/" + selectedLvap + "/ports/0/next",
            function(data) {
                if (data[""]) {
                      html = "<img src='/static/apps/scylla/next_on.png' onclick='unchain()' width='180'>"
                      $("#next").html(html)
                } else {
                      html = "<img src='/static/apps/scylla/next_off.png' onclick='chain()' width='180'>"
                      $("#next").html(html)
                }
            });

    }

    if (lvnfs[selectedLvnf]) {
        // render cpps
        $("#cpps").html("")
        for (var i in cpps) {
            cpp = lvnfs[selectedLvnf].cpp
            if (cpp.addr == cpps[i].addr) {
                html = "<img title='" + cpps[i].addr + "' src='/static/apps/scylla/cpp_on.png' width='90'>"
                $("#cpps").append(html)
            } else {
                html = "<img title='" + cpps[i].addr + "' src='/static/apps/scylla/cpp_off.png' onclick='setCpp(\"" + cpps[i].addr + "\")' width='90'>"
                $("#cpps").append(html)
            }
        }
    }
}

function decodeBand(band) {
    if (band == 'L20') {
        return 0
    } else if (band == 'HT20') {
        return 1
    } else if (band == 'HT40') {
        return 2
    } else {
        return -1
    }
}

function enableMultipleUplinks() {

    console.log("Enabling multiple uplinks...")

    data = {"version":"1.0", "encap":"00:00:00:00:00:00", "scheduled_on": []}

    for (var i in wtps) {
        downlink = lvaps[selectedLvap].downlink[0]
        for (var j in wtps[i].supports) {
            block = wtps[i].supports[j]
            if (block.band == downlink.band && block.channel == downlink.channel) {
                data["scheduled_on"].push({'wtp':wtps[i].addr,'band': decodeBand(block.band),'channel':block.channel})
            }
        }
    }

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvaps/" + selectedLvap,
        type: 'PUT',
        dataType: 'json',
        data: JSON.stringify(data),
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            204: function (data) {
                console.log("Multiple uplinks enabled!")
            },
            400: function (data) {
                alert(data.responseJSON.message);
            },
            404: function (data) {
                alert(data.responseJSON.message);
            },
            500: function (data) {
                alert(data.responseJSON.message);
            }
        }
    });

}

function disableMultipleUplinks() {

    console.log("Disabling multiple uplinks...")

    data = {"version":"1.0", "encap":"00:00:00:00:00:00", "scheduled_on": []}

    downlink = lvaps[selectedLvap].downlink[0]
    data["scheduled_on"].push({'wtp':downlink.addr,'band': decodeBand(downlink.band),'channel':downlink.channel})

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvaps/" + selectedLvap,
        type: 'PUT',
        dataType: 'json',
        data: JSON.stringify(data),
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            204: function (data) {
                console.log("Multiple uplinks disabled!")
            },
            400: function (data) {
                alert(data.responseJSON.message);
            },
            404: function (data) {
                alert(data.responseJSON.message);
            },
            500: function (data) {
                alert(data.responseJSON.message);
            }
        }
    });

}

function setCpp(idCpp) {

    console.log("Setting new CPP...")

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + selectedLvnf,
        type: 'PUT',
        dataType: 'json',
        data: '{"version":"1.0","addr":"'+idCpp+'"}',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            204: function (data) {
                console.log("LVNF migrated")
            },
            400: function (data) {
                alert(data.responseJSON.message);
            },
            404: function (data) {
                alert(data.responseJSON.message);
            },
            500: function (data) {
                alert(data.responseJSON.message);
            }
        }
    });

}

function lvnfUp(idLvnf) {
    if (idLvnf == selectedLvnf) {

        console.log("LVNF " + selectedLvnf + " is up!")
        html = "<div class='tiny' id='stats'></div><img title='" + idLvnf + "' src='/static/apps/scylla/lvnf_on.png' onclick='undeployLvnf()' width='180'>"

        $("#lvnf").html(html)
        $("#cpps").html("")

        startReadHandler("in_0_count", addDataPoint, inputGraph2D, inputDataset, inputPrev)
        startReadHandler("out_0_count", addDataPoint, outputGraph2D, outputDataset, outputPrev)

        // monitor dupes table
        data = {"version": "1.0",
                "lvnf_id": selectedLvnf,
                "handler": "dupes_table",
                "every": READ_HANDLERS_PERIOD}

        // create read_handler poller
        $.ajax({
            url: "/api/v1/tenants/" + tenant_id + "/read_handler",
            type: 'POST',
            dataType: 'json',
            data: JSON.stringify(data),
            cache: false,
            beforeSend: function (request) {
                request.setRequestHeader("Authorization", BASE_AUTH);
            },
            statusCode: {
                201: function (data) {
                    console.log("Handler dupes_table created")
                    setTimeout(function() {
                        dupesTable();
                    }, AVERAGING_PERIOD)
                },
                400: function (data) {
                    alert(data.responseJSON.message);
                },
                404: function (data) {
                    alert(data.responseJSON.message);
                },
                500: function (data) {
                    alert(data.responseJSON.message);
                }
            }
        });

        // monitor lvnf_stats
        data = {"version": "1.0",
                "lvnf_id": selectedLvnf,
                "every": READ_HANDLERS_PERIOD}

        // create lvnf_stats poller
        $.ajax({
            url: "/api/v1/tenants/" + tenant_id + "/lvnf_stats",
            type: 'POST',
            dataType: 'json',
            data: JSON.stringify(data),
            cache: false,
            beforeSend: function (request) {
                request.setRequestHeader("Authorization", BASE_AUTH);
            },
            statusCode: {
                201: function (data) {
                    console.log("LVNF stats poller created")
                    setTimeout(function() {
                        lvnfStats();
                    }, AVERAGING_PERIOD)
                },
                400: function (data) {
                    alert(data.responseJSON.message);
                },
                404: function (data) {
                    alert(data.responseJSON.message);
                },
                500: function (data) {
                    alert(data.responseJSON.message);
                }
            }
        });

    }
}

function dupesTable() {
    $.getJSON("/api/v1/tenants/" + tenant_id + "/read_handler", function(data) {
        $('#dupes tr').slice(1).remove();
        for (var i in data) {
            if (data[i].lvnf_id==selectedLvnf && data[i].handler=="dupes_table") {
                if (!data[i].samples || data[i].samples.length == 0) {
                    continue
                }
                for (var j in data[i].samples) {
                    tokens = data[i].samples[j].split(" ")
                    html = '<tr><td>'+tokens[0]+'</td><td>'+tokens[1]+'</td><td>'+tokens.slice(3, tokens.length).join("&nbsp;")+'</td></tr>'
                    $('#dupes').append(html);
                }
            }
        }
        setTimeout(function() {
            dupesTable();
        }, AVERAGING_PERIOD)
    });
}

function lvnfStats() {
    $.getJSON("/api/v1/tenants/" + tenant_id + "/lvnf_stats", function(data) {
        for (var i in data) {
            if (data[i].lvnf_id==selectedLvnf) {
                if (!data[i].stats) {
                    continue
                }
                rss = data[i].stats.memory_rss/1000000
                vms = data[i].stats.memory_vms/1000000
                $("#stats").html("RSS: " + rss.toFixed(2) + " Mbytes VMS: " + vms.toFixed(2) + " Mbytes")
            }
        }
        setTimeout(function() {
            lvnfStats();
        }, AVERAGING_PERIOD)
    });
}
function lvnfDown(idLvnf) {
    if (idLvnf == selectedLvnf) {
        console.log("LVNF " + selectedLvnf + " is down!")
        html = "<img title='" + idLvnf + "' src='/static/apps/scylla/lvnf_off.png' onclick='deployLvnf()' width='180'>"
        $("#lvnf").html(html)
        $("#cpps").html("")
    }
}

function lvapUp(idLvap) {
    if (idLvap == selectedLvap) {
        console.log("LVAP " + selectedLvap + " is up!")
        html = "<img title='" + idLvap + "' src='/static/apps/scylla/lvap_on.png' width='180'></p>"
        $("#lvap").html(html)
        $("#wtps").html("")
    }
}

function lvapDown(idLvap) {
    if (idLvap == selectedLvap) {
        console.log("LVAP " + selectedLvap + " is down!")
        html = "<img title='" + idLvap + "' src='/static/apps/scylla/lvap_off.png' width='180'>"
        $("#lvap").html(html)
        $("#wtps").html("")
    }
}

function chain() {

    console.log("Chaining...")

    data = {"version":"1.0", "match":{}, "next": {"lvnf_id": selectedLvnf, "port_id": 0}}

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvaps/" + selectedLvap + "/ports/0/next",
        type: 'PUT',
        dataType: 'json',
        data: JSON.stringify(data),
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            204: function (data) {
                console.log("Chaining completed!")
                html = "<img src='/static/apps/scylla/next_on.png' onclick='unchain()' width='180'>"
                $("#next").html(html)
            },
            400: function (data) {
                alert(data.responseJSON.message);
            },
            404: function (data) {
                alert(data.responseJSON.message);
            },
            500: function (data) {
                alert(data.responseJSON.message);
            }
        }
    });

}

function unchain() {

    console.log("Unchaining...")

    data = {"version":"1.0", "match":{}}

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvaps/" + selectedLvap + "/ports/0/next",
        type: 'DELETE',
        dataType: 'json',
        data: JSON.stringify(data),
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            204: function (data) {
                console.log("Unchaining completed!")
                html = "<img src='/static/apps/scylla/next_off.png' onclick='chain()' width='180'>"
                $("#next").html(html)
            },
            400: function (data) {
                alert(data.responseJSON.message);
            },
            404: function (data) {
                alert(data.responseJSON.message);
            },
            500: function (data) {
                alert(data.responseJSON.message);
            }
        }
    });

}

function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function deployLvnf() {

    console.log("Deploying lvnf...")

    var keys = Object.keys(cpps);
    var addr = cpps[keys[0]].addr

    vnf = "in_0 -> Classifier(12/bbbb) -> Strip(14) -> dupe::ScyllaWifiDupeFilter() -> WifiDecap() -> out_0"

    image = {"nb_ports": 1,
             "vnf": vnf,
             "handlers": [["dupes_table", "dupe.dupes_table"]],
             "state_handlers": []}

    data = {"version": "1.0",
            "image": image,
            "addr": addr}

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + selectedLvnf,
        type: 'POST',
        dataType: 'json',
        data: JSON.stringify(data),
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            204: function (data) {
                console.log("LVNF deployed")
            },
            400: function (data) {
                alert(data.responseJSON.message);
            },
            404: function (data) {
                alert(data.responseJSON.message);
            },
            500: function (data) {
                alert(data.responseJSON.message);
            }
        }
    });

}

function undeployLvnf() {

    console.log("Undeploying lvnf...")

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + selectedLvnf,
        type: 'DELETE',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            204: function (data) {
                console.log("LVNF undeployed!")
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

function startReadHandler(handler, job, graph, dataset, prev) {

    data = {"version": "1.0",
            "lvnf_id": selectedLvnf,
            "handler": handler,
            "every": READ_HANDLERS_PERIOD}

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/read_handler",
        type: 'POST',
        dataType: 'json',
        data: JSON.stringify(data),
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            201: function (data) {
                console.log("Handler " + handler + " created")
                job(handler, graph, dataset, prev)
            },
            400: function (data) {
                alert(data.responseJSON.message);
            },
            404: function (data) {
                alert(data.responseJSON.message);
            },
            500: function (data) {
                alert(data.responseJSON.message);
            }
        }
    });

}

function addDataPoint(handler, graph, dataset, prev, timer) {
    $.getJSON("/api/v1/tenants/" + tenant_id + "/read_handler", function(data) {
        rate = 0.0
        found = false
        for (var i in data) {
            if (data[i].handler==handler) {
                found = true
                if (data[i].samples && data[i].samples.length > 0) {
                    curr = parseInt(data[i].samples[0])
                    if (prev > 0) {
                        rate = (curr - prev) / (AVERAGING_PERIOD / 1000)
                    }
                    prev = curr
                }
                break
            }
        }
        if (!found) {
            console.log("Handler " + handler + " not found. Removing timer.")
            return
        }
        if (rate < 0.0) {
            rate = 0.0
        }
        var now = vis.moment();
        dataset.add({
            x: now,
            y: rate
        });
        var range = graph.getWindow();
        var interval = range.end - range.start;
        var oldIds = dataset.getIds({
            filter: function(item) {
                return item.x < range.start - interval;
            }
        });
        dataset.remove(oldIds);
        setTimeout(function() {
            addDataPoint(handler, graph, dataset, prev);
        }, AVERAGING_PERIOD)
    });
}

function renderStep(graph) {
    // move the window (you can think of different strategies).
    var now = vis.moment();
    var range = graph.getWindow();
    var interval = range.end - range.start;
    graph.setWindow(now - interval, now, {animation: true});
    setTimeout(function() {
        renderStep(graph);
    }, RENDERING_PERIOD)
}
