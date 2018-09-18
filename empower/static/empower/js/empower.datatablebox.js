class EmpDataTableBox{

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

        this.datatable = new EmpDataTable(keys);
        this.buttonbox = new EmpButtonBox(keys);

    }

    getID(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.datatablebox.tag] );
        return this.hb.generateID( keys );
    }

    create(obj, bdata, keys=null){

        var id = this.getID(keys);
        if ($( "#"+id ).length > 0){
            console.warn("EmpDataTableBox "+id+" already available")
            return null;
        }

        var tag = this.hb.mapName(obj);

        var r =  this.hb.ceROW();
        r.id = id;

            var rdt = this.hb.ceROW();
            $( rdt ).attr("style", "margin:10px 20px; padding: 5px;");
        $( r ).append(rdt)

            $( rdt ).append( this.datatable.create(tag, keys) );

            var rbbx = this.hb.ceROW();
            $( rbbx  ).attr("style", "margin:0px 20px; padding: 5px;");//" border: 1px solid  #e7e7e7 !important");
        $( r ).append(rbbx );

        //console.log(bdata);

            $( rbbx  ).append( this.buttonbox.create(bdata, keys));

        return r;
    }

    remove(keys=null){
        $( "#"+this.getID(keys) ).remove();
    }

    show(show, keys=null){
        if (show){
            $( "#"+this.getID(keys) ).removeClass("hide");
        }
        else{
            $( "#"+this.getID(keys) ).addClass("hide");
        }
    }

    makeResponsive(keys=null){
        return this.datatable.makeResponsive(keys);
    }
}
