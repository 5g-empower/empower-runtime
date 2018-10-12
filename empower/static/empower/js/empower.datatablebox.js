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
        var tag = this.hb.mapName2Tag(obj);

        var id = this.getID(keys);
        if ($( "#"+id ).length > 0){
            console.warn("EmpDataTableBox "+id+" already available")
            return null;
        }
        var box = this.hb.cePANEL();
        box.id = id;
        $( box ).addClass("panel panel-info")

            var boxh = this.hb.cePANEL_H();
            $( box ).append(boxh);
            $( boxh  ).css("padding", "5px")
                var title = this.hb.ce("SPAN");
                $( boxh ).append(title);
                var txt = this.hb.mapName2Title(tag);
                $( title ).text(txt);

            var body = this.hb.cePANEL_B();
            $( box ).append(body);
            $( body ).css("margin", "10px 20px")
            $( body ).css("padding", "5px")
            $( body ).append( this.datatable.create(tag, keys) );

            var boxf = this.hb.cePANEL_F();
            $( box ).append(boxf);
            $( boxf ).css("padding", "5px");
        //console.log(bdata);
            $( boxf  ).append( this.buttonbox.create(bdata, keys) );

            var cf = this.hb.ceCLEARFIX();
            $( boxf ).append(cf);

        return box;
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
