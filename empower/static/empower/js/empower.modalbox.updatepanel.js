class EmpUpdateModalBox extends EmpModalBox{

    constructor(keys){
        super(keys);

        this.toUpdate = {};
        this.selObj = null;

        this.instances = {};

        console.log("AFRA EmpUpdateModalBox keys= ", keys)

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

        this.__tag = tag;

        console.log(this.__tag);

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
        if( __ROLE === "admin" || tag === this.qe.targets.ACCOUNT){
            if (tag !== this.qe.targets.TENANT)
                buttons.push(btn_Upd);
        }

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

                       console.log ("TAG", tag);
                       if (tag === this.qe.targets.LVAP){
                           var lvap_ho = this.hb.ce("LI");
                           $( u ).append(lvap_ho);
                           this.toUpdate["lvapHO"]=false;
                           $( lvap_ho ).html("<a href=\"#lvapHO\" id=\"lvaphoTab\" data-toggle=\"tab\">" + "Handover" + " </a>");
                       }
           }
                   else if(attrbts[a].type === this.desc.dt.OBJ.vbs){

                       console.log ("TAG", tag);
                       if (tag === this.qe.targets.UE){
                           var ue_ho = this.hb.ce("LI");
                           $( u ).append(ue_ho);
                           this.toUpdate["ueHO"]=false;
                           $( ue_ho ).html("<a href=\"#ueHO\" id=\"uehoTab\" data-toggle=\"tab\">" + "Handover" + " </a>");
                       }
           }
                    else if(attrbts[a].type === this.desc.dt.OBJ.datapath){
                        var datapath = this.hb.ce("LI");
                        $( u ).append(datapath);
                        this.toUpdate["datapath"]=false;
                            $( datapath ).html("<a href=\"#datapath\" id=\"datapathTab\" data-toggle=\"tab\">" + this.hb.mapName2Title(a) + " </a>");
            }
                    else if(attrbts[a].type === this.desc.dt.OBJ.slice){
                        var wtp = this.hb.ce("LI");
                        $( u ).append(wtp);
                        this.toUpdate["ueSlice"]=false;
                            $( wtp ).html("<a href=\"#ueSlice\" id=\"sliceTab\" data-toggle=\"tab\">" + this.hb.mapName2Title(a) + " </a>");
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
                    case "lvapWtp": panel = this.d_UP_WTPPanel(tag); break;
                    case "lvapHO":  
                        this.instances.lvapho = new LVAP_HO_UP_Panel(selObj)
                        panel = this.instances.lvapho.generate(); 
                        break;
                    case "ueHO":    
                        this.instances.ueho = new UE_HO_UP_Panel(selObj)
                        panel = this.instances.ueho.generate(); 
                        break;
                    case "ueSlice": 
                        this.instances.ueslice = new UE_Slice_Panel(selObj)
                        panel = this.instances.ueslice.generate(); 
                        break;//panel = new UE_Slice_Panel(selObj).generate(); break;// this.hb.cePANEL();break; //panel = this.d_UP_SlicePanel(tag); break;
                    default:        
                        panel = this.d_UP_ListObjectPanel(tag, tab);
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
                        $( s03 ).text("");
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
                        $( c11 ).append(s11); console.log(this.selObj)
                        $( s11 ).text( this.selObj["blocks"][0]["hwaddr"] );
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
                    $( s03 ).text( newWTP["label"] + " ( " + newWTP["addr"] + " )" );
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
                    $( s03 ).text( this.selObj["wtp"]["label"] + " ( " + this.selObj["wtp"]["addr"] + " )" );
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
                        var txt = $( this.hb.ge(id) ).text(); console.log(txt)
                        var addr = txt.substring(txt.length-19, txt.length-2); console.log(addr)
                        var block = $( this.hb.ge( id + "_block" ) ).text();
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
        if (this.instances.lvapho){
            console.log("there is a lvapho!");
            console.log("WTP modified?",this.instances.lvapho._wtp_pnc.has_been_modified())
            console.log("BLOCK modified?",this.instances.lvapho._block_pnc.has_been_modified())
            if (this.instances.lvapho._wtp_pnc.has_been_modified() || this.instances.lvapho._block_pnc.has_been_modified()){
                
                params = {}

                if (this.instances.lvapho._wtp_pnc.is_ANY()){
                    params.wtp = null;
                    console.log("WTP is ANY")
                }
                else{
                    params.wtp = this.instances.lvapho._wtp_pnc.get_currently_selected_obj();
                    console.log("WTP: ", params.wtp)
                }

                if (this.instances.lvapho._block_pnc.is_ANY()){
                    params.block = null
                    console.log("BLOCK is ANY")
                }
                else{
                    params.block = this.instances.lvapho._block_pnc.get_currently_selected_obj();
                    console.log("BLOCK: ", params.block)
                }
                params.lvap = input;
                console.log("LVAP: ", input);

                this.qe.scheduleQuery("PUT", [tag], null, params, null);
            }
        }
        if (this.instances.ueho){
            console.log("there is a ueho!");
            console.log("VBS modified?",this.instances.ueho._vbs_pnc.has_been_modified())
            console.log("CELL modified?",this.instances.ueho._cell_pnc.has_been_modified())
            if (this.instances.ueho._vbs_pnc.has_been_modified() || this.instances.ueho._cell_pnc.has_been_modified()){
                
                params = {}

                if (this.instances.ueho._vbs_pnc.is_ANY()){
                    params.vbs = null;
                    console.log("VBS is ANY")
                }
                else{
                    params.vbs = this.instances.ueho._vbs_pnc.get_currently_selected_obj();
                    console.log("VBS: ", params.vbs)
                }

                if (this.instances.ueho._cell_pnc.is_ANY()){
                    params.cell = null 
                    console.log("CELL is ANY")
                }
                else{
                    params.cell = this.instances.ueho._cell_pnc.get_currently_selected_obj();
                    console.log("CELL: ", params.cell)
                }
                params.ue = input;
                console.log("UE: ", input);

                this.qe.scheduleQuery("PUT", [tag], null, params, null);

            }
        }
        if (this.instances.ueslice){
            console.log("there is a ueslice!");
            console.log("Slice modified?",this.instances.ueslice._slice_pnc.has_been_modified())
            if (this.instances.ueslice._slice_pnc.has_been_modified() ){

                params = {};
                
                if (this.instances.ueslice._slice_pnc.is_ANY()){
                    params.slice = null 
                    console.log("Slice is ANY")
                }
                else{
                    params.slice = this.instances.ueslice._slice_pnc.get_currently_selected_obj();
                    console.log("Slice: ", params.slice)
                }

                params.ue = input;
                console.log("UE: ", input);

                this.qe.scheduleQuery("PUT", [tag], null, params, null);

            }
        }

        var id = this.getID();
        var m = this.hb.ge(id);
        $( m ).modal('hide');
    }

    f_WarningClose(){
        console.log(this.__tag);
        if (this.__tag === this.qe.targets.TENANT){
            var id = this.getID();
            var m = this.hb.ge(id);
            $( m ).modal('hide');
            return;
        }
        var str = "";
        for( var a in this.toUpdate ){
            if( this.toUpdate[a] ){
                str += a + " ";
            }
        }
        if (this.instances.lvapho){
            if (this.instances.lvapho._wtp_pnc.has_been_modified() || this.instances.lvapho._block_pnc.has_been_modified()){
                str += "LVAP_HandOver "
            }
        }
        if (this.instances.ueho){
            if (this.instances.ueho._vbs_pnc.has_been_modified() || this.instances.ueho._cell_pnc.has_been_modified()){
                str += "UE_HandOver "
            }
        }
        if (this.instances.ueslice){
            if (this.instances.ueslice._slice_pnc.has_been_modified() ){
                str += "UE_Slice "
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

/******************************************************************************
 * 
 * CODE INTEGRATION
 * 
 *****************************************************************************/

 class ReferenceObject{
    constructor(tag, obj){
        this.tag = tag;
        this.obj = obj;
    }

    is_valid(){
        return (this.tag != null) && (this.obj != null);
    }

    is_generic(){
        return this.tag === SelectorOptionDescriptor.get_generic_key();
    }
}

class SelectorOptionDescriptor{

    // __ANY_KEY = SelectorOptionDescriptor.get_generic_key();

    constructor(params){

        // console.log(params);

        if (("tag" in params) &&
            ("obj" in params)){
            this.set_from_tag(params.tag, params.obj);
        }
        else if (("txt" in params) &&
            ("key" in params)){
            this.txt = params.txt;
            this.key = params.key;
        }
        else{
            this.txt = null;
            this.key = null;
        }

    }

    static __ANY_KEY(){
        return SelectorOptionDescriptor.get_generic_key();
    }

    set_from_tag(tag, obj){
        this.txt = null;
        this.key = null;
        switch(tag){
            case SelectorOptionDescriptor.__ANY_KEY():
                this.txt = "ANY";
                this.key = SelectorOptionDescriptor.__ANY_KEY();
                break;
            case "wtps":
                this.txt= obj['label']+"("+obj['addr']+")";
                this.key= obj['addr']
                break;
            case "vbses":
                this.txt= obj['label']+"("+obj['addr']+")";
                this.key= obj['addr']
                break;
            case "blocks":
                this.txt= obj['hwaddr'];
                this.key= obj['hwaddr'];
                break;
            case "cells":
                this.txt= obj['addr'] + " ["+obj['pci']+"]";
                this.key= ""+obj['pci'];
                break;
            case "slices":
                this.txt= obj['dscp'];
                this.key= ""+obj['dscp'];
                break;
            default:
                console.warn("INVALID tag: ", tag);
        }
    }

    is_valid(){
        return ((this.txt != null) && (this.key != null));
    }

    is_key(key){
        return (key === this.key);
    }

    static get_generic(txt){
        var sod = new SelectorOptionDescriptor({"key": "__ANY__", "txt": txt});
        return sod;
    }

    static check_key(key, tag, obj){
        var params = {"tag": tag, "obj": obj};
        var sod = new SelectorOptionDescriptor(params);
        return (key === sod.key);
    }

    static get_generic_key(){
        return "__ANY__"
    }

}

class Selector{
    constructor(hb, selector_id, css, label_txt){
        this.hb = hb
        this._id = selector_id;
        this._css = css;
        this._lbl_txt = label_txt;
        this._me = null;
        this._label = null;
        this._select = null;
        this._onchange_functions = [];
    }

    get_COMPONENT_ID(){
        return this._id;
    }

    get_LABEL_ID(){
        return this._id+"_lbl";
    }

    get_SELECT_ID(){
        return this._id+"_slc";
    }

    generate(){
        var component = this.hb.ceROW();
        component.id = this.get_COMPONENT_ID();
        $( component ).addClass("form-group")
        
        var label = this.hb.ce("LABEL");
        label.for = this.get_SELECT_ID();
        $( label ).text( this._lbl_txt );
        $( label ).addClass("col-xs-2");
        $( label ).addClass("control-label");
        $( label ).css("height", "35px");
        $( component ).append(label);
        this._label = label
        
        var selector = this.hb.ce("SELECT");
        $( selector ).addClass("col-xs-10")
        $( selector ).addClass("form-control")
        selector.id = this.get_SELECT_ID();
        // Object.entries(this._css).forEach(([key, value]) => {
        //     $( selector ).css(key,value);
        // });
        $( component ).append(selector);
        this._select = selector
        this.apply_css(this._css);
        
        this._me = component;
        return component;
    }

    add_opt(opt_txt, opt_key){
        console.log("add_opt");
        // var opt = this.hb.ce("OPTION");
        // opt.id = opt_key;
        // opt.value = opt_key;
        // $( opt ).text( opt_txt );
        var opt = new Option(opt_txt, opt_key);
        $( this._select ).append( $( opt ) );
    }

    add_batch_opts(opts){
        console.log("add_batch_opts");
        for (var i in opts){
            var opt_txt = opts[i].txt
            var opt_key = opts[i].key
            this.add_opt(opt_txt, opt_key)
        }
    }

    remove_all_options(){
        $( this._select ).empty();
    }

    select(value){
        $( this._select ).val(value).trigger('change');
    }

    select_by_index(index){
        $( this._select ).prop("selectedIndex", index).trigger("change"); 
    }

    get_selected(){
        return $( this._select ).val();
    }

    assign_onChange(f, reset){
        if (reset){
            this._onchange_functions.length = 0;
        }
        this._onchange_functions.push(f);
        // console.log("this._onchange_functions: ", this._onchange_functions);
        var ff = (function(){
            // console.log("change ongoing!")
            for (var i = 0 ; i < this._onchange_functions.length; i++){
                // console.log("FUNCTION: [",i,"]", this._onchange_functions[i]);
                this._onchange_functions[i]();
            }
        }.bind(this));
        $( this._select ).off("change");
        $( this._select ).on("change", ff);
        // console.log("assign_onChange")
        // $( this._select ).off("change");
        // $( this._select ).on("change", f);
    }

    // add_onChange(f){
    //     this._onchange_functions.push(f);
    //     var ff = (function(){
    //         for (var i = 0 ; i < this._onchange_functions.length; i++){
    //             this._onchange_functions[i]();
    //         }
    //     }.bind(this));
    //     $( this._select ).off("change");
    //     $( this._select ).on("change", ff);
    // }

    reset_onChange(){
        $( this._select ).off("change");
    }

    apply_css(css){
        Object.entries(this._css).forEach(([key, value]) => {
            $( this._select ).css(key,value);
        });
    }
}


class InfoFrame{
    constructor(hb, desc, frame_id, params, black_list=[]){
        this.hb = hb
        this.desc = desc
        this._id = frame_id;
        this._css = params.css;
        this._me = null;
        this._fields = null;
        this._title = null;
        this._panel = null;
        this._title_text = "Default title";
        if ("title" in params)
            this._title_text = params.title;
        this._color = "info";
        if ("color" in params)
            this._color = params.color;
        this._reference = null;
        this._default_tag = SelectorOptionDescriptor.get_generic_key();
        this._black_list = black_list;
        this._counter = 0;
    }

    get_COMPONENT_ID(){
        return this._id;
    }

    get_FRAME_ID(){
        return this.get_COMPONENT_ID()+"_frm";
    }

    get_FIELDS_ID(){
        return this.get_COMPONENT_ID()+"_fields";
    }

    get_FIELD_ID(field_id){
        return this.get_FIELDS_ID()+"_"+field_id;
    }

    get_FIELDVALUE_ID(field_id){
        return this.get_FIELDS_ID()+"_"+field_id+"_v";
    }

    generate(){
        var component = this.hb.ceROW();
        component.id = this.get_COMPONENT_ID();
        $( component ).addClass("form-group")
        $( component ).css("padding", "10px");

        var pan = this.hb.cePANEL();
        this._panel = pan;
        $( pan ).addClass("panel panel-"+this._color);
        $( component ).append(pan);
        var ph = this.hb.cePANEL_H();
        $( pan ).append(ph);
        var ttl = this.hb.ce("DIV");
            
            $( ttl ).text(this._title_text);
            $( ph ).append(ttl);
            this._title = ttl;
        
        var pb = this.hb.cePANEL_B();
        $( pan ).append(pb);

            
        // $( r ).append(c0);
        // $( ph ).append(r);
        
        var fields = this.hb.ceCOL("xs", 12);
        fields.id = this.get_FIELDS_ID();
        // Object.entries(this._css).forEach(([key, value]) => {
        //     $( fields ).css(key,value);
        // });
        $( pb ).append(fields);
        this._fields = fields;
        //this.apply_css(this._css);
        this.update_status()

        this._me = component;
        return component;

    }

    add_field(tag, a, isEdit, value){

        if (this.is_blacklisted(a)){
            return;
        }

        var entry_id = this.get_FIELD_ID(a);
        var value_id = this.get_FIELDVALUE_ID(a);
        var field = ff_draw(tag, a, value_id, isEdit, value)
        if (( field === null) || (field === undefined)){
            return;
        }
        field.id = entry_id
        var existing_entry = this.hb.ge(this.get_FIELD_ID(a));
        // console.log(existing_entry);
        if (existing_entry === null){
            // console.log("NO ENTRY!");
            $( this._fields ).append(field);
            // console.log( $( this._fields ).children().show() )
            // console.log( this.hb.ge(this.get_FIELD_ID(a)) );
            // console.log();

        }
        else{
            // console.log("ENTRY!");
            $( existing_entry ).replaceWith(field)
        }

        // if (a === "band"){
        //     console.log("DEBUG BAND BAND");
        //     console.log("TAG",tag);
        //     console.log("A",a);
        //     console.log("VALUE",value);
        //     console.log(field);
        // }
    }

    set_generic(text){
        var generic = this.hb.ceROW();
        $( generic ).addClass("text-center");
        $( generic ).css("padding", "20px");
        $( generic ).css("font-size", "20px");
        $( generic ).css("font-weight", "bold");
        $( generic ).text(text);

        $( this._fields ).append(generic);

    }

    add_obj_fields(ref_tag, ref_obj){

        // console.log("REF_TAG", ref_tag)
        // console.log("REF_OBJ", ref_obj)

        $( this._fields ).empty();

        if (ref_tag === this._default_tag){
            this.set_generic(ref_obj);
        }
        else{
            var attrbts = this.desc.d[ref_tag].attr;

            // console.log(attrbts)


            for( var a in attrbts ){
                // var a = attrbts[i];
                var isEdit = false;
                var value = ref_obj[a];
                if (a === "band"){
                    var band = value
                    var channel = ref_obj['channel']
                    value = [band, channel]
                }
            

                // console.log(a, value)

                this.add_field(ref_tag,a,isEdit,value)
                
            }
        }

        this.update_reference( new ReferenceObject(ref_tag, ref_obj));
    }

    is_blacklisted(attr){
        if (this._black_list.includes(attr))
            return true;
        return false;
    }
    
    update_reference(ref){
        this._reference = ref;
    }

    get_reference(){
        return this._reference;
    }

    apply_css(css){
        Object.entries(css).forEach(([key, value]) => {
            $( this._fields ).css(key,value);
        });
        // this._counter = this._counter +1;
        // if ((this._counter % 2) == 0){
        //     $( this._title ).text("PARI: "+ (this._counter));
        // }
        // else{
        //     $( this._title ).text("DISPARI: "+ (this._counter));
        // }
    }

    update_status(title, color){
        if (title){
            $( this._title ).text(title);
        }
        if (color){
            $( this._panel ).removeClass().addClass("panel panel-"+color);
        }
    }

    get_title_text(){
        return this._title_text;
    }
}

class DoubleInfoFrame{
    constructor(hb, desc, frame_id, params, black_list=[]){
        this.hb = hb
        this.desc = desc
        this._id = frame_id;
        this._params = params;
        this._me = null
        this._left = new InfoFrame(this.hb, this.desc, this.get_LEFT_ID(), params.left, black_list)
        this._right = new InfoFrame(this.hb, this.desc, this.get_RIGHT_ID(), params.right, black_list)
    }

    get_COMPONENT_ID(){
        return this._id;
    }

    get_LEFT_ID(){
        return this.get_COMPONENT_ID()+"_l";
    }

    get_RIGHT_ID(){
        return this.get_COMPONENT_ID()+"_r";
    }

    generate(){
        var component = this.hb.ceROW();
        // component.id = this.get_COMPONENT_ID();
        $( component ).addClass("form-group")
        $( component ).addClass("vertical-align")
        $( component ).css("padding", "10px");
        
        var if1 = this.hb.ceCOL("xs", 5);
        $( component ).append(if1);
        var if1_elem = this._left.generate()
        $( if1 ).append(if1_elem);

        var separator = this.hb.ceCOL("xs", 2);
        $( component ).append(separator);
        $( separator ).addClass("text-center");
        var icon = this.hb.ceFAI("fa-sign-in");
        $( icon ).addClass("fa-5x")
        $( icon ).css("color", "#2e6da4");
        $( separator ).append(icon);

        var if2 = this.hb.ceCOL("xs", 5);
        $( component ).append(if2);
        var if2_elem = this._right.generate()
        $( if2 ).append(if2_elem);

        this._me = component;
        return component;
    }

    update(tag1, obj1, tag2, obj2){
        if ((tag1 != null) && (obj1 != null)){
            this.left().add_obj_fields(tag1, obj1);
            this.left().update_reference( new ReferenceObject(tag1, obj1));
        }
        if ((tag2 != null) && (obj2 != null)){
            this.right().add_obj_fields(tag2, obj2);
            this.right().update_reference( new ReferenceObject(tag2, obj2));
        }
    }

    get_references(){
        return {
            "left": this._left.get_reference(),
            "right": this._right.get_reference()
        }
    }

    left(){
        return this._left;
    }

    right(){
        return this._right;
    }

}

class PickNCheck{
    constructor(params){
        this.hb = params.hb
        this.desc = params.desc
        this._id = params.pnc_id;
        this._label = params.label;
        this._params = params.params;
        var bl = [];
        if ("black_list" in params){
            bl = params.black_list
        }
        this._me = null
        this._selector = new Selector(this.hb, this.get_SELECTOR_ID(), this._params.sel, this._label)
        this._dif = new DoubleInfoFrame(this.hb, this.desc, this.get_DIF_ID(), this._params.dif, bl)
    }

    get_COMPONENT_ID(){
        return this._id;
    }

    get_SELECTOR_ID(){
        return this.get_COMPONENT_ID()+"_slc";
    }

    get_DIF_ID(){
        return this.get_COMPONENT_ID()+"_dif";
    }

    generate(){
        var component = this.hb.ceROW();
        // component.id = this.get_COMPONENT_ID();
        $( component ).addClass("form-group")
        $( component ).css("padding", "10px");
     
        $( component ).append(this._selector.generate());

        $( component ).append(this._dif.generate());

        this._me = component;
        return component;
    }

    set_opts(opts){
        this._selector.add_batch_opts(opts);
    }

    remove_all_options(){
        this._selector.remove_all_options();
    }

    select(value){
        this._selector.select(value);
    }

    select_by_index(index){
        this._selector.select_by_index(index);
    }

    get_currently_selected(){
        return this._selector.get_selected();
    }

    update_infos(tag1, obj1, tag2, obj2){
        this._dif.update(tag1, obj1, tag2, obj2);
        this.conditional_format();
    }

    update_bothinfos(tag, obj){
        this._dif.update(tag, obj, tag, obj);
        this.conditional_format();
    }

    update_leftinfo(tag, obj){
        this._dif.update(tag, obj, null, null);
        this.conditional_format();
    }

    update_rightinfo(tag, obj){
        this._dif.update(null, null, tag, obj);
        this.conditional_format();
    }

    assign_selectOnChange(f, reset){
        this._selector.assign_onChange(f, reset);
    }

    // add_selectOnChange(f){
    //     this._selector.add_onChange(f);
    // }

    get_references(){
        return this._dif.get_references();
    }

    conditional_format(){
        references = this.get_references();
    }

    left(){
        return this._dif.left();
    }

    right(){
        return this._dif.right();
    }

}

class Entity_PNC extends PickNCheck{
    constructor(params){
        super(params);

        if ("selected_obj" in params){
            this._selected_obj = params.selected_obj;
        }
        else{
            this._selected_obj = null;
            console.warn("selected_obj not provided in params")
        }

        if ("candidates" in params){
            this._candidates = params.candidates;
        }
        else{
            this._candidates = null;
            console.warn("candidates not provided in params")
        }

        if ("tag" in params){
            this._tag = params.tag;
        }
        else{
            this._tag = null;
            console.error("tag not provided in params")
        }

        if ("cache" in params){
            this._cache = params.cache;
        }
        else{
            this._cache = null;
            console.error("cache not provided in params")
        }

        this._type = "Entity_PNC";
        if ("mytype" in params){
            this._type = params.mytype;
        }

        this._with_any_option = false;
        if ("with_any_option" in params){
            this._with_any_option = true;
            this._any_text = params.with_any_option;
        }

        this._default_tag = SelectorOptionDescriptor.get_generic_key();

        this.fill_and_config(true);

    }

    fill_and_config(reset){

        var option_list = this.generate_options(this._tag);

        // Need to use setTimeout beacuse of the delay in adding component to DOM
        // --> MutationObserver?

        setTimeout(
            (function(){

                console.log("FILL&CONFIG", this.my_type())
                // Add options to selector
                console.log("Add options to selector");
                this.set_opts(option_list);

                // Set selected option (IF any)

                console.log("SELECTED OBJECT1: ",this._selected_obj); 

                var selected_key = null;
                if (this._selected_obj != null){
                    console.log("Set selected option", this._selected_obj);
                    var params = {"tag": this._tag, "obj": this._selected_obj};
                    console.warn ("tag", this._tag, "obj", this._selected_obj)
                    var sod = new SelectorOptionDescriptor(params);
                    console.log("Selected SOD: ",sod)
                    selected_key = sod.key;
                }
                else{
                    console.log("NO Selected option");
                    if (this._with_any_option){
                        console.log("Set default option");
                        var params = {"tag": this._default_tag, "obj": null};
                        var sod = new SelectorOptionDescriptor(params);
                        selected_key = sod.key;
                    }
                }
                this.select(selected_key);

                console.log("SELECTED KEY: ",selected_key);
                
                // Set DIF initial InfoFrames
                if (selected_key != null){
                    var selected_obj = this.get_entity_by_key(selected_key);
                    if (selected_obj != null){
                        console.log("SELECTED OBJECT2: ",selected_obj);
                        this.update_bothinfos(this._tag, selected_obj);
                        var ff = (
                            function(){
                                // var selected_key = this.get_currently_selected();
                                // var selected_obj = this.get_entity_by_key(selected_key);
                                var selected_obj = this.get_currently_selected_obj();
                                console.log("SELECTED OBJ3: ", selected_obj);
                                if ((selected_obj === null || selected_obj === undefined) && this._with_any_option){
                                    sod = SelectorOptionDescriptor.get_generic("");
                                    this.update_rightinfo(SelectorOptionDescriptor.__ANY_KEY(), this._any_text);
                                    console.log("updating ANY");
                                }
                                else if (selected_obj != undefined){
                                    console.log("not undefined!");
                                    this.update_rightinfo(this._tag, selected_obj);
                                }
                            }.bind(this)
                        );
                        this.assign_selectOnChange(ff, reset);
                    }
                }
            }.bind(this)), 500
        );
    }

    get_currently_selected_obj(){
        var selected_key = this.get_currently_selected();
        console.log("SELECTED KEY:", selected_key)
        var selected_obj = this.get_entity_by_key(selected_key);
        return selected_obj;
    }

    reset(selected_object, candidates){
        console.log("RESET", this.my_type())
        console.log("selected_object =", selected_object)
        this._selected_obj = selected_object;
        console.log("this._selected_obj =", this._selected_obj)
        this._candidates = candidates;
        this.remove_all_options();
        this.fill_and_config(true);
    }


    get_entity_list(){
        console.log("CANDIDATES:",this._candidates);
        if (this._candidates != null)
            return this._candidates;
        return this._cache.c[this._tag];
    }

    get_entity_by_key(key){
        var ent_list = this.get_entity_list();
        console.log("ENT_LIST:",ent_list);
        console.log("tag",this._tag);
        console.log("key",key);

        for( var i=0; i< ent_list.length; i++ ){
            var entity = ent_list[i];
            var params = {"tag": this._tag, "obj": entity};
            var sod = new SelectorOptionDescriptor(params);
            console.log("SOD",sod);
            if (sod.is_key(key)){
                return entity;
            }
        } 
        var sod_any = SelectorOptionDescriptor.get_generic("");
        if (sod_any.is_key(key)){
            console.log("IT's ANY!!!");
            return null;
        }
        console.log("UNKNOWN item associated to key");
        return undefined;
    }

    generate_options(){
        var opts = []
        var ent_list = this.get_entity_list()
        for( var i=0; i< ent_list.length; i++ ){
            console.log("generate_options, ent list: ",ent_list[i]);
            var entity = ent_list[i];
            var params = {"tag": this._tag, "obj": entity};
            var sod = new SelectorOptionDescriptor(params);
            opts.push(sod);
        }
        if (this._with_any_option){
            //var params = {"txt": "ANY", "key": SelectorOptionDescriptor.__ANY_KEY()};
            var sod = SelectorOptionDescriptor.get_generic(this._any_text);
            opts.push(sod);
            console.log("Added ANY option", sod)
        }

        return opts;
    }

    conditional_format(){
        console.log("conditional_format");
        
        var obj = this.get_currently_selected_obj();
        console.log(obj)
        var color = "info";
        if (obj !== null && obj !== undefined){
            if ("state" in obj){
                if (obj["state"] === "disconnected"){
                    color = "danger";
                }
            }
        }

        if (this.has_been_modified()){
            this.right().update_status(this.right().get_title_text()+" (MODIFIED)", color);
        }
        else{
            this.right().update_status(this.right().get_title_text()+" (same as "+this.left().get_title_text()+")", color);
        }

        if (this.is_ANY()){
            console.warn("CURRENT value is ANY!!!");
        }
    }

    has_been_modified(){
        var references = this._dif.get_references();
        var left = references.left;
        var right = references.right;

        // console.log("LEFT ref:", left, "RIGHT ref", right);

        if ((left != null) && (right != null) && 
            (left.is_valid() && right.is_valid())){
            var params = {"tag": this._tag, "obj": left.obj};
            var sod_left = new SelectorOptionDescriptor(params);
            var params = {"tag": this._tag, "obj": right.obj};
            var sod_right = new SelectorOptionDescriptor(params);
            if (sod_left.key !== sod_right.key){
                return true;
            }
        }
        return false;
    }

    is_ANY(){
        return this._dif.get_references().right.is_generic();
    }

    my_type(){
        return this._type;
    }
}

class Basic_PNC extends Entity_PNC{
    constructor(params){

        params.params = {};

        var css_sel = {
            "max-width" : "600px",
            "width" : "100%",
            "height" : "35px",
        };
        
        params.params.sel = css_sel;

        var left = {
            "css": {},
            "title": "Original",
            "color": "info"
        }

        var right = {
            "css": {},
            "title": "Selected",
            "color": "info"
        }

        params.params.dif = {
            "left": left,
            "right": right
        };

        if (!("mytype" in params)){
            params.mytype = "Basic_PNC";
        }

        super(params);
    }
}

class WTP_PNC extends Basic_PNC{

    constructor(params){
        params.tag = "wtps";
        params.black_list=['datapath','supports','last_seen','connection','period'];
        params.mytype = "WTP_PNC";

        super(params);

        console.log("PARAMS",params);
    }
}

class LVAPBlock_PNC extends Basic_PNC{

    constructor(params){
        params.tag = "blocks";
        
        if (!("candidates" in params)){
            console.error("candidates not provided in params")
        }

        params.black_list=['ht_supports','ncqm','supports','tx_policies','ucqm', 'wifi_stats'];

        // params.params = {};

        params.mytype = "LVAPBlock_PNC";

        params["with_any_option"] = "ANY block";
        super(params);

        console.log("PARAMS",params);
    }
}

class VBS_PNC extends Basic_PNC{

    constructor(params){
        params.tag = "vbses";
        params.black_list=['datapath','supports','last_seen','connection','period','cells'];
        params.mytype = "VBS_PNC";
        
        super(params);

        console.log("PARAMS",params);
    }
}

class UECell_PNC extends Basic_PNC{

    constructor(params){
        params.tag = "cells";
        
        if (!("candidates" in params)){
            console.error("candidates not provided in params")
        }

        params.mytype = "UECell_PNC";

        params["with_any_option"] = "ANY cell";
        super(params);

        console.log("PARAMS",params);
    }
}

class Slice_PNC extends Basic_PNC{

    constructor(params){
        params.tag = "slices";
        
        super(params);

        console.log("PARAMS",params);
    }
}

class UE_HO_UP_Panel{
    constructor(ue){
        console.log ("SELECTED UE:", ue);
        this.hb = __HB;
        this.desc = __DESC;
        this.qe = __QE;
        this.cache = __CACHE;
        var selected_vbs = ue["vbs"];
        console.log ("SELECTED VBS:", selected_vbs);
        var cells_array = selected_vbs["cells"];
        var cells = [];
        for (var i in cells_array){
            cells.push(cells_array[i]);
        }
        console.log ("CANDIDATES:", cells);
        var selected_cell = null;
        if ("cell" in ue){
            selected_cell = ue["cell"];
        }
        console.log ("SELECTED CELL:", selected_cell);

        var params_vbs = {
            "hb": __HB,
            "desc": __DESC,
            "cache": __CACHE,
            "pnc_id": "ue_oh_vbs_pnc",
            "label": "VBSes:",
            "selected_obj": selected_vbs,
            "tag": null
        }

        if( __ROLE !== "admin"){
            var tenant = null;
            var tenant_name = $( "#navbar_tenantname" ).text();
            for( var i=0; i<this.cache.c[this.qe.targets.TENANT].length; i++ ){
                var tnt = this.cache.c[this.qe.targets.TENANT][i];
                console.log("candidate tenant name", tnt["tenant_name"]);
                if( tnt["tenant_name"] === tenant_name ){
                    tenant = tnt;
                    console.log("FOUND candidate tenant", tenant)
                    break;
                }
            }
            if (tenant === null){
                params_vbs.candidates = [];
            }
            else{
                var vbses = tenant["vbses"];
                params_vbs.candidates = [];
                for (var i in vbses){
                    params_vbs.candidates.push(vbses[i]);
                }
            }
        }

        this._vbs_pnc= new VBS_PNC(params_vbs);
        
        
        var params_cell = {
            "hb": __HB,
            "desc": __DESC,
            "cache": __CACHE,
            "pnc_id": "ue_oh_cell_pnc",
            "label": "Cells:",
            "selected_obj": selected_cell,
            "candidates": cells,
            "tag": "cells"
        }

        console.log("PARAMS_CELL", params_cell);
        this._cell_pnc= new UECell_PNC(params_cell); 
    }

    generate(){
        var panel = this.hb.cePANEL();
        $( panel ).addClass("panel panel-info")
        $( panel ).css("margin", "25px 5px");

        var body = this.hb.cePANEL_B();
        $( panel ).append(body);

        $( body ).append(this._vbs_pnc.generate());
        $( body ).append(this._cell_pnc.generate());

        // console.log("THIS1", this);

        setTimeout(
            (function(){
                var ff = (
                    function(){
                        console.log("**********************")
                        console.log("UE_HO_UP_Panel update");
                        var obj = this._vbs_pnc.get_currently_selected_obj();
                        console.log("SELECTED_VBS", obj)
                        var candidates = [];
                        if (obj != null){
                            if ("cells" in obj){
                                var cells_array = obj["cells"];
                                var candidates = [];
                                for (var i in cells_array){
                                    candidates.push(cells_array[i]);
                                }
                            }
                        }
                        this._cell_pnc.reset(null,candidates);
                    }.bind(this)
                );
                this._vbs_pnc.assign_selectOnChange(ff,false);
            }.bind(this)), 1000);

        return panel;
    }
}


class LVAP_HO_UP_Panel{
    constructor(lvap){
        this.hb = __HB;
        this.desc = __DESC;
        this.cache = __CACHE;
        this.qe = __QE;
        var selected_wtp = lvap["wtp"];
        var blocks = selected_wtp["supports"];
        console.log ("SELECTED WTP:", selected_wtp);
        var selected_block = null
        if ("blocks" in lvap){
            if (lvap.blocks.length > 0){
                selected_block = lvap["blocks"][0];
            }
        }

        var params_wtp = {
            "hb": __HB,
            "desc": __DESC,
            "cache": __CACHE,
            "pnc_id": "lvap_oh_wtp_pnc",
            "label": "WTPs:",
            "selected_obj": selected_wtp,
            "tag": null
        }

        if( __ROLE !== "admin"){
            var tenant = null;
            var tenant_name = $( "#navbar_tenantname" ).text();
            for( var i=0; i<this.cache.c[this.qe.targets.TENANT].length; i++ ){
                var tnt = this.cache.c[this.qe.targets.TENANT][i];
                console.log("candidate tenant name", tnt["tenant_name"]);
                if( tnt["tenant_name"] === tenant_name ){
                    tenant = tnt;
                    console.log("FOUND candidate tenant", tenant)
                    break;
                }
            }
            if (tenant === null){
                params_wtp.candidates = [];
            }
            else{
                var wtps = tenant["wtps"];
                params_wtp.candidates = [];
                for (var i in wtps){
                    params_wtp.candidates.push(wtps[i]);
                }
            }
        }

        this._wtp_pnc= new WTP_PNC(params_wtp);
        
        
        var params_block = {
            "hb": __HB,
            "desc": __DESC,
            "cache": __CACHE,
            "pnc_id": "lvap_oh_block_pnc",
            "label": "Blocks:",
            "selected_obj": selected_block,
            "candidates": blocks,
            "tag": "blocks"
        }

        this._block_pnc= new LVAPBlock_PNC(params_block); 
    }

    generate(){
        var panel = this.hb.cePANEL();
        $( panel ).addClass("panel panel-info")
        $( panel ).css("margin", "25px 5px");

        var body = this.hb.cePANEL_B();
        $( panel ).append(body);

        $( body ).append(this._wtp_pnc.generate());
        $( body ).append(this._block_pnc.generate());

        // console.log("THIS1", this);

        setTimeout(
            (function(){
                var ff = (
                    function(){
                        console.log("****** LVAP_HO_UP_Panel update START");
                        var obj = this._wtp_pnc.get_currently_selected_obj();
                        console.log("SELECTED_WTP", obj)
                        var candidates = [];
                        if (obj != null){
                            if ("supports" in obj){
                            candidates = obj["supports"];
                            }
                        }
                        this._block_pnc.reset(null,candidates);
                        console.log("****** LVAP_HO_UP_Panel update END");
                    }.bind(this)
                );
                this._wtp_pnc.assign_selectOnChange(ff,false)
            }.bind(this)), 1000);

        return panel;
    }
}


class UE_Slice_Panel{
    constructor(ue){
        console.log ("SELECTED UE:", ue);
        this.hb = __HB;
        this.desc = __DESC;
        this.cache = __CACHE;
        this.qe = __QE;

        var selected_slice = null;
        if ("slice" in ue){
            selected_slice = ue["slice"];
        }
        console.log("selected_slice:", selected_slice)

        var current_plmnid = ue["plmn_id"];

        var TenantList = [];
        if( __ROLE === "admin"){
            TenantList = this.cache.c[this.qe.targets.TENANT];
        }
        else{
            var tenant_name = $( "#navbar_tenantname" ).text();
            for( var i=0; i<this.cache.c[this.qe.targets.TENANT].length; i++ ){
                var tnt = this.cache.c[this.qe.targets.TENANT][i];
                if( tnt["tenant_name"] === tenant_name ){
                    TenantList.push( tnt );
                    break;
                }
            }
        }

        console.log("TenantListT",TenantList)

        var selected_tenantids = []
        for (var i = 0; i<TenantList.length; i++){
            var tnt = TenantList[i];
            if (tnt["plmn_id"] === current_plmnid){
                selected_tenantids.push(tnt["tenant_id"])
            }
        }


        console.log("TenantIds", selected_tenantids)


        var SliceList = this.cache.c[this.qe.targets.SLICE];

        console.log("FULL Slices", SliceList)

        var slices = []
        for (var i = 0; i<SliceList.length; i++){
            var slc = SliceList[i];
            for (var k = 0; k<selected_tenantids.length; k++){
                var tid = selected_tenantids[k];
                if (tid === slc["tenant_id"]){
                    slices.push(slc)
                    break;
                }
            }
        }

        console.log("Slices", slices)

        if (selected_slice != null){
            var found = false;
            for (var i = 0; i < slices.length; i++){
                if (slices[i]['dscp'] === selected_slice){
                    selected_slice = slices[i];
                    found = true;
                    console.log("selected slice FOUND!");
                    break;
                }
            }
            if (!found){
                selected_slice = null;
            }
        }
        if (selected_slice === null){
            selected_slice = slices[0];
            console.log("SEL SLICE", selected_slice);
        }

        
        var params_slice = {
            "hb": __HB,
            "desc": __DESC,
            "cache": __CACHE,
            "pnc_id": "ue_slice_pnc",
            "label": "Slices:",
            "selected_obj": selected_slice,
            "candidates": slices,
            "tag": "slices"
        }

        console.log("PARAMS_SLICE", params_slice);
        this._slice_pnc= new Slice_PNC(params_slice); 
    }

    generate(){
        var panel = this.hb.cePANEL();
        $( panel ).addClass("panel panel-info")
        $( panel ).css("margin", "25px 5px");

        var body = this.hb.cePANEL_B();
        $( panel ).append(body);

        $( body ).append(this._slice_pnc.generate());

        return panel;
    }
}