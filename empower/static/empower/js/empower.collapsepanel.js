class EmpCollapsePanel{

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

    }

    getID(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.collapsepanel.tag] );
        return this.hb.generateID( keys );
    }

    getID_TITLE(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.collapsepanel.elements.title] );
        return this.hb.generateID( keys );
    }

    getID_ICON(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.collapsepanel.elements.icon] );
        return this.hb.generateID( keys );
    }

    getID_COLLAPSINGPANEL(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.collapsepanel.elements.collapsingpanel] );
        return this.hb.generateID( keys );
    }

    getID_HEADER(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.collapsepanel.elements.header] );
        return this.hb.generateID( keys );
    }

    create(title, color=null, iconname=null, keys=null){

        if (color === null){ color = "primary"; }
        if (iconname === null){ iconname = "fa-question-circle"; }

        var cp = this.hb.cePANEL();
        cp.id = this.getID(keys);
        $( cp ).addClass("panel panel-"+color);

            var ph = this.hb.cePANEL_H();
            ph.id = this.getID_HEADER(keys);
            $( cp ).append(ph);
            // building HEADER
                var r = this.hb.ceROW();
                $( ph ).append(r);

                    var c0 = this.hb.ceCOL("xs", 2);
                    $( r ).append(c0);
                        var icon = this.hb.ceFAI(iconname);
                        icon.id = this.getID_ICON(keys);
                        $( icon ).addClass("fa-4x");
                        $( c0 ).append(icon);

                    var c1 = this.hb.ceCOL("xs", 10);
                    $( r ).append(c1);
                        var ttl = this.hb.ce("DIV");
                        ttl.id = this.getID_TITLE(keys);
                        $( ttl ).addClass("huge");
                        $( ttl ).text(title);
                        $( c1 ).append(ttl);


            var body = this.hb.cePANEL_B();
            $( cp ).append(body);
            body.id = this.getID_COLLAPSINGPANEL(keys);
            $( body ).addClass("panel-collapse collapse in");

        return cp;
    }

    remove(keys){
        $( "#"+this.getID(keys) ).remove();
    }

    update(title=null, color=null, iconname=null, keys=null){
        if (title !== null){
            $( "#"+this.getID_TITLE(keys) ).text(title);
        }

        if (color !== null){
            $( "#"+this.getID(keys) ).removeClass().addClass("panel panel-"+color);
        }

        if (iconname !== null){
            $( "#"+this.getID_ICON(keys) ).removeClass().addClass("fa "+iconname+" fa-4x");
        }
    }

    updateTitle(title, keys=null){
        this.update( title, null, null, keys );
    }

    updateColor(color, keys=null){
        this.update( null, color, null, keys );
    }

    updateIcon(iconname, keys=null){
        this.update( null, null, iconname, keys );
    }

    updateMargin( t=0, r=0, b=40, l=0, keys=null){
        $( "#"+this.getID(keys) ).attr("style", "margin: "+t+"px "+r+"px "+b+"px "+l+"px;")
    }

    hideHeader(){

    }

    setL2Panel(keys=null){
        //console.log("doing margin");
        $( "#"+this.getID(keys) ).removeClass();
        $( "#"+this.getID_HEADER(keys) ).addClass("hide");
        this.updateMargin(10,20,20,20, keys);
    }
}
