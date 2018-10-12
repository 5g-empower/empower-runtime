class EmpModalBox{

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
        var keys = keys.concat( [this.hb.conf.modalbox.tag] );
        return this.hb.generateID( keys );
    }

    getID_HEADER(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.modalbox.elements.header] );
        return this.hb.generateID( keys );
    }

    getID_BODY(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.modalbox.elements.body] );
        return this.hb.generateID( keys );
    }

    getID_FOOTER(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.modalbox.elements.footer] );
        return this.hb.generateID( keys );
    }

    create(title, body, buttons){

        var m = this.hb.ce("DIV");
        m.id = this.getID();
        $( m ).on("hidden.bs.modal", function () {
            // put your default event here
            $( this ).remove();
        });
        $( m ).addClass("modal fade");
    //    $( m ).attr("tabindex",-1);
        $( m ).attr("role","dialog");

            var md = this.hb.ce("DIV");
            $( md ).addClass("modal-dialog");
            $( md ).attr("role","document");
            $( md ).attr("style","width:80%");
            $( m ).append(md);

                var mc = this.hb.ce("DIV");
                $( mc ).addClass("modal-content");
                $( md ).append(mc);
    // ------------------------------------------- Header
                    var mh = this.hb.ce("DIV");
                    $( mh ).addClass("modal-header");
                    mh.id = this.getID_HEADER();
                    $( mc ).append(mh);
                    $( mh ).css("backgroundColor", PRIMARY);
                    $( mh ).css("color", "#FFFFFF");

                        var bth = this.hb.ce("BUTTON");
                        $( bth ).addClass("close");
                        $( bth ).attr("type", "button");
                        $( bth ).attr("data-dismiss", "modal");
                        $( bth ).attr("aria-label", "Close");
                        $( mh ).append(bth);
                        $( bth ).css("color", "#FFFFFF");

                            var bthsp = this.hb.ce("SPAN");
                            $( bthsp ).attr("aria-hidden", "true");
                            $( bthsp ).html("&times;");
                            $( bth ).append(bthsp);

                        var htitle = this.hb.ce("H4");
                        $( htitle ).addClass("modal-title");
                        $( htitle ).text(title);
                        $( mh ).append(htitle);
    // ------------------------------------------- Body
                    var mb = this.hb.ce("DIV");
                    $( mb ).addClass("modal-body");
                    $( mc ).append(mb);
                        $( mb ).append(body);
    // ------------------------------------------- Footer
                    var mf = this.hb.ce("DIV");
                    $( mf ).addClass("modal-footer");
                    $( mc ).append(mf);
                    mf.id = this.getID_FOOTER();
                        if (buttons != null){
                            for (var i = 0; i < buttons.length; i++){

                                var btf = this.hb.ce("BUTTON");
                                $( btf ).addClass("btn btn-"+buttons[i].color);
                                $( btf ).attr("type", "button");
                                $( btf ).text(buttons[i].text);
                                $( btf ).click(buttons[i].f);
                                $( mf ).append(btf);

                            }
                        }

        return m;
    }

}