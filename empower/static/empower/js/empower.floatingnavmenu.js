// TODO EMP_if: This class is simply the old one a bit updated. Further standardization needed

class EmpFloatingNavMenu{

    constructor(keys, hb){

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

    getID(keys=null){   // TODO EMP_if: da controllare!
        // if (keys === null)
        //     keys = this.keys;
        // var keys = keys.concat( [this.hb.conf.floatingnavmenu.tag] );
        // return this.hb.generateID( keys );
        return "side-menu";
    }

    getID_NAVBARCOLLAPSE(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.floatingnavmenu.elements.navbarcollapse] );
        return this.hb.generateID( keys );
    }

    getID_LEV1MENU(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.floatingnavmenu.elements.lev1menu] );
        return this.hb.generateID( keys );
    }

    getID_LEV2MENU(keys=null, l1label){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.floatingnavmenu.elements.lev1menu, l1label] );
        return this.hb.generateID( keys );
    }

    create(keys=null){

        var nm = this.hb.ce("NAV");
        //$( nm ).addClass("navbar navbar-default navbar-static-top affix");
        $( nm ).addClass("navbar navbar-default");
        $( nm ).attr("role", "navigation");
        $( nm ).attr("style", "margin-bottom: 0; min-height:0px;");
        nm.id = this.getID(keys);

            var nh = this.hb.ce("DIV");
            $( nm ).addClass("navbar-header");
        $( nm ).append(nh);

                var btn = this.hb.ce("BUTTON");
                $( btn ).addClass("navbar-toggle");
                $( btn ).attr("type", "button");
                $( btn ).attr("data-toggle", "collapse");
                $( btn ).attr("data-target", "#"+this.getID_NAVBARCOLLAPSE( keys));
            $( nh ).append(btn);

                    var s = this.hb.ce("SPAN");
                    $( s ).addClass("sr-only");
                    $( s ).text("Toggle navigation");
                $( btn ).append(s);
                    s = this.hb.ce("SPAN");
                    $( s ).addClass("icon-bar");
                $( btn ).append(s);
                    s = this.hb.ce("SPAN");
                    $( s ).addClass("icon-bar");
                $( btn ).append(s);
                    s = this.hb.ce("SPAN");
                    $( s ).addClass("icon-bar");
                $( btn ).append(s);

            var nb = this.hb.ce("DIV");
            $( nb ).addClass("navbar-default sidebar");
            $( nb ).attr("role", "navigation");
            $( nb ).attr("style", "margin-top:10px;");
        $( nm ).append(nb);

                var sb = this.hb.ce("DIV");
                $( sb ).addClass("sidebar-nav navbar-collapse");
                sb.id = this.getID_NAVBARCOLLAPSE(keys);
            $( nb ).append(sb);

                    var sm = this.hb.ce("UL");
                    $( sm ).addClass("nav");
                    sm.id = this.getID_LEV1MENU(keys);
                $( sb ).append(sm);

        return nm;
    }

    createLev2Menu(keys, label, icon=null, color=null, ref=null, func=null, lcode){
        var li = this.hb.ce("LI");

            var a = this.hb.ce("A");
        $( li ).append(a);

                if (func !== null){
                    //console.log("createMenuItem ", func);
                    $( a ).click(func);
                }
                if (ref !== null){
                    //console.log("createMenuItem ", func);
                    $( a ).attr("href", "#"+ref);
                }


                if (icon !== null){
                    var i = this.hb.ceFAI(icon);
                    $( i ).addClass("fa-fw");
            $( a ).append(i);
                }

                var s1 = this.hb.ce("SPAN");
                $( s1 ).text(label);
                if (color !== null){
                    $( s1 ).addClass("text-"+color);
                }
            $( a ).append(s1);

                var s2 = this.hb.ce("SPAN");
                $( s2 ).addClass("fa arrow");
            $( a ).append(s2);

            var l2m = this.hb.ce("UL");
            l2m.id = this.getID_LEV2MENU(keys, lcode)
            $( l2m ).addClass("nav nav-second-level");
        $( li ).append(l2m);

        return li;
    }

    createMenuItem(keys=null, label, icon=null, color=null, ref=null, func=null){
        var li = this.hb.ce("LI");

            var a = this.hb.ce("A");

            if (func !== null){
                //console.log("createMenuItem ", func);
                $( a ).click(func);
            }
            if (ref !== null){
                //console.log("createMenuItem ", func);
                $( a ).attr("href", "#"+ref);
            }


        $( li ).append(a);

                var s0 = this.hb.ce("SPAN");
                if (color !== null){
                    $( s0 ).addClass("text-"+color);
                }
            $( a ).append(s0);

                    var i = this.hb.ceFAI(icon);
                    $( i ).addClass("fa-fw");
                $( s0 ).append(i);

                    var s = this.hb.ce("SPAN");
                    $( s ).text(" "+label);
                $( s0 ).append(s);

        return li;
    }

    addMenuItem(keys=null, menu=false, label, icon=null, color=null, ref=null, func=null, l1code=null){
        //console.log("CIAO");
        if (menu){
            var l2m = this.createLev2Menu( keys, label, icon, color, ref, func, l1code);
            $( "#"+this.getID_LEV1MENU( keys ) ).append( l2m );
        }
        else {
            var item = this.createMenuItem(keys, label, icon, color, ref, func);
            // console.log("ITEM", item);
            if (l1code != null){
                //console.log(this.getID_LEV2MENU( keys, l1code ));
                $( "#"+this.getID_LEV2MENU( keys, l1code ) ).append( item );
            }
            else{
                $( "#"+this.getID_LEV1MENU( keys ) ).append( item );
                // console.log("added item to #",this.getID_LEV1MENU( keys ));
                // console.log("keys ",this.keys);
            }
        }
    }
}
