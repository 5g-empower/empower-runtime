// https://fontawesome.com/icons?d=gallery&c=interfaces&m=free

var __VIS_OPTIONS = {
    "groups":{
        "wtp": {
            "shape": "circularImage",
            "image": "/static/pics/wtp.png"
        },
        "vbs": {
            "shape": "circularImage",
            "image": "/static/pics/vbs.png"
        },
        "client_lvap": {
            "shape": "circularImage",
            "image": "/static/pics/lvap.png"
        },
        "client_ue": {
            "shape": "circularImage",
            "image": "/static/pics/ue.png"
        },
        "client_hybrid": {
            "shape": "circularImage",
            "image": "/static/pics/hybrid.png"
        },
    }
}


class EmpVisCreator{

    constructor(data=null,options=null){
        if (data === null){
            this.data = {
                "nodes": [],
                "edges": []
            }
        }
        else{
            this.data = data;
        }

        if (options === null){
            this.options = {}
        }
        else{
            this.options = options;
        }

    }

    reset( data=null, options=null){
        if (data === null){
            this.data = {
                "nodes": [],
                "edges": []
            }
        }
        else{
            this.data = data;
        }
        if (options === null){
            this.options = {}
        }
        else{
            this.options = options;
        }
    }

    getNode(nid){
        var nodes = this.data.nodes;
        for (var i = 0; i < nodes.length; i++){
            if (nodes[i].id === nid){
                return nodes[i];
            }
        }
        return null;
    }

    getEdge(eid){
        var edges = this.data.edges;
        for (var i = 0; i < edges.length; i++){
            if (edges[i].id === eid){
                return edges[i];
            }
        }
        return null;
    }

    getNodeIndex(nid){
        var nodes = this.data.nodes;
        for (var i = 0; i < nodes.length; i++){
            if (nodes[i].id === nid){
                return i;
            }
        }
        return -1;
    }

    getEdgeIndex(eid){
        var edges = this.data.edges;
        for (var i = 0; i < edges.length; i++){
            if (edges[i].id === eid){
                return i;
            }
        }
        return -1;
    }

    updateNode(newnode){
        var nodes = this.data.nodes;
        for (var i = 0; i < nodes.length; i++){
            if (nodes[i].id === newnode.id){
                nodes[i] = newnode;
                return true;
            }
        }
        return false;
    }

    updateNode(newedge){
        var edges = this.data.edges;
        for (var i = 0; i < edges.length; i++){
            if (edges[i].id === newedge.id){
                edges[i] = newedge;
                return true;
            }
        }
        return false;
    }

    addNode(newnode){
        if (typeof newnode.id === "undefined"){
            console.error("EmpVisCreator.addNode: new node has no ID field");
            return false;
        }
        var nodes = this.data.nodes;
        for (var i = 0; i < nodes.length; i++){
            if (nodes[i].id === newnode.id){
                console.error("EmpVisCreator.addNode: new node id "+newnode.id+" is already IN");
                return false;
            }
        }
        nodes.push(newnode);
        return true;
    }

    addEdge(newedge){
        if (typeof newedge.id === "undefined"){
            console.error("EmpVisCreator.addEdge: new edge has no ID field");
            return false;
        }
        if (this.getNodeIndex(newedge.from) === -1){
            console.error("EmpVisCreator.addEdge: node 'from' ("+newedge.from+") of edge "+newedge.id+" is NOT IN");
            return false;
        }
        if (this.getNodeIndex(newedge.to) === -1){
            console.error("EmpVisCreator.addEdge: node 'to' ("+newedge.to+") of edge "+newedge.id+" is NOT IN");
            return false;
        }
        var edges = this.data.edges;
        for (var i = 0; i < edges.length; i++){
            if (edges[i].id === newedge.id){
                console.error("EmpVisCreator.addEdge: new edge id "+newedge.id+" is already IN");
                return false;
            }
        }
        edges.push(newedge);
        return true;
    }

    removeNode(nid){
        var i = this.getNodeIndex(nid);
        if (i < 0){
            console.warn("EmpVisCreator.removeNode: no node has id "+nid);
            return false;
        }
        else{
            this.data.nodes.splice(i, 1);
        }
    }

    removeEdge(eid){
        var i = this.getEdgeIndex(nid);
        if (i < 0){
            console.warn("EmpVisCreator.removeNode: no edge has id "+eid);
            return false;
        }
        else{
            this.data.edges.splice(i, 1);
        }
    }



    createNode(id, label, title, group=null){
        var node = {
            "id": id,
            //"label": label,
            "title": title,
            "physics": false
        }
        if (group !== null){
            node["group"] = group;
        }
        return node;
    }

    createEdge(id, from, to){
        var edge = {
            "id": id,
            "from": from,
            "to": to,
            // "smooth":{
            //     "type": "discrete"
            // }
            //"physics": false
        }
        return edge;
    }

    createSpecialEdge(id, from , to, type, params=null){
        var edge = this.createEdge(id, from, to);
        switch (type) {
            case "ASSOCIATION":
            //console.log("createSpecialEdge.ASSOCIATION");
                edge.dashes = [2,3];
                edge.color = {
                    "color": "#c0c0c0"
                };
                break;
            case "DOWNLINK":
                edge.color = {
                    "color": "#0000ff"
                };
                edge.arrows = "to";
                edge.label = "DOWNLINK"
                break;
            case "UPLINK":
                edge.color = {
                    "color": "#ff0000"
                };
                edge.arrows = "to";
                edge.label = "UPLINK"
                break;

        }

        return edge;
    }

    addOption(key, value){
        this.options[key] = value;
    }

    removeOption(key){
        delete this.options[key];
    }
}

class EmpGraphBox{

    constructor(keys, hb, data=null, options=null){
        if (hb === null){
            hb = new HBuilder();
        }
        this.hb = hb;

        if ( !this.hb.isArray( keys ) ){
            keys = [ keys ];
        }
        this.keys = keys;

        if (data === null){
            this.data = {
                "nodes": [],
                "edges": []
            };
        }
        else{
            this.data = data;
        }
        if (options === null)
            this.options = {};
        else {
            this.options = options;
        }

        this.vcreator = new EmpVisCreator(this.data, this.options);

        this.buttonbox = new EmpButtonBox(keys);
    }

    getID(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.graphbox.suffixes.graphbox] );
        return this.hb.generateID( keys );
    }

    getID_Container(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.graphbox.params.container] );
        return this.hb.generateID( keys );
    }

    getID_ButtonBox(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.graphbox.params.buttonbox] );
        return this.hb.generateID( keys );
    }

    getContainer(keys=null){
        //return $("#"+this.getID());
        //console.log(this.getID());
        return this.hb.ge(this.getID_Container());
    }

    deployContainer(where){
        var container = this.hb.ce("DIV");
        container.id = this.getID();
        $( container ).attr("style","width: 100%; height: 400px; padding: 20px; border: 1px solid #e7e7e7 !important;");
        $( "#"+where ).append(container);
    }

    create(bdata, keys=null){

        var id = this.getID(keys);
        if ($( "#"+id ).length > 0){
            console.warn("EmpGraphBox "+id+" already available")
            return null;
        }

        var r =  this.hb.ceROW();
        r.id = id;

            var rgb = this.hb.ceROW();
            $( rgb ).attr("style", "margin:10px 20px; padding: 5px;");
        $( r ).append(rgb)

                var container = this.hb.ce("DIV");
                container.id = this.getID_Container(keys);
                $( container ).addClass("center-block");
                $( container ).attr("style","width: 75%; height: 400px; padding: 20px; border: 1px solid #e7e7e7 !important;");
            $( rgb ).append( container );

            var rbbx = this.hb.ceROW();
            $( rbbx  ).attr("style", "margin:0px 20px; padding: 5px;");//" border: 1px solid  #e7e7e7 !important");
        $( r ).append(rbbx );

        //console.log(bdata);

            $( rbbx  ).append( this.buttonbox.create(bdata, keys));

        return r;
    }

    deploy(where, bdata, keys=null){
        $( "#"+where ).append(this.create(bdata, keys));
    }

    reset(){

        this.data = {
            "nodes": [],
            "edges": []
        }

        this.options = {
            "groups":{
                "wtp": {
                    "shape": "circularImage",
                    "image": "/static/pics/wtp.png"
                },
                "vbs": {
                    "shape": "circularImage",
                    "image": "/static/pics/vbs.png"
                },
                "client_lvap": {
                    "shape": "circularImage",
                    "image": "/static/pics/lvap.png"
                },
                "client_ue": {
                    "shape": "circularImage",
                    "image": "/static/pics/ue.png"
                },
                "client_hybrid": {
                    "shape": "circularImage",
                    "image": "/static/pics/hybrid.png"
                },
            }
        }

        this.vcreator.reset(this.data, this.options);
    }

    run(){
        //console.log(this.getContainer());
        console.log("RUN");
        console.log(this.data);
        console.log(this.options);
        this.graph = new vis.Network(this.getContainer(), this.data, this.options);
        var g = this.graph;//.fit();
        setInterval(function() {
             g.fit();
         }, 1000);
    }
}
