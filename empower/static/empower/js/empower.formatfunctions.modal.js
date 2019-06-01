var COL_0 = 4;
var COL_1 = 8;

function ff_draw(tag, a, id, isInput, values=null){
    if( isInput ){
        return ff_DrawInput(tag, a, id, values);
    }
    else{
        return ff_DrawStaticVar(tag, a, id, values);
    }
}

// ---------------------------- DRAW INPUT

function ff_DrawInput(tag, a, id, values){

    //console.log(tag, a, id, values)

    if ((tag ===__QE.targets.TENANT) && (a === "owner")){
        return ff_DIF_TenantOwner(tag, a, id, values);
    }

    var type = __DESC.d[tag].attr[a].type;
    switch( type ){
        case __DESC.dt.LIST.a:
        case __DESC.dt.LIST.d:
            break;
        case __DESC.dt.STR.def:
        case __DESC.dt.STR.mac:
        case __DESC.dt.STR.owner:
            return ff_DIF_String(tag, a, id, values);
        break;
        case __DESC.dt.NUM.intgr:
        case __DESC.dt.STR.plmnid:
            return ff_DIF_Number(tag, a, id, values);
        case __DESC.dt.STR.role:
        case __DESC.dt.STR.bssid_type:
            return ff_DIF_Bool(tag, a, id, values);
        case __DESC.dt.OBJ.dscp:
            return ff_DIF_DSCP(tag, a, id, values);
        case __DESC.dt.OBJ.match:
            return ff_DIF_Match(tag, a, id, values);
        case __DESC.dt.OBJ.tID:
            return ff_DIF_TenantID(tag, a, id, values);
        default:
            console.log("ff_DrawInput: " + type.type_id + " not implemented (" + tag + "." + a + ")" );
            return null;
    }
}

function ff_DIF_String(tag, a, id, values){
    var r = __HB.ceROW();
    $( r ).css("margin", "8px")
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( r ).append(c1);

            var input = __HB.ce("INPUT");
            $( c1 ).append(input);
            input.id = id
            if( values ){
                $( input ).attr("value",values)
            }
            else{
                $( input ).attr("placeholder","Type here...")
            }
            $( input ).attr("size", 30)

            var ff_focusOut = function(){
                var ctrl = false;
                var type = __DESC.d[tag].attr[a].type;
                var value = $( input ).val();
                if( type.validation ){
                    ctrl = type.validation(value);
                }
                else{
                    ctrl = true;
                    console.log("EmpModalBox.ff_String_IF: " + type.type_id + " validation function not impemented");
                }
                var clr = ctrl? "rgb(223, 240, 216)":"rgb(238, 98, 98)";
                $( input ).css('backgroundColor', clr);
            };
            $( input ).blur(ff_focusOut);

    return r;
}

function ff_DIF_Number(tag, a, id, values){
    var r = __HB.ceROW();
    $( r ).css("margin", "8px")
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( r ).append(c1);

            var input = __HB.ce("INPUT");
            $( c1 ).append(input);
            input.id = id
            if( values ){
                $( input ).attr("value",values)
            }
            else{
                $( input ).attr("placeholder","Type here...")
            }
            $( input ).attr("size", 20)
    return r;
}

function ff_DIF_DSCP(tag, a, id, values){
    var r = __HB.ceROW();
    $( r ).css("margin", "8px")
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( r ).append(c1);

            var selector = __HB.ce("SELECT");
            $( c1 ).append(selector);
            $( selector ).css("width","100%");
            $( selector ).css("height","35px");
                // DSCP are manually controlled
                var DSCPList = ["0x00", "0x01", "0x02", "0x03", "0x04",
                                "0x08", "0x0A", "0x0C", "0x0E",
                                "0x10", "0x12", "0x14", "0x16", "0x18",
                                "0x1A", "0x1C", "0x1E", "0x20", "0x22",
                                "0x24", "0x26", "0x28", "0x2C", "0x2E", "0x30", "0x38"];
                for(var i=0; i<DSCPList.length; i++){
                    var opt = __HB.ce("OPTION");
                    $( selector ).append(opt);
                    $( opt ).text(DSCPList[i])
                }
            var ff_change = function(){
                var el = selector.options[selector.selectedIndex];
                var input = __HB.ge( id );
                $( input ).text( $(el).text() )
            }
            $( selector ).change(ff_change)
            setTimeout( function(){ $( selector ).change() }, 1/8*__DELAY )
            var input = __HB.ce("SPAN");
            $( c1 ).append(input);
            $( input ).addClass("hide");
            input.id = id;

    return r;
}

function ff_DIF_Match(tag, a, id, values){
    var r = __HB.ceROW();
    $( r ).css("margin", "8px");
    var MatchRules = [];
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( r ).append(c1);

            var input = __HB.ce("SPAN");
            $( c1 ).append(input);
            $( input ).addClass("hide");
            input.id = id;
            $( input ).css("backgroundColor", "rgb(238, 98, 98)");

            var DefineNewMatch = function(){
                var rr = __HB.ceROW();
                $( c1 ).append(rr);

                    var cc1 = __HB.ceCOL("xs", 4);
                    $( rr ).append(cc1);
                        var MatchStructure = ["wildcards", "dl_src", "dl_dst",
                                                "dl_vlan", "dl_pcp", "pad",
                                                "dl_type", "nw_tos", "nw_proto",
                                                "nw_src", "nw_dst", "tp_src",
                                                "tp_dst"];
                        var selector = __HB.ce("SELECT");
                        $( cc1 ).append(selector);
                        $( selector ).css("width","100%");
                        $( selector ).css("height","26px");
                        for(var i=0; i<MatchStructure.length; i++){
                            var opt = __HB.ce("OPTION");
                            $( selector ).append(opt);
                            opt.id = MatchStructure[i]
                            $( opt ).text(MatchStructure[i])
                        }
                        var i1 = __HB.ce("SPAN");
                        $( cc1 ).append(i1);
                        $( i1 ).addClass("hide");
                        var ff_change = function(){
                            var el = selector.options[selector.selectedIndex];
                            $( i1 ).text( el.id )
                        }
                        $( selector ).change(ff_change)
                        setTimeout( function(){ $( selector ).change() }, 1/8*__DELAY )
                    var cc2 = __HB.ceCOL("xs", 1);
                    $( rr ).append(cc2);
                    $( cc2 ).addClass("text-center");
                        var s = __HB.ce("SPAN");
                        $( cc2 ).append(s);
                        $( s ).text(" - ");
                    var cc3 = __HB.ceCOL("xs", 4);
                    $( rr ).append(cc3);
                        var i3 = __HB.ce("INPUT");
                        $( cc3 ).append(i3);
                        $( i3 ).attr("placeholder","Value");
                        $( i3 ).attr("size", 10);
                    var cc4 = __HB.ceCOL("xs", 3);
                    $( rr ).append(cc4);
                        var btn_ADD = __HB.ce("BUTTON");
                        $( cc4 ).append(btn_ADD);
                        $( btn_ADD ).attr("type", "button");
                        $( btn_ADD ).attr("style", "margin: 0px 2px;");
                        $( btn_ADD ).attr("title", "Add");
                            var icon_ADD = __HB.ceFAI("fa-plus");
                            $( icon_ADD ).addClass("fa-1x");
                            $( btn_ADD ).prepend(icon_ADD);
                        var btn_REMOVE = __HB.ce("BUTTON");
                        $( cc4 ).append(btn_REMOVE);
                        $( btn_REMOVE ).addClass("hide");
                        $( btn_REMOVE ).attr("type", "button");
                        $( btn_REMOVE ).attr("style", "margin: 0px 2px;");
                        $( btn_REMOVE ).attr("title", "Remove");
                            var icon_REMOVE = __HB.ceFAI("fa-times");
                            $( icon_REMOVE ).addClass("fa-1x");
                            $( btn_REMOVE ).prepend(icon_REMOVE);

                var defineMatch = function(){
                    var txt = "";
                    for( var i=0; i<MatchRules.length; i++){
                        txt += MatchRules[i] + ", "
                    }
                    txt = txt.substr(0, txt.length-2)
                    $( input ).text(txt);
                    if( MatchRules.length > 0)
                        $( input ).css("backgroundColor", "rgb(223, 240, 216)");
                    else
                        $( input ).css("backgroundColor", "rgb(238, 98, 98)");
                }
                var ADDclick = function(){
                    $( btn_REMOVE ).removeClass("hide");
                    $( btn_ADD ).addClass("hide");
                    var field = $( i1 ).text(); selector.disabled = true;
                    var value = $( i3 ).val(); i3.disabled = true;
                    var txt = field + "=" + value
                    if( txt === "=")
                        alert("No match rule added")
                    else{
                        MatchRules.push(txt);
                        DefineNewMatch();
                    }
                    defineMatch();
                }
                $( btn_ADD ).click( ADDclick );
                var REMOVEclick = function(){
                    $( btn_REMOVE ).addClass("hide");
                    $( btn_ADD ).removeClass("hide");
                    var field = $( i1 ).text();
                    var value = $( i3 ).val();
                    var txt = field + "=" + value
                    var idx = MatchRules.indexOf(txt);
                    MatchRules.splice(idx,1);
                    $( rr ).remove();
                    defineMatch();
                }
                $( btn_REMOVE ).click( REMOVEclick );

            }
            DefineNewMatch();

    return r;
}

function ff_DIF_TenantID(tag, a, id, values){
    var r = __HB.ceROW();
    $( r ).css("margin", "8px")
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( r ).append(c1);

            var selector = __HB.ce("SELECT");
            $( c1 ).append(selector);
            $( selector ).css("width","100%");
            $( selector ).css("height","35px");
            var TenantList = [];
                if( __ROLE === "admin"){
                    TenantList =  __CACHE.c[__QE.targets.TENANT];
                }
                else{
                    var tenant_name = $( "#navbar_tenantname" ).text();
                    for( var i=0; i<__CACHE.c[__QE.targets.TENANT].length; i++ ){
                        var tnt = __CACHE.c[__QE.targets.TENANT][i];
                        if( tnt["tenant_name"] === tenant_name ){
                            TenantList.push( tnt );
                            break;
                        }
                    }
                }
            for(var i=0; i<TenantList.length; i++){
                var opt = __HB.ce("OPTION");
                $( selector ).append(opt);
                opt.id = TenantList[i]["tenant_id"]
                $( opt ).text(TenantList[i]["tenant_name"])
            }
            var ff_change = function(){
                var el = selector.options[selector.selectedIndex];
                var input = __HB.ge( id );
                $( input ).text( el.id )
            }
            $( selector ).change(ff_change)
            setTimeout( function(){ $( selector ).change() }, 1/8*__DELAY )
            var input = __HB.ce("SPAN");
            $( c1 ).append(input);
            $( input ).addClass("hide");
            input.id = id;
    return r;
}

function ff_DIF_TenantOwner(tag, a, id, values){
    var r = __HB.ceROW();
    $( r ).css("margin", "8px")
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( r ).append(c1);

            var selector = __HB.ce("SELECT");
            $( c1 ).append(selector);
            $( selector ).css("width","100%");
            $( selector ).css("height","35px");

            selected_owners = [];
            owner_list =  __CACHE.c[__QE.targets.ACCOUNT];
            for(var i=0; i<owner_list.length; i++){
                var o = owner_list[i];
                // console.log(o);
                if (o.role != "admin"){
                    selected_owners.push(o);
                }
            }
            for(var i=0; i<selected_owners.length; i++){
                var opt = __HB.ce("OPTION");
                $( selector ).append(opt);
                opt.id = selected_owners[i]["username"]
                $( opt ).text(selected_owners[i]["username"])
            }
            var ff_change = function(){
                var el = selector.options[selector.selectedIndex];
                var input = __HB.ge( id );
                $( input ).text( el.id )
            }
            $( selector ).change(ff_change)
            setTimeout( function(){ $( selector ).change() }, 1/8*__DELAY )
            var input = __HB.ce("SPAN");
            $( c1 ).append(input);
            $( input ).addClass("hide");
            input.id = id;
    return r;
}

function ff_DIF_Bool(tag, a, id, values){
                                            // values = [first, second] -> OFF -> first
                                            //                             ON -> scd!
    if( values === null ){
        if( a === "bssid_type" ) values = ["unique", "shared"];
        if( a === "role" ) values = ["admin", "user"];
    }

    var r = __HB.ceROW();
    $( r ).css("margin", "8px");
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( c1 ).addClass("text-left");
        $( r ).append(c1);
            var swtch = __HB.ce("INPUT");
            $( c1 ).append(swtch);
            $( swtch ).attr("id", id)
            $( swtch ).addClass("switch");
            $( swtch ).attr("type", "checkbox");
            $( swtch ).attr("data-on-text", values[1]);
            $( swtch ).attr("data-off-text", values[0]);
            $( swtch ).attr("data-on-color", "primary");
            $( swtch ).attr("data-off-color", "primary");
            $( swtch ).bootstrapSwitch()
    return r;
}

// ---------------------------- DRAW STATIC VARIABLES

function ff_DrawStaticVar(tag, a, id, values){
    var type = __DESC.d[tag].attr[a].type;
    switch( type ){
        case __DESC.dt.STR.work:
            return;
        case __DESC.dt.LIST.a:
        case __DESC.dt.LIST.d:
            break;
        case __DESC.dt.STR.def:
        case __DESC.dt.STR.mac:
        case __DESC.dt.STR.uuid:
        case __DESC.dt.STR.owner:
        case __DESC.dt.STR.plmnid:
        case __DESC.dt.STR.data:
        case __DESC.dt.STR.dpid:
        case __DESC.dt.STR.ip_addr:
        case __DESC.dt.STR.tmsi:
        case __DESC.dt.STR.tenantid:
        case __DESC.dt.STR.ueid:
        case __DESC.dt.NUM.intgr:
        case __DESC.dt.OBJ.dscp:
        case __DESC.dt.OBJ.match:
        case __DESC.dt.OBJ.tID:
            return ff_DSV_String(tag, a, id, values);
        case __DESC.dt.NUM.bool:
            return ff_DSV_Boolean(tag, a, id, values);
        case __DESC.dt.STR.bssid_type:
            return ff_DSV_BSSIDType(tag, a, id, values);
        case __DESC.dt.STR.role:
            return ff_DSV_Role(tag, a, id, values);
        case __DESC.dt.STR.state:
            return ff_DSV_State(tag, a, id, values);
        case __DESC.dt.OBJ.connection:
            return ff_DSV_Connection(tag, a, id, values);
        case __DESC.dt.OBJ.networks:
            return ff_DSV_Networks(tag, a, id, values);
        case __DESC.dt.OBJ.ssids:
            return ff_DSV_SSIDs(tag, a, id, values);
        case __DESC.dt.STR.band:
            return ff_DSV_Band(tag, a, id, values);
        case __DESC.dt.OBJ.datapath:
            return ff_DSV_Datapath(tag, a, id, values);
        default:
            console.log("ff_DrawStaticVar: " + type.type_id + " not implemented (" + tag + "." + a + ")" );
            return null
    }
    if( a === "blocks" || a === "supports" ){
        return ff_DSV_Supports(tag, a, id, values);
    }
    else if( a === "cells"){
        console.log("Formatting cells...")
        return ff_DSV_Cells(tag, a, id, values);
    }
    else if( a === "components" ){
        return ff_DSV_Components(tag, a, id, values);
    }
    else if( a === "lvaps" ){
        return ff_DSV_LVAPs(tag, a, id, values);
    }
    else if( a === "slices" ){
        return ff_DSV_Slices(tag, a, id, values);
    }
    else if( a === "traffic_rules" ){
        return ff_DSV_TRs(tag, a, id, values);
    }
    else if( a === "network_ports" ){
        return ff_DSV_NetworkPorts(tag, a, id, values);
    }
    else if( a === "wifi_stats" ){
        return ff_DSV_WifiStats(tag, a, id, values);
    }
    else if( a === "wtps" || a === "cpps" || a === "vbses" ){
        return ff_DSV_Devices(tag, a, id, values);
    }
    else if( a === "tx_policies" || a === "hosts"){
        return null;    // working values
    }
    else{
        console.log("ff_DrawStaticVar: drawlist not implemented (" + tag + "." + a + ")" );
        return null
    }
}

function ff_DSV_String(tag, a, id, values){
    var r = __HB.ceROW();
    $( r ).css("margin", "8px")
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( r ).append(c1);
        $( c1 ).addClass("text-left");
        c1.id = id;
        $( c1 ).text(values);
    return r;
}

function ff_DSV_BSSIDType(tag, a, id, values){
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
            s.id = id;
            $( s ).text( values.toUpperCase() );
    return d;
}

function ff_DSV_Role(tag, a, id, values){
    var d = __HB.ce("DIV");
    var params = { "admin": ADMIN, "user": USER};
        var r0 = __HB.ceROW();
        $( d ).append(r0);
        $( r0 ).css("margin", "0% 10%")
            var i = __HB.ceFAI("fa-user");
            $( r0 ).append(i)
            $( i ).addClass("fa-4x");
            $( i ).css("color", params[values])
        var r1 = __HB.ceROW();
        $( d ).append(r1);
        $( r1 ).css("margin", "0% 10%")
            var s = __HB.ce("SPAN");
            $( r1 ).append(s)
            s.id = id;
            $( s ).text( values.toUpperCase() );
    return d;
}

function ff_DSV_State(tag, a, id, values){
    var r = __HB.ceROW();
    $( r ).css("margin", "8px")
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( r ).append(c1);
            var icon = __HB.ceFAI("fa-circle");
            $( c1 ).append(icon);
            switch(tag){
                case __QE.targets.WTP:
                case __QE.targets.CPP:
                case __QE.targets.VBS:
                    if( values === "disconnected") clr = RED;
                    else if( values === "connected") clr = YELLOW;
                    else if( values === "online") clr = GREEN;
                break;
                case __QE.targets.UE:
                    if( values === "stopped") clr = RED;
                    else if( values === "stopping") clr = YELLOW;
                    else if( values === "running") clr = GREEN;
                    else if( values === "spawning") clr = BLUE;
                    else if( values === "migrating_stop") clr = YELLOW;
                    else if( values === "migrating_start") clr = YELLOW;
                break;
                case __QE.targets.LVAP:
                    if( values === "stopped") clr = RED;
                    else if( values === "stopping") clr = YELLOW;
                    else if( values === "running") clr = GREEN;
                    else if( values === "spawning") clr = BLUE;
                    else if( values === "migrating_stop") clr = YELLOW;
                    else if( values === "migrating_start") clr = YELLOW;
                break;
            }
            $( icon ).css("color", clr);
            $( icon ).css("margin", "0px 5px");
            var span = __HB.ce("SPAN");
            $( c1 ).append(span)
            span.id = id;
            $( span ).text(values);
            $( span ).css("margin", "0px 5px");
    return r;
}

function ff_DSV_Boolean(tag, a, id, values){
    var r = __HB.ceROW();
    $( r ).css("margin", "8px")
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( r ).append(c1);
            var icon = __HB.ceFAI("fa-circle");
            $( c1 ).append(icon);
            var clr = "";
            if( values == false) clr = RED;
            else if( values == true) clr = GREEN;
            $( icon ).css("color", clr);
            $( icon ).css("margin", "0px 5px");
            var span = __HB.ce("SPAN");
            $( c1 ).append(span)
            span.id = id;
            var txt = "";
            if( values == false) txt = "Not Active";
            else if( values == true) txt = "Active";
            $( span ).text(txt);
            $( span ).css("margin", "0px 5px");
    return r;
}

function ff_DSV_Connection(tag, a, id, values){
    var r = __HB.ceROW();
    $( r ).css("margin", "8px")
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( r ).append(c1);
            var txt = ""
            if( values )
                txt = values[0] + " ( " + values[1] + " )";
            else
                txt = "No connection"
            var span = __HB.ce("SPAN");
            $( c1 ).append(span)
            span.id = id;
            $( span ).text(txt);
    return r;
}

function ff_DSV_Networks(tag, a, id, values){
    var r = __HB.ceROW();
    $( r ).css("margin", "8px")
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( r ).append(c1);
            var txt = "";
            for( var i=0; i< values.length; i++ ){
                txt += values[i][0] + " - " + values[i][1] + "\n"
            }
            txt += ""
            var span = __HB.ce("SPAN");
            $( c1 ).append(span)
            span.id = id;
            $( span ).text(txt);
    return r;
}

function ff_DSV_SSIDs(tag, a, id, values){
    var r = __HB.ceROW();
    $( r ).css("margin", "8px")
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( r ).append(c1);
            var txt = " [ ";
            for( var i=0; i<values.length; i++){
                txt += values[i] + ", ";
            }
            txt += " ]";
            var span = __HB.ce("SPAN");
            $( c1 ).append(span)
            span.id = id;
            $( span ).text(txt);
    return r;
}

function ff_DSV_Band(tag, a, id, values){   // values [band, channel]
    var r = __HB.ceROW();
    $( r ).css("margin", "8px")
        var c0 = __HB.ceCOL("xs", COL_0);
        $( r ).append(c0);
        $( c0 ).addClass("text-right");
        $( c0 ).text( __DESC.d[tag].attr[a].name + ": " );
        var c1 = __HB.ceCOL("xs", COL_1);
        $( r ).append(c1);
            var txt = "";
            var band = values[0];
            var channel = values[1];
            switch(band){
                case "L20":
                    if( channel < 14 ) txt = "802.11g"
                    else txt = "802.11a"
                break;
                case "HT20": txt = "802.11n"
                break;
                case "HT40": txt = "802.11n"
                break;
                default:
                    console.log("ff_DSV_Band, unknown band: ",band);
            }
            var span = __HB.ce("SPAN");
            $( c1 ).append(span)
            span.id = id;
            $( span ).text(txt);
    return r;
}

function ff_DSV_Datapath(tag, a, id, values){
    var p = __HB.cePANEL();
    $( p ).addClass("panel panel-info");
//    $( p ).css("margin", "20px");
//    $( p ).css("border", "1px solid #ccc");
    p.id = id;

    if( values && Object.keys(values).length ){
        var pH = __HB.cePANEL_H();
        $( p ).append(pH);
        var pB = __HB.cePANEL_B();
        $( p ).append(pB);
        var pF = __HB.cePANEL_F();
        $( p ).append(pF);

        var params = [];
            params.push( { "attr": "dpid", "style": "color:" + BLUE } );
            params.push( { "attr": "ip_addr"} );
        var btns = [];
            btns.push( { "dict": "network_ports"} );

        for( var i=0; i<params.length; i++){
            var subA = params[i].attr;
            var subID = p.id + subA;
            var subValue = values[ subA ]
            var r = ff_draw( a, subA, subID, false, subValue);
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
                    var subA = attr;
                    var subID = p.id + subA;
                    var subValue = values[ subA ]
                    var div = ff_draw( a, subA, subID, false, subValue);
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

    }
    else{
        return ff_DSV_Empty(tag, a)
    }

    return p;
}

// ---------------------------- DSV of LIST

function ff_DSV_Cell(tag, cell){

    var fields = __HB.ceCOL("xs", 12);

    var attrbts = __DESC.d[tag].attr;

    // console.log("ff_DSV_Cell");
    for( var a in attrbts ){
        // var a = attrbts[i];
        var isEdit = false;
        var value = cell[a];

        if (a in cell){

            var attr_id = a+"_id";

            // console.log("DRAW:",tag, a, attr_id, isEdit, value);

            var field = ff_draw(tag, a, attr_id, isEdit, value)

            if ((field != null) && (field != undefined)){
                $( fields ).append(field);
            }
        }
    }

    return fields;
}

function ff_DSV_Cells(tag, a, id, values){
    //console.log(" ff_DSV_Cells:",tag, a, id, values);
    var div = __HB.ce("DIV");
    var counter = 0
    div.id = id;
    for(var c in values){
        var cell = values[c];

        var panel = __HB.cePANEL();
        $( div ).append(panel);
        panel.id = id + "_" + cell["pci"];
        $( panel ).addClass("panel panel-info")
            var ph = __HB.cePANEL_H();
            $( panel ).append(ph);
                $( ph ).text("Cell " + c +"(PCI)")
            var body = __HB.cePANEL_B();
            $( panel ).append(body);
            var pf = __HB.cePANEL_F();
            $( panel ).append(pf);

            if (tag === "vbses"){
                body.append(this.ff_DSV_Cell(a, cell));
            }
            else{
                body.append(this.ff_DSV_Cell(tag, cell));
            }

        counter += 1;
    }
    if (counter === 0){
        $( div ).append( ff_DSV_Empty(tag, a) );
    }
    return div;
}

function ff_DSV_Supports(tag, a, id, values){
    console.log("ff_DSV_Supports");
    var div = __HB.ce("DIV");
    div.id = id;
    if( values.length ){
        for(var i=0; i<values.length; i++){
            var support = values[i];
            var panel = __HB.cePANEL();
            $( div ).append(panel);
            panel.id = id + "_" + support["hwaddr"];
            $( panel ).addClass("panel panel-info")
                var ph = __HB.cePANEL_H();
                $( panel ).append(ph);
                    $( ph ).text("Block " + (i+1))
                var body = __HB.cePANEL_B();
                $( panel ).append(body);
                var pf = __HB.cePANEL_F();
                $( panel ).append(pf);

                var attrbts = __DESC.d[a].attr;
                for( var subA in attrbts ){
                    var subIsEdit = __DESC.d[ a ].attr[subA].update;
                    var subId = panel.id + "_" + subA;
                    var subValue = null;
                    if( subA === "band" ){
                        subValue = []
                        subValue.push( support[subA] )
                        subValue.push( support["channel"] );
                    }
                    else{
                        subValue = support[subA];
                    }
                    var d = ff_draw(a, subA, subId, subIsEdit, subValue);
                    if( subA === "wifi_stats"){
                        $( pf ).append(d)
                    }
                    else{
                    $( body ).append(d)
                }
        }
    }
    }
    else{
        $( div ).append( ff_DSV_Empty(tag, a) );
    }
    return div;
}

function ff_DSV_WifiStats(tag, a, id, values){

    var panelID = id.substr(0, id.length-11);

    var btn = __HB.ce("BUTTON");
    $( btn ).attr("type", "button");
    $( btn ).attr("style", "margin: 0px 2px;");
    $( btn ).attr("title", "show " + a);
    $( btn ).text( __HB.mapName2Title(a) );
    btn.id = panelID + "_btn";
        var div = __HB.ce("DIV");
        $( div ).addClass("hide");
        div.id = panelID + "_divgrphbox";
        if( !$.isEmptyObject( values ) ){
            var graph = new EmpNetGraphBox( [tag, a, panelID.substr(panelID.length-17, panelID.length)] );
            var params = [tag, a, values];
            var bar = graph.create();
            $( div ).append(bar);
            graph.addGraph("stackedBarGraph", params); // params = [tag, a, values]
        }

        var f_Click = function(){
            var id = this.id.substr(0, this.id.length-4);
            var cnt = __HB.ge(id + "_divgrphbox");
            $( cnt ).hasClass("hide")? $( div ).removeClass("hide") : $( div ).addClass("hide");
        }
        $( btn ).click(f_Click);


        var ff = function(){
            var pb = $( __HB.ge(panelID) )[0].children[1];
            $( pb ).append(div);
        }
        setTimeout(ff, 1/8*__DELAY)
    return btn;
}

function ff_DSV_TRs(tag, a, id, values){
    var div = __HB.ce("DIV");
    div.id = id;
    if( Object.keys(values).length ){
        for( var v in values ){
            var tr = values[v];
            var panel = __HB.cePANEL();
            $( div ).append(panel);
            panel.id = id + "_" + tr["dscp"];
            $( panel ).addClass("panel panel-info")
    //            var ph = __HB.cePANEL_H();
    //            $( panel ).append(ph);
                var body = __HB.cePANEL_B();
                $( panel ).append(body);
    //            var pf = __HB.cePANEL_F();
    //            $( panel ).append(pf);

                var attrbts = __DESC.d[ __QE.targets.TR ].attr;
                for( var subA in attrbts ){
                    var subIsEdit = __DESC.d[ __QE.targets.TR ].attr[subA].update;
                    var subId = panel.id + "_" + subA;
                    var subValue = tr[subA];
                    var d = ff_draw( __QE.targets.TR, subA, subId, subIsEdit, subValue );
                    $( body ).append(d)
                }
        }
    }
    else{
        $( div ).append( ff_DSV_Empty(tag, a) );
    }
    return div;
}

function ff_DSV_Slices(tag, a, id, values){
    var div = __HB.ce("DIV");
    div.id = id;
    if( Object.keys(values).length ){
        for( var slice in values ){
            var panel = __HB.cePANEL();
            $( div ).append(panel);
            $( panel ).addClass("panel panel-info")
                var ph = __HB.cePANEL_H();
                $( panel ).append(ph);
                $( ph ).text("Slice: " + slice)
                var pb = __HB.cePANEL_B();
                $( panel ).append(pb);
                    var pre = __HB.ce("PRE");
                    $( pb ).append(pre)
                        var txt = JSON.stringify(values[slice], undefined, 4);
                        $( pre ).html( __HB.syntaxHighlight(txt));
                        $( pre ).css("margin", "20px")
        }
    }
    else{
        $( div ).append( ff_DSV_Empty(tag, a) );
    }
    return div;
}

function ff_DSV_Components(tag, a, id, values){
    var div = __HB.ce("DIV");
    div.id = id;
    if( Object.keys(values).length ){
        for( var cmp in values ){
            var panel = __HB.cePANEL();
            $( div ).append(panel);
            $( panel ).addClass("panel panel-info")
                var ph = __HB.cePANEL_H();
                $( panel ).append(ph);
                $( ph ).text("Component: " + cmp)
                var pb = __HB.cePANEL_B();
                $( panel ).append(pb);
                    var pre = __HB.ce("PRE");
                    $( pb ).append(pre)
                        var txt = JSON.stringify(values[cmp], undefined, 4);
                        $( pre ).html( __HB.syntaxHighlight(txt));
                        $( pre ).css("margin", "20px")
        }
    }
    else{
        $( div ).append( ff_DSV_Empty(tag, a) );
    }
    return div;
}

function ff_DSV_LVAPs(tag, a, id, values){
    var div = __HB.ce("DIV");
    div.id = id;
    if( Object.keys(values).length ){
        for( var lvap in values ){
            var panel = __HB.cePANEL();
            $( div ).append(panel);
            $( panel ).addClass("panel panel-info")
                var ph = __HB.cePANEL_H();
                $( panel ).append(ph);
                $( ph ).text("LVAP: " + lvap)
                var pb = __HB.cePANEL_B();
                $( panel ).append(pb);
                    var pre = __HB.ce("PRE");
                    $( pb ).append(pre)
                        var txt = JSON.stringify(values[lvap], undefined, 4);
                        $( pre ).html( __HB.syntaxHighlight(txt));
                        $( pre ).css("margin", "20px")
        }
    }
    else{
        $( div ).append( ff_DSV_Empty(tag, a) );
    }
    return div;
}

function ff_DSV_Devices(tag, a, id, values){
    var div = __HB.ce("DIV");
    div.id = id;
    if( Object.keys(values).length ){
        for( var el in values ){
            var panel = __HB.cePANEL();
            $( div ).append(panel);
            $( panel ).addClass("panel panel-info")
            panel.id = id + values[el]["addr"];
                var ph = __HB.cePANEL_H();
                $( panel ).append(ph);
                $( ph ).text( __HB.mapName2Title(a) + ": " + el)
                var pb = __HB.cePANEL_B();
                $( panel ).append(pb);

                var attrbts = ["label", "addr", "state", "connection"];
                for(var i=0; i<attrbts.length; i++){
                    var subA = attrbts[i];
                    var subIsEdit = false;
                    var subId = panel.id + "_" + subA;
                    var subValue = values[el][subA];
                    var d = ff_draw(a, subA, subId, subIsEdit, subValue);
                    $( pb ).append(d)
                }
        }
    }
    else{
        $( div ).append( ff_DSV_Empty(tag, a) );
    }
    return div;
}

function ff_DSV_NetworkPorts(tag, a, id, values){
    var d = __HB.ce("DIV");
    if( Object.keys(values).length ){
        for( var nP in values ){
            var p = __HB.cePANEL();
            $( d ).append(p);
            $( p ).addClass("panel panel-info");
            $( p ).css("margin", "20px");
            $( p ).css("padding", "20px");
            $( p ).css("border", "1px solid #ccc");
            p.id = id;
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
                    params.push( { "attr": "hwaddr", "style": "color:" + BLUE } );
                    params.push( { "attr": "dpid"} );
                    params.push( { "attr": "iface"} );
                    params.push( { "attr": "neighbour"} );
                    params.push( { "attr": "port_id"} );
                for( var i=0; i<params.length; i++){
                        var subA = params[i].attr;
                        var subID = p.id + subA;
                        var subValue = values[nP][ params[i].attr ]
                        var rr = ff_draw( a, subA, subID, false, subValue);
                        $( c1 ).append(rr);
                    if( params[i].style )
                            $( rr ).attr("style", params[i].style );
                }
        }
    }
    else{
        $( div ).append( ff_DSV_Empty(tag, a) );
    }
    return d;
}

function ff_DSV_Empty(tag, a){
    var panel = __HB.cePANEL();
    $( panel ).addClass("panel panel-info")
        var ph = __HB.cePANEL_H();
        $( panel ).append(ph);
        $( ph ).text(__HB.mapName2Title(a) + ": no entries")
        var pb = __HB.cePANEL_B();
        $( panel ).append(pb);
    return panel
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
