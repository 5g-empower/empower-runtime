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

    getID_BLOCKSELECTOR(){
        var id = this.getID_SELECTOR() + "_block";
        return id;
    }

    initResources(obj){
        var tag = this.hb.mapName2Tag(obj);
        var title = "Show and update selected " + this.hb.mapName2Title(tag);

// ------------------- Body
        var body = this.hb.ce("DIV");
        body.id = this.getID_BODY_UPDPANEL();

        if( __ROLE === "admin" ){
            var dt = this.cache.DTlist[ tag ];
            var datatable = $("#"+ dt.getID()).DataTable();
            var key = "";
            if( datatable.row('.selected').data() ){
                key = this.hb.getDTKeyFields(datatable.row('.selected').data());
            }
            else if( datatable.row('.selected').data() == null && tag === this.qe.targets.ACCOUNT ){
                key = __USERNAME;
            }
            else{
                return [title, body, buttons];
            }
        }
        else if( __ROLE === "user" && this.cache.DTlist[ tag ]) {
            var dt = this.cache.DTlist[ tag ];
            var datatable = $("#"+ dt.getID()).DataTable();
            var key = "";
            if( datatable.row('.selected').data() ){
                key = this.hb.getDTKeyFields(datatable.row('.selected').data());
            }
            else{
                return [title, body, buttons];
            }
        }
        else if( __ROLE === "user" && tag === this.qe.targets.ACCOUNT) {
            key = __USERNAME;
        }
        else{
            return [title, body, buttons];
        }
        this.selObj = this.hb.getKeyValue(tag , key);

        var div = this.d_UpdatePanel(tag, this.selObj);
        $( body ).append(div);

// ------------------- Buttons
        var buttons = [];

        var json = this.hb.getKeyValue( tag , key);
        var ff_Download = this.hb.wrapFunction(this.f_Download.bind(this), ["SELECTED"+obj.toUpperCase(), json]);
        var btn_Download = {"text": "Download",
                         "color": "primary",
                         "f": ff_Download};
        buttons.push(btn_Download);

        var ff_Upd = this.hb.wrapFunction(this.f_Save.bind(this), [tag]);
        var btn_Upd = {"text": "Save",
                         "color": "primary",
                         "f": ff_Upd};
        if( __ROLE === "admin" || tag === this.qe.targets.ACCOUNT)
            buttons.push(btn_Upd);

        var ff_Close = this.f_WarningClose.bind(this);
        var btn_Close = {"text": "Close",
                         "color": "primary",
                         "f": ff_Close};
         buttons.push(btn_Close);

        return [title, body, buttons];
        }

// -----------------------------------------------------------------------------

    d_UpdatePanel(tag, selObj){

        var div = this.hb.ce("DIV");
        $( div ).css("margin", "20px");
//        $( div ).css("padding", "5px");
        this.selObj = selObj;

        var attrbts = this.desc.d[tag].attr;

        var u = this.hb.ce("UL");
            $( div ).append(u);
        $( u ).addClass("nav nav-tabs");
            // --------------------- Info TAB
                var info = this.hb.ce("LI");
                $( u ).append(info);
                this.toUpdate["Info"]=false;
                    $( info ).html("<a href=\"#Info\" id=\"InfoTab\" data-toggle=\"tab\">Info </a>");
                    var info = [];
            // --------------------- a TAB for each list of objects
        for( var a in attrbts ){
                    if( attrbts[a].type === this.desc.dt.LIST.a || attrbts[a].type === this.desc.dt.LIST.d ){
                var tab = this.hb.ce("LI");
                $( u ).append(tab);
                this.toUpdate[a]=false;
                            $( tab ).html("<a href=\"#" + a + "\" id=\"" + a + "Tab\" data-toggle=\"tab\">" + this.hb.mapName2Title(a) + " </a>");
            }
                    else if(attrbts[a].type === this.desc.dt.OBJ.wtp){
                        var wtp = this.hb.ce("LI");
                        $( u ).append(wtp);
                        this.toUpdate["lvapWtp"]=false;
                            $( wtp ).html("<a href=\"#lvapWtp\" id=\"wtpTab\" data-toggle=\"tab\">" + this.hb.mapName2Title(a) + " </a>");
            }
                    else if(attrbts[a].type === this.desc.dt.OBJ.datapath){
                        var datapath = this.hb.ce("LI");
                        $( u ).append(datapath);
                        this.toUpdate["datapath"]=false;
                            $( datapath ).html("<a href=\"#datapath\" id=\"datapathTab\" data-toggle=\"tab\">" + this.hb.mapName2Title(a) + " </a>");
                    }
                    else{
                        info.push(a);
            }
        }
            // --------------------- JSON TAB
                var JSON = this.hb.ce("LI");
                $( u ).append(JSON);
                this.toUpdate["JSON"]=false;
                    $( JSON ).html("<a href=\"#JSON\" id=\"JSONTab\" data-toggle=\"tab\">JSON </a>");

            var content = this.hb.ce("DIV");
            $( div ).append(content);
            $( content ).addClass("tab-content");
            for( var tab in this.toUpdate ){
                var panel = null;
                switch( tab ){
                    case "Info":    panel = this.d_UP_infoPanel(tag, info); break;
                    case "JSON":    panel = this.d_UP_JSONPanel(tag); break;
                    case "lvapWtp":     panel = this.d_UP_WTPPanel(tag); break;
                    default:        panel = this.d_UP_ListObjectPanel(tag, tab);
                }
                $( content ).append(panel);
                $( panel ).addClass("tab-pane fade")
                panel.id = tab;
            }

            var ff = function(){
                $('a[href="#Info"]').click();
            }
            setTimeout(ff.bind(this), 1/8*this.delay)

        return div;
    }

// -----------------------------------------------------------------------------

    d_UP_infoPanel(tag, info){
        var panel = this.hb.cePANEL();
        $( panel ).addClass("panel panel-info");
        $( panel ).css("margin", "25px 5px");
        $( panel ).css("padding", "25px 5px");

                    var r = this.hb.ceROW();
            $( panel ).append(r);
            var c0 = this.hb.ceCOL("xs",2);
            $( r ).append(c0);
            var c1 = this.hb.ceCOL("xs",10);
            $( r ).append(c1);

            var isToUpdate = function(){
                var tab = arguments[0];
                this.toUpdate[tab] = true;
            }
            $( c1 ).click( this.hb.wrapFunction(isToUpdate.bind(this), ["Info"] ) );

            for( var i=0; i<info.length; i++ ){
                var a = info[i];
                var isEdit = this.desc.d[ tag ].attr[a].update;
                var id = this.getID_BODY_UPDPANEL_ATTR(a);
                var value = this.selObj[a];
                var r = ff_draw(tag, a, id, isEdit, value);
                if( a === "bssid_type" ||
                    a === "role" ){
                    $( c0 ).append(r)
                }
                else if( a === "password" ||
                            a === "new_password" ||
                            a === "new_password_confirm" ){
                    continue
                }
                else{
                    $( c1 ).append(r);
                }
            }
            if( tag === this.qe.targets.ACCOUNT ){
                var change = this.hb.cePANEL();
                $( panel ).append(change);
                $( change ).addClass("panel panel-info");
                $( change ).css("margin", "40px 20px")
                    var change_H = this.hb.cePANEL_H();
                    $( change ).append(change_H);
                    $( change_H ).text("Change Password")
                    var change_B = this.hb.cePANEL_B();
                    $( change ).append(change_B);
                    var list = ["password", "new_password", "new_password_confirm"];
                    for( var i=0; i<list.length; i++ ){
                        var a = list[i];
                        var isEdit = this.desc.d[ tag ].attr[a].update;
                        var id = this.getID_BODY_UPDPANEL_ATTR(a);
                        var value = this.selObj[a];
                        var r = ff_draw(tag, a, id, isEdit, value);
                        $( change_B ).append(r);
                        $( r ).click( this.hb.wrapFunction(isToUpdate.bind(this), ["Info"] ) );
            }
    }

        return panel;
    }

    d_UP_WTPPanel(tag){
        var panel = this.hb.cePANEL();
        $( panel ).addClass("panel panel-info")
        $( panel ).css("margin", "25px 5px");
            var body = this.hb.cePANEL_B();
            $( panel ).append(body);

            var wtp = this.selObj["wtp"];
    var div = this.hb.ce("DIV");
            $( body ).append(div);
            $( div ).css("margin", "25px 0px");
    var r0 = this.hb.ceROW();
    $( div ).append(r0);
                $( r0 ).css("margin", "8px");
                    var c00 = this.hb.ceCOL("xs", 2);
                    $( r0 ).append(c00);
                    $( c00 ).addClass("text-right")
                        var s00 = this.hb.ce("SPAN");
                        $( c00 ).append(s00);
                        $( s00 ).text("Current WTP: ")
                        $( s00 ).css("fontWeight", 700)
                    var c01 = this.hb.ceCOL("xs", 4);
                    $( r0 ).append(c01);
                        var s01 = this.hb.ce("SPAN");
                        $( c01 ).append(s01);
                        $( s01 ).text( wtp["label"] + " ( " + wtp["addr"] + " ) " );
                    var c02 = this.hb.ceCOL("xs", 2);
                    $( r0 ).append(c02);
                    $( c02 ).addClass("text-right")
                        var s02 = this.hb.ce("SPAN");
                        $( c02 ).append(s02);
                        $( s02 ).text("Handover to: ")
                        $( s02 ).css("fontWeight", 700)
                    var c03 = this.hb.ceCOL("xs", 4);
                    $( r0 ).append(c03);
                        var s03 = this.hb.ce("SPAN");
                        $( c03 ).append(s03);
                        s03.id = this.getID_BODY_UPDPANEL_ATTR("wtp");
                        $( s01 ).text("");
    var r1 = this.hb.ceROW();
                $( div ).append(r1);
                $( r1 ).css("margin", "8px");
                    var c10 = this.hb.ceCOL("xs", 2);
        $( r1 ).append(c10);
                    $( c10 ).addClass("text-right")
                        var s10 = this.hb.ce("SPAN");
                        $( c10 ).append(s10);
                        $( s10 ).text("Current block: ")
                        $( s10 ).css("fontWeight", 700)
                    var c11 = this.hb.ceCOL("xs", 4);
        $( r1 ).append(c11);
                        var s11 = this.hb.ce("SPAN");
                        $( c11 ).append(s11);
                        $( s11 ).text( this.selObj["blocks"]["hwaddr"] );
                    var c12 = this.hb.ceCOL("xs", 2);
                    $( r1 ).append(c12);
                    $( c12 ).addClass("text-right")
                        var s12 = this.hb.ce("SPAN");
                        $( c12 ).append(s12);
                        $( s12 ).text("Selected block: ")
                        $( s12 ).css("fontWeight", 700)
                    var c13 = this.hb.ceCOL("xs", 4);
                    $( r1 ).append(c13);
                        var s13 = this.hb.ce("SPAN");
                        $( c13 ).append(s13);
                        s13.id = this.getID_BODY_UPDPANEL_ATTR("wtp") + "_block";
                        $( s13 ).text("");

            if( __ROLE === "user" )
                return panel;

            // built selector
                var handover = this.hb.cePANEL();
                $( panel ).append(handover);
                $( handover ).addClass("panel panel-info");
                $( handover ).css("margin", "40px 20px")
                    var handover_H = this.hb.cePANEL_H();
                    $( handover ).append(handover_H);
                    $( handover_H ).text("Perform handover")
                    var handover_B = this.hb.cePANEL_B();
                    $( handover ).append(handover_B);

                    var rr0 = this.hb.ceROW();
                    $( handover_B ).append(rr0);
                    $( rr0 ).css("margin", "8px");
                    var rr1 = this.hb.ceROW();
                    $( handover_B ).append(rr1);
                    $( rr1 ).css("margin", "8px")
                        var cc00 = this.hb.ceCOL("xs", COL_0);
                        $( rr0 ).append(cc00);
                        $( cc00 ).addClass("text-right")
                            var ss00 = this.hb.ce("SPAN");
                            $( cc00 ).append(ss00);
                            $( ss00 ).text("Connect to a new WTP : ")
                            $( ss00 ).css("fontWeight", 700)
                        var cc01 = this.hb.ceCOL("xs", COL_1);
                        $( rr0 ).append(cc01);
                var selector = this.hb.ce("SELECT");
                            $( cc01 ).append(selector);
                selector.id = this.getID_SELECTOR()
                $( selector ).css("width","100%");
                $( selector ).css("height","35px");
                        var ff_change = function(){
                    var el = selector.options[selector.selectedIndex];
                            var id = el.id;
                            var newWTP = this.hb.getKeyValue(this.qe.targets.WTP, id);
                            this.selObj["wtp"] = newWTP;
                    $( s03 ).text( newWTP["label"] + " ( " + newWTP["addr"] + " ) " );
                    $( s13 ).text("")
                            this.f_UpdateBlockSelector.bind(this)([newWTP]);
                            this.toUpdate["lvapWtp"] = true;
    }
                        $( selector ).change(ff_change.bind(this));

                        var ccc00 = this.hb.ceCOL("xs", COL_0);
                        $( rr1 ).append(ccc00);
                        $( ccc00 ).addClass("text-right")
                            var sss00 = this.hb.ce("SPAN");
                            $( ccc00 ).append(sss00);
                            $( sss00 ).text("Select a block : ")
                            $( sss00 ).css("fontWeight", 700)
                        var ccc01 = this.hb.ceCOL("xs", COL_1);
                        $( rr1 ).append(ccc01);
                            var blockSelector = this.hb.ce("SELECT");
                            $( ccc01 ).append(blockSelector);
                            blockSelector.id = this.getID_BLOCKSELECTOR()
                            $( blockSelector ).css("width","100%");
                            $( blockSelector ).css("height","35px");
                        var fff_change = function(){
                            var el = blockSelector.options[blockSelector.selectedIndex];
                    var id = el.id;
                    var txt = "";
                            if( el.id != "ALL" ){
                                txt = el.id;
                            }
                    else{
                        $( s12 ).text("Any block")
                    }
                    $( s13 ).text(txt);
                    $( s03 ).text( this.selObj["wtp"]["label"] + " ( " + this.selObj["wtp"]["addr"] + " ) " );
                    this.toUpdate["lvapWtp"] = true;
                        }
                        $( blockSelector ).change(fff_change.bind(this));

                var ff = function(){
                    this.f_UpdateWTPSelector.bind(this)();
                    this.f_UpdateBlockSelector.bind(this)([wtp]);
                }
                setTimeout( ff.bind(this), 1/8*this.delay);

        return panel;
            }

    d_UP_ListObjectPanel(tag, tab){
        var panel = this.hb.cePANEL();
//            var ph = this.hb.cePANEL_H();
//            $( panel ).append(ph);
            var body = this.hb.cePANEL_B();
            $( panel ).append(body);

            var a = tab;
            var isEdit = this.desc.d[ tag ].attr[a].update;
            var id = this.getID_BODY_UPDPANEL_ATTR(a);
            var value = this.selObj[a];
            var div = ff_draw(tag, a, id, isEdit, value);
            $( body ).append(div);

        return panel;
        }

    d_UP_JSONPanel(tag){
        var panel = this.hb.cePANEL();
            var pre = this.hb.ce("PRE");
            $( panel ).append(pre)
                var txt = JSON.stringify(this.selObj, undefined, 4);
                $( pre ).html( this.hb.syntaxHighlight(txt));
                $( pre ).css("margin", "20px")
        return panel;
            }

// -----------------------------------------------------------------------------

    f_UpdateWTPSelector(){
        var selector = this.hb.ge( this.getID_SELECTOR() );
        $( selector ).empty();

        var currentWTP = this.selObj["wtp"];
        var allWTP = this.cache.c[ this.qe.targets.WTP ];

                var opt0 = this.hb.ce("OPTION");
                $( selector ).append(opt0);
                opt0.id = currentWTP["addr"];
                var txt0 = currentWTP["label"] + " ( " + currentWTP["addr"] + " ) ";
                $( opt0 ).text( txt0 );

        for( var i=0; i<allWTP.length; i++){
            if( allWTP[i]["addr"] != currentWTP["addr"] ){
                var opt = this.hb.ce("OPTION");
                $( selector ).append(opt);
                opt.id = allWTP[i]["addr"];
                var txt = allWTP[i]["label"] + " ( " + allWTP[i]["addr"] + " ) ";
                $( opt ).text( txt );
                var clr = "";
                ( allWTP[i]["state"] === "online" )? clr = "#7DFF7D" : clr = RED;
                $( opt ).css("color", clr);
            }
        }
    }

    f_UpdateBlockSelector(args){
        var blockselector = this.hb.ge( this.getID_BLOCKSELECTOR() );
        $( blockselector ).empty();

        var selObj = args[0];
        var allBlocks = selObj["supports"];
            var opt = this.hb.ce("OPTION");
            $( blockselector ).append(opt);
            opt.id = "ALL";
            var txt = "Any block";
            $( opt ).text( txt );
        for( var i=0; i<allBlocks.length; i++){
            opt = this.hb.ce("OPTION");
            $( blockselector ).append(opt);
            opt.id = allBlocks[i]["hwaddr"];
            txt = allBlocks[i]["hwaddr"];
            $( opt ).text( txt );
        }
        }

    f_Save(args){
        var tag = args[0];
        var attrbts = this.desc.d[tag].attr;
        var input = this.selObj ;
//        var input = jQuery.extend(true, {}, this.selObj) ;
                        var ctrl = true;
        var nextSelObj = null;
        for( var a in attrbts ){
            var id = this.getID_BODY_UPDPANEL_ATTR(a);
            var clr = $( "#" + id ).css('backgroundColor');
            if( clr === "rgb(238, 98, 98)"){
                return
                        }
            if( attrbts[a].update ){
                switch(a){
                    case "wtp":
                        var txt = $( this.hb.ge(id) ).text();
                        var addr = txt.substring(txt.length-20, txt.length-3);
                        var block = $( this.hb.ge( id + "_block" ) ).text(); console.log(block, block.length)
                        if( block.length > 20 ){
                            block = "";
                        }
                        console.log( addr, block)
                        var wtp = this.hb.getKeyValue("wtps", addr);
                        var params = [input, wtp, block]
                    break;
                    default:
                        input[a] = $( this.hb.ge(id) ).val();
                        break;
            }
        }
    }
        var fff = function(){
            var target = ( tag === this.qe.targets.TENANT)? [tag] : [tag, this.qe.targets.TENANT];
            this.qe.scheduleQuery("GET", target, null, null, this.cache.update.bind(this.cache) );

            var ff = function(){
                var body = this.hb.ge( this.getID_BODY_UPDPANEL() );
                $( body ).empty();
                var key = this.hb.getKeyFields(tag);
                this.selObj = this.hb.getKeyValue(tag, this.selObj[key]);
                var div = this.d_UpdatePanel(tag, this.selObj);
                $( body ).append(div);
        }
            setTimeout(ff.bind(this), 1/2*this.delay)
    //            var id = this.getID();
    //            var m = this.hb.ge(id);
    //            $( m ).modal('hide');
    }

        for(var tab in this.toUpdate ){
            switch( tab ){
                case "Info":
                    if( this.toUpdate["Info"] ){
                        this.toUpdate["Info"] = false;
                        this.qe.scheduleQuery("PUT", [tag], null, input, fff.bind(this));
        }
                    break;
                case "lvapWtp":
                    if( this.toUpdate["lvapWtp"] ){
                        this.toUpdate["lvapWtp"] = false;
                        this.qe.scheduleQuery("PUT", [tag], null, params, fff.bind(this));
                    }
                    break;
                default:
                    if( this.toUpdate[tab] )
                        console.log("EmpUpdateModalBox.f_Save: " + tag + "." + tab + " not implemented")
        }
    }
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

    f_Download(args){
        var title = args[0];
        var json = args[1];
        var txt = JSON.stringify(json, undefined, 4);
        var filename = __USERNAME.toUpperCase() + "_" + title + "_" +Date.now()+".txt";
        this.hb.fdownload(txt, filename);
    }

}