class EmpNetGraphBox{

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

        this.box = null;
        this.netGraphList = {};

    }

    getID(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.netgraphbox.tag] );
        return this.hb.generateID( keys );
    }

    create(){

        var box = this.hb.ce("DIV");
        box.id = this.getID();
        $( box ).css("padding", "10px 5px")
        this.box = box;

        return box;
    }

    removeGraph(type){
        if( type in this.netGraphList ){
            var graph = this.netGraphList[type];
            $( "#" + graph.getID() ).remove();
            delete this.netGraphList[type];
        }
    }

    addGraph(type, params){ // params = [tag, a, values]
        var graph = new EmpNetGraph(this.keys)
        this.netGraphList[type] = graph;
        $( this.box ).append( graph.create(type,params) );
    }

}

