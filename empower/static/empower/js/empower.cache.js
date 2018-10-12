class EmpCache{

    constructor(){

        this.hb = __HB;
        this.qe = __QE;
        this.desc = __DESC;

        this.DTlist = {};
        this.BBlist = {};

        this.c = {};
        for( var obj in this.qe.targets ){
            this.c[ this.qe.targets[obj] ] = [];
        }

    }

    update(){
        var args = arguments[0];
        for( var tag in args ){
            var results = null;
            if( tag === "accounts" ){
                var tmp = [];
                for( var user in args[tag] ){
                    tmp.push( args[tag][user] )
                }
                results = tmp;
            }
            else if( tag === "components" ){
                var tmp = [];
                for( var user in args[tag] ){
                    tmp.push( args[tag][user] )
                }
                results = tmp;
            }
            else{
                results = args[tag]
            }
//            console.log(tag, results );
            this.updateCache(tag, results);
    }

    }

    updateCache(tag, results){
        this.c[tag] = results;

        this.updateBB(tag);
        this.updateDT(tag);
    }

    updateDT(tag){
        if( this.DTlist[tag] ){
            var dt = this.DTlist[ tag ];
            var datatable = $( "#"+ dt.getID() ).DataTable();

            var DTdata = dt.ceDtBody(tag);

            datatable.clear();
            datatable.rows.add(DTdata);
            datatable.draw();
            }
        else{
            console.log("EmpCache.updateDT: DTlist[" + tag + "] not exists.")
        }
    }

    updateBB(tag){

        var n = this.checkCardinality(tag);
        var obj = this.hb.mapName2Obj(tag);
//        console.log( obj, this.BBlist[obj] )
        if( this.BBlist[obj] ){
            $( "#" + this.BBlist[obj] ).text(n)
        }
        else{
            console.log("EmpCache.updateBB: BBlist[" + obj + "] not exists.")
        }
    }

    checkCardinality(tag){
        var n = 0;
        switch(tag){
            case this.qe.targets.WTP:
            case this.qe.targets.CPP:
            case this.qe.targets.VBS:
                this.updateBB("devices");
                n = this.c[tag].length;
                break;
            case "devices":
                n = this.c[this.qe.targets.WTP].length + this.c[this.qe.targets.CPP].length + this.c[this.qe.targets.VBS].length ;
                break;
            case this.qe.targets.LVAP:
            case this.qe.targets.UE:
                this.updateBB("clients");
                n = this.c[tag].length;
                break;
            case "clients":
                n = this.c[this.qe.targets.LVAP].length + this.c[this.qe.targets.UE].length;
                break;
            default:
                n = this.c[tag].length;
        }
//        console.log(tag,n);
        return n;

    }

}

