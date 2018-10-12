class EmpBadge{

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
        var keys = keys.concat( [this.hb.conf.badge.tag] );
        return this.hb.generateID( keys );
    }

    getID_PANEL(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.badge.elements.badgepanel] );
        return this.hb.generateID( keys );
    }

    getID_ICON(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.badge.elements.icon] );
        return this.hb.generateID( keys );
    }

    getID_STATUS(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.badge.elements.status] );
        return this.hb.generateID( keys );
    }

    getID_TITLE(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.badge.elements.title] );
        return this.hb.generateID( keys );
    }

    getID_FOOTER(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.badge.elements.footer] );
        return this.hb.generateID( keys );
    }

    getID_FUNCTION(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.badge.elements.function] );
        return this.hb.generateID( keys );
    }

    create(title, colsize="xs", coln=1, color=null, iconname=null, status=0, func=null, keys=null){

        var badge = this.hb.ceCOL(colsize, coln);
        badge.id = this.getID(keys);

            var p =  this.hb.cePANEL();
            p.id = this.getID_PANEL(keys);
            $( p ).addClass("panel-"+color);
        $( badge ).append(p);

                var ph = this.hb.cePANEL_H();
            $( p ).append(ph);

                    var r = this.hb.ceROW();
                $( ph ).append(r);

                        var c1 = this.hb.ceCOL("xs", 3);
                    $( r ).append(c1);

                            var i1 = this.hb.ceFAI(iconname);
                            i1.id = this.getID_ICON(keys);
                            $( i1 ).addClass("fa-4x");
                        $( c1 ).append(i1);

                        var c2 = this.hb.ceCOL("xs", 9);
                        $( c2 ).addClass("text-right");
                    $( r ).append(c2);

                            var v = this.hb.ce("DIV");
                            v.id = this.getID_STATUS(keys);
                            $( v ).addClass("huge");
                            $( v ).text(status);
                        $( c2 ).append(v);

                            var n = this.hb.ce("DIV");
                            n.id = this.getID_TITLE(keys);
                            //$( n ).css("margin-top","5px");
                            //     var s = this.hb.ce("STRONG");
                            //     $( s ).text(title);
                            // $( n ).append(s);
                            // $( n ).addClass("");
                            $( n ).text(title);
                        $( c2 ).append(n);

                var pf = this.hb.cePANEL_F()
                pf.id = this.getID_FOOTER(keys);
            $( p ).append(pf);
                $( pf ).css("cursor","pointer");
                    var r = this.hb.ceROW();
                    $( pf ).append(r);
                        var c0 = this.hb.ceCOL("xs", 8);
                        $( r ).append(c0);
                    var s1 = this.hb.ce("SPAN");
                    $( s1 ).addClass("pull-left text-"+color);
                    $( s1 ).text("View details");
                            $( c0 ).append(s1);
                        var c1 = this.hb.ceCOL("xs", 4);
                        $( r ).append(c1);
                    var s2 = this.hb.ce("SPAN");
                    $( s2 ).addClass("pull-right text-"+color);
                            $( c1 ).append(s2);
                        var i2 = this.hb.ceFAI("fa-arrow-circle-right");
//                                i2.id = this.getID_FUNCTION(keys);
                    $( s2 ).append(i2);

                    var cf = this.hb.ceCLEARFIX();
                $( pf ).append(cf);

        return badge;
    };

    remove(keys=null){
        var spans = $( "#"+this.getID_FOOTER(keys) ).find("span");
        for (var i = 0; i , spans.length; i++)
            span[i].unbind();
        $( "#"+this.getID(keys) ).remove();
    }

    update(title, color=null, iconname=null, status=null, func=null, keys=null){
        if (title !== null){
            $( "#"+this.getID_TITLE(keys) ).text(title);
        }

        if (color !== null){
            $( "#"+this.getID_PANEL(keys) ).removeClass().addClass("panel panel-"+color);
            $( "#"+this.getID_FOOTER(keys) ).find("span.pull-left").removeClass().addClass("pull-left text-"+color);
            $( "#"+this.getID_FOOTER(keys) ).find("span.pull-right").removeClass().addClass("pull-right text-"+color);
        }

        if (iconname !== null){
            $( "#"+this.getID_ICON(keys) ).removeClass().addClass("fa "+iconname+" fa-5x");
        }

        if (status !== null){
            $( "#"+this.getID_STATUS(keys) ).text(status);
        }

        if (func !== null){
//            $( "#"+this.getID_FUNCTION(keys) ).unbind().click(func);
            $( "#"+this.getID_FOOTER(keys) ).unbind().click(func);
//            $( "#"+this.getID(keys) ).unbind().click(func);
        }
    }

    updateTitle(text, keys=null){
        this.update( text, null, null, null, null, keys );
    }

    updateColor(color, keys=null){
        this.update( null, color, null, null, null, keys );
    }

    updateIcon(iconname, keys=null){
        this.update( null, null, iconname, null, null, keys );
    }

    updateStatus(status, keys=null){
        this.update( null, null, null, status, null, keys );
    }

    updateOnClick(onclick, keys=null){
        this.update( null, null, null, null, onclick, keys );
    }

    incrementStatus(keys=null){
        var v = parseInt( $( "#"+this.getID_STATUS(keys) ).text());
        this.updateTotal(v+1);
    }

    decrementTotal(keys=null){
        var v = parseInt( $( "#"+this.getID_STATUS(keys) ).text());
        this.updateTotal(v-1);
    }
}