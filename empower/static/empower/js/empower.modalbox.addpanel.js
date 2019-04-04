class EmpAddModalBox extends EmpModalBox{

    getID_BODY_ADDPANEL(){
        var id = this.getID_BODY() + "_addpnl";
        return id;
    }

    getID_BODY_ADDPANEL_ATTR(a){
        var id = this.getID_BODY_ADDPANEL() + "_" + a;
        return id;
    }

    initResources(obj){
        var tag = this.hb.mapName2Tag(obj);
        var title = "Add new " + this.hb.mapName2Title(tag);

// ------------------- Body
        var body = this.hb.ce("DIV");
        body.id = this.getID_BODY_ADDPANEL();

        var div = this.d_AddBodyPanel(tag);
        $( body ).append(div);

// ------------------- Buttons
        var buttons = [];

        var ff_Add = this.hb.wrapFunction(this.f_Add.bind(this), [tag]);
        var btn_Save = {"text": "Save",
                         "color": "primary",
                         "f": ff_Add};
         buttons.push(btn_Save);

        var ff_Close = this.f_Close.bind(this);
        var btn_Close = {"text": "Close",
                         "color": "primary",
                         "f": ff_Close};
         buttons.push(btn_Close);

        return [title, body, buttons];
    }

// --------------------------------------------------------------------------------

    d_AddBodyPanel(tag){

        var div = this.hb.ce("DIV");
        $( div ).css("margin", "20px");
        $( div ).css("padding", "5px");
        $( div ).css("border", "1px solid #ccc");
        $( div ).css("background-color", "#f5f5f5");

        var selObj = {};
        var attrbts = this.desc.d[ tag ].attr;
        for( var a in attrbts ){
            selObj[a]=null;
            if( attrbts[a].add != "empty" ){
                var isInput = true;
                var id = this.getID_BODY_ADDPANEL_ATTR(a);
                var r = ff_draw(tag, a, id, isInput);
                $( div ).append(r);
                if( attrbts[a].add === "mandatory")
                    $( $(r)[0].children[0] ).css("fontWeight", 700)
            }
        }

        return div;
    }

// -----------------------------------------------------------------------------

    f_Add(args){
        var tag = args[0];
        var input = {};
        var attrbts = this.desc.d[ tag ].attr;
        var ctrl = true;

        for( var a in attrbts ){
            if( attrbts[a].add != "empty" ){
                var id = this.getID_BODY_ADDPANEL_ATTR(a);

                var clr = $( "#" + id ).css('backgroundColor');
                if( clr === "rgb(238, 98, 98)"){
                    ctrl = false;
                }
                if( attrbts[a].add === "mandatory" && clr === "rgb(255, 255, 255)"){
                    ctrl = false;
                }

                if( ctrl ){
                    var value = "";
                    switch(a){
                        case "bssid_type":
                            value = $( "#" + id ).is(':checked')? "shared" : "unique";
                        break;
                        case "role":
                            value = $( "#" + id ).is(':checked')? "user" : "admin"
                        break;
                        case "match":
                        case "dscp":
                        case "tenant_id":
                        case "owner":
                            value = $( "#" + id ).text();
                        break;
                        default:
                            value = $( "#" + id ).val();
                    }
                    input[a] = value;
            }
        }
        }

        if( ctrl ){
            var ff = function(){
                if( tag === this.qe.targets.TENANT )
                        this.qe.scheduleQuery("GET", [tag], null, null, this.cache.update.bind(this.cache));
                    else
                        this.qe.scheduleQuery("GET", [tag, this.qe.targets.TENANT], null, null, this.cache.update.bind(this.cache));
                }
            this.qe.scheduleQuery("POST", [tag], null, input, ff.bind(this));
                this.f_Close();
            }
        else{
            alert("Mandatory values are missing!");
        }
        }

    f_Close(){
        var id = this.getID();
        var m = this.hb.ge(id);
        $( m ).modal('hide');
    }

}