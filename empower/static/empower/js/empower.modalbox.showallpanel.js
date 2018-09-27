class EmpShowAllModalBox extends EmpModalBox{

    getID_BODY_SHOWALLPANEL(key){
        var id = this.getID_BODY() + "_shwallpnl_" + key;
        return id;
    }

    getID_BODY_SHOWALLPANEL_ATTR(a){
        var id = this.getID_BODY_SHOWALLPANEL() + "_" + a;
        return id;
    }

    initResources(obj){
        var tag = this.hb.mapName(obj);
        var title = "Show all " + tag;

// ------------------- Body
        var body = this.hb.ce("DIV");
        body.id = this.getID_BODY();

        var pre = this.hb.ce("PRE");
        $( body ).append(pre);
            var json = this.cache.c[ tag ] ;
            var txt = JSON.stringify(json, undefined, 4);
            $( pre ).html( this.hb.syntaxHighlight(txt));
            $( pre ).css("margin", "20px")

// ------------------- Buttons
        var ff_Close = this.f_Close.bind(this);
        var buttons = [];

        var ff_Download =  this.hb.wrapFunction(this.f_Download.bind(this), ["ALL"+tag.toUpperCase(), json]);
        var btn_Download = {"text": "Download",
                         "color": "primary",
                         "f": ff_Download};
        buttons.push(btn_Download);

        return [title, body, buttons, ff_Close];
    }

    f_HidePanel(args){
        var key = args[0]; var p = 1;
        var id = this.getID_BODY_SHOWALLPANEL(key);
        var div = this.hb.ge(id);
        $( div ).hasClass("hide") ? $( div ).removeClass("hide") : $( div ).addClass("hide");
    }

}