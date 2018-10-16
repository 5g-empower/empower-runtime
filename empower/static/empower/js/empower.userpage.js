class EmpUserPage{

    constructor(selTnt){

        this.hb = __HB;
        this.qe = __QE;
        this.desc = __DESC;
        this.cache = __CACHE;
        this.delay = __DELAY;

        var keys = __USERNAME;
        if ( !this.hb.isArray( keys ) ){
            keys = [ keys ];
        }
        this.keys = keys;

        this.selTnt = selTnt;
        this.resources = null;
    }

    getID_TENANTVIEWER(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.userpage.elements.tenantviewer] );
        return this.hb.generateID( keys );
    }

    getID_TENANTSELECTOR(keys=null){
        if (keys === null)
            keys = this.keys;
        var keys = keys.concat( [this.hb.conf.userpage.elements.tenantselector] );
        return this.hb.generateID( keys );
    }

    getID_TENANTSELECTOR_RADIOBOX(){
        var id = this.getID_TENANTSELECTOR() + "_rdbx";
        return id;
    }

    getID_TENANTSELECTOR_SELECTOR(){
        var id = this.getID_TENANTSELECTOR() + "_slctr";
        return id;
    }

    initUserPage(){

        this.resources = {};

        $( "#navbar" ).append(createNavbar());
        $( "#footer" ).append(createFooter());

        var r0 = this.hb.ceROW();
        $( "#userpage" ).append(r0);
            var c0 = this.hb.ceCOL("xs",12);
            $( r0 ).append(c0);
                var selector = this.hb.ce("DIV");
                $( c0 ).append(selector);
                selector.id = this.getID_TENANTSELECTOR();
        var r1 = this.hb.ceROW();
        $( "#userpage" ).append(r1);
            var c1 = this.hb.ceCOL("xs",12);
            $( r1 ).append(c1);
                var viewer = this.hb.ce("DIV");
                $( c1 ).append(viewer);
                viewer.id = this.getID_TENANTVIEWER();
                $( viewer ).addClass("hide");

        this.resources["tenantList"] = [];
        var target = [this.qe.targets.TENANT, this.qe.targets.ACCOUNT];
        var ff = function(){
            for( var i=0; i<arguments[0][this.qe.targets.TENANT].length; i++){
                var tnt = arguments[0][this.qe.targets.TENANT][i];
                this.resources["tenantList"].push( {"tenant": tnt, "color": "info"} );
            }
            for( var user in arguments[0][this.qe.targets.ACCOUNT])
                this.cache.c[this.qe.targets.ACCOUNT].push( arguments[0]["accounts"][user] );

            this.selectTenant();
        }
        this.qe.scheduleQuery("GET", target, null, null, ff.bind(this) );

        this.viewTenant();
    }

// --------------------------------------------------------------------- SELECTOR
    selectTenant(){
        var selector = this.hb.ge( this.getID_TENANTSELECTOR() );
        $( selector ).empty();
        var numPerRow = 3;
            var tntBdgeBx = this.d_TenantBadgeBox(numPerRow);
            $( selector ).append(tntBdgeBx);
    }

    d_TenantBadgeBox(numPerRow){

            var div = this.hb.ce("DIV");

        var tList = this.resources.tenantList;
        for( var i=0; i<tList.length; i++){
            var tnt = tList[i].tenant;
            var ff = this.hb.wrapFunction( this.f_selectTenantBadge.bind(this),[tnt])
            // title, colsize="xs", coln=1, color=null, iconname=null, status=0, func=null, keys=null
            var bdg = new EmpTenantBadge([this.keys, tnt.tenant_name]).create(tnt, "xs", 12/numPerRow, tList[i].color, ff, null);
            $( div ).append(bdg)
            $( bdg ).attr("key", tnt.tenant_id)
        }

        return div;
    }

    f_selectTenantBadge(args){
        var tnt = args[0]; var p = 1;
        this.selTnt = tnt;

        var tList = this.resources.tenantList;
        for( var i=0; i<tList.length; i++){
            if( tList[i].tenant.tenant_id === tnt.tenant_id ){
                var tmp = {"tenant": tList[i].tenant, "color": "primary", "icon": "fa-users"}
                tList.splice(i,1);
                tList.unshift(tmp);
            }
    }
        this.selectTenant();

        var selector = this.hb.ge( this.getID_TENANTSELECTOR() );
        $( selector ).addClass("hide");
        var viewer = this.hb.ge( this.getID_TENANTVIEWER() );
        $( viewer ).removeClass("hide");
        this.updateViewer();
        this.switchTo(["overview"]);

    }

// --------------------------------------------------------------------- init VIEWER

    initViewerResources(){
        // Page skeleton
        if (this.resources !== null){
            console.warn("EmpAdminPage.initPageResources: "+this.tenant_id+" has already initialized resources");
            return;
        }
        this.resources = {};

        var res = this.resources;

        /* RECEIPE SECTION
        * Contains all the instance specific descriptions (recipe) for the
        * entities in the page
        */
        res.recipes = {};

        /* Has to be built:
            - Collapse Panel Level 1 and Level 2
            - BadgeBox for all CP in level 1 (except OVerview) and for all CP in level 2
            - DatatableBox with the Wrapper, the Datatable and the function buttons
        */

        /* CollapsePanels (CPs) are the first level containers in a page
        */
        res.recipes.collapsepanels_l1 = {
            "overview": {"text": "Overview", "color": "primary", "icon": "fa-info-circle"},
            "clients": {"text": "Clients", "color": "primary", "icon": "fa-laptop"},
            "services": {"text": "Network Services", "color": "primary", "icon": "fa-cogs"},
            "devices": {"text": "Devices", "color": "primary", "icon": "fa-hdd-o"},
            "component": {"text": "Components", "color": "primary", "icon": "fa-bolt"},
            "qos": {"text": "Quality of Service", "color": "primary", "icon": "fa-bullseye"},
            "acl": {"text": "ACL", "color": "primary", "icon": "fa-filter"},
            "tenant": {"text": "Tenants", "color": "primary", "icon": "fa-cubes"},
            "account": {"text": "Accounts", "color": "primary", "icon": "fa-users"},
        };

        res.recipes.collapsepanels_l2 = {
            "clients": {
                "lvap": {"text": "LVAPs", "color": "info", "icon": "fa-star-o"},
                "ue": {"text": "UEs", "color": "info", "icon": "fa-mobile"}
            },
            "services": {
                "images": {"text": "Images", "color": "info", "icon": "fa-save"},
                "lvnf": {"text": "LVNFs", "color": "info", "icon": "fa-toggle-right"},
                "endpoint": {"text": "End Points", "color": "info", "icon": "fa-bullseye"},
                "links": {"text": "Virtual Links", "color": "info", "icon": "fa-link"}

            },
            "devices": {
                "wtp": {"text": "WTPs", "color": "info", "icon": "fa-wifi"},
                "cpp": {"text": "CPPs", "color": "info", "icon": "fa-gears"},
                "vbs": {"text": "VBSes", "color": "info", "icon": "fa-code"},
            },
            "qos": {
                "slice": {"text": "Network Slices", "color": "info", "icon": "fa-database"},
                "tr": {"text": "Traffic Rules", "color": "info", "icon": "fa-arrows-alt"},
            },
        };

        /* BadgeBoxes (BBs) are defined in some CPs and show some aggregated
        * info.
        * They have functionalities associated on clicking on them
        * They are identified by the CP where they are deployed by a TAG
        * cp: [TAG, [param1, param2, ...]]
        */

        res.recipes.badgeboxes = {};
        var cpl1 = res.recipes.collapsepanels_l1
        for (var cp in cpl1){
            if (cp === "overview"){             // Overview CP contains all other BB
                res.recipes.badgeboxes[cp] = [];
                var excluded = [ "overview", "qos", "services"]
                var cardinality = Object.keys(cpl1).length - excluded.length;
                var size = "lg";
                var slots = 4;

                for (var cpsub in cpl1){
                    if ( excluded.indexOf(cpsub) == -1 ){
                        // EmpBadge.create(title, colsize, coln, color, iconname, status, func=null, keys=null)
                        var bbx = [ cpsub,
                                    [ cpl1[cpsub].text, size, slots, "primary", cpl1[cpsub].icon, 0 ]
                        ]
                        res.recipes.badgeboxes[cp].push( bbx );
                    }
                }
            }
            if (typeof res.recipes.collapsepanels_l2[cp] !== "undefined"){ // BB created only for 2nd level of cp
                var cpl2 = res.recipes.collapsepanels_l2;

                res.recipes.badgeboxes[cp] = [];
                var cardinality = Object.keys(cpl2[cp]).length;
                var size = -1;
                var slots = -1;
                switch (cardinality){
                    case 1:
                    case 2:
                    case 3:
                    case 4:
                    case 6:
                    case 12:
                        size = "lg";
                        slots = 12 / cardinality;
                }

                for (var cpsub in cpl2[cp]){
                    var bbx = [ cpsub,
                                    [ cpl2[cp][cpsub].text, size, slots, "primary", cpl2[cp][cpsub].icon, 0 ]
                        ]
                    res.recipes.badgeboxes[cp].push( bbx );
                }
            }

        }

        /* DataTableBoxes (DTBs) are defined in some CPs, to visualize and
        * manage data in table format
        * They are identified by the CP where they are deployed and by a TAG
        * cp: [tag1, tag2, tag3, ...]
        */
        res.recipes.datatableboxes = {};

        res.recipes.datatableboxes.list = [];
        var cpl1 = res.recipes.collapsepanels_l1
        for (var cp in cpl1){
            if ( cp != "overview" ){
                var cpl2 = res.recipes.collapsepanels_l2
                if (typeof cpl2[cp] === "undefined"){
                        res.recipes.datatableboxes.list.push(cp);
                }
                else{
                    for (var cpsub in res.recipes.collapsepanels_l2[cp]){
                            res.recipes.datatableboxes.list.push(cpsub);
                    }
                }
            }
        }

        res.recipes.datatableboxes.buttonboxes = {};
        for (var index = 0; index < res.recipes.datatableboxes.list.length; index++){
            var cp = res.recipes.datatableboxes.list[index];

            var f_add = this.hb.wrapFunction( this.f_AddFunction.bind(this),[cp])
            var f_addbatch = this.hb.wrapFunction( this.f_AddBatchFunction.bind(this),[cp])
            var f_upd = this.hb.wrapFunction( this.f_UpdateFunction.bind(this),[cp])
            var f_switch = this.hb.wrapFunction( this.f_SwitchFunction.bind(this),[cp])
            var f_showall = this.hb.wrapFunction( this.f_ShowAllFunction.bind(this),[cp])
            var f_refresh = this.hb.wrapFunction( this.f_RefreshFunction.bind(this),[cp])
            var f_erases = this.hb.wrapFunction( this.f_EraseSelectedFunction.bind(this),[cp])
            var f_erasea = this.hb.wrapFunction( this.f_EraseAllFunction.bind(this),[cp])

            switch(cp){
                case "component":
                            // EmpButton.create(text, iconname, color, tooltip, onclick, keys)
                        res.recipes.datatableboxes.buttonboxes[cp] = [
                            {   "tag": "show", "left": true,
                                "params": [ null, "fa-search", "primary", "show selected " + cp.toUpperCase(), f_upd ]
                            },
                            {   "tag": "showAll", "left": true,
                                "params": [ null, "fa-file-text", "primary", "show all " + cp.toUpperCase(), f_showall ]
                            },
                            {   "tag": "refresh", "left": true,
                                "params": [ null, "fa-refresh", "primary", cp.toUpperCase() + " table refresh", f_refresh ]
                            },
                            {   "tag": "I/O", "left": false,
                                "params": [ null, "fa-power-off", "primary", "switch selected "+cp.toUpperCase(), f_switch ]
                            }
                        ]
                break;
                case "lvap":
                case "ue":
                            // EmpButton.create(text, iconname, color, tooltip, onclick, keys)
            res.recipes.datatableboxes.buttonboxes[cp] = [
                        {   "tag": "show", "left": true,
                                "params": [ null, "fa-search", "primary", "update selected " + cp.toUpperCase(), f_upd ]
                },
                        {   "tag": "showAll", "left": true,
                                "params": [ null, "fa-file-text", "primary", "show all " + cp.toUpperCase(), f_showall ]
                },
                        {   "tag": "refresh", "left": true,
                                "params": [ null, "fa-refresh", "primary", cp.toUpperCase() + " table refresh", f_refresh ]
                        }
                    ]
                break;
                default:
                    res.recipes.datatableboxes.buttonboxes[cp] = [
                        {   "tag": "add", "left": true,
                            "params": [ null, "fa-plus-circle", "primary", "add new "+cp.toUpperCase(), f_add ]
                },
                        {   "tag": "addb", "left": true,
                            "params": [ null, "fa-upload", "primary", "batch add new "+cp.toUpperCase(), f_addbatch ]
                },
                        {   "tag": "show", "left": true,
                            "params": [ null, "fa-search", "primary",  "update selected "+cp.toUpperCase(), f_upd ]
                    },
                        {   "tag": "showAll", "left": true,
                            "params": [ null, "fa-file-text", "primary", "show all "+cp.toUpperCase(), f_showall ]
                    },
                        {   "tag": "refresh", "left": true,
                            "params": [ null, "fa-refresh", "primary", cp.toUpperCase() + " table refresh", f_refresh ]
                    },
                        {   "tag": "erase", "left": false,
                            "params": [ null, "fa-trash-o", "danger", "erase selected "+cp.toUpperCase(), f_erases ]
                    },
                        {   "tag": "eraseAll", "left": false,
                            "params": [ null, "fa-bomb", "danger", "erase all "+cp.toUpperCase(), f_erasea ]
                    }
                ]
            }
        }

        /* PAGESTRUCT SECTION
        * Provides a list of the entity instances in a tree format that mirrors
        * the placement of the entities in the Page
        */

        res.pagestruct = {};
        var rp = res.pagestruct;
        var rr = res.recipes;
        // For each CP..
        rp.cps = {};
        var rpcps = rp.cps;
        for (var cp in rr.collapsepanels_l1){
            var cp_desc = rr.collapsepanels_l1[cp];
            // .. define a sub section
            rpcps[cp] = {};
            // .. define keys
            var cp_keys = this.keys.concat([cp]);
            // .. and then instantiate the CP
            rpcps[cp].collapsepanel = {};
            rpcps[cp].collapsepanel.instance = new EmpCollapsePanel(cp_keys);
            rpcps[cp].collapsepanel.parent = null;
            rpcps[cp].collapsepanel.children = [];

            if (typeof rr.badgeboxes[cp] !== "undefined"){
                rpcps[cp].badgebox = new EmpBadgeBox(cp_keys);
            }

            for (var cpsub in rr.collapsepanels_l2[cp]){
                var cp_desc = rr.collapsepanels_l2[cp][cpsub];
                // .. define a sub section
                rpcps[cpsub] = {};
                // .. define keys
                var cp_keys = this.keys.concat([cpsub]);
                // .. and then instantiate the CP
                rpcps[cpsub].collapsepanel = {};
                rpcps[cpsub].collapsepanel.instance = new EmpCollapsePanel(cp_keys);
                rpcps[cpsub].collapsepanel.parent = cp;
                rpcps[cpsub].collapsepanel.children = [];
                // .. and update parent cp's children list
                rpcps[cp].collapsepanel.children.push(rpcps[cpsub].collapsepanel.instance);

            }

        }

        for (var i = 0; i < rr.datatableboxes.list.length; i++){
            // Get tag
            var tag = rr.datatableboxes.list[i];
            // Define DTB c_keys
            var keys = this.keys.concat([tag]);
            // Instance DTB
            if( this.qe.targets[tag.toUpperCase()] ){
                rpcps[tag].datatablebox = new EmpDataTableBox(keys);
            }
            else{
                console.log("EmpAdminPage.initAdminPageResources: " + tag + " is not a QE target")
            }
        }

        rp.floatingnavmenu = new EmpFloatingNavMenu("menu");

//        console.log(res);

    }

    viewTenant(){

        this.initViewerResources();
        var viewer = this.hb.ge( this.getID_TENANTVIEWER() );
        $( viewer ).empty();

        var tr = this.resources;

        var trp = tr.pagestruct;
        var trr = tr.recipes;

        $( "#userpage" ).append(tr.pagestruct.floatingnavmenu.create());

        var pwrapper = createPageWrapper();
        $( "#userpage" ).append(pwrapper);

        // Start deploying CPs
        for (var cp in trp.cps){
            //console.log("NOW Processing CP "+cp)
            // Create the BB according to the associated recipe
            var p = trp.cps[cp].collapsepanel.parent;
            var tag = this.hb.mapName2Tag(cp);

            var cpblock = null
            if ( p === null){   //
                cpblock = trp.cps[cp].collapsepanel.instance.create(
                    trr.collapsepanels_l1[cp].text,
                    trr.collapsepanels_l1[cp].color,
                    trr.collapsepanels_l1[cp].icon
                )
                $( pwrapper ).append(cpblock);
            }
            else{
                cpblock = trp.cps[cp].collapsepanel.instance.create(
                    trr.collapsepanels_l2[p][cp].text,
                    trr.collapsepanels_l2[p][cp].color,
                    trr.collapsepanels_l2[p][cp].icon
                )
                var cpid = trp.cps[p].collapsepanel.instance.getID_COLLAPSINGPANEL();
                $( "#"+cpid ).append(cpblock);
                trp.cps[cp].collapsepanel.instance.setL2Panel();
            }
            // Deploy the CP
            // $( pwrapper ).append(cpblock);

            // Retrieve the ID of the collapsing panel of CP
            var cpid = trp.cps[cp].collapsepanel.instance.getID_COLLAPSINGPANEL();

            // Create and deploy DataTableBoxes (if any) into CP
            if (typeof trp.cps[cp].datatablebox !== "undefined"){
                //console.log(trp.cps[cp].datatablebox);
                //console.log(cp, trr.datatableboxes.buttonboxes[cp]);

                    // Create the DTB according to the specified type
                var dt = trp.cps[cp].datatablebox.create(
                        cp, // get headers descriptor
                        trr.datatableboxes.buttonboxes[cp] // get associated buttons recipes
                    )
                dt.id = cp
                $( "#"+cpid ).append( dt );
                this.cache.DTlist[ tag ] = trp.cps[cp].datatablebox.datatable;

                //console.log("Added DataTableBox "+dtb_type+" to "+cp);

                // Hide DTB
                //trp.cps[cp].datatablebox[cp].show(false);
                // Make DataTable associated to DTB responsive
                trp.cps[cp].datatablebox.makeResponsive();
                // Keep a DataTable instance for faster reference and data handling
                // trp.cps[cp].datatable[dtb_type] = $("#"+trp.cps[cp].datatablebox[dtb_type].datatable.getID()).DataTable();

            }

            // Create and deploy BadgeBox (if any) into CP
            if (typeof trp.cps[cp].badgebox !== "undefined"){
                    // Create the BB according to the recipe given for current CP
                var bb = trp.cps[cp].badgebox.create(trr.badgeboxes[cp]);
                // Deploy BB into CP
                $( "#"+cpid ).append( bb );
                //console.log("Added BadgeBox to "+cp);
            }
            else{
                //console.log("NO BADGEBOX", cp)
            }

            var menu = (trp.cps[cp].collapsepanel.children.length > 0);
            var label = "DEFAULT_LABEL";
            var icon = "fa-frown-o";
            var l1code = null;
            var p = trp.cps[cp].collapsepanel.parent;
            if (p === null){
                label = trr.collapsepanels_l1[cp].text;
                icon = trr.collapsepanels_l1[cp].icon;
                if (menu)
                    l1code = cp;
            }
            else{
                label = trr.collapsepanels_l2[p][cp].text;
                icon = trr.collapsepanels_l2[p][cp].icon;
                l1code = p;
            }
            var color = null;
            var ref = null;
            var f = this.hb.wrapFunction(this.switchTo.bind(this), [cp]);

//             console.log( null, menu, label, icon, color, ref, f, l1code );
            tr.pagestruct.floatingnavmenu.addMenuItem(
                null, //keys
                menu, //menu
                label, //label
                icon, //icon
                color, //color
                ref, //ref
                f,  //function
                l1code //l1code
            );

            //console.log("Added item to floatingMenu "+cp);

        }

        // Update BadgeBox functions
        for (var cp in trp.cps){
            if (typeof trp.cps[cp].badgebox !== "undefined"){
                if (cp === "overview"){
                    for (var cpsub in this.resources.recipes.collapsepanels_l1){
                        if (cpsub != "overview" ){

                            var f = this.hb.wrapFunction(this.switchTo.bind(this), [cpsub]);
                            trp.cps[cp].badgebox.updateBadge(cpsub,[
                                null, //title
                                null, //color
                                null, //iconname
                                null, //status
                                f
                            ])
                        }
                    }
                }
                else{
                    //console.log(cp);
                    for (var cpsub in this.resources.recipes.collapsepanels_l2[cp]){
                        var f = this.hb.wrapFunction(this.switchTo.bind(this), [cpsub]);
                        trp.cps[cp].badgebox.updateBadge(cpsub,[
                            null, //title
                            null, //color
                            null, //iconname
                            null, //status
                            f
                        ])
                    }
                }
            }
        }

        // update Db
//        this.qe.showAll();

        this.switchTo(["overview"])

    }

    uncollapseAll(){
        for (var cp in this.resources.pagestruct.cps){
            var id  = this.resources.pagestruct.cps[cp].collapsepanel.instance.getID();
            $("#"+id).removeClass("hide");
        }
    }
    uncollapseOne(cp){
        var cpid = this.resources.pagestruct.cps[cp].collapsepanel.instance.getID();
        var pid = null;
        for (var cp in this.resources.pagestruct.cps){
            var id  = this.resources.pagestruct.cps[cp].collapsepanel.instance.getID();
            if (id === cpid){
                var p = this.resources.pagestruct.cps[cp].collapsepanel.parent;
                if (p !== null){
                    pid = this.resources.pagestruct.cps[p].collapsepanel.instance.getID();
                    break;
                }
            }

            if (this.resources.pagestruct.cps[cp].badgebox !== undefined){
                //console.log("BBX in "+cp+": ", this.resources.pagestruct.cps[cp].badgebox);
                for (var subcp in this.resources.recipes.collapsepanels_l2[cp]){
                    if (this.resources.pagestruct.cps[subcp].collapsepanel.instance.getID() === cpid){
                        //console.log("FOUND");
                        this.resources.pagestruct.cps[cp].badgebox.updateBadge(subcp, [null, "info", null, null, null])
                    }
                    else{
                        //console.log(subcp, " =?= ", cpid);
                        this.resources.pagestruct.cps[cp].badgebox.updateBadge(subcp, [null, "primary", null, null, null])
                    }
                }
            }
        }
        for (var cp in this.resources.pagestruct.cps){
            var id  = this.resources.pagestruct.cps[cp].collapsepanel.instance.getID();

            if (id !== pid){
                $("#"+id).addClass("hide");
            }
            else{
                $("#"+id).removeClass("hide");
            }

        }
        $("#"+cpid).removeClass("hide");
    }

    switchTo( args ){
        var cp = args[0];
        if( cp in this.resources.recipes.collapsepanels_l2 ){
            var first = Object.keys( this.resources.recipes.collapsepanels_l2[cp] )[0];
            this.switchTo([first])
        }
        else{
            this.uncollapseOne(cp);
        }
    }

    wrapAddFunction(cp){
        var f = function(){
        };

        return f.bind(this);
    }

    wrapAddBatchFunction(cp){
        var f = function(){
        };

        return f.bind(this);
    }

    wrapShowAllFunction(cp){
        var f = function(){
            var tag = this.hb.mapName2Tag(cp);
            var cp_keys = this.keys.concat([tag]);
            var mdl = new EmpShowAllModalBox( cp_keys );
            var args = mdl.initResources(cp);
            var m = mdl.create(args[0], args[1], args[2], args[3]);
            $( m ).modal({backdrop: 'static'});
        };

        return f.bind(this);
    }

    wrapShowSelectedFunction(cp){
        var f = function(){
        };

        return f.bind(this);
    }

    wrapEraseSelectedFunction(cp){
        var f = function(){
        };

        return f.bind(this);
    }

    wrapEraseAllFunction(cp){
        var f = function(){
        };

        return f.bind(this);
                }

    wrapRefreshFunction(cp){
        var f = function(){
            var tag = this.hb.mapName2Tag(cp);
            this.qe.scheduleQuery("GET", [tag], tenant_id, null, this.cache.update.bind(this.cache));
        };

        return f.bind(this);
    }

    f_CloseViewer(){
        var selector = this.hb.ge( this.getID_TENANTSELECTOR() );
        $( selector ).removeClass("hide");
        var viewer = this.hb.ge( this.getID_TENANTVIEWER() );
        $( viewer ).addClass("hide");
    }

// --------------------------------------------------------------------- update VIEWER

    updateViewer(){
        var tenant_name = this.selTnt.tenant_name;
        var tenant_id = this.selTnt.tenant_id;

        var targets = [  this.qe.targets.WTP,
                        this.qe.targets.CPP,
                        this.qe.targets.VBS,
                        this.qe.targets.LVAP,
                        this.qe.targets.UE,
                        this.qe.targets.COMPONENT,
                        ];
        this.qe.scheduleQuery("GET", targets, tenant_id, null, this.cache.update.bind(this.cache));
    }

}