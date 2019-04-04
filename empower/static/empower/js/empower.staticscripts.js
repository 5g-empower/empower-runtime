function createNavbar(){
    var navbar = __HB.ceROW();
    $( navbar ).addClass("vertical-align");
    if( __ROLE === "admin"){    $( navbar ).css("backgroundColor", ADMIN); }
    else{                       $( navbar ).css("backgroundColor", USER); }

        var c0 = __HB.ceCOL("xs", 5);
        $( c0 ).addClass("text-center");
        $( navbar ).append(c0);
            var r0 = __HB.ceROW();
            $( c0 ).append(r0);
            $( r0 ).css("padding", "5px");
                var c00 = __HB.ceCOL("xs",6);
                $( r0 ).append(c00);
                var c01 = __HB.ceCOL("xs",6);
                $( r0 ).append(c01);

    var navbarBrand = __HB.ce("DIV");
                    $( c00 ).append(navbarBrand);
        $( navbarBrand ).addClass("navbar-header");
        $( navbarBrand ).css("width", "250px");
//                    $( navbarBrand ).attr("style","display:block; padding: 10px 2%; float:left;");
        var navbarBrandA = __HB.ce("A");
        $( navbarBrand ).append(navbarBrandA);
            $( navbarBrandA ).addClass("navbar-brand");
                        $( navbarBrandA ).attr("href", "/");
            var navbarBrandAImg = __HB.ce("IMG");
            $( navbarBrandA ).append(navbarBrandAImg);
                $( navbarBrandAImg ).attr("alt", "Brand");
                $( navbarBrandAImg ).attr("src", "../../static/pics/empower_logo.png");
                $( navbarBrandAImg ).attr("style", "float:left");
                            var navbarBrandATxt = "&emsp;5G-EmPOWER";
            $( navbarBrandA ).append(navbarBrandATxt);
                                // var navbarTenantID = __HB.ce("SPAN")
                                // $( navbarBrandA ).append(navbarTenantID);
                                // navbarTenantID.id = "navbar_tenantname"
                                // $( navbarTenantID ).css("margin-left", "30px")

                    var pendingQueryStatus = __HB.ce("DIV");
                    $( c01 ).append(pendingQueryStatus);
                        $(pendingQueryStatus).addClass("navbar-text");
                        pendingQueryStatus.id = "navbar_pendingQuery"
//                        $( pendingQueryStatus ).addClass("hide");
                        $( pendingQueryStatus ).text(" ");

        var c1 = __HB.ceCOL("xs",7);
        $( navbar ).append(c1);
            var r1 = __HB.ceROW();
            $( c1 ).append(r1);
            $( r1 ).addClass("text-center");
//            $( r1 ).addClass("nav navbar-nav navbar-right");
            $( r1 ).css("padding", "5px");
//            $( r1 ).css("width", "400px");
//            $( r1 ).css("float", "right");
            $( r1 ).css("color", "#FFFFFF");

                var c10 = __HB.ceCOL("xs",4);
                $( c10 ).addClass("text-left vertical-align");
                $( r1 ).append(c10);
                var navbarTenantID = __HB.ce("SPAN")
                $( navbarTenantID ).css("font-size", "20px");
                $( navbarTenantID ).css("font-weight", "bold");
                $( c10 ).append(navbarTenantID);
                navbarTenantID.id = "navbar_tenantname"
                // $( navbarTenantID ).css("margin-left", "30px")
                // $( navbarTenantID ).css("padding-top", "5px");
                $( navbarTenantID ).addClass("text-left");

                var c11 = __HB.ceCOL("xs",5);
                $( c11 ).addClass("text-right");
                $( r1 ).append(c11);
//                $( c10 ).css("padding", "15px 0px");
                    var span = __HB.ce("SPAN");
                    $( c11 ).append(span);
                    $( span ).text("Autorefresh: ")
                    var refresh = __HB.ce("INPUT");
                    $( c11 ).append(refresh);
                    $( refresh ).addClass("switch");
                    $( refresh ).attr("type", "checkbox");
                    $( refresh ).attr("data-on-text", "ON");
                    $( refresh ).attr("data-off-text", "OFF");
                    $( refresh ).attr("data-on-color", "info");
                    $( refresh ).attr("data-off-color", "info");
                    $( refresh ).on('switchChange.bootstrapSwitch', __HB.wrapFunction( toggleAutoRefresh, [refresh] ));
                    $( refresh ).bootstrapSwitch()
                // var c11 = __HB.ceCOL("xs",3);
                var c12 = __HB.ceCOL("xs",3);
                $( c12 ).addClass("text-right");
                // $( c12 ).addClass("vertical-align");
                // $( r1 ).append(c11);
                $( r1 ).append(c12);
                    var user = __HB.ce("DIV");
                    $( c12 ).append(user);
                    $( user ).css("padding-top", "5px");
                    $( user ).css("display", "inline-block");
//                    $(user).addClass("navbar-text");
                    $(user).html("<strong>" + __USERNAME + "</strong>" + " (" + ( __ROLE==="user"? "User)&emsp;":"Admin)&emsp;" ) );
                // var c12 = __HB.ceCOL("xs",3);
                // $( r1 ).append(c12);
                // $( c12 ).css("color", "#FFFFFF");
                    var ms = __HB.ce("DIV");
                    $( c12 ).append(ms);
            $( ms ).addClass("dropdown");
                    $( ms ).css("padding-top", "5px");
                    $( ms ).css("display", "inline-block");
                    $( ms ).css("margin-right", "10px");
            var a = __HB.ce("A");
            $( ms ).append(a);
                $( a ).addClass("dropdown-toggle");
                $( a ).attr("data-toggle","dropdown", "style", "float:left");
                var i = __HB.ceFAI("fa-user");
                $( a ).append(i);
                    $( i ).addClass("fa-fw");
                            $( i ).css("color", "#FFFFFF");
                    var i = __HB.ceFAI("fa-caret-down");
                    $( a ).append(i);
                                $( i ).css("color", "#FFFFFF");
            var ul = __HB.ce("UL");
            $( ms ).append(ul);
            $( ul ).addClass("dropdown-menu dropdown-menu-right dropdown-user");
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
                    var tag = __QE.targets.ACCOUNT;
                    var cp = __HB.mapName2Obj(tag);
                        var cp_keys = __USERNAME;
                    var mdl = new EmpUpdateModalBox( cp_keys );;
                    var args = mdl.initResources(cp); // return [title, body, buttons];
                    var m = mdl.create(args[0], args[1], args[2]);
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
                        $( a ).attr("href","/auth/logout");
                        $( a ).text("Logout");
                        var i = __HB.ceFAI(" fa-sign-out");
                        $( a ).prepend(i);
                            $( i ).addClass("fa-fw");

    return navbar;
}

function createFooter(){
    var footer = __HB.ceROW();
    $( footer ).attr("style","padding: 5px 2%");
        var sp = __HB.ce("SPAN");
        $( footer ).append(sp);
            $( sp ).addClass("pull-right");

            var txt = __HB.ce("STRONG");
            $( sp ).append(txt);
                $( txt ).addClass("text-primary");
                $( txt ).text("@FBK CREATE-NET, 2018");

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
                $( mh ).css("color", "#FFFFFF");

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

function toggleAutoRefresh(args){
    var state = args[0].checked;
    if( state ){
        if( __ROLE === "admin" ){
            var targets = [
                                __QE.targets.TENANT,
                                __QE.targets.WTP,
                                __QE.targets.CPP,
                                __QE.targets.VBS,
                                __QE.targets.LVAP,
                                __QE.targets.UE,
                                __QE.targets.ACL,
                                __QE.targets.COMPONENT,
                                __QE.targets.ACCOUNT,
                                __QE.targets.TR,
                                __QE.targets.SLICE,
                            ];
            __QE.scheduleQuery("GET", targets, null, null, __CACHE.update.bind(__CACHE));
        }
        else{
            var tenant_name = $( "#navbar_tenantname" ).text();
            var tenant_id = "";
            for(var tnt in __CACHE.c["tenants"]){
                if( __CACHE.c["tenants"]["tenant_name"] === tenant_name ){
                    tenant_id = __CACHE.c["tenants"]["tenant_id"];
                    break;
                }
            }

            var targets = [  __QE.targets.WTP,
                            __QE.targets.CPP,
                            __QE.targets.VBS,
                            __QE.targets.LVAP,
                            __QE.targets.UE,
                            __QE.targets.TR,
                            __QE.targets.SLICE,
                            ];
            __QE.scheduleQuery("GET", targets, tenant_id, null, __CACHE.update.bind(__CACHE));
        }
        var ff = function(){
            toggleAutoRefresh(args);
        }
        setTimeout(ff, 5000)
    }
}