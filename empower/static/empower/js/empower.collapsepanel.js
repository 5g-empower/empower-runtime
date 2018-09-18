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

        if (color === null){
            color = "primary";
        }
        if (iconname === null){
            iconname = "fa-question-circle";
        }


        var ecp = this.hb.cePANEL();
        ecp.id = this.getID(keys);
        $( ecp ).addClass("panel panel-"+color);
        $( ecp ).attr("style","margin-bottom: 40px");

            var ph = this.hb.cePANEL_H();
            ph.id = this.getID_HEADER(keys);
        $( ecp ).append(ph);

                var r1 = this.hb.ceROW();
            $( ph ).append(r1);

                    var d1 = this.hb.ceCOL("xs", 1);
                $( r1 ).append(d1);

                    //     var a1 = this.hb.ce("A");
                    //     $( a1 ).attr("data-toggle", "collapse");
                    //     $( a1 ).attr("href", "#"+this.getID_COLLAPSINGPANEL(keys));
                    // $( d1 ).append(a1);

                        var i1 = this.hb.ceFAI(iconname);
                        i1.id = this.getID_ICON(keys);
                        $( i1 ).addClass("fa-4x");
                    $( d1 ).append(i1);

                    var d2 = this.hb.ceCOL("xs", 11);
                    $( d2 ).addClass("text-left")
                $( r1 ).append(d2);

                        var d3 = this.hb.ce("DIV");
                        d3.id = this.getID_TITLE(keys);
                        $( d3 ).addClass("huge");
                        $( d3 ).text(title);
                    $( d2 ).append(d3);

                            var s1 = this.hb.ce("SPAN");
                            $( s1 ).addClass("pull-right");
                        $( d3 ).append(s1);

/*
                                var a1 = this.hb.ce("A");
                                $( a1 ).attr("data-toggle", "collapse");
                                $( a1 ).attr("href", "#"+this.getID_COLLAPSINGPANEL(keys));
                            $( s1 ).append(a1);

                                    var i2 = this.hb.ceFAI("fa-sort text-default");
                                $( a1 ).append(i2);
*/
            var pc = this.hb.cePANEL_B();
            pc.id = this.getID_COLLAPSINGPANEL(keys);
            $( pc ).addClass("panel-collapse collapse in");
        $( ecp ).append(pc);

        return ecp;
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
        //$( "#"+this.getID_HEADER(keys) ).addClass("hide");
        $( "#"+this.getID_HEADER(keys) ).css("padding", '0px 10px');
        $( "#"+this.getID_TITLE(keys) ).addClass("hide");
        $( "#"+this.getID_ICON(keys) ).removeClass("fa-4x");
        this.updateMargin(10,20,20,20, keys);
    }
}
