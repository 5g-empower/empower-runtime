// Format Functions
/*
    HEADER ctrl = h
        type: i -> icon
        type: h -> header label
        type: d -> char separator
        type: k -> key header label
    BODY ctrl = d
        type: i -> icon
        type: a -> attribute value
        type: d -> char separator
        type: l -> list
        type: o -> object
*/

// DTable fancy functions

function ff_Tenant_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "h", "value": "Name"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "value": "ID",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "h", "value": "WTPs"},
                         ]);
        params.push( [ { "type": "h", "value": "CPPs"},
                         ]);
        params.push( [ { "type": "h", "value": "VBSes"},
                         ]);
        params.push( [ { "type": "h", "value": "UEs"},
                         ]);
        params.push( [ { "type": "h", "value": "PLMN ID"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "a", "attr": "tenant_name"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "attr": "tenant_id",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "l", "attr": "wtps"},
                         ]);
        params.push( [ { "type": "l", "attr": "cpps"},
                         ]);
        params.push( [ { "type": "l", "attr": "vbses"},
                         ]);
        params.push( [ { "type": "l", "attr": "ues"},
                         ]);
        params.push( [ { "type": "a", "attr": "plmn_id"},
                         ]);
    }
    return params;
};

function ff_Wtp_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "h", "value": "Label"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "value": "MAC Address",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "h", "value": "Last seen (date)"},
                         ]);
        params.push( [ { "type": "h", "value": "Status"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "a", "attr": "label"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "attr": "addr",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "a", "attr": "last_seen_ts"},
                         ]);
        params.push( [ { "type": "i", "icon": "fa-circle",
                            "attr": "state",
                            "color": {"disconnected": "#FF0000",
                                        "connected": "#FFFF00",
                                        "online":"#00FF00"} },
                         ]);
    }
    return params;
};

function ff_Cpp_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "h", "value": "Label"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "value": "MAC Address",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "h", "value": "Last seen (date)"},
                         ]);
        params.push( [ { "type": "h", "value": "Status"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "a", "attr": "label"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "attr": "addr",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "a", "attr": "last_seen_ts"},
                         ]);
        params.push( [ { "type": "i", "attr": "state",
                            "icon": "fa-circle",
                            "color": {"disconnected": "#FF0000",
                                        "connected": "#FFFF00",
                                        "online":"#00FF00"} },
                         ]);
    }
    return params;
};

function ff_Active_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "Component",
                            "style": "color:#0000FF" },
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "k", "attr": "component_id",
                            "style": "color:#0000FF" },
                         ]);
    }
    return params;
};

function ff_Vbs_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "h", "value": "Label"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "value": "MAC Address",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "h", "value": "Last seen (date)"},
                         ]);
        params.push( [ { "type": "h", "value": "Status"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "a", "attr": "label"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "attr": "addr",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "a", "attr": "last_seen_ts"},
                         ]);
        params.push( [ { "type": "i", "attr": "state",
                            "icon": "fa-circle",
                            "color": {"disconnected": "#FF0000",
                                        "connected": "#FFFF00",
                                        "online":"#00FF00"} },
                         ]);
    }
    return params;
};

function ff_Account_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "Username",
                            "style": "color:#0000FF" },
                        { "type": "d", "value": "( "},
                        { "type": "h", "value": "Role"},
                        { "type": "d", "value": " )"},
                         ]);
        params.push( [ { "type": "h", "value": "Email"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "k", "attr": "username",
                            "style": "color:#0000FF" },
                        { "type": "d", "value": "( "},
                        { "type": "a", "attr": "role"},
                        { "type": "d", "value": " )"},
                         ]);
        params.push( [ { "type": "a", "attr": "email"},
                         ]);
    }
    return params;
};

function ff_Ue_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "IMSI",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "h", "value": "UE id"},
                         ]);
        params.push( [ { "type": "h", "value": "RNTI"},
                         ]);
        params.push( [ { "type": "h", "value": "PLMN ID"},
                         ]);
        params.push( [ { "type": "h", "value": "VBS"},
                         ]);
        params.push( [ { "type": "h", "value": "State"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "k", "attr": "imsi",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "a", "attr": "ue_id"},
                         ]);
        params.push( [ { "type": "a", "attr": "rnti"},
                         ]);
        params.push( [ { "type": "a", "attr": "plmnid"},
                         ]);
        params.push( [ { "type": "a", "attr": "vbs"},
                         ]);
        params.push( [ { "type": "i", "attr": "state",
                            "icon": "fa-circle",
                            "color": {"ho_in_progress_removing": "#FF0000",
                                        "ho_in_progress_adding": "#FFFF00",
                                        "active":"#00FF00"} },
                         ]);
    }
    return params;
};

function ff_Lvap_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "MAC Address",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "h", "value": "SSID"},
                         ]);
        params.push( [ { "type": "h", "value": "WTP"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "k", "attr": "addr",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "a", "attr": "ssid"},
                         ]);
        params.push( [ { "type": "o", "attr": "wtp"},
                         ]);
    }
    return params;
};

function ff_Lvnf_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "h", "value": "State"},
                         ]);
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "LVNF ID",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "h", "value": "CPP"},
                         ]);
        params.push( [ { "type": "h", "value": "Tenant ID"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "a", "attr": "state"},
                         ]);
        params.push( [ { "type": "k", "attr": "lvnf_id",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "a", "attr": "cpp"},
                         ]);
        params.push( [ { "type": "a", "attr": "tenant_id"},
                         ]);
    }
    return params;
};

function ff_Acl_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "MAC Address",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "h", "value": "Laptop/Mobile"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "k", "attr": "addr",
                            "style": "color:#0000FF" },
                         ]);
        params.push( [ { "type": "a", "attr": "label"},
                         ]);
    }
    return params;
};

//-----------------------------------------------------------------------------------  fancy functions

function ff_draw(tag, a, values, ff_ID){
    var r = null
    var type = __DESC.d[tag].attr[a].type;
        switch(type){
        case __DESC.dt.LIST.a:
        case __DESC.dt.LIST.d:  // TODO EMP_if: qui values deve passare anche la chiave -> values = [key, dict[key]]
            if( a === "blocks")   r = ff_draw_Supports(tag, a, values, ff_ID);
                else if( a === "supports")   r = ff_draw_Supports(tag, a, values, ff_ID);
                else if( a === "network_ports")  r = ff_draw_NetworkPorts(tag, a, values, ff_ID);
                else if( a === "components" )    r = ff_draw_Components(tag, a, values, ff_ID);
                else if( a === "lvaps" )    r = ff_draw_Lvaps(tag, a, values, ff_ID);
                else if( a === "params" )    r = ff_draw_Params(tag, a, values, ff_ID);
                else console.log( "ff_draw LIST: " + tag + "." + a + " not implemented.")
                break;
            case __DESC.dt.OBJ.datapath:
            r = ff_draw_Datapath(tag, a, values, ff_ID);
                break;
        case __DESC.dt.STR.bssid_type:
            r = ff_draw_BSSID_type(values);
                break;
        case __DESC.dt.OBJ.networks:
            r = ff_draw_Networks(tag, a, values, ff_ID);
                break;
            case __DESC.dt.OBJ.ssids:
            r = ff_draw_SSIDS(tag, a, values, ff_ID);
                break;
        case __DESC.dt.STR.band: // TODO EMP_if: qui values deve passare anche il canale -> values = [band, channel]
            r = ff_draw_BAND(tag, a, values, ff_ID);
                break;
            default:
            r = __HB.ceROW();
            var c0 = __HB.ceCOL("xs",1);
            $( r ).append(c0);
            $( c0 ).css("visibility","hidden");
            if( __DESC.d[tag].attr[a].update ){
                var i = __HB.ceFAI( "fa-edit" );
            }
            else{
                var i = __HB.ceFAI( "fa-ban" );
            }
                $( c0 ).append(i)
                $( i ).addClass("fa-fw");
            var c1 = __HB.ceCOL("xs",4);
            $( r ).append(c1);
            $( c1 ).text( a + ": " );
            var c2 = __HB.ceCOL("xs",7);
            $( r ).append(c2);
            c2.id = ff_ID( a );
            var txt = values;
            if( typeof values === "undefined") txt = "...";
            $( c2 ).text( txt );
            if( __DESC.d[tag].attr[a].isKey )
                $( c2 ).css("color", "#0000FF")
                var ff_over = function(){
                    $( c0 ).css("visibility","visible");
                }
                $( r ).mouseover(ff_over);
                var ff_leave = function(){
                    $( c0 ).css("visibility","hidden");
                }
                $( r ).mouseleave(ff_leave);
        }
        return r;
}

function ff_draw_SSIDS(tag, a, ssids, ff_ID){
    var r = __HB.ceROW();
        var c0 = __HB.ceCOL("xs",1);
        $( r ).append(c0);
        $( c0 ).css("visibility","hidden");
        if( __DESC.d[tag].attr[a].update ){
            var i = __HB.ceFAI( "fa-edit" );
        }
        else{
            var i = __HB.ceFAI( "fa-ban" );
        }
        $( c0 ).append(i)
        $( i ).addClass("fa-fw");
        var c1 = __HB.ceCOL("xs",4);
        $( r ).append(c1);
        $( c1 ).text( "ssids: " );
        var c2 = __HB.ceCOL("xs",7);
        $( r ).append(c2);
        c2.id = ff_ID( a );
        var str = "[ ";
        for( var i=0; i< ssids.length; i++ ){
            str += ssids[i] + ", "
        }
        str += " ]"
        $( c2 ).text(str);
    return r;
}

function ff_draw_Networks(tag, a, values, ff_ID){
    var r = __HB.ceROW();
        var c0 = __HB.ceCOL("xs",1);
        $( r ).append(c0);
        $( c0 ).css("visibility","hidden");
        if( __DESC.d[tag].attr[a].update ){
            var i = __HB.ceFAI( "fa-edit" );
        }
        else{
            var i = __HB.ceFAI( "fa-ban" );
        }
        $( c0 ).append(i)
        $( i ).addClass("fa-fw");
        var c1 = __HB.ceCOL("xs",4);
        $( r ).append(c1);
        $( c1 ).text( "networks: " );
        var c2 = __HB.ceCOL("xs",7);
        $( r ).append(c2);
        c2.id = ff_ID( a );
        var str = "";
        for( var i=0; i< values.length; i++ ){
            str += values[i][0] + " - " + values[i][1] + "\n"
        }
        str += ""
        $( c2 ).text(str);
    return r;
}

function ff_draw_BAND(tag, a, values, ff_ID){
    var band = values[0];
    var channel = values[1];
    var r = __HB.ceROW();
        var c0 = __HB.ceCOL("xs",1);
        $( r ).append(c0);
        $( c0 ).css("visibility","hidden");
        if( __DESC.d[tag].attr[a].update ){
            var i = __HB.ceFAI( "fa-edit" );
        }
        else{
            var i = __HB.ceFAI( "fa-ban" );
        }
        $( c0 ).append(i)
        $( i ).addClass("fa-fw");
        var c1 = __HB.ceCOL("xs",4);
        $( r ).append(c1);
        $( c1 ).text( "band: " );
        var c2 = __HB.ceCOL("xs",7);
        $( r ).append(c2);
        c2.id = ff_ID( a );
        var txt = "";
        switch(band){
            case "L20":
                if( channel < 14 ) txt = "801.11a"
                else txt = "801.11g"
            break;
            case "HT20": txt = "801.11n"
            break;
            case "HT40": txt = "801.11n"
            break;
        }
        $( c2 ).text(txt)
    return r;
}

function ff_draw_BSSID_type(values){
    var d = __HB.ce("DIV");
    var params = { "unique": "fa-comment-o", "shared": "fa-comments-o"};

        var r0 = __HB.ceROW();
        $( d ).append(r0);
        $( r0 ).css("margin", "0% 10%")
            var i = __HB.ceFAI( params[ values ]);
            $( r0 ).append(i)
            $( i ).addClass("fa-4x");
        var r1 = __HB.ceROW();
        $( d ).append(r1);
        $( r1 ).css("margin", "0% 10%")
            var s = __HB.ce("SPAN");
            $( r1 ).append(s)
            $( s ).text( values.toUpperCase() );
    return d;
}

function ff_draw_Components(tag, a, values, ff_ID){
    var el = values[0];
    var values = values[1];
    var p = __HB.cePANEL();
    $( p ).addClass("panel-default");
    $( p ).css("margin", "20px");
    $( p ).css("border", "1px solid #ccc");
        var pH = __HB.cePANEL_H();
        $( p ).append(pH);
        var pB = __HB.cePANEL_B();
        $( p ).append(pB);

        $( pH ).text(el)
        var pre = __HB.ce("PRE");
        $( pB ).append(pre)
        var txt = JSON.stringify(values, undefined, 4);
        $( pre ).html( __HB.syntaxHighlight(txt));
//            $( pre ).css("margin", "20px")

    return p;
}

function ff_draw_Params(tag, a, values, ff_ID){
    var el = values[0];
    var values = values[1];
    var d = __HB.ce("DIV");
    $( d ).css("margin", "20px");
        var r = __HB.ceROW();
        $( d ).append(r)
            var c0 = __HB.ceCOL("xs",2);
            $( r ).append(c0);
                var span = __HB.ce("SPAN");
                $( c0 ).append(span);
                $( span ).text(el + ":");
            var c1 = __HB.ceCOL("xs",10);
            $( r ).append(c1);
                var pre = __HB.ce("PRE");
                $( c1 ).append(pre)
                var txt = JSON.stringify(values, undefined, 4);
                $( pre ).html( __HB.syntaxHighlight(txt));

    return d;
}

function ff_draw_Datapath(tag, a, values, ff_ID){
    var p = __HB.cePANEL();
    $( p ).addClass("panel-default");
    $( p ).css("margin", "20px");
    $( p ).css("border", "1px solid #ccc");
        var pH = __HB.cePANEL_H();
        $( p ).append(pH);
        var pB = __HB.cePANEL_B();
        $( p ).append(pB);
        var pF = __HB.cePANEL_F();
        $( p ).append(pF);
            var params = [];
                params.push( { "attr": "dpid", "style": "color:#0000FF" } );
                params.push( { "attr": "ip_addr"} );
            var btns = [];
                btns.push( { "dict": "network_ports"} );

        for( var i=0; i<params.length; i++){
            var r = ff_draw( "datapath", params[i].attr, values[ params[i].attr ], ff_ID);
            $( pB ).append(r);
            if( params[i].style )
                $( r ).attr("style", params[i].style );
        }

        var rF = __HB.ceROW();
        $( pF ).append(rF);
        for( var i=0; i<btns.length; i++){
            var c = __HB.ceCOL("xs", 1);
            $( rF ).append(c);
            var attr = "";
                if( "dict" in btns[i] ){
                    attr = btns[i]["dict"];
                    var type = __DESC.d[a].attr[attr].type;
                    var btn = __HB.ce("BUTTON");
                    $( c ).append(btn);
                    $( btn ).attr("type", "button");
                    $( btn ).attr("style", "margin: 0px 2px;");
                    $( btn ).attr("title", "show " + attr);
                    $( btn ).text( attr );
                    if( !$.isEmptyObject(values[attr]) ){
                        var div = ff_draw(a, attr, values[attr], ff_ID);
                        $( pB ).append(div);
                        $( div ).addClass("hide");
                        var f_Click = function(){
                            $( div ).hasClass("hide")? $( div ).removeClass("hide") : $( div ).addClass("hide");
        }
                        $( btn ).click(f_Click);
                    }
                    else{
                        $( btn ).addClass("hide")
                    }
                }
        }
    return p;
}

function ff_draw_NetworkPorts(tag, a, values, ff_ID){
    var d = __HB.ce("DIV");
    for( var nP in values ){
        var p = __HB.cePANEL();
        $( d ).append(p);
        $( p ).addClass("panel-default");
        $( p ).css("margin", "20px");
        $( p ).css("padding", "20px");
        $( p ).css("border", "1px solid #ccc");
            var r = __HB.ceROW();
            $( p ).append(r);
                var c0 = __HB.ceCOL("xs",2);
                $( r ).append(c0);
                    var r0 = __HB.ceROW();
                    $( c0 ).append(r0);
                    $( r0 ).css("margin", "0% 18%")
                        var i = __HB.ceFAI( "fa-road");
                        $( r0 ).append(i)
                        $( i ).addClass("fa-5x");
                    var r1 = __HB.ceROW();
                    $( c0 ).append(r1);
                    $( r1 ).css("margin", "0% 10%")
                        var s = __HB.ce("SPAN");
                        $( r1 ).append(s)
                        $( s ).text( "Network Port " + values[nP]["port_id"] );
                var c1 = __HB.ceCOL("xs",10);
                $( r ).append(c1);
            var params = [];
                params.push( { "attr": "hwaddr", "style": "color:#0000FF" } );
                params.push( { "attr": "dpid"} );
                params.push( { "attr": "iface"} );
                params.push( { "attr": "neighbour"} );
                params.push( { "attr": "port_id"} );
            for( var i=0; i<params.length; i++){
                    var rr = ff_draw( "network_ports", params[i].attr, values[nP][ params[i].attr ], ff_ID);
                    $( c1 ).append(rr);
                if( params[i].style )
                        $( rr ).attr("style", params[i].style );
            }
    }
    return d;
}

function ff_draw_Lvaps(tag, a, values, ff_ID){
    var el = values[0];
    var values = values[1];
    var p = __HB.cePANEL();
    $( p ).addClass("panel-default");
    $( p ).css("margin", "20px");
    $( p ).css("border", "1px solid #ccc");
        var pH = __HB.cePANEL_H();
        $( p ).append(pH);
        var pB = __HB.cePANEL_B();
        $( p ).append(pB);
        var pF = __HB.cePANEL_F();
        $( p ).append(pF);
            var params = [];
                params.push( { "attr": "addr", "style": "color:#0000FF" } );
                params.push( { "attr": "assoc_id"} );
                params.push( { "attr": "association_state"} );
                params.push( { "attr": "authentication_state"} );
                params.push( { "attr": "lvap_bssid"} );
                params.push( { "attr": "net_bssid"} );
                params.push( { "attr": "ssid"} );
                params.push( { "attr": "ssids"} );
                params.push( { "attr": "state"} );
                params.push( { "attr": "supported_band"} );
            var btns = [];
                btns.push( { "dict": "blocks"} );
                btns.push( { "dict": "wtp"} );

        $( pH ).text(el);
        for( var i=0; i<params.length; i++){
            var r = ff_draw( "lvaps", params[i].attr, values[ params[i].attr ], ff_ID);
            $( pB ).append(r);
            if( params[i].style )
                $( r ).attr("style", params[i].style );
        }
    return p;
}

function ff_draw_Supports(tag, a, values, ff_ID){
    var p = __HB.cePANEL();
    $( p ).addClass("panel-default");
    $( p ).css("margin", "20px");
    $( p ).css("border", "1px solid #ccc");
        var pH = __HB.cePANEL_H();
        $( p ).append(pH);
        var pB = __HB.cePANEL_B();
        $( p ).append(pB);
        var pF = __HB.cePANEL_F();
        $( p ).append(pF);
            var params = [];
                params.push( { "attr": "hwaddr", "style": "color:#0000FF" } );
                params.push( { "attr": "addr"} );
                params.push( { "attr": "channel"} );
            var btns = [];
                btns.push( { "graph": "wifi_stats"} );

        for( var i=0; i<params.length; i++){
            var r = ff_draw( "supports", params[i].attr, values[ params[i].attr ], ff_ID);
            $( pB ).append(r);
            if( params[i].style )
                $( r ).attr("style", params[i].style );
        }
            var r = ff_draw( "supports", "band", [ values[ "band" ], values["channel"] ], ff_ID);
            $( pB ).append(r);

        var rF = __HB.ceROW();
        $( pF ).append(rF);
        for( var i=0; i<btns.length; i++){
            var c = __HB.ceCOL("xs", 1);
            $( rF ).append(c);
            var attr = "";
                if( "graph" in btns[i] ){
                    attr = btns[i]["graph"];
                    var btn = __HB.ce("BUTTON");
                    $( c ).append(btn);
                    $( btn ).attr("type", "button");
                    $( btn ).attr("style", "margin: 0px 2px;");
                    $( btn ).attr("title", "show " + attr);
                    $( btn ).text( attr );
                    if( !$.isEmptyObject(values[attr]) ){
                        var graph = new EmpNetGraphBox( __USERNAME );
                        var params = [tag, attr, values];
                        var bar = graph.create();
                        $( pB ).append(bar);
                        graph.addGraph("stackedBarGraph", params); // params = [tag, a, values]
                        $( bar ).addClass("hide")
                        var f_Click = function(){
                            $( bar ).hasClass("hide")? $( bar ).removeClass("hide") : $( bar ).addClass("hide");
                }
                        $( btn ).click(f_Click);
            }
            else{
                        $( btn ).addClass("hide")
            }
                }
        }
    return p;
}

// ------------------------------------------------------------------------------------- INPUT FIELD

function ff_drawInputField(tag, a, values, ff_ID){
    var r = null
    var type = __DESC.d[tag].attr[a].type;
        switch(type){
            case __DESC.dt.STR.def:
            case __DESC.dt.STR.mac:
            case __DESC.dt.STR.uuid:
            case __DESC.dt.STR.plmnid:
            case __DESC.dt.STR.owner:
            case __DESC.dt.STR.dpid:
            case __DESC.dt.STR.ip_addr:
        case __DESC.dt.NUM.intgr:
            r = ff_String_IF(tag, a, values, ff_ID);
                break;
            case __DESC.dt.STR.bssid_type:
            case __DESC.dt.STR.role:
            case __DESC.dt.NUM.bool:
            r = ff_FixedString_IF(tag, a, values, ff_ID);
                break;
            default:
                console.log("ff_drawInputField: " + type.type_id + " type not impemented");
        }
        return r;
}

function ff_String_IF(tag, a, values, ff_ID){
    var r = __HB.ceROW();
    var type = __DESC.d[tag].attr[a].type;
            var div = __HB.ce("DIV");
        $( r ).append(div);
            $( div ).addClass("form-group");
                var l1 = __HB.ce("LABEL");
                $( div ).append(l1);
                    var i1 = __HB.ce("INPUT");
                    $( l1 ).append(i1);
                i1.id = ff_ID( a ) + "_IF";
                    $( i1 ).addClass("form-control");
                $( i1 ).attr("value", values);
                var ff_focusOut = function(){
                    var ctrl = false;
                    var value = $( i1 )[0].value;
                    if( type.validation ){
                        ctrl = type.validation(value);
                    }
                    else{
                        ctrl = true;
                        console.log("EmpModalBox.ff_String_IF: " + type.type_id + " validation function not impemented");
                    }
                    var clr = ctrl? "rgb(223, 240, 216)":"rgb(238, 98, 98)";
                    $( i1 ).css('backgroundColor', clr);
                };
                $( i1 ).blur(ff_focusOut);
    return r;
}

function ff_FixedString_IF(tag, a, values, ff_ID){
    var r = __HB.ceROW();
    var type = __DESC.d[tag].attr[a].type;
    var params = null;
    switch(type){
        case __DESC.dt.STR.bssid_type: params = ["unique", "shared"]; break;
        case __DESC.dt.STR.role:    params = ["admin", "user"]; break;
        case __DESC.dt.NUM.bool:    params = ["yes", "no"]; break;
    }
            var div = __HB.ce("DIV");
        $( r ).append(div);
            $( div ).addClass("form-group");
                var l1 = __HB.ce("LABEL");
                $( div ).append(l1);
                $( l1 ).addClass("radio-inline");
                    var i1 = __HB.ce("INPUT");
                    $( l1 ).append(i1);
                    $( i1 ).attr("type", "radio");
                    $( i1 ).attr("name", "optionsRadiosInline");
                $( i1 ).attr("value", params[0]);
                    var lb1 = __HB.ce("SPAN")
                    $(l1).append(lb1);
                $( lb1 ).text( params[0] );
                var l2 = __HB.ce("LABEL");
                $( div ).append(l2);
                $( l2 ).addClass("radio-inline");
                    var i2 = __HB.ce("INPUT");
                    $( l2 ).append(i2);
                    $( i2 ).attr("type", "radio");
                    $( i2 ).attr("name", "optionsRadiosInline");
                $( i2 ).attr("value", params[1]);
                    var lb2 = __HB.ce("SPAN")
                    $(l2).append(lb2);
                $( lb2 ).text( params[1] );
            var l3 = __HB.ce("INPUT");
                $( div ).append(l3);
            l3.id = ff_ID( a ) + "_IF";
            l3.disabled = true;
                $( l3 ).css('height', '34px');
            $( l3 ).css('width', '72px');
                $( l3 ).css('margin', '-7px 10px');
            $( l3 ).css('backgroundColor', 'rgb(238, 98, 98)');
                $( l3 ).text(" ")
                    $( i1 ).click(function(){
                    $( l3 ).css('backgroundColor', 'rgb(223, 240, 216)');
                    $( l3 ).attr("value", params[0])
                    });
                    $( i2 ).click(function(){
                    $( l3 ).css('backgroundColor', 'rgb(223, 240, 216)');
                    $( l3 ).attr("value", params[1])
                    });
    return r;
}

// ------------------------------------------------------------------------------------- BATCH FIELD

function ff_drawBatch_Object( attr, value, id){
    var r = [];
        var r1 = __HB.ceROW();
        $( r1 ).css("margin", "5px 0px")
            var c1 = __HB.ceCOL("xs", 6);
            c1.id = id + "_V";
            var desc = __DESC.d[attr];
            var key = "";
            var str = "{ "
            if( desc ){
                for( var a in desc.attr ){
                    if( desc.attr[a].isKey ){
                        key = a;
                        break;
                    }
                }
                str += key + ": " + value[key] + ", ";
            }
            else{
                console.log("ff_Object: no description of " + attr);
            }
            str += "...}";
            $( c1 ).text(str);
            $( r1 ).append(c1);
            var c2 = __HB.ceCOL("xs", 2);
                var btn = __HB.ce("BUTTON");
                $( c2 ).append(btn);
                $( btn ).attr("type", "button");
                $( btn ).attr("title", "click for more details");
                $( btn ).text("...");
                $( btn ).click( function(){
                    $( c3 ).hasClass('hide')? $( c3 ).removeClass('hide') : $( c3 ).addClass('hide')
                });
                var ico = __HB.ceFAI("fa-th-list");
                $( ico ).addClass("fa-1x");
                $( btn ).prepend(ico);
            $( r1 ).append(c2);
        r.push(r1)
        var r2 = __HB.ceROW();
        $( r2 ).css("margin", "5px 0px")
            var c3 = __HB.ceCOL("xs", 10);
            $( c3 ).addClass("hide");
                var pre = __HB.ce("PRE");
                $( c3 ).append(pre);
                    var txt = JSON.stringify(value, undefined, 4);
                    $( pre ).html( __HB.syntaxHighlight(txt));
                    $( pre ).css("margin", "0px 10px");
            $( r2 ).append(c3)
        r.push(r2);
    return r;
}