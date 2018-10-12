class EmpBatchModalBox extends EmpModalBox{

    getID_BODY_BATCHPANEL(){
        var id = this.getID_BODY() + "_btchpnl";
        return id;
    }

    initResources(obj){
        var tag = this.hb.mapName2Tag(obj);
        var title = "Add batch of " + this.hb.mapName2Title(tag);

// ------------------- Body
        var body = this.hb.ce("DIV");
        body.id = this.getID_BODY();

        var div = this.d_BatchBodyPanel(tag);
        $( body ).append(div);


// ------------------- Buttons
        var ff_Close = this.f_Close.bind(this);
        var buttons = [];

        return [title, body, buttons, ff_Close];
    }

    d_BatchBodyPanel(tag){
        var div = this.hb.ce("DIV");
        $( div ).css("margin", "20px");
        $( div ).css("padding", "5px");
        div.id = this.getID_BODY_BATCHPANEL();

            var r0 = this.hb.ceROW();
            $( div ).append(r0);
            $( r0 ).css("margin", "10px 0px")
                var c0 = this.hb.ceCOL("xs", 3);
                $( r0 ).append(c0);
                $( c0 ).css("margin", "0px 10px")
                $( c0 ).text( "Add batch file:" )
                var c1 = __HB.ceCOL("xs", 8);
                $( r0 ).append(c1);
                    var group = __HB.ce("DIV");
                    $( c1 ).append(group);
                    $( group ).addClass("form-group");
                        var l1 = __HB.ce("LABEL");
                        $( group ).append(l1);
                        $( l1 ).addClass("radio-inline");
                            var i1 = __HB.ce("INPUT");
                            $( l1 ).append(i1);
                            $( i1 ).attr("type", "radio");
                            $( i1 ).attr("name", "optionsRadiosInline");
                            var lb1 = __HB.ce("SPAN")
                            $(l1).append(lb1);
                            $( lb1 ).text( "Absolute" );
                        var l2 = __HB.ce("LABEL");
                        $( group ).append(l2);
                        $( l2 ).addClass("radio-inline");
                            var i2 = __HB.ce("INPUT");
                            $( l2 ).append(i2);
                            $( i2 ).attr("type", "radio");
                            $( i2 ).attr("name", "optionsRadiosInline");
                            var lb2 = __HB.ce("SPAN")
                            $(l2).append(lb2);
                            $( lb2 ).text( "Relative" );
                        var l3 = __HB.ce("LABEL");
                        $( group ).append(l3);
                        $( l3 ).css('height', '34px');
                        $( l3 ).css('width', '34px');
                        $( l3 ).css('margin', '-7px 10px');
                        $( l3 ).attr("id", r0.id + "_IF")
                        $( l3 ).text(" ")
                            $( i1 ).click(function(){
                                $( l3 ).css("backgroundColor", "rgb(223, 240, 216)")
                                $( l3 ).attr("value", "absolute")
                            });
                            $( i2 ).click(function(){
                                $( l3 ).css("backgroundColor", "rgb(223, 240, 216)")
                                $( l3 ).attr("value", "relative")
                            });

            var r1 = this.hb.ceROW();
            $( div ).append(r1);
            $( r1 ).css("margin", "10px 0px")

            var r2 = this.hb.ceROW();
            $( div ).append(r2);
            $( r2 ).css("margin", "10px 0px")
                var area = this.hb.ce("TEXTAREA");
                $( r2 ).append(area);
                area.id = this.getID_BODY_BATCHPANEL() + "_IF";
                $( area ).attr("rows", 15);
                $( area ).attr("cols", 90);

            var r3 = this.hb.ceROW();
            $( div ).append(r3);
            $( r3 ).css("margin", "10px 0px")
                var result = this.hb.ce("DIV");
                $( r2 ).append(result);
                result.id = this.getID_BODY_BATCHPANEL() + "_V";
                $( result ).addClass("hide");

            var r4 = this.hb.ceROW();
            $( div ).append(r4);
            $( r4 ).css("margin", "10px 0px");
                var btn1 = this.hb.ce("BUTTON");
                $( r3 ).append(btn1);
                $( btn1 ).attr("type", "button");
                $( btn1 ).attr("style", "margin: 0px 2px;");
                $( btn1 ).attr("title", "parse");
                var btn2 = this.hb.ce("BUTTON");
                $( r3 ).append(btn2);
                $( btn2 ).attr("type", "button");
                $( btn2 ).attr("style", "margin: 0px 2px;");
                $( btn2 ).attr("title", "add batch");
                btn2.disabled = true;

                var args = [tag, l3, btn1, btn2]
                var ff = this.hb.wrapFunction(this.f_parseBatch.bind(this), args);
                $( btn1 ).click( ff );
                    var span1 = this.hb.ce("SPAN");
                    $( btn1 ).append(span1);
                    $( span1 ).text("Parse JSON");
                var args = [tag, l3, btn1, btn2]
                var ff = this.hb.wrapFunction(this.f_addBatch.bind(this), args);
                $( btn2 ).click( ff );
                    var span2 = this.hb.ce("SPAN");
                    $( btn2 ).append(span2);
                    $( span2 ).text("Add batch")

        return div;
    }

    d_BatchResultPanel(tag, ctrl, result, onlyNew, onlyPast, sharedEqual, sharedDiff){
        var p0 = this.hb.cePANEL();
        $( result ).append(p0);
            var title = this.hb.cePANEL_H();
            $( p0 ).append(title);
                var span = this.hb.ce("SPAN");
                $( title ).append(span)
                $( span ).text("Shared elements");
            var body = this.hb.cePANEL_B();
            $( p0 ).append(body);
            for(var i=0; i<sharedEqual.length; i++){
                var el = sharedEqual[i];
                var r = this.hb.ceROW();
                $( body ).append(r);
                $( r ).css("margin","10px 0px");
                    var cntrs = ff_drawBatch_Object( tag, el, result.id);
                    if( cntrs.length != 0 ){
                        for( var jj=0; jj<cntrs.length; jj++ ){
                            $( r ).append( cntrs[jj] );
                        }
                    }
            }
            for(var i=0; i<sharedDiff.length; i++){
                var el = sharedDiff[i];
                var r = this.hb.ceROW();
                $( body ).append(r);
                $( r ).css("margin","10px 0px");
                $( r ).css("backgroundColor", "rgb(255, 255, 224)")
                    var cntrs = ff_drawBatch_Object( tag, el, result.id);
                    if( cntrs.length != 0 ){
                        for( var jj=0; jj<cntrs.length; jj++ ){
                            $( r ).append( cntrs[jj] );
                        }
                    }
            }
        var p1 = this.hb.cePANEL();
        $( result ).append(p1);
            var title = this.hb.cePANEL_H();
            $( p1 ).append(title);
                var span = this.hb.ce("SPAN");
                $( title ).append(span)
                $( span ).text("Add new elements");
            var body = this.hb.cePANEL_B();
            $( p1 ).append(body);
            for(var i=0; i<onlyNew.length; i++){
                var el = onlyNew[i];
                var r = this.hb.ceROW();
                $( body ).append(r);
                $( r ).css("margin","10px 0px");
                    var cntrs = ff_drawBatch_Object( tag, el, result.id);
                    if( cntrs.length != 0 ){
                        for( var jj=0; jj<cntrs.length; jj++ ){
                            $( r ).append( cntrs[jj] );
                        }
                    }
            }
        if(ctrl === "absolute"){
            var p2 = this.hb.cePANEL();
            $( result ).append(p2);
                var title = this.hb.cePANEL_H();
                $( p2 ).append(title);
                    var span = this.hb.ce("SPAN");
                    $( title ).append(span)
                    $( span ).text("Delete old elements");
                var body = this.hb.cePANEL_B();
                $( p2 ).append(body);
                for(var i=0; i<onlyPast.length; i++){
                    var el = onlyPast[i];
                    var r = this.hb.ceROW();
                    $( body ).append(r);
                    $( r ).css("margin","10px 0px");
                        var cntrs = ff_drawBatch_Object( tag, el, result.id);
                        if( cntrs.length != 0 ){
                            for( var jj=0; jj<cntrs.length; jj++ ){
                                $( r ).append( cntrs[jj] );
                            }
                        }
                }
        }
    }

    f_parseBatch(args){
        var tag = args[0]; var p = 1;
        var label = args[p]; p++;
        var btnParse = args[p]; p++;
        var btnAdd = args[p]; p++;
        var area = this.hb.ge( this.getID_BODY_BATCHPANEL() + "_IF" );
        var result = this.hb.ge( this.getID_BODY_BATCHPANEL() + "_V" );

        var ctrl = $( $(label)[0] ).attr('value');
        var text = $( $(area)[0] ).val()
        if( typeof ctrl === "undefined"){
            $( label ).css("backgroundColor", "rgb(238, 98, 98)");
        }
        else if( text.length == 0 ){
            $( area ).css("backgroundColor", "rgb(238, 98, 98)");
        }
        else{
            var parseTXT = JSON.parse(text);
            var attr = this.desc.d[tag].attr;
            var key = "";
            for( var a in attr ){
                if( attr[a].isKey ){
                    key = a;
                    break;
                }
            }
            var c = true;
            if( !this.hb.isArray(parseTXT) ){
                var tmp = parseTXT;
                parseTXT = [];
                parseTXT.push(tmp);
            }
//            console.log(parseTXT)
            for(var i=0; i<parseTXT.length; i++){
                var n = parseTXT[i];
                for( var a in attr ){
                    if ( a != "password" && !n.hasOwnProperty(a) ){ // TODO EMP_if : non si puo' recuperare la password?
                        c = false;
                        break;
                    }
                }
            }
            if( c ){
                var cached = {}
                for(var i=0; i<this.cache.c[tag].length; i++){
                    var e = this.cache.c[tag][i];
                    cached[ e[key] ] = e;
                }
                var input = {};
                for(var i=0; i<parseTXT.length; i++){
                    var e = parseTXT[i];
                    input[ e[key] ] = e;
                }
                var [onlyFrst, onlyScnd, sharedEqual, sharedDiff] = this.hb.checkAllDifferences(input, cached);
                $( area ).addClass("hide");
                $( result ).removeClass("hide");
                btnParse.disabled = true;
                btnAdd.disabled = false;
                this.d_BatchResultPanel(tag, ctrl, result, onlyFrst, onlyScnd, sharedEqual, sharedDiff);
            }
            else{
                $( area ).css("backgroundColor", "rgb(238, 98, 98)");
                alert( "Batch file is not matching " + tag + " structure." );
            }
        }
    }

    f_addBatch(args){
        var tag = args[0]; var p = 1;
        var label = args[p]; p++;
        var btnParse = args[p]; p++;
        var btnAdd = args[p]; p++;
        var ctrl = $( $(label)[0] ).attr('value');
        var area = this.hb.ge( this.getID_BODY_BATCHPANEL() + "_IF" );
        var text = $( $(area)[0] ).val();
        var parseTXT = JSON.parse(text);
        if( !this.hb.isArray(parseTXT) ){
            var tmp = parseTXT;
            parseTXT = [];
            parseTXT.push(tmp);
        }
        var attr = this.desc.d[tag].attr;
        var key = "";
        for( var a in attr ){
            if( attr[a].isKey ){
                key = a;
                break;
            }
        }
        var cached = {}
        for(var i=0; i<this.cache.c[tag].length; i++){
            var e = this.cache.c[tag][i];
            cached[ e[key] ] = e;
        }
        var input = {};
        for(var i=0; i<parseTXT.length; i++){
            var e = parseTXT[i];
            input[ e[key] ] = e;
        }
        var [onlyFrst, onlyScnd, sharedEqual, sharedDiff] = this.hb.checkAllDifferences(input, cached);
        if( ctrl === "absolute"){
            this.f_addBatchAbsolute(tag, onlyFrst, onlyScnd, sharedEqual, sharedDiff);
        }
        else if( ctrl === "relative"){
            this.f_addBatchRelative(tag, onlyFrst, onlyScnd, sharedEqual, sharedDiff);
        }
    }

    f_addBatchRelative(tag, onlyNew, onlyPast, sharedEqual, sharedDiff){
        var m = null;
        var f_YES = function(){
            var fff = function(){
                if( tag === this.qe.targets.TENANT)
                    this.qe.scheduleQuery("GET", [tag], null, null, this.cache.update.bind(this.cache));
                else
                    this.qe.scheduleQuery("GET", [tag, this.qe.targets.TENANT], null, null, this.cache.update.bind(this.cache));
            }
            for( var i=0; i<onlyNew.length; i++ ){
                var input = onlyNew[i];
                this.qe.scheduleQuery("POST", [tag], null, input, fff.bind(this));
            }
            $( m ).modal('hide');
            this.f_Close();
        }
        m = generateWarningModal( tag.toUpperCase() + ": add new elements", f_YES.bind(this));
        $( m ).modal({backdrop: 'static', keyboard: false});
    }

    f_addBatchAbsolute(tag, onlyNew, onlyPast, sharedEqual, sharedDiff){
        var m = null;
        var f_YES = function(){
            for( var i=0; i<onlyPast.length; i++ ){
                var input = onlyPast[i];
                this.qe.scheduleQuery("DELETE", [tag], null, input, function(){});
            }
            $( m ).modal('hide');
            this.f_addBatchRelative(tag, onlyNew, sharedEqual, sharedDiff);
        }
        m = generateWarningModal( tag.toUpperCase() + ": delete old elements", f_YES.bind(this));
        $( m ).modal({backdrop: 'static', keyboard: false});
    }

}