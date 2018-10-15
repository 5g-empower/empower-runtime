class EmpNetGraph{

    constructor(keys){

        this.hb = __HB;
        this.qe = __QE;
        this.desc = __DESC;
        this.cache = __CACHE;
        this.delay = __DELAY;

        if ( !this.hb.isArray( keys ) ){
            keys = [ keys ];
        }
        this.keys = keys;

        this.graph = null;
        this.play = false;
        this.type = null;
    }

    getID(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.netgraph.tag] );
        return this.hb.generateID( keys );
    }

    getID_BODY(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.netgraph.elements.body] );
        return this.hb.generateID( keys );
    }

    create(type, params){   // params = [tag, a, values]
        this.type = type;
        var p =  this.hb.cePANEL();
        $( p ).addClass("panel-info");
        p.id = this.getID();

            var ph = this.hb.cePANEL_H();
            $( p ).append(ph);
            var pb = this.hb.cePANEL_B();
            $( p ).append(pb);
            pb.id = this.getID_BODY();
            var pf = this.hb.cePANEL_F();
            $( p ).append(pf);

                switch(type){
                    case "topology":
                        $( ph ).text( "Topology" );
                        var g = this.d_TopologyGraph();
                        $( pb ).append(g);
                        break;
                    case "stackedBarGraph":
                        $( ph ).text( "Bar graph: " + params[1] );
                        var g = this.d_StackedBarGraph(params);
                        $( pb ).append(g);
                        break;
                    default:
                        console.log("EmpNetGraph.create: " + type + " graph not implemented")
                }
        return p;
    }

// ---------------------------------------------------------------------- TOPOLOGY

//    d_TopologyGraph(){
//        var options = this.d_TopologyGraph_ResetOptions();
//        var vc = new EmpVisCreator(null, options);
//        this.graph = vc;
//
//        $( "#" + this.getID_BODY() ).empty();
//
//        vc.addOption("autoResize", true);
//        vc.addOption("height", '100%');
//        vc.addOption("width", '100%');
//
//        vc.addOption("nodes", {
//            "size": 60,
//            "font": { "size": 15, "color": "#000000" },
//            "color":{ "border": "#ffffff" },
//            "borderWidth": 2
//        });
//        vc.addOption("edges", {
//            "width": 2,
//            "font": { "size": 10, "color": "#000000" }
//        })
//
//        var div = this.hb.ce("DIV");
//        $( div ).css("height", "350px")
//        var fff = function(){
//            var graph = new vis.Network(div, vc.data, vc.options);
//            var g = graph;//.fit();
//            setInterval(function() {
//                 g.fit();
//             }, 1000);
//        }
//        $( this.d_TopologyGraph_CreateNodeEdges(vc) ).ready(fff)
//        return div;
//    }
//
//    d_TopologyGraph_CreateNodeEdges(vc){
//
//        var wtps = this.cache.c[this.qe.targets.WTP];
//        var vbses = this.cache.c[this.qe.targets.VBS];
//        var lvaps = this.cache.c[this.qe.targets.LVAP];
//        var ueses = this.cache.c[this.qe.targets.UE];
////            console.log(wtps, vbses, lvaps, ueses)
//
//        for(var i=0; i<wtps.length; i++){
//            var id = wtps[i]["addr"]
//            var title = wtps[i]["label"]
//            var node = vc.createNode(id, title, "wtp");
//                node.x = 100 + 150*i;
//                node.y = 100;
//                node.fixed = true;
//            vc.addNode(node)
//        }
//        for(var i=0; i<lvaps.length; i++){
//            var id = lvaps[i]["addr"]
//            var title = lvaps[i]["ssid"]
//            var node = vc.createNode(id, title, "client_lvap");
//                node.x = 100 + 150*i;
//                node.y = 300;
//                node.fixed = true;
//            vc.addNode(node);
//
//            var wtp = lvaps[i]["wtp"];
//            for(var j=0; j<wtps.length; j++){
//                if( wtps[j]["addr"] === wtp["addr"] ){
//                    var idEdge = id + "To" + wtps[j]["addr"]
//                    var from = id;
//                    var to = wtps[j]["addr"]
//                    var edge = vc.createSpecialEdge(id, from , to, "ASSOCIATION");
//                    vc.addEdge(edge);
//                    break;
//                }
//            }
//        }
//
//
//        for(var i=0; i<vbses.length; i++){
//            var id = vbses[i]["addr"]
//            var title = vbses[i]["label"]
//            var node = vc.createNode(id, title, "vbs");
//                node.x = 100 + 150*i;
//                node.y = 500;
//                node.fixed = true;
//            vc.addNode(node);
//        }
//        for(var i=0; i<ueses.length; i++){
//            var id = ueses[i]["imsi"]
//            var title = ueses[i]["imsi"]
//            var node = vc.createNode(id, title, "client_ue");
//                node.x = 100 + 150*i;
//                node.y = 700;
//                node.fixed = true;
//            vc.addNode(node);
//        }
//
//    }
//
//    d_TopologyGraph_ResetOptions(){
//        var options = {
//            "groups":{
//                "wtp": {
//                    "shape": "circularImage",
//                    "image": "/static/pics/wtp.png"
//                },
//                "vbs": {
//                    "shape": "circularImage",
//                    "image": "/static/pics/vbs.png"
//                },
//                "client_lvap": {
//                    "shape": "circularImage",
//                    "image": "/static/pics/lvap.png"
//                },
//                "client_ue": {
//                    "shape": "circularImage",
//                    "image": "/static/pics/ue.png"
//                },
//                "client_hybrid": {
//                    "shape": "circularImage",
//                    "image": "/static/pics/hybrid.png"
//                },
//            }
//        }
//        return options;
//    }
//
//    d_TopologyGraph_SetTopology(conf_id){
//        switch (conf_id){
//
//            case 0: // BASE CASE
//                eacd.label = "ALL";
//                ebcd.label = "ALL";
//                eacu.label = "ALL";
//                vc.addNode(nA);
//                vc.addNode(nB);
//                vc.addNode(nC);
//                vc.addEdge(eacd);
//                vc.addEdge(eac);
//                vc.addEdge(eacu);
//                vc.addEdge(ebcd);
//                vc.addEdge(ebc);
//                //vc.addEdge(ebcu);
//                break;
//            case 1: // route UDP on LTE
//                eacd.label = "NOT [UDP]";
//                ebcd.label = "[UDP] ONLY";
//                eacu.label = "ALL";
//                vc.addNode(nA);
//                vc.addNode(nB);
//                vc.addNode(nC);
//                vc.addEdge(eacd);
//                vc.addEdge(eac);
//                vc.addEdge(eacu);
//                vc.addEdge(ebcd);
//                vc.addEdge(ebc);
//                //vc.addEdge(ebcu);
//                break;
//            case 2: // route UDP and TCP on LTE
//                eacd.label = "NOT [UDP, TCP]";
//                ebcd.label = "[UDP, TCP] ONLY";
//                eacu.label = "ALL";
//                vc.addNode(nA);
//                vc.addNode(nB);
//                vc.addNode(nC);
//                vc.addEdge(eacd);
//                vc.addEdge(eac);
//                vc.addEdge(eacu);
//                vc.addEdge(ebcd);
//                vc.addEdge(ebc);
//                //vc.addEdge(ebcu);
//                break;
//            default:
//                vc.addNode(nA);
//                vc.addNode(nB);
//                vc.addNode(nC);
//                vc.addEdge(eacd);
//                vc.addEdge(eac);
//                vc.addEdge(eacu);
//                vc.addEdge(ebcd);
//                vc.addEdge(ebc);
//                vc.addEdge(ebcu);
//
//        }
//    }

// --------------------------------------------------------------------- STACKED BAR GRAPH

    d_StackedBarGraph(params){
        var tag = params[0]; var p=1;
        var a = params[p]; p++;
        var values = params[p]; p++;
        var d = null;
        switch(a){
            case "wifi_stats":
                d = this.d_StackedBarGraph_WifiStats(tag, values);
                var fff = function(){
                    this.f_StackedBarGraph_WifiStats_Play( tag, values )
                }
                $( d ).ready( fff.bind(this) )
                break;
            default: console.log("BarGrafh_" + a + " not implementes" );
        }
        return d;
    }

    d_StackedBarGraph_WifiStats(tag, values){
        var div = this.hb.ce("DIV");

        var r0 = this.hb.ceROW();
        $( div ).append(r0);
            var c = this.hb.ceCOL("xs",2);
            $( r0 ).append(c)
                var btn = this.hb.ce("BUTTON");
                $( c ).append(btn);
                btn.id = "BTN_" + values["hwaddr"]
                $( btn ).attr("type", "button");
                $( btn ).attr("style", "margin: 0px 2px;");
                $( btn ).attr("title", "play");
                var ico = this.hb.ceFAI("fa-play");
                $( ico ).addClass("fa-2x");
                $( btn ).prepend(ico);
                var f_Play = function(){
                    if( this.play ){
                        this.play = false;
                        $( btn ).attr("title", "play");
                        $( btn ).empty();
                        var ico = this.hb.ceFAI("fa-play");
                        $( ico ).addClass("fa-2x");
                        $( btn ).prepend(ico);
                    }
                    else{
                        this.play = true;
                        $( btn ).attr("title", "stop");
                        $( btn ).empty();
                        var ico = this.hb.ceFAI("fa-stop");
                        $( ico ).addClass("fa-2x");
                        $( btn ).prepend(ico);
                        this.f_StackedBarGraph_WifiStats_Play( tag, values )
                    }
                }
                $( btn ).click( f_Play.bind(this) )

        var r1 = this.hb.ceROW();
        $( div ).append(r1);
            var c = this.hb.ceCOL("xs", 12);
            $( r1 ).append(c);
                var d = this.hb.ce("DIV");
                $( c ).append(d);
                d.id = "SBG_" + values["hwaddr"]
                var ff = function(){
                    var axis = ['x', ['ed', 'rx', 'tx', 'idle']]
                    var labels = ['ed', 'rx', 'tx', 'idle'];
                    var stacked = true;
                    var graph = Morris.Bar({
                        element: "SBG_" + values["hwaddr"],
                        data: [],
                        xkey: axis[0],
                        ykeys: axis[1],
                        labels: labels,
                        stacked: stacked,
                    });
                    this.graph = graph;
                    this.f_StackedBarGraph_WifiStats_UpdateBarGraph(values["wifi_stats"]);
                }
                setTimeout(ff.bind(this), 1/2*this.delay)

        return div;
    }

    f_StackedBarGraph_WifiStats_Play( tag, values ){
        this.qe.scheduleQuery("GET", [tag], null, null, this.cache.update.bind(this.cache));
        var ff = function(){
       if( tag === "wtps" )
                var supp = this.hb.getKeyValue(tag, values["addr"] )["supports"];
            else if( tag === "lvaps"){
                var keyValue = Object.keys( values["tx_policies"] )[0]; // TODO EMP_if: barbatrucco?
                var supp = this.hb.getKeyValue(tag, keyValue )["blocks"];
            }
            var el = null
            for(var i=0; i<supp.length; i++){
                if( supp[i]["hwaddr"] === values["hwaddr"] ){
                    el = supp[i];
                    break;
                }
            }
            this.f_StackedBarGraph_WifiStats_UpdateBarGraph(el["wifi_stats"]);
            var id = this.hb.generateID([this.keys, tag, this.hb.conf.modalbox.tag]);
            if( this.play && this.hb.ge(id) != null){
                this.f_StackedBarGraph_WifiStats_Play.bind(this)(tag, values);
            }
        }
        setTimeout(ff.bind(this), 1/2*this.delay)
    }

    f_StackedBarGraph_WifiStats_setData( values ){
        var ed = [];
        var rx = [];
        var tx = [];
        var idle = [];
        var timestamp = [];
        var data = [];
        var tmp = [];
        for(  var i=0; i<values["ed"].length; i++){
            timestamp[i] = values["ed"][i].timestamp;
            if( values["ed"][i].sample == 200){
                ed[i] = 0;
                rx[i] = 0;
                tx[i] = 0;
                idle[i] = 0;
            }
            else{
                idle[i] = 100 - values["ed"][i].sample;
                ed[i] = values["ed"][i].sample - ( values["rx"][i].sample + values["tx"][i].sample );
                rx[i] = values["rx"][i].sample;
                tx[i] = values["tx"][i].sample
            }
            data.push({ x: Math.floor(timestamp[i]/1000000), ed: ed[i], rx: rx[i], tx: tx[i], idle: idle[i] })
            if( i+1 < values["ed"].length && values["ed"][i].timestamp > values["ed"][i+1].timestamp ){
                tmp = JSON.parse(JSON.stringify(data));
                data = [];
            }
//            console.log( idle[i] + ed[i] + rx[i] + tx[i] )
        }
        data = data.concat(tmp);
        return data;
    }

    f_StackedBarGraph_WifiStats_UpdateBarGraph( values ){
        var data = this.f_StackedBarGraph_WifiStats_setData(values);
        this.graph.setData(data);
    }

}
