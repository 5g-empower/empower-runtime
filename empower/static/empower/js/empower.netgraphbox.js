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
        this.netGraphList = [];

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

    addGraph(type, params){ // params = [tag, a, values]
        var graph = new EmpNetGraph(this.keys).create(type,params);
        this.netGraphList.push(graph);
        $( this.box ).append(graph);
    }

}

