class EmpShowAllModalBox extends EmpModalBox{

    getID_BODY_SHOWALLPANEL(key){
        var id = this.getID_BODY() + "_shwallpnl_" + key;
        return id;
    }

    initResources(obj){
        var tag = this.hb.mapName2Tag(obj);
        var title = "Show all " + this.hb.mapName2Title(tag);

// ------------------- Body
        var body = this.hb.ce("DIV");
        body.id = this.getID_BODY();

        var pre = this.hb.ce("PRE");
        $( body ).append(pre);
            var json = this.cache.c[ tag ] ;
            var txt = JSON.stringify(json, undefined, 4);
            $( pre ).html( this.hb.syntaxHighlight(txt));
            $( pre ).css("margin", "20px");

// ------------------- Buttons
        var buttons = [];

        var ff_Download =  this.hb.wrapFunction(this.f_Download.bind(this), ["ALL"+tag.toUpperCase(), json]);
        var btn_Download = {"text": "Download",
                         "color": "primary",
                         "f": ff_Download};
        buttons.push(btn_Download);

        var ff_Close = this.f_Close.bind(this);
        var btn_Close = {"text": "Close",
                         "color": "primary",
                         "f": ff_Close};
         buttons.push(btn_Close);

        return [title, body, buttons, ff_Close];
    }

    f_HidePanel(args){
        var key = args[0]; var p = 1;
        var id = this.getID_BODY_SHOWALLPANEL(key);
        var div = this.hb.ge(id);
        $( div ).hasClass("hide") ? $( div ).removeClass("hide") : $( div ).addClass("hide");
    }

    f_Close(){
        var id = this.getID();
        var m = this.hb.ge(id);
        $( m ).modal('hide');
    }

    f_Download(args){
        var title = args[0];
        var json = args[1];
        var txt = JSON.stringify(json, undefined, 4);
        var filename = __USERNAME.toUpperCase() + "_" + title + "_" +Date.now()+".txt";
        this.hb.fdownload(txt, filename);
    }

}