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
        var tag = this.hb.mapName(obj);
        var title = "Add new " + obj;

// ------------------- Body
        var body = this.hb.ce("DIV");
        body.id = this.getID_BODY();

        var div = this.d_AddBodyPanel(tag);
        $( body ).append(div);

// ------------------- Buttons
        var ff_Close = this.f_Close.bind(this);
        var buttons = [];

        var ff_Add = this.hb.wrapFunction(this.f_Add.bind(this), [tag]);
        var btn_Save = {"text": "Save",
                         "color": "primary",
                         "f": ff_Add};
         buttons.push(btn_Save);

        return [title, body, buttons, ff_Close];
    }

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
            if( attrbts[a].set ){
                var r = this.hb.ceROW();
                r.id = this.getID_BODY_ADDPANEL_ATTR(a);
                $( div ).append(r);
                $( r ).css("margin", "10px 0px")

                    var c1 = __HB.ceCOL("xs", 2);
                    $( r ).append(c1);
                    $( c1 ).text(a + ": ");
                    var type = attrbts[a].type;
                    var value = "";
                    var c2 = __HB.ceCOL("xs", 10);
                    $( r ).append(c2);
                        var cnt = ff_drawInputField(tag, a, value, this.getID_BODY_ADDPANEL_ATTR.bind(this));
                        $( c2 ).append(cnt);
            }
        }

        return div;
    }

    f_Add(args){
        var tag = args[0];
        var input = {};
        var attrbts = this.desc.d[ tag ].attr;
        var ctrl = true;
        for( var a in attrbts ){
            input[a]=null;
            if( attrbts[a].set ){
                var id = this.getID_BODY_ADDPANEL_ATTR(a)
                var cnt = this.hb.ge(id + "_IF");
                var value = $(cnt).val();
                if( value != "null") input[a] = value;
                var clr = $( cnt ).css('backgroundColor');
                if( clr === "rgb(238, 98, 98)"){
                    ctrl = false;
                }
                else if( clr === "rgba(0, 0, 0, 0)"){
                    ctrl = false;
                    if(tag === "tenants" && a === "plmn_id") ctrl = true;
                }
            }
        }
        if( ctrl == true ){
            var m = null;
            var f_YES = function(){
                var fff = function(){
                    if( tag === this.qe.targets.TENANT)
                        this.qe.scheduleQuery("GET", [tag], null, null, this.cache.update.bind(this.cache));
                    else
                        this.qe.scheduleQuery("GET", [tag, this.qe.targets.TENANT], null, null, this.cache.update.bind(this.cache));
                }
                this.qe.scheduleQuery("POST", [tag], null, input, fff.bind(this));
                $( m ).modal('hide');
                this.f_Close();
            }
            m = generateWarningModal( tag.toUpperCase() + ": add new element", f_YES.bind(this));
            $( m ).modal({backdrop: 'static', keyboard: false});
        }
    }

}