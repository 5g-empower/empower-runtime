class EmpButtonBox{

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
        var keys = keys.concat( [this.hb.conf.buttonbox.tag] );
        return this.hb.generateID( keys );
    }

    getID_LEFT(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.buttonbox.elements.left] );
        return this.hb.generateID( keys );
    }

    getID_RIGHT(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.buttonbox.elements.right] );
        return this.hb.generateID( keys );
    }

    create(bdata=null, keys=null){

        if (keys === null)
            keys = this.keys;

        var bbox = this.hb.ce("DIV");
        bbox.id = this.getID(keys);

            var sl = this.hb.ce("SPAN");
            sl.id = this.getID_LEFT(keys);
            $( sl ).addClass("pull-left tooltip-henanced");
            $( sl ).attr("style", "padding: 5px;");
//            $( sl ).attr("style", "padding: 5px; border: 1px solid  #e7e7e7 !important");
        $( bbox ).append(sl);

            var sr = this.hb.ce("SPAN");
            sr.id = this.getID_RIGHT(keys);
            $( sr ).addClass("pull-right tooltip-henanced");
            $( sr ).attr("style", "padding: 5px;");
//            $( sr ).attr("style", "padding: 5px; border: 1px solid  #e7e7e7 !important");
        $( bbox ).append(sr);

        //console.log("bdata");
        //console.log(bdata);

        var sl_used = false;
        var sr_used = false;

        for (var i = 0; i < bdata.length; i++){
            var btn = this.createButton( bdata[i].tag, bdata[i].params, keys);
            if (bdata[i].left){
                $( sl ).append(btn);
                sl_used = true;
            }
            else{
                $( sr ).append(btn);
                sr_used = true;
            }
        }
        if (!sl_used){
            $( sl ).addClass("hide");
        }
        if (!sr_used){
            $( sr ).addClass("hide");
        }

        return bbox;
    }

    remove(){
        $( "#"+this.getID(keys) ).remove();
    }

    getButtonKeys(tag, keys=null){
        if ( !this.hb.isArray( tag ) ){
            tag = [ tag ];
        }
        var keys = tag.concat(this.keys);

        return keys
    }

    createButton(tag, params, keys=null){
        if (keys === null)
            keys = this.keys;

        var btn =  (new EmpButton(this.getButtonKeys(tag, keys)))
        return btn.create.apply(btn, params);
    }

    updateButton(tag, params, keys=null){
        if (keys === null)
            keys = this.keys;

        var btn =  (new EmpButton(this.getButtonKeys(tag, keys)))
        return btn.update.apply(btn, params);
    }


}
