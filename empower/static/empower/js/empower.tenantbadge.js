class EmpTenantBadge{

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
        var keys = keys.concat( [this.hb.conf.tenantbadge.tag] );
        return this.hb.generateID( keys );
    }

    getID_PANEL_H(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.tenantbadge.elements.badgepanelH] );
        return this.hb.generateID( keys );
    }

    getID_PANEL_F(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.tenantbadge.elements.badgepanelF] );
        return this.hb.generateID( keys );
    }

    create(tenant, colsize="xs", coln=1, color=null, func=null, keys=null){

        var badge = this.hb.ceCOL(colsize, coln);
        badge.id = this.getID(keys);
        $( badge ).click(func);

            var p =  this.hb.cePANEL();
            $( badge ).append(p);
            $( p ).addClass("panel-"+color);

                var ph = this.hb.cePANEL_H();
                $( p ).append(ph);
                ph.id = this.getID_PANEL_H();
                var pf = this.hb.cePANEL_F();
                $( p ).append(pf);
                pf.id = this.getID_PANEL_F();

                    var rH = this.hb.ceROW();    // HEADER
                    $( ph ).append(rH);
                        var c1 = this.hb.ceCOL("xs", 3);
                        $( rH ).append(c1);
                            var rr = this.hb.ceROW();
                            $( c1 ).append(rr);
                            var cc = this.hb.ceCOL("xs",12);
                            $( rr ).append(cc);
                            var iconname = (tenant.bssid_type === "unique")? "fa-comment-o" : "fa-comments-o"
                                var i1 = this.hb.ceFAI(iconname);
                                $( cc ).append(i1)
                                $( i1 ).addClass("fa-3x");
                            var rr = this.hb.ceROW();
                            $( c1 ).append(rr);
                            var cc = this.hb.ceCOL("xs",12);
                            $( rr ).append(cc);
                                var span = this.hb.ce("SPAN");
                                $( cc ).append(span);
                                $( span ).text( tenant.bssid_type.toUpperCase() )

                        var c2 = this.hb.ceCOL("xs", 9);
                        $( rH ).append(c2);
                        $( c2 ).addClass("text-right");
                            var rr = this.hb.ceROW();
                            $( c2 ).append(rr);
                            var cc = this.hb.ceCOL("xs",12);
                            $( rr ).append(cc);
                                var span = this.hb.ce("SPAN");
                                $( cc ).append(span);
                                $( span ).css("font-size", "30px");
                                $( span ).text( tenant.tenant_name );
                            var rr = this.hb.ceROW();
                            $( c2 ).append(rr);
                            var cc = this.hb.ceCOL("xs",12);
                            $( rr ).append(cc);
                                var span = this.hb.ce("SPAN");
                                $( cc ).append(span);
                                $( span ).css("font-size", "10px");
                                $( span ).text( tenant.tenant_id );

                    var s1 = this.hb.ce("SPAN");
                    $( s1 ).addClass("pull-left text-"+color);
                    $( s1 ).text("Select tenant");
                    $( pf ).append(s1);

                    var s2 = this.hb.ce("SPAN");
                    $( s2 ).addClass("pull-right text-"+color);
                    //s2.onclick= func;
                    $( pf ).append(s2);

                    var i2 = this.hb.ceFAI("fa-arrow-circle-right");
                        //i2.id = this.getID_FUNCTION(keys);
                        //$( i2 ).click(func);
                    $( s2 ).append(i2);

                    var cf = this.hb.ceCLEARFIX();
                    $( pf ).append(cf);

//                    var rF = this.hb.ceROW();   // FOOTER with overview infos
//                    $( pf ).append(rF);
//                        var overviewList = {};
//                        overviewList["clients"] = [ "fa-laptop", ["lvaps", "ues"] ];
//                        overviewList["devices"] = [ "fa-hdd-o", ["wtps", "cpps", "vbses"] ];
//                        overviewList["components"] = [ "fa-plug", ["components"] ];
//                        var nCol = Object.keys(overviewList).length*2;
//                        var c1 = this.hb.ceCOL("xs",(12-nCol)/2);
//                        $( rF ).append(c1);
//                        for( var tag in overviewList ){
//                            var el = overviewList[tag];
//                            var c = this.hb.ceCOL("xs",2);
//                            $( rF ).append(c);
//                            $( c ).css("border", "1px solid #ccc");
//                            $( c ).css("margin", "2px");
//                            $( c ).addClass("text-center");
//                            $( c ).attr("title", tag);
//                                var r0 = this.hb.ceROW();
//                                $( c ).append(r0);
//                                    var c0 = this.hb.ceCOL("xs",12);
//                                    $( r0 ).append(c0);
//                                        var i0 = this.hb.ceFAI(el[0]);
//                                        $( c0 ).append(i0);
//                                        $( i0 ).addClass("fa-fw");
//                                var r1 = this.hb.ceROW();
//                                $( c ).append(r1);
//                                    var c1 = this.hb.ceCOL("xs",12);
//                                    $( r1 ).append(c1);
//                                        var span = this.hb.ce("SPAN");
//                                        $( c1 ).append(span);
//                                        var cntr = 0;
//                                        for( var i=0; i<el[1].length; i++ ){
//                                            if( this.hb.isArray(tenant[ el[1][i] ]) ){
//                                                cntr += tenant[ el[1][i] ].length;
//                                            }
//                                            else{
//                                                cntr += Object.keys(tenant[ el[1][i] ]).length;
//                                            }
//                                        }
//                                        $( span ).text(cntr)
//                        }
//                        var c2 = this.hb.ceCOL("xs",(12-nCol)/2);
//                        $( rF ).append(c2);

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