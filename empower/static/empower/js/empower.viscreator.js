// https://fontawesome.com/icons?d=gallery&c=interfaces&m=free
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
// ------------------------------------------------------------------ GET
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
// ---------------------------------------------------------------------- UPDATE
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

    updateEdge(newedge){
        var edges = this.data.edges;
        for (var i = 0; i < edges.length; i++){
            if (edges[i].id === newedge.id){
                edges[i] = newedge;
                return true;
            }
        }
        return false;
    }
// ------------------------------------------------------------------------- ADD
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
// ------------------------------------------------------------------------- REMOVE
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
// ------------------------------------------------------------------------- CREATE
    createNode(id, title, group=null){
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
// ---------------------------------------------------------- ADD/REMOVE OPTION
    addOption(key, value){
        this.options[key] = value;
    }
    removeOption(key){
        delete this.options[key];
    }
}
