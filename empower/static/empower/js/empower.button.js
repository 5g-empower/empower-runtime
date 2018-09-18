class EmpButton{

    constructor(keys){

        this.hb = __HB;
        this.qe = __QE;
        this.desc = __DESC;
        this.cache = __CACHE;
        this.delay = __DELAY;

        if ( !this.hb.isArray( keys ) ){
            keys = [ keys ];
        }
        this.keys = keys;

    }

    getID(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.button.tag] );
        return this.hb.generateID( keys );
    }

    getID_ICON(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.button.elements.icon] );
        return this.hb.generateID( keys );
    }

    create(text=null, iconname=null, color=null, tooltip=null, onclick=null, keys=null){

        var btn = this.hb.ce("BUTTON");
        btn.id = this.getID(keys);

        if (color === null){
            color = "info";
        }

        $( btn ).addClass("btn btn-"+color+" btn-social-icon");
        //btn.setAttribute("type", "button");
        $( btn ).attr("type", "button");
        //btn.style.margin = "0px 2px";
        $( btn ).attr("style", "margin: 0px 2px;");

        if (tooltip !== null){
            $( btn ).attr("data-toggle", "tooltip");
            $( btn ).attr("data-placement", "top");
            $( btn ).attr("title", tooltip);
        }

        if (text !== null){
            $( btn ).text(text);
        }

        if (iconname !== null){
            var ico = this.hb.ceFAI(iconname);
            ico.id = this.getID_ICON(keys);
            $( ico ).addClass("fa-2x");
            $( btn ).prepend(ico);
        }

        if (onclick !== null){
            $( btn ).unbind();
            $( btn ).click(onclick);
        }

        return btn;
    }

    remove(keys=null){
        $( "#"+this.getID(keys) ).unbind();
        $( "#"+this.getID(keys) ).remove();
    }

    update(text=null, iconname=null, color=null, tooltip=null, onclick=null, keys=null){

        if (text !== null){
            $("#"+this.getID(keys)).text(text);
        }

        if (iconname !== null){
            $("#"+this.getID_ICON(keys)).removeClass().addClass("fa "+iconname+" fa-2x");
        }

        if (color !== null){
            $("#"+this.getID(keys)).removeClass().addClass("btn btn-"+color+" btn-social-icon");
        }

        if (tooltip !== null){
            $("#"+this.getID(keys)).attr("data-toggle", "tooltip");
            $("#"+this.getID(keys)).attr("data-placement", "top");
            $("#"+this.getID(keys)).attr("title", tooltip);
        }

        if (onclick !== null){
            $("#"+this.getID(keys)).unbind();
            $("#"+this.getID(keys)).click(onclick);
        }

    }

    updateText(text, keys=null){
        this.update(text, null, null, null, null, keys);
    }

    updateIcon(iconname, keys=null){
        this.update(null, iconame, null, null, null, keys);
    }

    updateColor(color, keys=null){
        this.update(null, null, color, null, null, keys);
    }

    updateTooltip(tooltip, keys=null){
        this.update(null, null, null, tooltip, null, keys);
    }

    updateOnClick(tooltip, keys=null){
        this.update(null, null, null, null, onclick, keys);
    }
}


