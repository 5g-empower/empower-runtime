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

    initResources(obj, userDetails=false){
        var tag = this.hb.mapName2Tag(obj);
        var title = "Show and update selected " + this.hb.mapName2Title(tag);

// ------------------- Body
        var body = this.hb.ce("DIV");
        body.id = this.getID_BODY_UPDPANEL();

        var dt = this.cache.DTlist[ tag ];
        var datatable = $("#"+ dt.getID()).DataTable();
        var key = "";
        if( datatable.row('.selected').data() ){
            var key = this.hb.getDTKeyFields(datatable.row('.selected').data());
        }
        else{
            return [title, body, buttons, ff_Close];
        }
        this.selObj = this.hb.getKeyValue( tag , key)

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
         buttons.push(btn_Upd);

        var ff_Close = this.f_WarningClose.bind(this);
        var btn_Close = {"text": "Close",
                         "color": "primary",
                         "f": ff_Close};
         buttons.push(btn_Close);

        return [title, body, buttons, ff_Close];
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

            for( var i=0; i<info.length; i++ ){
                var a = info[i];
                var isEdit = this.desc.d[ tag ].attr[a].update;
                var id = this.getID_BODY_UPDPANEL_ATTR(a);
                var value = this.selObj[a];
                var r = ff_draw(tag, a, id, isEdit, value);
                var isToUpdate = function(){
                    var tab = arguments[0];
                    this.toUpdate[tab] = true;
                }
                if( a === "bssid_type" ||
                    a === "role" ){
                    $( c0 ).append(r)
                }
                else{
                    $( c1 ).append(r);
                    $( c1 ).click( this.hb.wrapFunction(isToUpdate.bind(this), ["Info"] ) );
            }
    }

        return panel;
    }

    d_UP_WTPPanel(tag){
        var panel = this.hb.cePANEL();
        $( panel ).addClass("panel panel-info")
        $( panel ).css("margin", "25px 5px");
//        $( panel ).css("padding", "25px 5px");
//            var ph = this.hb.cePANEL_H();
//            $( panel ).append(ph);
            var body = this.hb.cePANEL_B();
            $( panel ).append(body);
//            var pf = this.hb.cePANEL_F();
//            $( panel ).append(pf);

//            var span = this.hb.ce("SPAN");
//            var span = this.hb.ce("SPAN");
//            $( ph ).append(span);
//            $( span ).text("Perform handover");

            var wtp = this.selObj["wtp"];
    var div = this.hb.ce("DIV");
            $( body ).append(div);
            $( div ).css("margin", "25px 0px");
    var r0 = this.hb.ceROW();
    $( div ).append(r0);
                    var c00 = this.hb.ceCOL("xs", COL_0);
                    $( r0 ).append(c00);
                    $( c00 ).addClass("text-right")
                        var s00 = this.hb.ce("SPAN");
                        $( c00 ).append(s00);
                        $( s00 ).text("Current WTP : ")
                        $( s00 ).css("fontWeight", 700)
                    var c01 = this.hb.ceCOL("xs", COL_1);
                    $( r0 ).append(c01);
                        var s01 = this.hb.ce("SPAN");
                        $( c01 ).append(s01);
                        s01.id = this.getID_BODY_UPDPANEL_ATTR("wtp");
                        $( s01 ).text( wtp["label"] + " ( " + wtp["addr"] + " ) " );
                        var s02 = this.hb.ce("SPAN");
                        $( c01 ).append(s02);
                        s02.id = this.getID_BODY_UPDPANEL_ATTR("wtp") + "_block";
                        $( s02 ).addClass("hide");
                        $( s02 ).text( "" );

            // built selector
            var wtpSelector = this.hb.ce("DIV");
            $( body ).append(wtpSelector);
            $( wtpSelector ).css("margin", "25px 0px");
    var r1 = this.hb.ceROW();
                $( wtpSelector ).append(r1);
                    var c10 = this.hb.ceCOL("xs", COL_0);
        $( r1 ).append(c10);
                    $( c10 ).addClass("text-right")
                        var s10 = this.hb.ce("SPAN");
                        $( c10 ).append(s10);
                        $( s10 ).text("Connect to a new WTP : ")
                        $( s10 ).css("fontWeight", 700)
                    var c11 = this.hb.ceCOL("xs", COL_1-2);
        $( r1 ).append(c11);

                var selector = this.hb.ce("SELECT");
                $( c11 ).append(selector);
                selector.id = this.getID_SELECTOR()
                $( selector ).css("width","100%");
                $( selector ).css("height","35px");
                setTimeout(this.hb.wrapFunction( this.f_UpdateWTPSelector.bind(this),[] ), 1/8*this.delay);

                    var c12 = this.hb.ceCOL("xs", 2);
                    $( r1 ).append(c12);
                        var btn1 = this.hb.ce("BUTTON");
                        $( c12 ).append(btn1);
                        $( btn1 ).attr("type", "button");
                        $( btn1 ).attr("style", "margin: 0px 2px;");
                        $( btn1 ).attr("title", "check blocks");
                            var icon1 = this.hb.ceFAI("fa-share-square-o");
                            $( icon1 ).addClass("fa-2x");
                            $( btn1 ).append(icon1);

            var blockSelector = this.hb.ce("DIV");
            $( body ).append(blockSelector);
            $( blockSelector ).addClass("hide");
            $( blockSelector ).css("margin", "25px 0px");
                var r2 = this.hb.ceROW();
                $( blockSelector ).append(r2);
                    var c20 = this.hb.ceCOL("xs", COL_0);
                    $( r2 ).append(c20);
                    $( c20 ).addClass("text-right")
                        var s20 = this.hb.ce("SPAN");
                        $( c20 ).append(s20);
                        $( s20 ).text("Select a block : ")
                        $( s20 ).css("fontWeight", 700)
                    var c21 = this.hb.ceCOL("xs", COL_1-2);
                    $( r2 ).append(c21);

                var blockselector = this.hb.ce("SELECT");
                $( c21 ).append(blockselector);
                blockselector.id = this.getID_BLOCKSELECTOR()
                $( blockselector ).css("width","100%");
                $( blockselector ).css("height","35px");
                setTimeout(this.hb.wrapFunction( this.f_UpdateBlockSelector.bind(this),[this.selObj["wtp"]] ), 1/8*this.delay);

                    var c22 = this.hb.ceCOL("xs", 2);
                    $( r2 ).append(c22);
                        var btn2 = this.hb.ce("BUTTON");
                        $( c22 ).append(btn2);
                        $( btn2 ).attr("type", "button");
                        $( btn2 ).attr("style", "margin: 0px 2px;");
                        $( btn2 ).attr("title", "discard");
                            var icon2 = this.hb.ceFAI("fa-times");
                            $( icon2 ).addClass("fa-2x");
                            $( btn2 ).prepend(icon2);
                        var btn3 = this.hb.ce("BUTTON");
                        $( c22 ).append(btn3);
                        $( btn3 ).attr("type", "button");
                        $( btn3 ).attr("style", "margin: 0px 2px;");
                        $( btn3 ).attr("title", "select");
                            var icon3 = this.hb.ceFAI("fa-share-square-o");
                            $( icon3 ).addClass("fa-2x");
                            $( btn3 ).prepend(icon3);

                var goToSelectBlock = function(){
                    this.toUpdate["lvapWtp"] = true;
                    var selector = this.hb.ge( this.getID_SELECTOR() );
                    var el = selector.options[selector.selectedIndex];
                    var addr = el.id.substring(el.id.length-17, el.id.length);
                    var selectedWTP = this.hb.getKeyValue(this.qe.targets.WTP, addr);
                    var clr = $( el ).css("color");
                    if( selectedWTP["state"] != "online" ){
                        alert( addr + " device is offline!" );
    }
                    else{
                        $( btn1 ).addClass("hide");
                        $( blockSelector ).removeClass("hide");
                        this.f_UpdateBlockSelector([selectedWTP]);
        }
    }
                $( btn1 ).click( goToSelectBlock.bind(this) )

                var returnToSelectWTP = function(){
                    $( btn1 ).removeClass("hide");
                    $( blockSelector ).addClass("hide");
    }
                $( btn2 ).click( returnToSelectWTP.bind(this) )

                var changeCurrentWTP = function(){
                    $( btn1 ).removeClass("hide");
                    $( blockSelector ).addClass("hide");

                    var currentWTP = this.selObj["wtp"];
                    var selector = this.hb.ge( this.getID_SELECTOR() );
                    var el = selector.options[selector.selectedIndex];
                    var addr = el.id.substring(el.id.length-17, el.id.length);
                    var selectedWTP = this.hb.getKeyValue(this.qe.targets.WTP, addr);
                    var span = this.hb.ge( this.getID_BODY_UPDPANEL_ATTR("wtp") )
                    span.id = this.getID_BODY_UPDPANEL_ATTR("wtp");
                    $( span ).text( selectedWTP["label"] + " ( " + selectedWTP["addr"] + " ) " );
                    this.selObj["wtp"] = selectedWTP;

                    var blockselector = this.hb.ge( this.getID_BLOCKSELECTOR() );
                    var block = blockselector.options[blockselector.selectedIndex];
                    var blockaddr = "";
                    if( block.id.indexOf("ALL") == -1 ){
                        blockaddr = block.id.substring(block.id.length-17, block.id.length);
    }
                    var span = this.hb.ge( this.getID_BODY_UPDPANEL_ATTR("wtp") + "_block")
                    $( span ).text( blockaddr );

                    this.f_UpdateWTPSelector();
    }
                $( btn3 ).click( changeCurrentWTP.bind(this) )

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
        for( var i=0; i<allWTP.length; i++){
            if( allWTP[i]["addr"] != currentWTP["addr"] ){
                var opt = this.hb.ce("OPTION");
                $( selector ).append(opt);
                opt.id = this.getID_SELECTOR() + "_" + allWTP[i]["addr"];
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
            opt.id = this.getID_BLOCKSELECTOR() + "_ALL";
            var txt = "All blocks";
            $( opt ).text( txt );
        for( var i=0; i<allBlocks.length; i++){
            opt = this.hb.ce("OPTION");
            $( blockselector ).append(opt);
            opt.id = this.getID_BLOCKSELECTOR() + "_" + allBlocks[i]["hwaddr"];
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
                        var block = $( this.hb.ge( id + "_block" ) ).text();
//                        console.log( addr, block)
                        var wtp = this.hb.getKeyValue("wtps", addr);
                        var params = [input, wtp, block]
                    break;
                    case this.qe.targets.WTP:
                        var txt = $( this.hb.ge(id) ).text();
                        var currentList = txt.split(";");
                        var allList = [];
                        for( var el in this.cache.c[a] ){
                            allList.push( this.cache.c[a][el]["addr"] )
                }
                        var [toDelete, toAdd, other] = this.hb.checkDifferenceArray(allList, currentList)
//                        console.log(toDelete, toAdd, other)
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
                $( body ).empty();  console.log(this.selObj)
                var div = this.d_UpdatePanel(tag, this.selObj);
                $( body ).append(div);
        }
            setTimeout(ff.bind(this), 1/4*this.delay)
    }

        for(var tab in this.toUpdate ){
            switch( tab ){
                case "Info":
                    console.log(tag, input)
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
                case this.qe.targets.WTP:
                case this.qe.targets.CPP:
                case this.qe.targets.VBS:
//                    if( this.toUpdate[ tab ] ){
//                        this.toUpdate[ tab ] = false;
//                        if( tag === this.qe.targets.TENANT){
//                            for( var i=0; i<toDelete.length; i++){
//                                var device = this.hb.getKeyValue(tab, toDelete[i])
//                                this.qe.scheduleQuery("DELETE", [tab], this.selObj.tenant_id, device, fff.bind(this));
//                            }
//                        }
//                    }
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