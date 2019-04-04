class EmpDataTable{

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
        this.responsive = null;
    }

    getID(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.datatable.tag] );
        return this.hb.generateID( keys );
    }

    getID_THEAD(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.datatable.elements.thead] );
        return this.hb.generateID( keys );
    }

    getID_TBODY(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.datatable.elements.tbody] );
        return this.hb.generateID( keys );
    }

    create(obj, keys=null){
        // <table>
        var t =  this.hb.ce("TABLE");
        t.id = this.getID(keys);

        //console.log("createDataTable: TID "+t.id);

        $( t ).addClass("table table-striped table-bordered table-hover");
        $( t ).attr("style","width: 100%;");

        // <thead>
            var thead = this.ceDtHeader(obj);
            thead.id = this.getID_THEAD(keys);
        $( t ).append(thead);

        // <tbody>
            var tbody = this.hb.ce("TBODY");
            tbody.id = this.getID_TBODY(keys);
            var tableid = this.getID();
            $( tbody ).on( 'click', 'tr', function () {
                var table = $("#"+tableid).DataTable();
                if ( $(this).hasClass('selected') ) {
                    $(this).removeClass('selected');
                }
                else {
                    table.$('tr.selected').removeClass('selected');
                    $(this).addClass('selected');
                }
                //console.log(table.$('tr.selected')[0]);
            });
        $( t ).append(tbody);;

        return t;
    }

    ceDtHeader(obj){
        var thead = this.hb.ce("THEAD");
        var trh = this.hb.ce("TR");
        $( thead ).append(trh);

        var tag = this.hb.mapName2Tag(obj);
        var params = this.desc.d[tag].ff.TBL("h");
        if(params){
            for (var k= 0; k < params.length; k++){
                var th = this.hb.ce("TH");
                $( trh ).append(th);
                for( var j=0; j<params[k].length; j++){
                    switch( params[k][j].type ){
                        case "i": var i = this.hb.ceFAI(params[k][j].value);
                                    $( i ).addClass("fa-fw");
                                    $( th ).prepend(i);
                                    break;
                        case "d":
                        case "h": var s = this.hb.ce("SPAN");
                                    $( s ).text(" " + params[k][j].value);
                                    $( th ).append(s);
                                    break;
                        case "k": var s = this.hb.ce("SPAN");
                                    $( s ).text(" " + params[k][j].value);
                                    $( th ).append(s);

                                    if(params[k][j].style){
                                        $( s ).attr("style",params[k][j].style);
                                    }
                                    break;
                        default: console.log("EmpDataTable.ceDtHeader: param " + params[k][j].type + " not implemented.")
                    }
                }
            }
        }
        else{
            console.log("FormatFunction for " + tag + " not implemented");
            var th = this.hb.ce("TH");
            $( trh ).append(th);
        }
//        console.log(thead)
        return thead;
    }

    f_get_tenant_name(tenant_id){
        if( __ROLE === "admin"){
            for( var i=0; i<this.cache.c[this.qe.targets.TENANT].length; i++ ){
                var tnt = this.cache.c[this.qe.targets.TENANT][i];
                if( tnt["tenant_id"] === tenant_id ){
                    return tnt["tenant_name"];
                }
            }
        }
        else{
            var tenant_name = $( "#navbar_tenantname" ).text();
            for( var i=0; i<this.cache.c[this.qe.targets.TENANT].length; i++ ){
                var tnt = this.cache.c[this.qe.targets.TENANT][i];
                if( tnt["tenant_id"] === tenant_id ){
                    if (tnt["tenant_name"] === tenant_name){
                        return tenant_name;
                    }
                }
            }
        }
        return "NOT FOUND: ";
    }

    ceDtBody(obj){

        var tag = this.hb.mapName2Tag(obj);

        var DTdata = [];
        var results = this.cache.c[tag];

        var params = this.desc.d[tag].ff.TBL("d");
        if( !params ) return DTdata;

        for( var k=0; k<results.length; k++){
            var item = results[k];
            var DTrow = [];
            for( var j=0; j<params.length; j++ ){
                var r = __HB.ce("DIV");
                var p = params[j];
                for( var i = 0; i<p.length; i++){
                    switch( p[i].type ){

                        case "f":
                            var c = __HB.ce("SPAN");
                            $( r ).append(c);
                            // console.log(p[i]);
                            var f_name = "f_"+p[i].fname;
                            // console.warn(f_name)
                            $( c ).text( this[f_name](item[p[i].attr]));
                        break;

                        case "s":
                            var c = __HB.ce("SPAN");
                            $( r ).append(c);
                            $( c ).text( p[i].txt);
                        break;

                        case "d":
                            var c = __HB.ce("SPAN");
                            $( r ).append(c);
                                $( c ).text( p[i].value + " " );
                                if(p[i].style){
                                    $( c ).attr("style",p[i].style);
                                }
                        break;

                        case "a":
                            var c = __HB.ce("SPAN");
                            $( r ).append(c);
                                var v = item[p[i].attr] != null? item[p[i].attr] : ""
                                $( c ).text( v + " " );
                                if(p[i].style){
                                    $( c ).attr("style",p[i].style);
                                }
                        break;

                        case "k":
                            var c = __HB.ce("SPAN");
                            $( r ).append(c);
                            $( r ).attr("key", item[ p[i].attr ]);
                                var v = item[p[i].attr] != null? item[p[i].attr] : ""
                                $( c ).text( v + " " );
                                if(p[i].style){
                                    $( c ).attr("style",p[i].style);
                                }
                        break;

                        case "l":
                            var c = __HB.ce("SPAN");
                            $( r ).append(c);
                            var list = "";
                            for( var tmp in item[ p[i].attr ])
                                list += tmp + "<br>";
                            $( c ).html(list);
                        break;

                        case "o":
                            var c = __HB.ce("SPAN");
                            $( r ).append(c);
                                var keyAttr = "";
                                var el = this.hb.mapName2Tag( p[i].attr );
                                for( var a in __DESC.d[el].attr ){
                                    if (__DESC.d[el].attr[a].isKey){
                                        keyAttr = a;
                                        break;
                                    }
                                }
                                $( c ).text( item[p[i].attr][keyAttr] + " " );
                                if(p[i].style){
                                    $( c ).attr("style",p[i].style);
                                }
                                break;

                        case "i":
                            var c1 = __HB.ceFAI(p[i].icon);
                            $( r ).append(c1);
                                if(p[i].attr){
                                    var v = item[ p[i].attr ];
                                    if( p[i].color && p[i].color[v] ){
                                        $( c1 ).css("color", p[i].color[v])
                                    }
                                    else
                                        console.log("EmpFF.ceDtBody: color attribute only!")
                                }
                            var c2 = __HB.ce("SPAN");
                            $( r ).append(c2);
                                var v = item[p[i].attr] != null? item[p[i].attr] : ""
                                $( c2 ).text( " " + v);
                        break;

                        default: console.log("EmpFF.ceDtBody: param " + p[i].type + " not implemented.")
                    }
                }
    //            console.log(r.outerHTML)
                DTrow.push(r.outerHTML);
            }
            DTdata.push(DTrow);
        }

        return DTdata;
    }

    remove(keys=null){
        $( "#"+this.getID(keys) ).remove();
    }

    makeResponsive(keys=null){
        var tid = this.getID(keys);
        //console.log("makeResponsive: TID "+tid);
        if ( this.responsive === null){
            var rdt = $('#'+tid).DataTable({
                responsive: true
                // select: true
            });
            this.responsive = rdt;
            //console.log("makeResponsive: Databale"+tid+" is now responsive");
            return rdt;
        }
        else{
            console.log("DataTable "+tid+" is already responsive");
            return this.responsive;
        }
    }

}


