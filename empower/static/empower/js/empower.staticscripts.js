function createNavbar(){
    var navbar = __HB.ceROW();

    var navbarBrand = __HB.ce("DIV");
    $( navbar ).append(navbarBrand);
        $( navbarBrand ).addClass("navbar-header");
        $( navbarBrand ).attr("style","display:block; padding: 10px 2%; float:left;");

        var navbarBrandA = __HB.ce("A");
        $( navbarBrand ).append(navbarBrandA);
            $( navbarBrandA ).addClass("navbar-brand");
            $( navbarBrandA ).attr("href", "/", "style","padding: 0px;");

            var navbarBrandAImg = __HB.ce("IMG");
            $( navbarBrandA ).append(navbarBrandAImg);
                $( navbarBrandAImg ).attr("alt", "Brand");
                $( navbarBrandAImg ).attr("src", "../../static/pics/empower_logo.png");
                $( navbarBrandAImg ).attr("style", "float:left");

            var navbarBrandATxt = "&nbsp;5G-EmPOWER v0.1";
            $( navbarBrandA ).append(navbarBrandATxt);

    var navbarUL = __HB.ce("DIV");
    $( navbar ).append(navbarUL);
        $( navbarUL ).addClass("nav navbar-nav navbar-right");
        $( navbarUL ).attr("style","display:block; padding: 10px 2%; float:left;");

        var pendingQuery = __HB.ce("LI");
        $( navbarUL ).append(pendingQuery);
            $(pendingQuery).addClass("navbar-text");
            pendingQuery.id = "navbar_pendingQuery"
            $( pendingQuery ).addClass("hide");
            $( pendingQuery ).text("Loading... ");
            $( pendingQuery ).css("color", "#FF0000");

        var user = __HB.ce("LI");
        $( navbarUL ).append(user);
            $(user).addClass("navbar-text");
            $(user).html("<strong>" + __USERNAME + "</strong>" + " (" + ( __ROLE==="user"? "U)":"A)" ) );

        var ms = __HB.ce("LI");
        $( navbarUL ).append(ms);
            $( ms ).addClass("dropdown");

            var a = __HB.ce("A");
            $( ms ).append(a);
                $( a ).addClass("dropdown-toggle");
                $( a ).attr("data-toggle","dropdown", "style", "float:left");

                var i = __HB.ceFAI("fa-user");
                $( a ).append(i);
                    $( i ).addClass("fa-fw");

                    var i = __HB.ceFAI("fa-caret-down");
                    $( a ).append(i);



            var ul = __HB.ce("UL");
            $( ms ).append(ul);
                $( ul ).addClass("dropdown-menu dropdown-user");

                var li = __HB.ce("li");
                $( ul ).append(li);
                    var a = __HB.ce("A");
                    $( li ).append(a);
                        $( a ).attr("href","/auth/logout");
                        $( a ).text("Logout");
                        var i = __HB.ceFAI(" fa-sign-out");
                        $( a ).prepend(i);
                            $( i ).addClass("fa-fw");

                var li = __HB.ce("li");
                $( ul ).append(li);
                    var a = __HB.ce("A");
                    $( li ).append(a);
                        $( a ).attr("href","#");
                        $( a ).text("User details");
                        var i = __HB.ceFAI("fa-user");
                        $( a ).prepend(i);
                        $( i ).addClass("fa-fw");
                var userDetails = function(){
                    var mdl = new EmpUpdateModalBox( __USERNAME );
                    var args = mdl.initResources("accounts", true);
                    var m = mdl.create(args[0], args[1], args[2], args[3]);
                    $( m ).modal({backdrop: 'static'});
                }
                    $( a ).click( userDetails );

                var li = __HB.ce("li");
                $( ul ).append(li);
                    $( li ).addClass("divider");

                var li = __HB.ce("li");
                $( ul ).append(li);
                    var a = __HB.ce("A");
                    $( li ).append(a);
                        $( a ).attr("href","#");
                        $( a ).text("Toggle Autorefresh");
                        var i = __HB.ceFAI("fa-spinner");
                        $( a ).prepend(i);
                            i.id = "toggle_autorefresh_icon";
                            $( i ).addClass("fa-fw");
                        $( a ).click(function(){toggleAutoRefresh("toggle_autorefresh_icon", 10000)});

    return navbar;
}

function createFooter(){
    var footer = __HB.ceROW();
    $( footer ).attr("style","padding: 2%");
        var sp = __HB.ce("SPAN");
        $( footer ).append(sp);
            $( sp ).addClass("pull-right");

            var txt = __HB.ce("STRONG");
            $( sp ).append(txt);
                $( txt ).addClass("text-primary");
                $( txt ).text("@CREATE-NET FBK, 2018");

    return footer;
}

function createPageWrapper(){
        var wrap = __HB.ce("DIV");
        wrap.id = "page-wrapper"; // NB: THERE IS CSS FORMATTING ASSOCIATED TO THIS ID!!! --> sb-admin-2.css
        $( wrap ).attr("style","border: 1px solid #e7e7e7 !important; padding: 0px 20px 20px 20px !important;")

            var r = __HB.ceROW();
            $( r ).attr("style","padding-top:20px");
        $( wrap ).append(r);

                var c = __HB.ceCOL("lg",12);
            $( r ).append(c);
                $( c ).append(__HB.ceCLEARFIX());

        return wrap;
}

function generateWarningModal(title, f_YES, f_NO=null){
    var m =__HB.ce("DIV");
    m.id = "warning-modal"
    $( m ).on("hidden.bs.modal", function () {
        // put your default event here
        $( this ).remove();
    });
    $( m ).addClass("modal fade");
    $( m ).attr("tabindex",-1);
    $( m ).attr("role","dialog");

        var md = __HB.ce("DIV");
        $( m ).append(md);
        $( md ).addClass("modal-dialog");
        $( md ).attr("role","document");

            var mc = __HB.ce("DIV");
            $( md ).append(mc);
            $( mc ).addClass("modal-content");

                var mh = __HB.ce("DIV");
                $( mc ).append(mh);
                $( mh ).addClass("modal-header");

                    var htitle = __HB.ce("H4");
                    $( mh ).append(htitle);
                    $( htitle ).addClass("modal-title");
                    $( htitle ).text(title);

                var mb = __HB.ce("DIV");
                $( mc ).append(mb);
                $( mb ).addClass("modal-body");

                    var body = __HB.ce("DIV");
                    $( mb ).append(body);
                    $( body ).addClass("huge");
                    $( body ).text("Are you sure?");

                var mf = __HB.ce("DIV");
                $( mc ).append(mf);
                $( mf ).addClass("modal-footer");

                    var btf_YES = __HB.ce("BUTTON");
                    $( mf ).append(btf_YES);
                    $( btf_YES ).addClass("btn btn-default");
                    $( btf_YES ).attr("type", "button");
                    $( btf_YES ).text("YES");
                    $( btf_YES ).click(f_YES);

                    var btf_NO = __HB.ce("BUTTON");
                    $( mf ).append(btf_NO);
                    $( btf_NO ).addClass("btn btn-default");
                    $( btf_NO ).attr("type", "button");
                    $( btf_NO ).text("NO");
                    if( f_NO )  $( btf_NO ).click(f_NO);
                    else    $( btf_NO ).attr("data-dismiss", "modal");
    return m;
}

