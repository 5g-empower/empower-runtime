class EmpSliceModalBox extends EmpModalBox{

    constructor(keys){
        super(keys);

        this.toUpdate = {};

        this.LTEdetails = {};
        this.WIFIdetails = {};
        this.selObj = {};

    }

    getID_BODY_SLICEPANEL(){
        var id = this.getID_BODY() + "_slcpnl";
        return id;
    }

    getID_BODY_SLICEPANEL_ATTR(a){
        var id = this.getID_BODY_SLICEPANEL() + "_" + a;
        return id;
    }

    initResources(obj, type){
        var tag = this.hb.mapName2Tag(obj);
        var title = "";
        var div = null;
        var f = null;

// ------------------- Body
        var body = this.hb.ce("DIV");
        body.id = this.getID_BODY_SLICEPANEL();

        var div = null;
        if( type === "ADD" ){
            title = "Add new " + this.hb.mapName2Title(tag);
            div = this.d_SliceBodyAddPanel();
            f = this.hb.wrapFunction(this.f_Add.bind(this), [tag]);
        }
        else if( type === "UPD" ){
            var dt = this.cache.DTlist[ tag ];
            var datatable = $("#"+ dt.getID()).DataTable();
            var key = "";
            if( datatable.row('.selected').data() ){
                var data = datatable.row('.selected').data();
                //console.log("DATA", data);
                //var tenantID = data[0].substring(11, data[0].length-14)
                var tenantID = $(data[0]).attr('key').trim();
                // var dscp = $( data[1] )[0]["attributes"]['key']['value'];
                var dscp = $(data[1]).attr('key').trim();
                //var dscp = data[1].substring(11, data[1].length-14)
                var found = null;
                for( var i=0; i<this.cache.c[tag].length; i++){
                    if( this.cache.c[tag][i]["tenant_id"] === tenantID && this.cache.c[tag][i]["dscp"] === dscp ){
                        found = this.cache.c[tag][i];
                        break;
                    }
                }
                if (found === null){
                    console.error("NOT FOUND", found);
                }
                this.selObj = found;
                title = "Update " + this.hb.mapName2Title(tag);

                this.WIFIdetails = JSON.parse(JSON.stringify(this.selObj["wifi"]["wtps"]));
                this.LTEdetails = JSON.parse(JSON.stringify(this.selObj["lte"]["vbses"]));
                div = this.d_SliceBodyUpdatePanel( this.selObj );
                f = this.hb.wrapFunction(this.f_Update.bind(this), [tag]);
            }
        }

        $( body ).append(div);

// ------------------- Buttons
        var buttons = [];

        if( type !== "ADD" ){
            var json = this.selObj; //this.hb.getKeyValue( tag , key);
            var ff_Download = this.hb.wrapFunction(this.f_Download.bind(this), ["SELECTED"+obj.toUpperCase(), json]);
            var btn_Download = {"text": "Download",
                            "color": "primary",
                            "f": ff_Download};
            buttons.push(btn_Download);
        }

        var btn_Save = {"text": "Save",
                         "color": "primary",
                         "f": f};
        buttons.push(btn_Save);

        var ff_Close = this.f_Close.bind(this);
        var btn_Close = {"text": "Close",
                         "color": "primary",
                         "f": ff_Close};
         buttons.push(btn_Close);

        return [title, body, buttons];
    }

// --------------------------------------------------------------------------------

    d_SliceBodyAddPanel(){
        var tag = this.qe.targets.SLICE;
        var div = this.hb.ce("DIV");

            var u = this.hb.ce("UL");
            $( div ).append(u);
            $( u ).addClass("nav nav-tabs");
                var tab1 = this.hb.ce("LI");
                $( u ).append(tab1);
                $( tab1 ).html("<a href=\"#sliceTab\" id=\"tab1\" data-toggle=\"tab\">Network Slice </a>");
                var tab2 = this.hb.ce("LI");
                $( u ).append(tab2);
                $( tab2 ).html("<a href=\"#lteTab\" id=\"tab2\" data-toggle=\"tab\">LTE </a>");
                var tab3 = this.hb.ce("LI");
                $( u ).append(tab3);
                $( tab3 ).html("<a href=\"#wifiTab\" id=\"tab3\" data-toggle=\"tab\">Wi-Fi </a>");

            var content = this.hb.ce("DIV")
            $( div ).append(content);
            $( content ).addClass("tab-content");
                var slice = this.hb.ce("DIV");
                $( content ).append(slice);
                $( slice ).addClass("panel panel-info")
                $( slice ).addClass("tab-pane fade");
                $( slice ).css("margin", "20px");
                $( slice ).css("padding", "5px");
                $( slice ).css("border", "1px solid #ccc");
                $( slice ).css("background-color", "#f5f5f5");
                slice.id = "sliceTab"
                    $( slice ).append(this.d_SliceBodyAddPanel_Info());
                var lte = this.hb.ce("DIV");
                $( content ).append(lte);
                $( lte ).addClass("panel panel-info")
                $( lte ).addClass("tab-pane fade");
                $( lte ).css("margin", "20px");
                $( lte ).css("padding", "5px");
                $( lte ).css("border", "1px solid #ccc");
                $( lte ).css("background-color", "#f5f5f5");
                lte.id = "lteTab"
                    $( lte ).append(this.d_SliceBodyPanel_LTE());
                var wifi = this.hb.ce("DIV");
                $( content ).append(wifi);
                $( wifi ).addClass("panel panel-info")
                $( wifi ).addClass("tab-pane fade");
                $( wifi ).css("margin", "20px");
                $( wifi ).css("padding", "5px");
                $( wifi ).css("border", "1px solid #ccc");
                $( wifi ).css("background-color", "#f5f5f5");
                wifi.id = "wifiTab"
                    $( wifi ).append(this.d_SliceBodyPanel_WIFI());

        var ff = function(){
            $('a[href="#sliceTab"]').click();
        }
        setTimeout(ff.bind(this), 1/8*this.delay)
        return div
    }

    d_SliceBodyUpdatePanel(selObj){
        var tag = this.qe.targets.SLICE;
        var div = this.hb.ce("DIV");

            var u = this.hb.ce("UL");
            $( div ).append(u);
            $( u ).addClass("nav nav-tabs");
                var tab1 = this.hb.ce("LI");
                $( u ).append(tab1);
                $( tab1 ).html("<a href=\"#sliceTab\" id=\"tab1\" data-toggle=\"tab\">Network Slice </a>");
                var tab2 = this.hb.ce("LI");
                $( u ).append(tab2);
                $( tab2 ).html("<a href=\"#lteTab\" id=\"tab2\" data-toggle=\"tab\">LTE </a>");
                var tab3 = this.hb.ce("LI");
                $( u ).append(tab3);
                $( tab3 ).html("<a href=\"#wifiTab\" id=\"tab3\" data-toggle=\"tab\">Wi-Fi </a>");
                var tab4 = this.hb.ce("LI");
                $( u ).append(tab4);
                $( tab4 ).html("<a href=\"#JSONTab\" id=\"tab4\" data-toggle=\"tab\">JSON </a>");

            var content = this.hb.ce("DIV")
            $( div ).append(content);
            $( content ).addClass("tab-content");
                var slice = this.hb.ce("DIV");
                $( content ).append(slice);
                $( slice ).addClass("panel panel-info")
                $( slice ).addClass("tab-pane fade");
                $( slice ).css("margin", "20px");
                $( slice ).css("padding", "5px");
                $( slice ).css("border", "1px solid #ccc");
                $( slice ).css("background-color", "#f5f5f5");
                slice.id = "sliceTab"
                    $( slice ).append(this.d_SliceBodyUpdPanel_Info(selObj));
                var lte = this.hb.ce("DIV");
                $( content ).append(lte);
                $( lte ).addClass("panel panel-info")
                $( lte ).addClass("tab-pane fade");
                $( lte ).css("margin", "20px");
                $( lte ).css("padding", "5px");
                $( lte ).css("border", "1px solid #ccc");
                $( lte ).css("background-color", "#f5f5f5");
                lte.id = "lteTab"
                    $( lte ).append(this.d_SliceBodyPanel_LTE(selObj));
                var wifi = this.hb.ce("DIV");
                $( content ).append(wifi);
                $( wifi ).addClass("panel panel-info")
                $( wifi ).addClass("tab-pane fade");
                $( wifi ).css("margin", "20px");
                $( wifi ).css("padding", "5px");
                $( wifi ).css("border", "1px solid #ccc");
                $( wifi ).css("background-color", "#f5f5f5");
                wifi.id = "wifiTab"
                    $( wifi ).append(this.d_SliceBodyPanel_WIFI(selObj));
                var jT = this.hb.ce("DIV");
                $( content ).append(jT);
                $( jT ).addClass("panel panel-info")
                $( jT ).addClass("tab-pane fade");
                $( jT ).css("margin", "20px");
                $( jT ).css("padding", "5px");
                jT.id = "JSONTab"
                    var pre = __HB.ce("PRE");
                    $( jT ).append(pre);
                        var txt = JSON.stringify(selObj, undefined, 4);
                        $( pre ).html( __HB.syntaxHighlight(txt));

        var ff = function(){
            $('a[href="#sliceTab"]').click();
        }
        setTimeout(ff.bind(this), 1/8*this.delay)
        return div
    }

// --------------------------------------------------------------------------------

    d_SliceBodyAddPanel_Info(){
        var div = this.hb.ce("DIV")
        // Mandatory attributes for creating a new Network slice are: DSCP and a Tenant ID
            var attrbts = {}
            attrbts["tenant_id"] = { "name": "Select Tenant: ", "d": this.d_SliceBodyPanel_SelectTenant.bind(this) };
            attrbts["dscp"] = { "name": "Select Tag: ", "d": this.d_SliceBodyPanel_SelectDSCP.bind(this) };
            for( var a in attrbts){
                var r = this.hb.ceROW();
                $( div ).append(r);
                $( r ).css("margin", "20px 0px")
                var c0 = this.hb.ceCOL("xs", 4);
                $( r ).append(c0);
                $( c0 ).addClass("text-right");
                $( c0 ).text( attrbts[a].name );
                $( c0 ).css("fontWeight", 700)
                var c1 = this.hb.ceCOL("xs", 8);
                $( r ).append(c1);
                    var selector = attrbts[a].d();
                    $( c1 ).append(selector);
                    var input = this.hb.ce("SPAN");
                    $( c1 ).append(input);
                    $( input ).addClass("hide");
                    input.id = this.getID_BODY_SLICEPANEL_ATTR(a);
            }
        return div;
    }

    d_SliceBodyUpdPanel_Info(values){
        var div = this.hb.ce("DIV")
            var attrbts = {}
            var tnt = this.hb.getKeyValue(this.qe.targets.TENANT, values["tenant_id"]);
            attrbts["tenant_id"] = { "name": "Select Tenant: ", "value": tnt["tenant_name"] };
            attrbts["dscp"] = { "name": "Select Tag: ", "value": values["dscp"] };
            for( var a in attrbts){
                var r = this.hb.ceROW();
                $( div ).append(r);
                $( r ).css("margin", "20px 0px")
                var c0 = this.hb.ceCOL("xs", 4);
                $( r ).append(c0);
                $( c0 ).addClass("text-right");
                $( c0 ).text( attrbts[a].name );
                $( c0 ).css("fontWeight", 700)
                var c1 = this.hb.ceCOL("xs", 8);
                $( r ).append(c1);
                $( c1 ).text( attrbts[a].value )
            }
        return div;
    }

    d_SliceBodyPanel_LTE(values=null){
        var tag = this.qe.targets.SLICE;
        var div = this.hb.ce("DIV");
            var attrbts = {}
            attrbts["sched_id"] = { "name": "Scheduler ID: ", "ph": "2147483649"};
            attrbts["rbgs"] = { "name": "RBGs: ", "ph": "6"};
            attrbts["window"] = { "name": "Window: ", "ph": "1"};
            attrbts["period"] = { "name": "Period: ", "ph": "1"};
            // attrbts["rntis"] = { "name": "RNTIs (inside brackets [ , ]) :", "ph": "[RNTI_1, RNTI_2, ...]"};
            if( values != null ){
                attrbts["sched_id"]["value"] = values["lte"]["static-properties"]["sched_id"];
                attrbts["rbgs"]["value"] = values["lte"]["static-properties"]["rbgs"];
                attrbts["window"]["value"] = values["lte"]["static-properties"]["window"];
                attrbts["period"]["value"] = values["lte"]["static-properties"]["period"];
                // attrbts["rntis"]["value"] = values["lte"]["runtime-properties"]["rntis"];
            }
            for( var a in attrbts){
                var r = this.hb.ceROW();
                $( div ).append(r);
                $( r ).css("margin", "20px 0px")
                var c0 = this.hb.ceCOL("xs", 4);
                $( r ).append(c0);
                $( c0 ).addClass("text-right");
                $( c0 ).text( attrbts[a].name );
                var c1 = this.hb.ceCOL("xs", 8);
                $( r ).append(c1);
                    var input = this.hb.ce("INPUT");
                    $( c1 ).append(input);
                    $( input ).attr("placeholder",attrbts[a].ph)
                    $( input ).attr("size", 30)
                    input.id = this.getID_BODY_SLICEPANEL_ATTR(a);
                    if( values != null ){
                        $( input ).val( attrbts[a].value )
                    }
            }

            var r0 = this.hb.ce("HR");
            $( div ).append(r0);
            $( r0 ).css("margin", "20px");
            $( r0 ).css("border", "1px solid #999");

            var panel = this.hb.cePANEL();
            $( div ).append(panel);
            $( panel ).addClass("panel panel-info");
                var ph = this.hb.cePANEL_H();
                $( panel ).append(ph);
                var pb = this.hb.cePANEL_B();
                $( panel ).append(pb);
                var pf = this.hb.cePANEL_F();
                $( panel ).append(pf);
                $( pf ).css("backgroundColor", "#FFFFFF");
                var selObj = null;

            if( this.cache.c["vbses"].length == 0 ){
                $( ph ).text( "No VBSes defined" )
                return div
            }

            var detailsLTE = this.hb.ce("div");
            $( div ).append(detailsLTE);
            this.d_SliceBodyPanel_ConfigLTE(detailsLTE);

                    var title = this.hb.ce("SPAN");
                    $( ph ).append(title);
                    $( title ).text("Define configuration for a specific VBS")
                    var body = this.hb.ce("DIV");
                    $( pb ).append(body);
                        var selector = this.hb.ce("SELECT");
                        $( body ).append(selector);
                        $( selector ).css("width","100%");
                        $( selector ).css("height","35px");
                            var VBSesList = this.cache.c[this.qe.targets.VBS];
                            for(var i=0; i<VBSesList.length; i++){
                                var opt = this.hb.ce("OPTION");
                                $( selector ).append(opt);
                                opt.id = VBSesList[i]["addr"]
                                $( opt ).text(VBSesList[i]["label"] + " - " + VBSesList[i]["addr"])
                            }
                        var input = this.hb.ce("DIV");
                        $( body ).append(input);
                        $( input ).css("margin", "20px 0px");
                        // New details
                        var LTEattrbts = {}
                        LTEattrbts["sched_id"] = { "name": "Scheduler ID: ", "ph": "2147483649"};
                        LTEattrbts["rbgs"] = { "name": "RBGs: ", "ph": "6"};
                        LTEattrbts["window"] = { "name": "Window: ", "ph": "1"};
                        LTEattrbts["period"] = { "name": "Period: ", "ph": "1"};
                        // LTEattrbts["rntis"] = { "name": "RNTIs (inside brackets [ , ]) :", "ph": "[RNTI_1, RNTI_2, ...]"};
                        var ff_change = function(){
                            var el = selector.options[selector.selectedIndex];
                            var id = el.id;
                            selObj = this.hb.getKeyValue(this.qe.targets.VBS, id);
                            $( input ).empty();
                            var row = this.hb.ceROW();
                            $( input ).append(row);
                                var col0 = this.hb.ceCOL("xs",1);
                                $( row ).append(col0);
                                    var s0 = this.hb.ce("SPAN");
                                    $( col0 ).append(s0);
                                    $( s0 ).text( selObj["label"] );
                                    $( s0 ).css("fontWeight", 700);
                                var col1 = this.hb.ceCOL("xs",11);
                                $( row ).append(col1);
                                    for( var a in LTEattrbts){
                                        var rr = this.hb.ceROW();
                                        $( col1 ).append(rr);
                                        $( rr ).css("margin", "10px 0px")
                                            var cc0 = this.hb.ceCOL("xs", 4);
                                            $( rr ).append(cc0);
                                            $( cc0 ).addClass("text-right");
                                            $( cc0 ).text( LTEattrbts[a].name );
                                            var cc1 = this.hb.ceCOL("xs", 8);
                                            $( rr ).append(cc1);
                                                var ii = this.hb.ce("INPUT");
                                                $( cc1 ).append(ii);
                                                $( ii ).attr("placeholder",LTEattrbts[a].ph)
                                                $( ii ).attr("size", 50)
                                                ii.id = this.getID_BODY_SLICEPANEL_ATTR(a) + "_" + id;
                                    }
                        }
                        $( selector ).change(ff_change.bind(this))
                        setTimeout( function(){ $( selector ).change() }, 1/8*this.delay )
                    var btn_ADD = this.hb.ce("BUTTON");
                    $( pf ).append(btn_ADD);
                    $( btn_ADD ).attr("type", "button");
                    $( btn_ADD ).attr("style", "margin: 0px 2px;");
                    $( btn_ADD ).attr("title", "Add");
                        var span_ADD = this.hb.ce("SPAN");
                        $( btn_ADD ).append(span_ADD);
                        $( span_ADD ).text("Add new configuration")
                    var ff_ADDclick = function(){
                        var id = selObj["addr"];
                        if( id in this.LTEdetails ){
                            alert("Configuration already defined.")
                        }
                        else{
                            this.LTEdetails[id] = {};
                            // this.LTEdetails[id]["runtime-properties"] = {};
                            this.LTEdetails[id]["static-properties"] = {};
                            var void_fields_counter = 0;
                            for( var a in LTEattrbts){
                                var tmp = this.hb.ge( this.getID_BODY_SLICEPANEL_ATTR(a) + "_" + id );
                                var txt = $( tmp ).val();
                                switch(a){
                                    case "sched_id":
                                        if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                                            txt = "2147483649"
                                        }
                                    case "rbgs":
                                        if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                                            txt = "6"
                                        }
                                    case "window":
                                        if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                                            txt = "1"
                                        }
                                    case "period":
                                        if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                                            txt = "1"
                                        }
                                        this.LTEdetails[id]["static-properties"][a] = txt;
                                        // if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                                        //     void_fields_counter =  void_fields_counter + 1;
                                        // }
                                        break;
                                    // case "rntis":
                                    //     this.LTEdetails[id]["runtime-properties"][a] = txt;
                                    //     break;
                                }
                            }
                            if ( void_fields_counter < 4){
                                this.d_SliceBodyPanel_ConfigLTE(detailsLTE);
                                this.toUpdate["LTE"] = true;
                            }
                            else{
                                alert("Set at least one field...")
                            }
                        }
                    }
                    $( btn_ADD ).click( ff_ADDclick.bind(this) );

        return div;
    }

    d_SliceBodyPanel_WIFI(values=null){
        var tag = this.qe.targets.SLICE;
        var div = this.hb.ce("DIV");
            var r0 = this.hb.ceROW();
            $( div ).append(r0);
            $( r0 ).css("margin", "20px 0px")
            var c00 = this.hb.ceCOL("xs", 4);
            $( r0 ).append(c00);
            $( c00 ).addClass("text-right");
            $( c00 ).text( "AMSDU aggregation: " );
            var c01 = this.hb.ceCOL("xs", 8);
            $( r0 ).append(c01);
                var swtch = __HB.ce("INPUT");
                $( c01 ).append(swtch);
                $( swtch ).addClass("switch");
                $( swtch ).attr("type", "checkbox");
                $( swtch ).attr("data-on-text", "True");
                $( swtch ).attr("data-off-text", "False");
                $( swtch ).attr("data-on-color", "info");
                $( swtch ).attr("data-off-color", "info");
                $( swtch ).bootstrapSwitch();
                var i0 = this.hb.ce("SPAN");
                $( c01 ).append(i0);
                $( i0 ).text("false");
                i0.id = this.getID_BODY_SLICEPANEL_ATTR("amsdu_aggregation");
                $( i0 ).addClass("hide");
                var ff_Switch = function(args){
                    var state = args[0].checked;
                    $( i0 ).text(state);
                }
                $( swtch ).on('switchChange.bootstrapSwitch', this.hb.wrapFunction( ff_Switch, [swtch] ));
                if( values ){
                    var state = values["wifi"]["static-properties"]["amsdu_aggregation"];
                    if( state ) $( swtch ).click();
                }
            var r1 = this.hb.ceROW();
            $( div ).append(r1);
            $( r1 ).css("margin", "20px 0px")
            var c10 = this.hb.ceCOL("xs", 4);
            $( r1 ).append(c10);
            $( c10 ).addClass("text-right");
            $( c10 ).text( "Quantum: " );
            var c11 = this.hb.ceCOL("xs", 8);
            $( r1 ).append(c11);
                var i1 = this.hb.ce("INPUT");
                $( c11 ).append(i1);
                $( i1 ).attr("placeholder", "12000")
                $( i1 ).attr("size", 50)
                i1.id = this.getID_BODY_SLICEPANEL_ATTR("quantum");
                if( values ){
                    var value = values["wifi"]["static-properties"]["quantum"];
                    $( i1 ).val(value);
                }

            var r2 = this.hb.ceROW();
            $( div ).append(r2);
            $( r2 ).css("margin", "20px 0px")
            var c20 = this.hb.ceCOL("xs", 4);
            $( r2 ).append(c20);
            $( c20 ).addClass("text-right");
            $( c20 ).text( "Scheduler: " );
            var c21 = this.hb.ceCOL("xs", 8);
            $( r2 ).append(c21);
                var i2 = this.hb.ce("INPUT");
                $( c21 ).append(i2);
                $( i2 ).attr("placeholder", "0")
                $( i2 ).attr("size", 50)
                i2.id = this.getID_BODY_SLICEPANEL_ATTR("scheduler");
                if( values ){
                    var value = values["wifi"]["static-properties"]["scheduler"];
                    $( i2 ).val(value);
                }

            var r0 = this.hb.ce("HR");
            $( div ).append(r0);
            $( r0 ).css("margin", "20px");
            $( r0 ).css("border", "1px solid #999");

            var panel = this.hb.cePANEL();
            $( div ).append(panel);
            $( panel ).addClass("panel panel-info");
                var ph = this.hb.cePANEL_H();
                $( panel ).append(ph);
                var pb = this.hb.cePANEL_B();
                $( panel ).append(pb);
                var pf = this.hb.cePANEL_F();
                $( panel ).append(pf);
                $( pf ).css("backgroundColor", "#FFFFFF");
                var selObj = null;

            if( this.cache.c["wtps"].length == 0 ){
                $( ph ).text( "No WTPs defined" )
                return div
            }

            var WTPdetails = this.hb.ce("div");
            $( div ).append(WTPdetails);
            this.d_SliceBodyPanel_ConfigWIFI(WTPdetails);

            if( this.cache.c[this.qe.targets.WTP].length == 0){
                var title = this.hb.ce("SPAN");
                $( ph ).append(title);
                $( title ).text("No connected WTP")
            }
            else{
                var title = this.hb.ce("SPAN");
                $( ph ).append(title);
                $( title ).text("Define configuration for a specific WTP")
                var body = this.hb.ce("DIV");
                $( pb ).append(body);
                    var selector = this.hb.ce("SELECT");
                    $( body ).append(selector);
                    $( selector ).css("width","100%");
                    $( selector ).css("height","35px");
                        var WTPsList = this.cache.c[this.qe.targets.WTP];
                        for(var i=0; i<WTPsList.length; i++){
                            var opt = this.hb.ce("OPTION");
                            $( selector ).append(opt);
                            opt.id = WTPsList[i]["addr"]
                            $( opt ).text(WTPsList[i]["label"] + " - " + WTPsList[i]["addr"])
                        }
                    var input = this.hb.ce("DIV");
                    $( body ).append(input);
                    $( input ).css("margin", "20px 0px");
                    var ff_change = function(){
                        var el = selector.options[selector.selectedIndex];
                        var id = el.id;
                        selObj = this.hb.getKeyValue(this.qe.targets.WTP, id);
                        $( input ).empty();
                        var row = this.hb.ceROW();
                        $( input ).append(row);
                            var col0 = this.hb.ceCOL("xs",1);
                            $( row ).append(col0);
                                var s0 = this.hb.ce("SPAN");
                                $( col0 ).append(s0);
                                $( s0 ).text( selObj["addr"] );
                                $( s0 ).css("fontWeight", 700);
                            var col1 = this.hb.ceCOL("xs",11);
                            $( row ).append(col1);
                                // New details
                                var r0 = this.hb.ceROW();
                                $( col1 ).append(r0);
                                $( r0 ).css("margin", "20px 0px")
                                var c00 = this.hb.ceCOL("xs", 4);
                                $( r0 ).append(c00);
                                $( c00 ).addClass("text-right");
                                $( c00 ).text( "AMSDU aggregation: " );
                                var c01 = this.hb.ceCOL("xs", 8);
                                $( r0 ).append(c01);
                                    var swtch = __HB.ce("INPUT");
                                    $( c01 ).append(swtch);
                                    $( swtch ).addClass("switch");
                                    $( swtch ).attr("type", "checkbox");
                                    $( swtch ).attr("data-on-text", "True");
                                    $( swtch ).attr("data-off-text", "False");
                                    $( swtch ).attr("data-on-color", "info");
                                    $( swtch ).attr("data-off-color", "info");
                                    $( swtch ).bootstrapSwitch();
                                    var i0 = this.hb.ce("SPAN");
                                    $( c01 ).append(i0);
                                    $( i0 ).text("false");
                                    i0.id = this.getID_BODY_SLICEPANEL_ATTR("amsdu_aggregation") + "_" + id;
                                    $( i0 ).addClass("hide")
                                    var ff_Switch = function(args){
                                        var state = args[0].checked;
                                        $( i0 ).text(state);
                                    }
                                    $( swtch ).on('switchChange.bootstrapSwitch', this.hb.wrapFunction( ff_Switch, [swtch] ));
                                var r1 = this.hb.ceROW();
                                $( col1 ).append(r1);
                                $( r1 ).css("margin", "20px 0px")
                                var c10 = this.hb.ceCOL("xs", 4);
                                $( r1 ).append(c10);
                                $( c10 ).addClass("text-right");
                                $( c10 ).text( "Quantum: " );
                                var c11 = this.hb.ceCOL("xs", 8);
                                $( r1 ).append(c11);
                                    var i1 = this.hb.ce("INPUT");
                                    $( c11 ).append(i1);
                                    $( i1 ).attr("placeholder", "12000")
                                    $( i1 ).attr("size", 50)
                                    i1.id = this.getID_BODY_SLICEPANEL_ATTR("quantum") + "_" + id;

                                var r2 = this.hb.ceROW();
                                ( col1 ).append(r2);
                                $( r2 ).css("margin", "20px 0px")
                                var c20 = this.hb.ceCOL("xs", 4);
                                $( r2 ).append(c20);
                                $( c20 ).addClass("text-right");
                                $( c20 ).text( "Scheduler: " );
                                var c21 = this.hb.ceCOL("xs", 8);
                                $( r2 ).append(c21);
                                    var i2 = this.hb.ce("INPUT");
                                    $( c21 ).append(i2);
                                    $( i2 ).attr("placeholder", "0")
                                    $( i2 ).attr("size", 50)
                                    i2.id = this.getID_BODY_SLICEPANEL_ATTR("scheduler") + "_" + id;
                        }
                        $( selector ).change(ff_change.bind(this))
                        setTimeout( function(){ $( selector ).change() }, 1/8*this.delay )
                        var btn_ADD = this.hb.ce("BUTTON");
                        $( pf ).append(btn_ADD);
                        $( btn_ADD ).attr("type", "button");
                        $( btn_ADD ).attr("style", "margin: 0px 2px;");
                        $( btn_ADD ).attr("title", "Add");
                            var span_ADD = this.hb.ce("SPAN");
                            $( btn_ADD ).append(span_ADD);
                            $( span_ADD ).text("Add new configuration")
                        var ff_ADDclick = function(){
                            var id = selObj["addr"];
                            if( id in this.WIFIdetails ){
                                alert("Configuration already defined.")
                            }
                            else{
                                this.WIFIdetails[id] = {}
                                this.WIFIdetails[id]["static-properties"] = {};
                                var a = "amsdu_aggregation"
                                var tmp = this.hb.ge( this.getID_BODY_SLICEPANEL_ATTR(a) + "_" + id );
                                var txt = $( tmp ).text();
                                if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                                    txt = "false"
                                }
                                this.WIFIdetails[id]["static-properties"][a] = txt;
                                a = "quantum"
                                tmp = this.hb.ge( this.getID_BODY_SLICEPANEL_ATTR(a) + "_" + id );
                                txt = $( tmp ).val();
                                if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                                    txt = "12000"
                                }
                                this.WIFIdetails[id]["static-properties"][a] = txt;
                                a = "scheduler"
                                tmp = this.hb.ge( this.getID_BODY_SLICEPANEL_ATTR(a) + "_" + id );
                                txt = $( tmp ).val();
                                if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                                    txt = "0"
                                }
                                this.WIFIdetails[id]["static-properties"][a] = txt;

                                this.toUpdate["WiFi"] = true;
                                this.d_SliceBodyPanel_ConfigWIFI(WTPdetails);
                            }
                        }
                        $( btn_ADD ).click( ff_ADDclick.bind(this) );
            }
        return div;
    }

    d_SliceBodyPanel_SelectTenant(){
        var tag = this.qe.targets.SLICE;
        var a = "tenant_id";
        var div = this.hb.ce("DIV");
            var selector = this.hb.ce("SELECT");
            $( div ).append(selector);
            $( selector ).css("width","100%");
            $( selector ).css("height","35px");
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
                for(var i=0; i<TenantList.length; i++){
                    var opt = this.hb.ce("OPTION");
                    $( selector ).append(opt);
                    opt.id = TenantList[i]["tenant_id"]
                    $( opt ).text(TenantList[i]["tenant_name"])
                }
            var ff_change = function(){
                var el = selector.options[selector.selectedIndex];
                var input = this.hb.ge( this.getID_BODY_SLICEPANEL_ATTR(a) );
                $( input ).text(el.id)
            }
            $( selector ).change(ff_change.bind(this))
            setTimeout( function(){ $( selector ).change() }, 1/8*this.delay )
        return div;
    }

    d_SliceBodyPanel_SelectDSCP(){
        var tag = this.qe.targets.SLICE;
        var a = "dscp";
        var div = this.hb.ce("DIV");
            var selector = this.hb.ce("SELECT");
            $( div ).append(selector);
            $( selector ).css("width","100%");
            $( selector ).css("height","35px");
                // DSCP are manually controlled
                var DSCPList = ["0x00", "0x01", "0x02", "0x03", "0x04",
                "0x08", "0x0A", "0x0C", "0x0E",
                                "0x10", "0x12", "0x14", "0x16", "0x18",
                                "0x1A", "0x1C", "0x1E", "0x20", "0x22",
                                "0x24", "0x26", "0x28", "0x2C", "0x2E", "0x30", "0x38"];
                for(var i=0; i<DSCPList.length; i++){
                    var opt = this.hb.ce("OPTION");
                    $( selector ).append(opt);
                    $( opt ).text(DSCPList[i])
                }
            var ff_change = function(){
                var el = selector.options[selector.selectedIndex];
                var input = this.hb.ge( this.getID_BODY_SLICEPANEL_ATTR(a) );
                $( input ).text( $(el).text() )
            }
            $( selector ).change(ff_change.bind(this))
            setTimeout( function(){ $( selector ).change() }, 1/8*this.delay )
        return div;
    }

    d_SliceBodyPanel_ConfigLTE(cnt){
        $( cnt ).empty();
        for( var lte in this.LTEdetails ){
            var selObj = this.hb.getKeyValue(this.qe.targets.VBS, lte);
            var d = this.hb.cePANEL();
            $( cnt ).append(d);
            $( d ).addClass("panel panel-info");
            $( d ).css("margin", "10px 0px");
                var title = this.hb.ceROW();
                $( d ).append(title);
                $( title ).css("margin", "10px")
                $( title ).css("fontWeight", 700);
                    var span = this.hb.ce("DIV");
                    $( title ).append(span);
                    $( span ).text( selObj["label"] + " - " + selObj["addr"] )
                var attrbts = {}
                attrbts["sched_id"] = { "name": "Scheduler ID: ", "ph": "2147483649", "value": this.LTEdetails[lte]["static-properties"]["sched_id"]};
                attrbts["rbgs"] = { "name": "RBGs: ", "ph": "6", "value": this.LTEdetails[lte]["static-properties"]["rbgs"]};
                attrbts["window"] = { "name": "Window: ", "ph": "1", "value": this.LTEdetails[lte]["static-properties"]["window"]};
                attrbts["period"] = { "name": "Period: ", "ph": "1", "value": this.LTEdetails[lte]["static-properties"]["period"]};
                // attrbts["rntis"] = { "name": "RNTIs (inside brackets [ , ]) :", "ph": "[RNTI_1, RNTI_2, ...]", "value": this.LTEdetails[lte]["runtime-properties"]["rntis"]};
                for( var a in attrbts){
                    var rr = this.hb.ceROW();
                    $( d ).append(rr);
                    $( rr ).css("margin", "10px 0px")
                        var cc0 = this.hb.ceCOL("xs", 4);
                        $( rr ).append(cc0);
                        $( cc0 ).addClass("text-right");
                        $( cc0 ).text( attrbts[a].name );
                        var cc1 = this.hb.ceCOL("xs", 8);
                        $( rr ).append(cc1);
                        var txt = attrbts[a].value;
                        if( txt && Object.keys(txt).length )
                            $( cc1 ).text( txt );
                        else{
                            $( cc1 ).text("")
                        }
                }
                var ftr = this.hb.cePANEL_F();
                $( d ).append(ftr);
                $( ftr ).css("backgroundColor", "#FFFFFF");
                    var btn_REMOVE = this.hb.ce("BUTTON");
                    $( ftr ).append(btn_REMOVE);
                    $( btn_REMOVE ).attr("type", "button");
                    $( btn_REMOVE ).attr("style", "margin: 0px 2px;");
                    $( btn_REMOVE ).attr("title", "Remove");
                    btn_REMOVE.id = selObj["addr"]
                    btn_REMOVE.ref = this;
                        var span_REMOVE = this.hb.ce("SPAN");
                        $( btn_REMOVE ).append(span_REMOVE);
                        $( span_REMOVE ).text("Remove this configuration")
                    var ff_REMOVEclick = function(sup){
                        var id = this.id;
                        delete sup.LTEdetails[id];
                        sup.d_SliceBodyPanel_ConfigLTE(cnt);
                        // console.log("this", this)
                        this.ref.toUpdate["LTE"] = true;
                    }
                    $( btn_REMOVE ).click( this.hb.wrapFunction( ff_REMOVEclick.bind(btn_REMOVE), this ));
        }
    }


    d_SliceBodyPanel_ConfigWIFI(cnt){
        $( cnt ).empty();
        for( var wifi in this.WIFIdetails ){
            var d = this.hb.cePANEL();
            $( cnt ).append(d);
            $( d ).addClass("panel panel-info");
            $( d ).css("margin", "10px 0px");
                var title = this.hb.ceROW();
                $( d ).append(title);
                $( title ).css("margin", "10px")
                $( title ).css("fontWeight", 700);
                    var span = this.hb.ce("DIV");
                    $( title ).append(span);
                    $( span ).text( wifi )
                var attrbts = {}
                attrbts["amsdu_aggregation"] = { "name": "AMSDU aggregation: ", "ph": false, "value": this.WIFIdetails[wifi]["static-properties"]["amsdu_aggregation"]};
                attrbts["quantum"] = { "name": "Quantum: ", "ph": "12000", "value": this.WIFIdetails[wifi]["static-properties"]["quantum"]};
                attrbts["scheduler"] = { "name": "Scheduler: ", "ph": "0", "value": this.WIFIdetails[wifi]["static-properties"]["scheduler"]};
                for( var a in attrbts){
                    var rr = this.hb.ceROW();
                    $( d ).append(rr);
                    $( rr ).css("margin", "10px 0px")
                        var cc0 = this.hb.ceCOL("xs", 4);
                        $( rr ).append(cc0);
                        $( cc0 ).addClass("text-right");
                        $( cc0 ).text( attrbts[a].name );
                        var cc1 = this.hb.ceCOL("xs", 8);
                        $( rr ).append(cc1);
                        var txt = attrbts[a].value;
                        if( txt && Object.keys(txt).length )
                            $( cc1 ).text( txt );
                        else{
                            $( cc1 ).text(attrbts[a].ph);
                        }
                }
                var ftr = this.hb.cePANEL_F();
                $( d ).append(ftr);
                $( ftr ).css("backgroundColor", "#FFFFFF");
                    var btn_REMOVE = this.hb.ce("BUTTON");
                    $( ftr ).append(btn_REMOVE);
                    $( btn_REMOVE ).attr("type", "button");
                    $( btn_REMOVE ).attr("style", "margin: 0px 2px;");
                    $( btn_REMOVE ).attr("title", "Remove");
                    btn_REMOVE.id = wifi
                    btn_REMOVE.ref = this;
                        var span_REMOVE = this.hb.ce("SPAN");
                        $( btn_REMOVE ).append(span_REMOVE);
                        $( span_REMOVE ).text("Remove this configuration")
                    var ff_REMOVEclick = function(sup){
                        var id = this.id;
                        delete sup.WIFIdetails[id];
                        sup.d_SliceBodyPanel_ConfigWIFI(cnt);
                        this.ref.toUpdate["WiFi"] = true;
                    }
                    $( btn_REMOVE ).click( this.hb.wrapFunction( ff_REMOVEclick.bind(btn_REMOVE), this ));
        }
    }
// --------------------------------------------------------------------------------

    f_Add(){

        // console.log("ADD")

        var tag = this.qe.targets.SLICE;
        // var attrbts = ["tenant_id", "dscp", "sched_id", "rbgs", "rntis", "amsdu_aggregation", "quantum"];
        var attrbts = ["tenant_id", "dscp", "sched_id", "rbgs", "window", "period", "amsdu_aggregation", "quantum", "scheduler"];
        var input = {};
        input["lte"] = {};
        // input["lte"]["runtime-properties"] = {};
        input["lte"]["static-properties"] = {};
        input["lte"]["vbses"] = {};
        input["wifi"] = {};
        input["wifi"]["static-properties"] = {};
        input["wifi"]["wtps"] = {};
        for( var i=0; i<attrbts.length; i++){
            var a = attrbts[i];
            var tmp = this.hb.ge( this.getID_BODY_SLICEPANEL_ATTR(a) );
            var txt = null;
            switch(a){
                case "tenant_id":
                case "dscp":
                    input[a] = $( tmp ).text();
                    break;
                case "rbgs":
                    if (txt === null){
                        txt = $( tmp ).val()
                    }
                    if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                        txt = "6"
                    }
                case "sched_id":
                    if (txt === null){
                        txt = $( tmp ).val()
                    }
                    if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                        txt = "2147483649"
                    }
                case "window":
                    if (txt === null){
                        txt = $( tmp ).val()
                    }
                    if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                        txt = "1"
                    }
                case "period":
                    if (txt === null){
                        txt = $( tmp ).val()
                    }
                    if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                        txt = "1"
                    }
                    input["lte"]["static-properties"][a] = txt;
                    break;
                // case "rntis":
                //     input["lte"]["runtime-properties"][a] = $( tmp ).val();
                //     break;
                case "quantum":
                    if (txt === null){
                        txt = $( tmp ).val()
                    }
                    if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                        txt = "12000"
                    }
                case "scheduler":
                    if (txt === null){
                        txt = $( tmp ).val()
                    }
                    if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                        txt = "0"
                    }
                    input["wifi"]["static-properties"][a] = txt;
                    break;
                case "amsdu_aggregation":
                    if (txt === null){
                        txt = $( tmp ).text()
                    }
                    if ((txt === null) || (txt === undefined) || (String(txt).length === 0)){
                        txt = "false"
                    }
                    input["wifi"]["static-properties"][a] = txt;
                    break;
            }
        }
        for(var id in this.LTEdetails){
            input["lte"]["vbses"][id] = {};
            input["lte"]["vbses"][id]["static-properties"] = {};
            // input["lte"]["vbses"][id]["runtime-properties"] = {};
            // var attrbts = ["sched_id", "rbgs", "rntis"];
            var attrbts = ["sched_id", "rbgs", "window", "period"];
            for( var i=0; i<attrbts.length; i++){
                var a = attrbts[i];
                switch(a){
                    case "rbgs":
                    case "sched_id":
                    case "window":
                    case "period":
                        input["lte"]["vbses"][id]["static-properties"][a] = this.LTEdetails[id]["static-properties"][a];
                        break;
                    // case "rntis":
                    //     input["lte"]["vbses"][id]["runtime-properties"][a] = this.LTEdetails[id]["runtime-properties"][a];
                    //     break;
                }
            }
        }
        for(var id in this.WIFIdetails){
            input["wifi"]["wtps"][id] = {};
            input["wifi"]["wtps"][id]["static-properties"] = {};
            var attrbts = ["amsdu_aggregation", "quantum", "scheduler"];
            for( var i=0; i<attrbts.length; i++){
                var a = attrbts[i];
                switch(a){
                    case "quantum":
                    case "scheduler":
                        input["wifi"]["wtps"][id]["static-properties"][a] = this.WIFIdetails[id]["static-properties"][a];
                        break;
                    case "amsdu_aggregation":
                        input["wifi"]["wtps"][id]["static-properties"][a] = this.WIFIdetails[id]["static-properties"][a];
                        break;
                }
            }
        }
//        console.log(input)
        var ff = function(){
            if( tag === this.qe.targets.TENANT )
                this.qe.scheduleQuery("GET", [tag], null, null, this.cache.update.bind(this.cache));
            else
                this.qe.scheduleQuery("GET", [tag, this.qe.targets.TENANT], null, null, this.cache.update.bind(this.cache));
        }
        this.qe.scheduleQuery("POST", [tag], null, input, ff.bind(this));
        
        // console.log("ADD input", input);

        var id = this.getID();
        var m = this.hb.ge(id);
        $( m ).modal('hide');
    }

    f_Update(){

        // console.log("UPDATE")
        var tag = this.qe.targets.SLICE;
        // var attrbts = ["sched_id", "rbgs", "rntis", "amsdu_aggregation", "quantum"];
        var attrbts = ["sched_id", "rbgs", "window", "period", "amsdu_aggregation", "quantum", "scheduler"];
        var input = jQuery.extend(true, {}, this.selObj) ;
        input["lte"] = {};
        // input["lte"]["runtime-properties"] = {};
        input["lte"]["static-properties"] = {};
        input["lte"]["vbses"] = {};
        input["wifi"] = {};
        input["wifi"]["static-properties"] = {};
        input["wifi"]["wtps"] = {};
        for( var i=0; i<attrbts.length; i++){
            var a = attrbts[i];
            var tmp = this.hb.ge( this.getID_BODY_SLICEPANEL_ATTR(a) );
            switch(a){
                case "rbgs":
                case "sched_id":
                case "window":
                case "period":
                    input["lte"]["static-properties"][a] = $( tmp ).val();
                    break;
                // case "rntis":
                //     input["lte"]["runtime-properties"][a] = $( tmp ).val();
                //     break;
                case "quantum":
                case "scheduler":
                    input["wifi"]["static-properties"][a] = $( tmp ).val();
                    break;
                case "amsdu_aggregation":
                    input["wifi"]["static-properties"][a] = $( tmp ).text();
                    break;
            }
        }
        for(var id in this.LTEdetails){
            // console.log("LTEdetails, id=",id);
            input["lte"]["vbses"][id] = {};
            input["lte"]["vbses"][id]["static-properties"] = {};
            // input["lte"]["vbses"][id]["runtime-properties"] = {};
            // var attrbts = ["sched_id", "rbgs", "rntis"];
            var attrbts = ["sched_id", "rbgs", "window", "period"];
            for( var i=0; i<attrbts.length; i++){
                var a = attrbts[i];
                switch(a){
                    case "rbgs":
                    case "sched_id":
                    case "window":
                    case "period":
                        input["lte"]["vbses"][id]["static-properties"][a] = this.LTEdetails[id]["static-properties"][a];
                        break;
                    // case "rntis":
                    //     input["lte"]["vbses"][id]["runtime-properties"][a] = this.LTEdetails[id]["runtime-properties"][a];
                    //     break;
                }
            }
        }
        for(var id in this.WIFIdetails){
            input["wifi"]["wtps"][id] = {};
            input["wifi"]["wtps"][id]["static-properties"] = {};
            var attrbts = ["amsdu_aggregation", "quantum", "scheduler"];
            for( var i=0; i<attrbts.length; i++){
                var a = attrbts[i];
                switch(a){
                    case "quantum":
                    case "scheduler":
                        input["wifi"]["wtps"][id]["static-properties"][a] = this.WIFIdetails[id]["static-properties"][a];
                        break;
                    case "amsdu_aggregation":
                        input["wifi"]["wtps"][id]["static-properties"][a] = this.WIFIdetails[id]["static-properties"][a];
                        break;
                }
            }
        }
        // console.log(input)
        var ff = function(){
            if( tag === this.qe.targets.TENANT )
                this.qe.scheduleQuery("GET", [tag], null, null, this.cache.update.bind(this.cache));
            else
                this.qe.scheduleQuery("GET", [tag, this.qe.targets.TENANT], null, null, this.cache.update.bind(this.cache));
        }
        // console.log("UPDATE input", input);

        this.qe.scheduleQuery("PUT", [tag], null, input, ff.bind(this));
        
        var id = this.getID();
        var m = this.hb.ge(id);
        $( m ).modal('hide');
    }

    f_Close(){
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