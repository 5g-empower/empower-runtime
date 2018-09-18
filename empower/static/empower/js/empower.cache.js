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
            else if( tag === "active" ){
                var tmp = [];
                for( var cmpnt in args[tag] ){
                    var c = args[tag][cmpnt];
                    c["component_id"] = cmpnt;
                    tmp.push(c);
                }
                results = tmp;
            }
            else if( tag === "marketplace" ){
                var tmp = [];
                for( var cmpnt in args[tag] ){
                    var c = args[tag][cmpnt];
                    c["component_id"] = cmpnt;
                    tmp.push(c);
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

    updateBB(el){

        var n = this.checkCardinality(el);
        var tag = "";
        switch(el){
            case this.qe.targets.TENANT:
                this.updateBB("admin");
                tag = "tenant"; break;
            case this.qe.targets.ACCOUNT:
                this.updateBB("admin");
                tag = "account"; break;
            case this.qe.targets.WTP:
                this.updateBB("devices");
                tag = "wtp"; break;
            case this.qe.targets.CPP:
                this.updateBB("devices");
                tag = "cpp"; break;
            case this.qe.targets.VBS:
                this.updateBB("devices");
                tag = "vbs"; break;
            case this.qe.targets.LVAP:
                this.updateBB("clients");
                tag = "lvap"; break;
            case this.qe.targets.UE:
                this.updateBB("clients");
                tag = "ue"; break;
            case this.qe.targets.ACL:
                tag = "acl"; break;
            case this.qe.targets.FEED:
                tag = "feed"; break;
            case this.qe.targets.ACTIVE:
                this.updateBB("components");
                tag = "active"; break;
            case this.qe.targets.MARKETPLACE:
                this.updateBB("components");
                tag = "marketplace"; break;
            default: tag = el;
        }
//        console.log( this.BBlist[tag] )
        if( this.BBlist[tag] ){
            $( "#" + this.BBlist[tag] ).text(n)
        }
        else{
            console.log("EmpCache.updateBB: BBlist[" + tag + "] not exists.")
        }
    }

    checkCardinality(tag){

        var n = 0;
        switch(tag){
            case this.qe.targets.ACCOUNT:
            case this.qe.targets.TENANT:
                this.checkCardinality("admin");
                n = this.c[tag].length;
                break;
            case "admin":
                n = this.c[this.qe.targets.TENANT].length + this.c[this.qe.targets.ACCOUNT].length;
                break;
            case this.qe.targets.WTP:
            case this.qe.targets.CPP:
            case this.qe.targets.VBS:
                this.checkCardinality("devices");
                n = this.c[tag].length;
                break;
            case "devices":
                n = this.c[this.qe.targets.WTP].length + this.c[this.qe.targets.CPP].length + this.c[this.qe.targets.VBS].length ;
                break;
            case this.qe.targets.LVAP:
            case this.qe.targets.UE:
                this.checkCardinality("clients");
                n = this.c[tag].length;
                break;
            case "clients":
                n = this.c[this.qe.targets.LVAP].length + this.c[this.qe.targets.UE].length;
                break;
            case this.qe.targets.ACTIVE:
                this.checkCardinality("components");
                n = this.c[tag].length;
                break;
            case this.qe.targets.MARKETPLACE:
                this.checkCardinality("components");
                n = this.c[tag].length;
                break;
            case "components":
                n = this.c[this.qe.targets.ACTIVE].length + this.c[this.qe.targets.MARKETPLACE].length;
                break;
            case this.qe.targets.LVNF:
                this.checkCardinality("services");
                n = this.c[tag].length;
                break;
            case "services":
                n = this.c[this.qe.targets.LVNF].length;
                break;
            case this.qe.targets.ACL:
                n = this.c[tag].length;
                break;
        }

//        console.log(tag,n);
        return n;

    }

}

