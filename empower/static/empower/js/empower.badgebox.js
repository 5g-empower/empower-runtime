class EmpBadgeBox{
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
        var keys = keys.concat( [this.hb.conf.badgebox.tag] );
        return this.hb.generateID( keys );
    }

    create(data=null, keys=null){
        //console.log(JSON.stringify(data);
        var bbx = this.hb.ceROW();
        $( bbx ).attr("style","padding: 20px 20px 0px 20px");
        bbx.id = this.getID(keys);
        if (data !== null){
            //console.log(data);
            for (var i = 0; i < data.length; i++){
                //console.log(data[i]);
                $( bbx ).append(this.createBadge.apply(this, data[i]));
            }
        }
        return bbx;
    }

    remove(keys=null){
        $( "#"+this.getID(keys) ).remove();
    }

    getBadgeKeys(tag, keys=null){
        if ( !this.hb.isArray( tag ) ){
            tag = [ tag ];
        }
        var keys = tag.concat(this.keys);

        return keys
    }

    getBadgeID(tag, keys=null){
        refkeys = this.getBadgeKeys(tag, keys);
        refID = (new EmpBadge(refkeys)).getID();
        return refID;
    }

    createBadge(tag, params=null, keys=null){
        var tp = new EmpBadge(this.getBadgeKeys(tag, keys));
        //console.log(tp);
        var id = tp.getID();
        this.cache.BBlist[tag] = tp.getID_STATUS();
        if ($( "#"+id ).length > 0){
            console.warn("EmpBadge "+id+" already available")
            return null;
        }
        if (params !== null){
            tp = tp.create.apply(tp, params);
        }
        else{
            tp = tp.create();
        }
        return tp;
    }

    addBadge(tag, params=null, keys=null){
        $( "#"+this.getID(keys) ).append(this.createBadge(tag, params, keys));
        return true;
    }

    updateBadge(tag, params, keys=null){
        var b = new EmpBadge(this.getBadgeKeys(tag, keys));
        b.update.apply(b, params);
    }

    removeBadge(tag){
        $( "#"+this.getBadgeID(tag) ).remove();
    }
}
