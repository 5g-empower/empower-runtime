networks = {}
conflict = {}

function refreshTab(tab) {
    $.getJSON("/api/v1/tenants/" + tenant_id + "/components/empower.apps.conflictgraph.conflictgraph", function(data) {
        updateCm(data, 36, 'im5')
        updateCm(data, 6, 'im24')
    });
    $.getJSON("/api/v1/tenants/" + tenant_id + "/ucqm", function(data) {
        updateCqm(data, 36, 'cqm5')
        updateCqm(data, 6, 'cqm24')
    });
}

function addNodeIfMissing(found, nodes, id) {
        if (found.indexOf(id) == -1) {
            nodes.push({
                id: id,
                label: id,
            shape: 'box',
            color: '#FF9900',
            size: 10
            })
            found.push(id)
        }
}

function updateCm(data, channel, element) {

    var found = []

    var nodes = [];
    var edges = [];

    for (i in data['conflicts'].networks) {

        src = data['conflicts'].networks[i][0]
        dst = data['conflicts'].networks[i][1]

        for (j in src.blocks) {
            block = src.blocks[j]
            if (block.channel != channel) {
                continue
            }
         }

        id_src = src.wtp.addr + "->" + src.addr
        id_dst = dst.addr + "->" + dst.wtp.addr

        addNodeIfMissing(found, nodes, id_src)
        addNodeIfMissing(found, nodes, id_dst)

        edges.push({
            from: id_src,
            to: id_dst,
            color: "#000000"
        })

    }

    for (i in data['conflicts'].stations) {

        src = data['conflicts'].stations[i][0]
        dst = data['conflicts'].stations[i][1]

        for (j in src.blocks) {
            block = src.blocks[j]
            if (block.channel != channel) {
                continue
            }
         }

        id_src = src.addr + "->" + src.wtp.addr
        id_dst = dst.addr + "->" + dst.wtp.addr

        addNodeIfMissing(found, nodes, id_src)
        addNodeIfMissing(found, nodes, id_dst)

        edges.push({
            from: id_src,
            to: id_dst,
            color: "#000000"
        })

    }

    // create a network
    var container = document.getElementById(element);
    var data = {
        nodes: nodes,
        edges: edges
    };

    var options = {edges: {style:"arrow"},};

    conflict[element] = new vis.Network(container, data, options);
    conflict[element].redraw()

}

function updateCqm(data, channel, element) {

    var found = []

    var nodes = [];
    var edges = [];

    for (i in data) {

        wtp = data[i]

        if (wtp.block.channel != channel) {
            continue
        }

        if (wtp.block.channel <= 13) {
            color = 'read'
        } else {
            color = 'blue'
        }

        idWtp = wtp.block.addr + ':' + wtp.block.channel

        var container = document.getElementById(element);

        nodes.push({
            id: idWtp,
            label: wtp.block.addr,
            shape: 'triangle',
            color: '#FF9900',
            size: 10
        })

        for (j in wtp.maps) {
            sta = wtp.maps[j]
            if (found.indexOf(sta.addr) == -1) {
                nodes.push({
                    id: sta.addr,
                    label: sta.addr,
                    shape: 'dot',
                    size: 10
                })
                found.push(sta.addr)
            }
            if (sta.sma_rssi > -60) {
                color = '#00FF00'
            } else if (sta.sma_rssi > -80) {
                color = '#FF9900'
            } else {
                color = '#FF0000'
            }
            edges.push({
                from: idWtp,
                to: sta.addr,
                width: 4,
                label: sta.sma_rssi,
                color: color
            })
        }

    }

    // create a network
    var container = document.getElementById(element);
    var data = {
        nodes: nodes,
        edges: edges
    };

    var options = {};

    if (networks[element]) {
        networks[element].setData(data)
        networks[element].redraw()
    } else {
        networks[element] = new vis.Network(container, data, options);
    }

}
