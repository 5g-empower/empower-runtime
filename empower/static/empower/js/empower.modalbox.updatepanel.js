class EmpUpdateModalBox extends EmpModalBox{

    constructor(keys){
        super(keys);

        this.toUpdate = {};
        this.selObj = null;

    }

    getID_BODY_UPDPANEL(){
        var id = this.getID_BODY() + "_updpnl";
        return id;
    }

    getID_BODY_UPDPANEL_ATTR(a){
        var id = this.getID_BODY_UPDPANEL() + "_" + a;
        return id;
    }

    getID_SELECTOR(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.modalbox.elements.selector] );
        return this.hb.generateID( keys );
    }

    getID_SELECTOBJ(keys){
        var id = this.getID_SELECTOR(keys) + "_obj";
        return id;
    }

    getID_SELECTOBJ_DETAILS(keys){
        var id = this.getID_SELECTOR(keys) + "_dtls";
        return id;
    }

    initResources(obj, userDetails=false){
        var tag = this.hb.mapName(obj);
        var title = "Show and update selected " + obj;

// ------------------- Body
        var body = this.hb.ce("DIV");
        body.id = this.getID_BODY();

        if( userDetails ){
            var key = __USERNAME;
            this.selObj = jQuery.extend(true, {}, this.hb.getKeyValue(tag, key) );
        }
        else{
        var dt = this.cache.DTlist[ tag ];
        var datatable = $("#"+ dt.getID()).DataTable();
        var key = "";
        if( datatable.row('.selected').data() ){
            var key = this.hb.getDTKeyFields(datatable.row('.selected').data());
        }
        else{
            return [title, body, buttons, ff_Close];
        }
        this.selObj = jQuery.extend(true, {}, this.hb.getKeyValue( tag , key))
        }

        var u = this.hb.ce("UL");
        $( body ).append(u);
        $( u ).addClass("nav nav-tabs");
                var info = this.hb.ce("LI");
                $( u ).append(info);
                $( info ).html("<a href=\"#Info\" id=\"InfoTab\" data-toggle=\"tab\">Info </a>");
                this.toUpdate["Info"]=false;
                var attrbts = this.desc.d[tag].attr;
        for( var a in attrbts ){
                    if( attrbts[a].type === this.desc.dt.LIST.a || attrbts[a].type === this.desc.dt.LIST.d ){
                var tab = this.hb.ce("LI");
                $( u ).append(tab);
                        $( tab ).html("<a href=\"#" + a + "\" id=\"" + a + "Tab\" data-toggle=\"tab\">" + a + " </a>");
                this.toUpdate[a]=false;
            }
                    else if(attrbts[a].type === this.desc.dt.OBJ.wtp){
                        var wtp = this.hb.ce("LI");
                        $( u ).append(wtp);
                        $( wtp ).html("<a href=\"#wtp\" id=\"wtpTab\" data-toggle=\"tab\">wtp </a>");
                this.toUpdate["wtp"]=false;
            }
                    else if(attrbts[a].type === this.desc.dt.OBJ.datapath){
                        var datapath = this.hb.ce("LI");
                        $( u ).append(datapath);
                        $( datapath ).html("<a href=\"#datapath\" id=\"datapathTab\" data-toggle=\"tab\">datapath </a>");
                        this.toUpdate["datapath"]=false;
            }
        }
                var JSON = this.hb.ce("LI");
                $( u ).append(JSON);
                $( JSON ).html("<a href=\"#JSON\" id=\"JSONTab\" data-toggle=\"tab\">JSON </a>");
                this.toUpdate["JSON"]=false;

        var div = this.d_UpdateBodyPanel(tag, this.selObj);
        $( body ).append(div);
        div.id = this.getID_BODY_UPDPANEL();

// ------------------- Buttons
        var ff_Close = this.f_WarningClose.bind(this);
        var buttons = [];

        var json = this.hb.getKeyValue( tag , key);
        var ff_Download = this.hb.wrapFunction(this.f_Download.bind(this), ["SELECTED"+obj.toUpperCase(), json]);
        var btn_Download = {"text": "Download",
                         "color": "primary",
                         "f": ff_Download};
        buttons.push(btn_Download);
        var args = [tag , key, this.selObj]
        var ff_Upd = this.hb.wrapFunction(this.f_Save.bind(this), args);
        var btn_Upd = {"text": "Save",
                         "color": "primary",
                         "f": ff_Upd};
         buttons.push(btn_Upd);

        return [title, body, buttons, ff_Close];
    }

    d_UpdateBodyPanel(tag, selObj){

        var div = this.hb.ce("DIV");
        $( div ).addClass("tab-content");
            this.selObj = jQuery.extend(true, {}, selObj)
            for( var tab in this.toUpdate ){
                var panel = null;
                switch( tab ){
                    case "Info":    panel = this.d_infoPanel(tag); break;
                    case "JSON":    panel = this.d_JSONPanel(tag); break;
                    default:        panel = this.d_ObjectPanel(tag, tab);
            }
                   $( div ).append(panel);
            }

            var ff = function(){
                $('a[href="#Info"]').click();
                var attrbs = this.desc.d[tag].attr;
                for(var a in attrbs){
                    if( !( a in this.toUpdate) && this.desc.d[tag].attr[a].update ){
                        var id = this.getID_BODY_UPDPANEL_ATTR(a);
                        var cnt = this.hb.ge(id);
                        $( cnt ).click( this.hb.wrapFunction(this.f_onClickInfo.bind(this),[tag, a, cnt]) );
            }
            }
        }
            setTimeout(ff.bind(this), 1/5*this.delay)
        return div;
    }

    d_JSONPanel(tag){

    var pre = this.hb.ce("PRE");
    $( pre ).addClass("tab-pane fade")
    pre.id = "JSON";
        var txt = JSON.stringify(this.selObj, undefined, 4);
        $( pre ).html( this.hb.syntaxHighlight(txt));
        $( pre ).css("margin", "20px")

    return pre;
}

d_infoPanel(tag){

    var div = this.hb.ce("DIV");
        $( div ).addClass("tab-pane fade");
        div.id = "Info";
    $( div ).css("margin", "20px");
    $( div ).css("padding", "5px");
    //    $( div ).css("border", "1px solid #ccc");
    //    $( div ).css("background-color", "#f5f5f5");

            var p = this.hb.ce("DIV");
            $( div ).append(p);
            $( p ).addClass("well well-sm");
                var r0 = this.hb.ceROW();
                $( p ).append(r0);
                    var c0 = this.hb.ceCOL("xs", 2);
                    $( r0 ).prepend(c0);
                    $( c0 ).addClass("hide");
                    var c1 = this.hb.ceCOL("xs", 12);
                    $( r0 ).append(c1);
            var attrbs = this.desc.d[tag].attr;
            for(var a in attrbs){
                if( !( a in this.toUpdate) ){
                    switch( this.desc.d[tag].attr[a].type ){
                        case this.desc.dt.STR.bssid_type:
                            $( c0 ).removeClass("hide");
                            $( c1 ).removeClass(); $( c1 ).addClass("col-xs-10");
                            var r = ff_draw_BSSID_type(this.selObj[a]);
                            $( c0 ).append(r);
            break;
                        default:
                            var r = ff_draw(tag, a, this.selObj[a], this.getID_BODY_UPDPANEL_ATTR.bind(this));
                            $( c1 ).append(r)
        }
    }
            }

        return div;
}

    d_ObjectPanel(tag, a){
        var div = null;
        var isEdit = this.desc.d[tag].attr[a].update;
        if( isEdit ){
            div = this.d_ObjectPanel_Editable(tag, a);
            return div;
        }
        div = this.hb.ce("DIV")
        $( div ).addClass("tab-pane fade");
        div.id = a;
        $( div ).css("margin", "20px");
        $( div ).css("padding", "5px");
    //    $( div ).css("border", "1px solid #ccc");
    //    $( div ).css("background-color", "#f5f5f5");

            var p = this.hb.cePANEL();
            $( div ).append(p);
            $( p ).addClass("panel-info");
                var pH = this.hb.cePANEL_H();
                $( p ).append(pH);
                var pB = this.hb.cePANEL_B();
                $( p ).append(pB);

                var values = this.selObj[a];
                if( values == null || values.length == 0 || $.isEmptyObject(values) ){
                    var num = 0;
                    $( pH ).text( num + " elements" );
                }
                else if( this.desc.d[tag].attr[a].type != this.desc.dt.LIST.a &&
                         this.desc.d[tag].attr[a].type != this.desc.dt.LIST.d ){
                    var num = 1;
                    var r = this.hb.ceROW();
                    $( pH ).append(r);
                        var c0 = this.hb.ceCOL("xs", 6);
                        $( r ).append(c0);
                            var lbl = this.hb.ce("LABEL");
                            $( c0 ).append(lbl);
                            $( lbl ).text( num + " element" );
                        var c1 = this.hb.ceCOL("xs", 6);
                        $( r ).append(c1);
                        $( c1 ).attr("align", "right");
                            var btn = __HB.ce("BUTTON");
                            $( c1 ).append(btn);
                            $( btn ).attr("type", "button");
                            $( btn ).attr("style", "margin: 0px 2px;");
                            $( btn ).attr("title", "refresh");
                            $( btn ).click(this.hb.wrapFunction(this.f_Refresh.bind(this), [tag, a] ));
                                var ico = this.hb.ceFAI("fa-refresh");
                                $( ico ).addClass("fa-2x");
                                $( btn ).prepend(ico);
                    var nP = ff_draw(tag, a, values, this.getID_BODY_UPDPANEL_ATTR.bind(this));
                    $( pB ).append(nP);
                }
                else if( this.hb.isArray( values ) ){
                    var num = values.length;
                    var r = this.hb.ceROW();
                    $( pH ).append(r);
                        var c0 = this.hb.ceCOL("xs", 6);
            $( r ).append(c0);
                            var lbl = this.hb.ce("LABEL");
                            $( c0 ).append(lbl);
                            $( lbl ).text( num + " element" );
                        var c1 = this.hb.ceCOL("xs", 6);
            $( r ).append(c1);
                        $( c1 ).attr("align", "right");
                            var btn = __HB.ce("BUTTON");
                            $( c1 ).append(btn);
                            $( btn ).attr("type", "button");
                            $( btn ).attr("style", "margin: 0px 2px;");
                            $( btn ).attr("title", "refresh");
                            $( btn ).click(this.hb.wrapFunction(this.f_Refresh.bind(this), [tag, a] ));
                                var ico = this.hb.ceFAI("fa-refresh");
                                $( ico ).addClass("fa-2x");
                                $( btn ).prepend(ico);
                    for( var i=0; i<num; i++){
                        var nP = ff_draw(tag, a, values[i], this.getID_BODY_UPDPANEL_ATTR.bind(this));
                        $( pB ).append(nP);
            }
                }
                else{
                    var num = Object.keys(values).length;
                    var r = this.hb.ceROW();
                    $( pH ).append(r);
                        var c0 = this.hb.ceCOL("xs", 6);
                        $( r ).append(c0);
                            var lbl = this.hb.ce("LABEL");
                            $( c0 ).append(lbl);
                            $( lbl ).text( num + " element" );
                        var c1 = this.hb.ceCOL("xs", 6);
                        $( r ).append(c1);
                        $( c1 ).attr("align", "right");
                            var btn = __HB.ce("BUTTON");
                            $( c1 ).append(btn);
                            $( btn ).attr("type", "button");
                            $( btn ).attr("style", "margin: 0px 2px;");
                            $( btn ).attr("title", "refresh");
                            $( btn ).click(this.hb.wrapFunction(this.f_Refresh.bind(this), [tag, a] ));
                                var ico = this.hb.ceFAI("fa-refresh");
                                $( ico ).addClass("fa-2x");
                                $( btn ).prepend(ico);
                    for(var el in values){
                        var nP = ff_draw(tag, a, [el, values[el]], this.getID_BODY_UPDPANEL_ATTR.bind(this));
                        $( pB ).append(nP);
            }
    }

    return div;
    }

    d_ObjectPanel_Editable(tag, a){
        var div = this.hb.ce("DIV")
        $( div ).addClass("tab-pane fade");
        div.id = a;
    $( div ).css("margin", "20px");
    $( div ).css("padding", "5px");
    //    $( div ).css("border", "1px solid #ccc");
    //    $( div ).css("background-color", "#f5f5f5");

            var p = this.hb.cePANEL();
            $( div ).append(p);
            $( p ).addClass("panel-default");
                var pH = this.hb.cePANEL_H();
                $( p ).append(pH);
                var pB = this.hb.cePANEL_B();
                $( p ).append(pB);

            var el = this.hb.mapName(a);
            var allObjList = this.cache.c[el];
            if( allObjList.length == 0 ){
                $( pH ).text( "No elements available" );
                return div;
    }
            var body = this.d_ObjectPanel_Editable_Obj(tag, a, this.selObj[a]);
            $( pB ).append(body);

    return div;
    }

    d_ObjectPanel_Editable_Obj(tag, a, values){
        var div = null;
        switch( a ){
            case "wtps":
            case "cpps":
            case "vbses":
                div = this.d_ObjectPanel_Editable_Obj_Devices(tag, a, values);
            break;
            case "wtp":
                div = this.d_ObjectPanel_Editable_Obj_Clients(tag, a, values);
            break;
            default:
                console.log( a + " object panel not implemented")
        }

        return div;
    }

    d_ObjectPanel_Editable_Obj_Devices(tag, a, values){
    var div = this.hb.ce("DIV");
        div.id = tag + "_" + a
    var desc = this.desc.d[a].attr;
    var key = "";
    for( var attr in desc ){
        if( desc[attr].isKey ){
            key = attr;
            break;
        }
    }
        var allObjList = this.cache.c[a];
        var currentObjList = values

    var r0 = this.hb.ceROW();
    $( div ).append(r0);
    $( r0 ).css("height","40px");
    $( r0 ).css("margin","10px 0px");
            var c0 = this.hb.ceCOL("xs", 10)
        $( r0 ).append(c0);
            var select = this.hb.ce("SELECT");
            $( c0 ).append(select);
            select.id = this.getID_SELECTOR([div.id])
            $( select ).css("width","100%");
            $( select ).css("height","35px");
            var c1 = this.hb.ceCOL("xs",1);
        $( r0 ).append(c1);
            var btn = this.hb.ce("BUTTON");
            $( c1 ).append(btn);
            btn.id = select.id + "_bttn" ;
            $( btn ).attr("type", "button");
            $( btn ).attr("style", "margin: 0px 2px;");
                $( btn ).attr("title", "add selected");
                var args = [select, tag, a, currentObjList, allObjList]
                var ff = this.hb.wrapFunction(this.f_AddToList.bind(this), args);
            $( btn ).click( ff );
                    var ico = this.hb.ceFAI("fa-plus");
                $( ico ).addClass("fa-2x");
                $( btn ).prepend(ico);

    var r1 = this.hb.ceROW();
    $( div ).append(r1);
    $( r1 ).css("margin","10px 0px");
            var c10 = this.hb.ceCOL("xs", 6);
        $( r1 ).append(c10);
            c10.id = this.getID_SELECTOBJ([div.id]);
            var c11 = this.hb.ceCOL("xs", 6);
        $( r1 ).append(c11);
            var details = this.hb.ce("DIV");
            $( c11 ).append(details);
                details.id = this.getID_SELECTOBJ_DETAILS([div.id]);
            $( details ).css("height", "100%")
            $( details ).css("width", "100%")

        var fff = function(){
            this.f_updateLists(tag, a, currentObjList, allObjList);
                            }
        setTimeout(fff.bind(this), 1/5*this.delay);
    return div;
    }

    d_ObjectPanel_Editable_Obj_Clients(tag, a, values){
    var div = this.hb.ce("DIV");
        div.id = tag + "_" + a
        var el = this.hb.mapName(a)
        var desc = this.desc.d[el].attr;
    var key = "";
    for( var attr in desc ){
        if( desc[attr].isKey ){
            key = attr;
            break;
        }
    }
//        var currentObjList = this.selObj[a];
        var allObjList = this.cache.c[ el ];
    var currentObjList = {};
        var keyValue = this.selObj[a][key];
        currentObjList[keyValue] = this.selObj[a];
        var fff = function(){
            this.f_updateLists(tag, a, currentObjList, allObjList);
    }
        setTimeout(fff.bind(this), this.delay);

    var r0 = this.hb.ceROW();
    $( div ).append(r0);
    $( r0 ).css("height","40px");
    $( r0 ).css("margin","10px 0px");
            var c0 = this.hb.ceCOL("xs", 9)
        $( r0 ).append(c0);
            $( c0 ).css("padding", "0px 5px")
            var select = this.hb.ce("SELECT");
            $( c0 ).append(select);
            select.id = this.getID_SELECTOR([div.id])
            $( select ).css("width","100%");
            $( select ).css("height","35px");
            var c1 = this.hb.ceCOL("xs",2);
        $( r0 ).append(c1);
            var btn = this.hb.ce("BUTTON");
            $( c1 ).append(btn);
            btn.id = select.id + "_bttn" ;
            $( btn ).attr("type", "button");
            $( btn ).attr("style", "margin: 0px 2px;");
                $( btn ).attr("title", "handover");
                var args = [select, tag, a, allObjList, currentObjList]
                var ff = this.hb.wrapFunction(this.f_AddToClient.bind(this), args);
            $( btn ).click( ff );
                    var ico = this.hb.ceFAI("fa-share-square-o");
                $( ico ).addClass("fa-2x");
                $( btn ).prepend(ico);
//                    var span = this.hb.ce("SPAN");
//                    $( span ).text("handover");
//                    $( span ).css("margin", "2px")
//                    $( btn ).append(span)

    var r1 = this.hb.ceROW();
    $( div ).append(r1);
    $( r1 ).css("margin","10px 0px");
        var c10 = this.hb.ceCOL("xs", 6);
        $( r1 ).append(c10);
            c10.id = this.getID_SELECTOBJ([div.id]);
        var c11 = this.hb.ceCOL("xs", 6);
        $( r1 ).append(c11);
            var details = this.hb.ce("DIV");
            $( c11 ).append(details);
                details.id = this.getID_SELECTOBJ_DETAILS([div.id]);
            $( details ).css("height", "100%")
            $( details ).css("width", "100%")
    return div;
    }

    f_AddToList(args){
        var select = args[0]; var p = 1;
        var tag = args[p]; p++;
        var a = args[p]; p++;
        var currentObjList = args[p]; p++;
        var allObjList = args[p]; p++;
        if( select.selectedIndex != -1 ){
            var el = select.options[select.selectedIndex];
            var keyValue = $( el ).attr('key');
            var toAdd = this.hb.getKeyValue(a, keyValue);
            currentObjList[keyValue] = toAdd;
            this.f_updateLists(tag, a, currentObjList, allObjList);
            this.f_updateName(a, false)
        }
    }

   f_AddToClient(args){
        var select = args[0]; var p = 1;
        var tag = args[p]; p++;
        var a = args[p]; p++;
        var allObjList = args[p]; p++;
        var currentObjList = args[p]; p++;
        var desc = this.desc.d[a].attr;
        var key = "";
        for( var attr in desc ){
            if( desc[attr].isKey ){
                key = attr;
                break;
            }
        }
        var el = select.options[select.selectedIndex];
        var keyValue = $( el ).attr('key');
        var toAdd = this.hb.getKeyValue(a, keyValue);
        var keyValue = toAdd[key];
        if( toAdd.state === "online" ){
            currentObjList = {};
            currentObjList[keyValue] = toAdd;
            this.f_updateLists(tag, a, currentObjList, allObjList);
            this.f_updateName(a, false);
        }
        else{
            alert( keyValue + " device is offline!" )
        }
    }

    f_RemoveFromList(args){
        var key = args[0]; var p = 1;
        var keyValue = args[p]; p++;
        var tag = args[p]; p++;
        var a = args[p]; p++;
        var currentObjList = args[p]; p++;
        var allObjList = args[p]; p++;
        delete currentObjList[keyValue];
        this.f_updateLists(tag, a, currentObjList, allObjList);
        this.f_updateName(a, false)
    }

    f_updateLists(tag, a, currentObjList, allObjList){
        var id = tag + "_" + a;
        var selector = this.getID_SELECTOR([id]);
        var selectobj = this.getID_SELECTOBJ([id]);
        var selectobjDet = this.getID_SELECTOBJ_DETAILS([id]) ;
        var desc = this.desc.d[a].attr;
        var key = "";
        for( var attr in desc ){
            if( desc[attr].isKey ){
                key = attr;
                break;
            }
        }
        $( "#" + selector ).empty();
        for( var i=0; i<allObjList.length; i++){
            var found = false;
            for( var e in currentObjList ){
                if( currentObjList[e][key] === allObjList[i][key])
                    found = true;
            }
            if( found == false ){
                var opt = this.hb.ce("OPTION");
                $( "#" + selector ).append(opt);
                    $( opt ).attr("key", allObjList[i][key])
                    $( opt ).text( allObjList[i][key] );
            }
        }
        $( "#" + selectobjDet ).empty();
        $( "#" + selectobj ).empty();
        for( var e in currentObjList ){
            var r = this.hb.ceROW();
            $( "#" + selectobj ).append(r);
            $( r ).css("margin","5px 0px");
                var c0 = this.hb.ceCOL("xs", 8);
                $( r ).append(c0);
                $( c0 ).text( currentObjList[e][key]);
                var t = this;
                $( c0 ).click(function(){
                    $( "#" + selectobjDet ).empty();
                    var key = $( this ).text();
                    var pre = t.hb.ce("PRE");
                    $( "#" + selectobjDet ).append(pre);
                    var json = t.cache.c[a] ? t.hb.getKeyValue(a, key) : currentObjList[key];
                    var txt = JSON.stringify(json, undefined, 4);
                    $( pre ).html( t.hb.syntaxHighlight(txt));
                });
                var c1 = this.hb.ce("xs",1);
                $( r ).append(c1);
                    var btn = this.hb.ce("BUTTON");
                    $( c1 ).append(btn);
                    $( btn ).attr("type", "button");
                    $( btn ).attr("title", "remove selected");
                    var upd = this.desc.d[ tag ].attr[a].update;
                    $( btn ).css("visibility", "hidden");
                    if( upd ) $( btn ).css("visibility", "visible");   // TODO EMP_if : forse estensibile ad UE?
                    var args = [key, currentObjList[e][key], tag, a, currentObjList, allObjList]
                    var ff = this.hb.wrapFunction(this.f_RemoveFromList.bind(this), args);
                    $( btn ).click( ff );
                        var ico = this.hb.ceFAI("fa-times");
                        $( ico ).addClass("fa-1x");
                        $( btn ).prepend(ico);
    }

    }

    f_Save(args){
        var tag = args[0]; var p = 1;
        var keyValue = args[p]; p++;
        var attrbts = this.desc.d[ tag ].attr;
        var key = "";
        for( var a in attrbts ){
            if( attrbts[a].isKey )
                key = a;
        }
        var fff = function(){
            var target = ( tag === this.qe.targets.TENANT)? [tag] : [tag, this.qe.targets.TENANT];
            this.qe.scheduleQuery("GET", target, null, null, this.cache.update.bind(this.cache) );
        }

        for( var a in this.toUpdate ){
            if( this.toUpdate[a] == true ){
                switch( a ){
                    case "Info":
                        var ctrl = true;
                        for(var attr in attrbts){
                            if( !( attr in this.toUpdate) ){
                            var id = this.getID_BODY_UPDPANEL_ATTR(attr);
                                var cnt = this.hb.ge(id + "_IF");
                                if( cnt ){
                                    if( $( cnt ).css("backgroundColor") === "rgb(238, 98, 98)" ){
                                    ctrl = false;
                                }
                                else{
                                        this.selObj[attr] = $( cnt ).val();
                                    }
                                }
                            }
                        }
                        if( ctrl == true ){
                            this.qe.scheduleQuery("PUT", [tag], null, this.selObj, fff.bind(this));
                        }
                    break;
                    case "wtp":
                        var div = this.hb.ge( this.getID_SELECTOBJ([tag + "_" + a]) );
                        var keyValue = $( div ).children().children().text();
                        var input = this.hb.getKeyValue(a, keyValue);
                        var params = [ this.selObj[key], input];
                        this.qe.scheduleQuery("PUT", [tag], null, params, fff.bind(this));
                    break;
                    default:
                        var cachedObj = null;
                        for( var i=0; i<this.cache.c[tag].length; i++){
                            if( keyValue === this.cache.c[tag][i][key] ){
                                cachedObj = this.cache.c[tag][i];
                                break
                            }
                        }
                        var [onlyNew, onlyPast, sharedEqual, sharedDiff] = this.hb.checkAllDifferences(this.selObj[a], cachedObj[a]);
                        for( var i=0; i<onlyNew.length; i++ ){
                            var nEl = onlyNew[i];
                            this.qe.scheduleQuery("ADD", [a], keyValue, nEl, fff.bind(this));
                        }
                        for( var j=0; j<onlyPast.length; j++ ){
                            var pEl = onlyPast[j];
                            this.qe.scheduleQuery("DELETE", [a], keyValue, fff.bind(this));
                        }
                }
                this.f_updateName(a, true);
            }
        }
        var ff_Reset = this.hb.wrapFunction(this.f_Reset.bind(this), [tag, this.selObj[key] ]);
        setTimeout( ff_Reset, this.delay );
    }

    f_Refresh(args){
        var tag = args[0]; var p = 1;
        var a = args[p]; p++;
        this.qe.scheduleQuery("GET", [tag], null, null, this.cache.update.bind(this.cache));
        var attrbts = this.desc.d[tag].attr;
        var key = "";
        for( var attr in attrbts ){
            if( attrbts[attr].isKey ){
                key = attr;
                break;
                }
                }
        var keyValue = this.selObj[key];
        var ff_Reset = this.hb.wrapFunction(this.f_Reset.bind(this), [tag, this.selObj[key] ]);
        setTimeout( ff_Reset, this.delay );
        var fff = function(){
                    $('a[href="#' + a + '"]').click();
            }
        setTimeout(fff, 6/4*this.delay);
    }

    f_Reset(args){
        var tag = args[0]; var p = 1;
        var key = args[p]; p++;
        var selObj = this.hb.getKeyValue(tag, key);
        for( var a in this.toUpdate ){
            var li = $( "#" + a + "Tab" )[0].parentElement;
            $( li ).removeClass("active");
        }
        var div = this.hb.ge( this.getID_BODY_UPDPANEL() );
        $( div ).remove();
        div = this.d_UpdateBodyPanel(tag, selObj);
        $( "#" + this.getID_BODY() ).append(div);
        div.id = this.getID_BODY_UPDPANEL();
    }

    f_updateName(tag, finished){
        if( finished ){
            var tab = this.hb.ge( tag + "Tab");
            $( tab ).text( tag + " ");
            this.toUpdate[tag] = false;
        }
        else{
            var tab = this.hb.ge( tag + "Tab");
            $( tab ).text( tag + "*");
            this.toUpdate[tag] = true;
        }
    }

    f_onClickInfo(args){
        var tag = args[0]; var p = 1;
        var a = args[p]; p++;
        var cnt = args[p]; p++;

        this.f_updateName("Info", false);
        var type = this.desc.d[tag].attr[a].type;
        var value = $( cnt ).text();
        var id = cnt.id;

        $( cnt ).empty();
        var n = ff_drawInputField(tag, a, value, this.getID_BODY_UPDPANEL_ATTR.bind(this));
        $( cnt ).append(n);
        $( cnt ).prop("onclick", null).off("click");
    }

    f_WarningClose(){
        var str = "";
        for( var a in this.toUpdate ){
            if( this.toUpdate[a] ){
                str += a + " ";
            }
        }
        if( str.length != 0){
            var f_YES = function(){
                    $( modal ).modal('hide');
                    var id = this.getID();
                    var m = this.hb.ge(id);
                    $( m ).modal('hide');
                };
            var modal = generateWarningModal("Discard all changes to: " + str, f_YES.bind(this));
            $( modal ).modal();
        }
        else{
            var id = this.getID();
            var m = this.hb.ge(id);
            $( m ).modal('hide');
        }
    }

}