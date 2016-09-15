
selectedLvap = "18:5E:0F:E2:10:8F"
//selectedLvap = "80:00:0B:6A:9B:81"

lvap = null

Lvnf_Counter = "20c7ecf7-be9e-4643-8f98-8ac582b4bc01"
Lvnf_To_Dump_icmp = "20c7ecf7-be9e-4643-8f98-8ac582b4bc05"
Lvnf_To_Dump_http = "20c7ecf7-be9e-4643-8f98-8ac582b4bc09"

lvnf = null

vlan_id_counter = 5
vlan_id_icmp_dump = 10
vlan_id_http_dump = 15

//IP Packet Filtering
eth_type = 2048

nw_proto1 = 1 //ICMP Packet Filtering
nw_proto2 = 6 // TCP Packet Filtering

AVERAGING_PERIOD=4000
READ_HANDLERS_PERIOD=1000
RENDERING_PERIOD=1000

var counterInputGraph2D
var counterInputDataset = new vis.DataSet();
var counterInputPrev = 0

var HTTPcounterInputGraph2D
var HTTPcounterInputDataset = new vis.DataSet();
var HTTPcounterInputPrev = 0

var ICMPcounterInputGraph2D
var ICMPcounterInputDataset = new vis.DataSet();
var ICMPcounterInputPrev = 0

var tenant_id="{{tenant_id}}"

function initialize() {

    lvapDown(selectedLvap)
    lvnfDown(Lvnf_Counter)
    lvnfDown(Lvnf_To_Dump_icmp)
    lvnfDown(Lvnf_To_Dump_http)

    var counterInputDiv = document.getElementById('counterincoming');
    counterInputGraph2D = new vis.Graph2d(counterInputDiv, counterInputDataset, options);
    renderStep(counterInputGraph2D);

    var HTTPcounterInputDiv = document.getElementById('httpincoming');
    HTTPcounterInputGraph2D = new vis.Graph2d(HTTPcounterInputDiv, HTTPcounterInputDataset, options);
    renderStep(HTTPcounterInputGraph2D);

    var ICMPcounterInputDiv = document.getElementById('icmpincoming');
    ICMPcounterInputGraph2D = new vis.Graph2d(ICMPcounterInputDiv, ICMPcounterInputDataset, options);
    renderStep(ICMPcounterInputGraph2D);

    runLoader(refreshLVNFs)
    runLoader(refreshLVAPs)
    runLoader(refreshWTPs)
    runLoader(refreshCPPs)

    runLoader(loop)

}

var options = {
    start: vis.moment().add(-60, 'seconds'), // changed so its faster
    end: vis.moment(),
    dataAxis: {
      left: {
        range: {
          min:0, max:200
        }
      }
    },
    drawPoints: {
        style: 'circle' // square, circle
    },
    shaded: {
        orientation: 'bottom' // top, bottom
    }
};

var chain1_next = false
var chain2_next = false
var chain3_next = false

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
                html = "<img title='" + wtps[i].addr + "' src='/static/apps/tropea/ap_dl_ul.png' width='90'>"
                $("#wtps").append(html)
                continue
            }
        }

        // render next
        $.getJSON("/api/v1/tenants/" + tenant_id + "/lvaps/" + selectedLvap + "/ports/0/next",
            function (data) {
                if (Object.keys(data).length > 0) {
                    html = "<img src='/static/apps/tropea/next_on.png' onclick='unchain_1()' width='180'>"
                    $("#next_count").html(html)
                    chain1_next = true
                } else {
                    html = "<img src='/static/apps/tropea/next_off.png' onclick='chain_1()' width='180'>"
                    $("#next_count").html(html)
                    chain1_next = false
                }
            });

        if (chain1_next == true) {

            $.getJSON("/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_Counter + "/ports/0/next",
                function (data) {
                    if (Object.keys(data).length > 0) {
                        html = "<img src='/static/apps/tropea/next_icmp.png' onclick='unchain2()' width='180'>"
                        $("#next_icmp").html(html)
                        chain2_next = true
                    } else {
                        html = "<img src='/static/apps/tropea/next_off.png' onclick='chain2()' width='180'>"
                        $("#next_icmp").html(html)
                        chain2_next = false
                    }
                });
        }

        if (chain1_next == true) {
        $.getJSON("/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_To_Dump_icmp + "/ports/0/next",
            function (data) {
                if (Object.keys(data).length > 0) {
                    html = "<img src='/static/apps/tropea/next_http.png' onclick='unchain3()' width='180'>"
                    $("#next_http").html(html)
                    chain3_next = true
                } else {
                    html = "<img src='/static/apps/tropea/next_off.png' onclick='chain3()' width='180'>"
                    $("#next_http").html(html)
                    chain3_next = false
                }
            });
        }
    }

    if (lvnfs[Lvnf_Counter]) {
        // render cpps
        $("#cpps1").html("")
        for (var i in cpps) {
            cpp = lvnfs[Lvnf_Counter].cpp
            if (cpp.addr == cpps[i].addr) {
                html = "<img title='" + cpps[i].addr + "' src='/static/apps/tropea/cpp_on.png' width='90'>"
                $("#cpps1").append(html)
            } else {
                html = "<img title='" + cpps[i].addr + "' src='/static/apps/tropea/cpp_off.png' onclick='setCpp(\"" + cpps[i].addr + "\")' width='90'>"
                $("#cpps1").append(html)
            }
        }
    }

    if (lvnfs[Lvnf_To_Dump_icmp]) {
        // render cpps
        $("#cpps2").html("")
        for (var i in cpps) {
            cpp = lvnfs[Lvnf_To_Dump_icmp].cpp
            if (cpp.addr == cpps[i].addr) {
                html = "<img title='" + cpps[i].addr + "' src='/static/apps/tropea/cpp_on.png' width='90'>"
                $("#cpps2").append(html)
            } else {
                html = "<img title='" + cpps[i].addr + "' src='/static/apps/tropea/cpp_off.png' onclick='setCpp(\"" + cpps[i].addr + "\")' width='90'>"
                $("#cpps2").append(html)
            }
        }
    }

    if (lvnfs[Lvnf_To_Dump_http]) {
        // render cpps
        $("#cpps3").html("")
        for (var i in cpps) {
            cpp = lvnfs[Lvnf_To_Dump_http].cpp
            if (cpp.addr == cpps[i].addr) {
                html = "<img title='" + cpps[i].addr + "' src='/static/apps/tropea/cpp_on.png' width='90'>"
                $("#cpps3").append(html)
            } else {
                html = "<img title='" + cpps[i].addr + "' src='/static/apps/tropea/cpp_off.png' onclick='setCpp(\"" + cpps[i].addr + "\")' width='90'>"
                $("#cpps3").append(html)
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

function setCpp(idCpp) {

    console.log("Setting new CPP...")

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_Counter,
        type: 'PUT',
        dataType: 'json',
        data: '{"version":"1.0","addr":"' + idCpp + '"}',
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

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_To_Dump_icmp,
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

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_To_Dump_http,
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
    if (idLvnf == Lvnf_To_Dump_icmp) {

        console.log("LVNF " + Lvnf_To_Dump_icmp + " is up!")
        html = "<div class='tiny' id='stats'></div><img title='" + idLvnf + "' src='/static/apps/tropea/ICMPPacketDumper_on.png' onclick='undeployLvnfToDump_icmp()' width='180'>"

        $("#todump_icmp").html(html)
        $("#cpps2").html("")


        // monitor ToDUmp HTTP Counter
        data = {"version": "1.0",
                "lvnf": Lvnf_To_Dump_icmp,
                "handler": "count",
                "every": READ_HANDLERS_PERIOD}

        // create read_handler poller
        $.ajax({
            url: "/api/v1/tenants/" + tenant_id + "/lvnf_get",
            type: 'POST',
            dataType: 'json',
            data: JSON.stringify(data),
            cache: false,
            beforeSend: function (request) {
                request.setRequestHeader("Authorization", BASE_AUTH);
            },
            statusCode: {
                201: function (data) {
                    console.log("Handler count created")
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

        // monitor HTTP ToDump lvnf_stats
        data = {"version": "1.0",
                "lvnf": Lvnf_To_Dump_icmp,
                "every": READ_HANDLERS_PERIOD}

        // create HTTP Counter lvnf_stats poller
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
                    console.log("ToDUmp LVNF Counter stats poller created")
                    console.log(data)
                    addDataPoint_icmp('tx_packets', ICMPcounterInputGraph2D, ICMPcounterInputDataset, ICMPcounterInputPrev)
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

    if (idLvnf == Lvnf_Counter) {

        console.log("LVNF " + Lvnf_Counter + " is up!")
        html = "<div class='tiny' id='stats'></div><img title='" + idLvnf + "' src='/static/apps/tropea/PacketCounter_on.png' onclick='undeployLvnfCounter()' width='180'>"

        $("#counter").html(html)
        $("#cpps1").html("")

        // monitor Counter
        data = {"version": "1.0",
                "lvnf": Lvnf_Counter,
                "handler": "count",
                "every": READ_HANDLERS_PERIOD}

        // create read_handler poller
        $.ajax({
            url: "/api/v1/tenants/" + tenant_id + "/lvnf_get",
            type: 'POST',
            dataType: 'json',
            data: JSON.stringify(data),
            cache: false,
            beforeSend: function (request) {
                request.setRequestHeader("Authorization", BASE_AUTH);
            },
            statusCode: {
                201: function (data) {
                    console.log("Handler count created")
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

        // monitor Counter lvnf_stats
        data = {"version": "1.0",
                "lvnf": Lvnf_Counter,
                "every": READ_HANDLERS_PERIOD}

        // create Counter lvnf_stats poller
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
                    console.log("Counter LVNF stats poller created")
                    console.log(data)
                    addDataPoint_counter('tx_packets', counterInputGraph2D, counterInputDataset, counterInputPrev)
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
    if (idLvnf == Lvnf_To_Dump_http) {

        console.log("LVNF " + Lvnf_To_Dump_http + " is up!")
        html = "<div class='tiny' id='stats'></div><img title='" + idLvnf + "' src='/static/apps/tropea/HTTPPacketDumper_on.png' onclick='undeployLvnfToDump_http()' width='180'>"

        $("#todump_http").html(html)
        $("#cpps3").html("")

        // monitor ToDUmp ICMP Counter
        data = {"version": "1.0",
                "lvnf": Lvnf_To_Dump_http,
                "handler": "count",
                "every": READ_HANDLERS_PERIOD}

        // create read_handler poller
        $.ajax({
            url: "/api/v1/tenants/" + tenant_id + "/lvnf_get",
            type: 'POST',
            dataType: 'json',
            data: JSON.stringify(data),
            cache: false,
            beforeSend: function (request) {
                request.setRequestHeader("Authorization", BASE_AUTH);
            },
            statusCode: {
                201: function (data) {
                    console.log("Handler count created")
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

        // monitor ICMP ToDump lvnf_stats
        data = {"version": "1.0",
                "lvnf": Lvnf_To_Dump_http,
                "every": READ_HANDLERS_PERIOD}

        // create ICMP Counter lvnf_stats poller
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
                    console.log("ToDump2 LVNF Counter stats poller created")
                    console.log(data)
                    addDataPoint_http('tx_packets', HTTPcounterInputGraph2D, HTTPcounterInputDataset, HTTPcounterInputPrev)
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

function lvnfDown(idLvnf) {
    if (idLvnf == Lvnf_Counter) {
        console.log("LVNF " + Lvnf_Counter + " is down!")
        html = "<img title='" + idLvnf + "' src='/static/apps/tropea/PacketCounter_off.png' onclick='deployLvnfCounter()' width='180'>"
        $("#counter").html(html)
        $("#cpps1").html("")
    }

    if (idLvnf == Lvnf_To_Dump_icmp) {
        console.log("LVNF " + Lvnf_To_Dump_icmp + " is down!")
        html = "<img title='" + idLvnf + "' src='/static/apps/tropea/ICMPPacketDumper_off.png' onclick='deployLvnfToDump_icmp()' width='180'>"
        $("#todump_icmp").html(html)
        $("#cpps2").html("")
    }

    if (idLvnf == Lvnf_To_Dump_http) {
        console.log("LVNF " + Lvnf_To_Dump_http + " is down!")
        html = "<img title='" + idLvnf + "' src='/static/apps/tropea/HTTPPacketDumper_off.png' onclick='deployLvnfToDump_http()' width='180'>"
        $("#todump_http").html(html)
        $("#cpps3").html("")
    }
}

function lvapUp(idLvap) {
    if (idLvap == selectedLvap) {
        console.log("LVAP " + selectedLvap + " is up!")
        html = "<img title='" + idLvap + "' src='/static/apps/tropea/lvap_on.png' width='180'></p>"
        $("#lvap").html(html)
        $("#wtps").html("")
    }
}

function lvapDown(idLvap) {
    if (idLvap == selectedLvap) {
        console.log("LVAP " + selectedLvap + " is down!")
        html = "<img title='" + idLvap + "' src='/static/apps/tropea/lvap_off.png' width='180'>"
        $("#lvap").html(html)
        $("#wtps").html("")
    }
}

function chain_1() {

    console.log("Enabling encap...")

    data = {"version":"1.0", "encap": "00:00:00:00:00:00"}

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
                console.log("Encap enabled!")
                setNextChain_1()
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

function setNextChain_1() {

    console.log("Chaining...")

    addr = lvaps[selectedLvap].addr

    data = {"version":"1.0",
            "match":"dl_src="+addr+",dl_vlan="+vlan_id_counter,
            "next": {"lvnf_id": Lvnf_Counter, "port_id": 0}}

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvaps/" + selectedLvap + "/ports/0/next",
        type: 'POST',
        dataType: 'json',
        data: JSON.stringify(data),
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            204: function (data) {
                alert(data);
                console.log("from tropea only"+ data);
                console.log("Next enabled!")
                console.log("Chaining completed!")
                html = "<img src='/static/apps/tropea/next_on.png' onclick='unchain_1()' width='180'>"
                $("#next_count").html(html)
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

function unchain_1() {

    console.log("Disabling encap...")

    data = {"version":"1.0", "encap": "00:00:00:00:00:00"}

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
                console.log("Encap enabled!")
                unsetNextChain_1()
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

function unsetNextChain_1() {

    console.log("Chaining...")

    addr = lvaps[selectedLvap].addr

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvaps/" + selectedLvap + "/ports/0/next/dl_src="+addr+",dl_vlan="+vlan_id_counter,
        type: 'DELETE',
        dataType: 'json',
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            204: function (data) {
                console.log("Unchaining completed!")
                html = "<img src='/static/apps/tropea/next_off.png' onclick='chain_1()' width='180'>"
                $("#next_count").html(html)
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

function chain2() {

    console.log("Chaining...")

    addr = lvaps[selectedLvap].addr

    data = {"version":"1.0",
            "match":"dl_src="+addr+",dl_vlan="+vlan_id_icmp_dump+",dl_type="+eth_type+",nw_proto="+nw_proto1,
            "next": {"lvnf_id": Lvnf_To_Dump_icmp, "port_id": 0}}

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_Counter + "/ports/0/next",
        type: 'PUT',
        dataType: 'json',
        data: JSON.stringify(data),
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            204: function (data) {
                console.log("Next enabled!")
                console.log("Chaining completed!")
                html = "<img src='/static/apps/tropea/next_icmp.png' onclick='unchain2()' width='180'>"
                $("#next_icmp").html(html)
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

function unchain2() {

    console.log("Chaining...")

    addr = lvaps[selectedLvap].addr

    data = {"version":"1.0",
            "match":"dl_src="+addr+",dl_vlan="+vlan_id_icmp_dump+",dl_type="+eth_type+",nw_proto="+nw_proto1}

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_Counter + "/ports/0/next/",
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
                html = "<img src='/static/apps/tropea/next_off.png' onclick='chain2()' width='180'>"
                $("#next_icmp").html(html)
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

function chain3() {

    console.log("Chaining...")

    addr = lvaps[selectedLvap].addr

    data = {"version":"1.0",
            "match":"dl_src="+addr+",dl_vlan="+vlan_id_http_dump+",dl_type="+eth_type+",nw_proto="+nw_proto2,
            "next": {"lvnf_id": Lvnf_To_Dump_http, "port_id": 0}}

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_To_Dump_icmp + "/ports/0/next",
        type: 'PUT',
        dataType: 'json',
        data: JSON.stringify(data),
        cache: false,
        beforeSend: function (request) {
            request.setRequestHeader("Authorization", BASE_AUTH);
        },
        statusCode: {
            204: function (data) {
                console.log("Next enabled!")
                console.log("Chaining completed!")
                html = "<img src='/static/apps/tropea/next_http.png' onclick='unchain3()' width='180'>"
                $("#next_http").html(html)
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

function unchain3() {

    console.log("Chaining...")

    addr = lvaps[selectedLvap].addr

    data = {"version":"1.0",
            "match":"dl_src="+addr+",dl_vlan="+vlan_id_http_dump+",dl_type="+eth_type+",nw_proto="+nw_proto2}

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_To_Dump_icmp + "/ports/0/next/",
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
                html = "<img src='/static/apps/tropea/next_off.png' onclick='chain3()' width='180'>"
                $("#next_http").html(html)
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

function deployLvnfCounter() {

    console.log("Deploying lvnf...")

    var keys = Object.keys(cpps);
    var addr = cpps[keys[0]].addr

    vnf = "in_0 -> cnt::Counter() -> out_0"
    image = {"nb_ports": 1,
             "vnf": vnf,
             "handlers": [["count", "cnt.count"]],
             "state_handlers": []}

    data = {"version": "1.0",
            "image": image,
            "addr": addr}

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_Counter,
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

function undeployLvnfCounter() {

    console.log("Undeploying lvnf...")

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_Counter,
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


function deployLvnfToDump_icmp() {

    console.log("Deploying lvnf...")

    var keys = Object.keys(cpps);
    var addr = cpps[keys[0]].addr

    vnf = "in_0 -> td::ToDump(httptraffic) -> out_0"
    image = {"nb_ports": 1,
             "vnf": vnf,
             "handlers": [["count", "td.count"]],
             "state_handlers": []}

    data = {"version": "1.0",
            "image": image,
            "addr": addr}

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_To_Dump_icmp,
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

function undeployLvnfToDump_icmp() {

    console.log("Undeploying lvnf...")

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_To_Dump_icmp,
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

function deployLvnfToDump_http() {

    console.log("Deploying lvnf...")

    var keys = Object.keys(cpps);
    var addr = cpps[keys[0]].addr

    vnf = "in_0 -> td2::ToDump(dump_file_2) -> out_0"
    image = {"nb_ports": 1,
             "vnf": vnf,
             "handlers": [["count", "td2.count"]],
             "state_handlers": []}

    data = {"version": "1.0",
            "image": image,
            "addr": addr}

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_To_Dump_http,
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

function undeployLvnfToDump_http() {

    console.log("Undeploying lvnf...")

    $.ajax({
        url: "/api/v1/tenants/" + tenant_id + "/lvnfs/" + Lvnf_To_Dump_http,
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

function addDataPoint_counter(type, graph, dataset, prev, timer) {

    $.getJSON("/api/v1/tenants/" + tenant_id + "/lvnf_stats", function(data) {
        rate = 0.0
        for (var i in data) {
            if (data[i].lvnf==Lvnf_Counter) {
                iface = lvnfs[Lvnf_Counter].ports['0'].iface
                stats = data[i]['stats'][iface]
                if (!stats) {
                    break
                }
                pkts = data[i]['stats'][iface][type]
                if (pkts) {
                    curr = parseInt(pkts)
                    if (prev > 0) {
                        rate = (curr - prev) / (AVERAGING_PERIOD / 1000)
                    }
                    prev = curr
                }
                break
            }
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
            addDataPoint_counter(type, graph, dataset, prev);
        }, AVERAGING_PERIOD)
    });
}

function addDataPoint_icmp(type, graph, dataset, prev, timer) {

    $.getJSON("/api/v1/tenants/" + tenant_id + "/lvnf_stats", function(data) {
        rate = 0.0
        for (var i in data) {
            if (data[i].lvnf==Lvnf_To_Dump_icmp) {
                iface = lvnfs[Lvnf_To_Dump_icmp].ports['0'].iface
                stats = data[i]['stats'][iface]
                if (!stats) {
                    break
                }
                pkts = data[i]['stats'][iface][type]
                if (pkts) {
                    curr = parseInt(pkts)
                    if (prev > 0) {
                        rate = (curr - prev) / (AVERAGING_PERIOD / 1000)
                    }
                    prev = curr
                }
                break
            }
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
            addDataPoint_icmp(type, graph, dataset, prev);
        }, AVERAGING_PERIOD)
    });
}

function addDataPoint_http(type, graph, dataset, prev, timer) {

    $.getJSON("/api/v1/tenants/" + tenant_id + "/lvnf_stats", function(data) {
        rate = 0.0
        for (var i in data) {
            if (data[i].lvnf==Lvnf_To_Dump_http) {
                iface = lvnfs[Lvnf_To_Dump_http].ports['0'].iface
                stats = data[i]['stats'][iface]
                if (!stats) {
                    break
                }
                pkts = data[i]['stats'][iface][type]
                if (pkts) {
                    curr = parseInt(pkts)
                    if (prev > 0) {
                        rate = (curr - prev) / (AVERAGING_PERIOD / 1000)
                    }
                    prev = curr
                }
                break
            }
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
            addDataPoint_http(type, graph, dataset, prev);
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
