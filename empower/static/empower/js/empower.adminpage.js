class EmpAdminPage{

    constructor(){

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
        this.resources = null;

    }

    initAdminPage(){

        $( "#navbar" ).append(createNavbar());
        $( "#footer" ).append(createFooter());

        this.create();

    }

    initPageResources(){
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
        /* CollapsePanels (CPs) are the first level containers in a page
        */
        res.recipes.collapsepanels_l1 = {
            "overview": {"text": "Overview", "color": "primary", "icon": "fa-info-circle"},
            "network": {"text": "Network Graph", "color": "primary", "icon": "fa-sitemap"},
            "clients": {"text": "Clients", "color": "primary", "icon": "fa-laptop"},
            "services": {"text": "Network Services", "color": "primary", "icon": "fa-cogs"},
            "devices": {"text": "Devices", "color": "primary", "icon": "fa-hdd-o"},
            "components": {"text": "Components", "color": "primary", "icon": "fa-plug"},
            "acl": {"text": "ACL", "color": "primary", "icon": "fa-filter"},
            "admin": {"text": "Admin", "color": "primary", "icon": "fa-trophy"},
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
                "links": {"text": "Virtual links", "color": "info", "icon": "fa-link"}

            },
            "devices": {
                "wtp": {"text": "WTPs", "color": "info", "icon": "fa-wifi"},
                "cpp": {"text": "CPPs", "color": "info", "icon": "fa-gears"},
                "vbs": {"text": "VBSes", "color": "info", "icon": "fa-code"},
            },
            "components": {
                "active": {"text": "Active", "color": "info", "icon": "fa-bolt"},
                "marketplace": {"text": "Marketplace", "color": "info", "icon": "fa-puzzle-piece"},
            },
            "admin": {
                "account": {"text": "Account", "color": "info", "icon": "fa-users"},
                "tenant": {"text": "Tenants", "color": "info", "icon": "fa-cubes"},
            }
        };

        /* GraphBoxes
        * GraphBoxes (GBs) show a graph depiction of the network configuration
        * They are identified by the CP where they are deployed and by a TAG
        */
        res.recipes.graphboxes = {
            "network": [
                [
                    {
                        "tag": "WTP",
                        "left": true,
                        //"params": [ "TEXT A", "fa-plug", "info", "text a", click]
                        "params": [ null, "fa-wifi", "info", "filter WTP" ]
                    },
                    {
                        "tag": "LVAP",
                        "left": true,
                        "params": [ null, "fa-circle", "info", "filter LVAP" ]
                    },
                    {
                        "tag": "VBS",
                        "left": true,
                        "params": [ null, "fa-code", "info", "filter VBS" ]
                    },
                    {
                        "tag": "UE",
                        "left": true,
                        "params": [ null, "fa-wrench", "info", "filter UE" ]
                    },
                    {
                        "tag": "refresh",
                        "left": false,
                        "params": [ null, "fa-refresh", "primary", "Force graph refresh " ]
                    }
                ]
            ]
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
            if (cp === "overview"){
                res.recipes.badgeboxes[cp] = [];
                var cardinality = Object.keys(cpl1).length - 2;
                var size = -1;
                var slots = cardinality;
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

                for (var cpsub in cpl1){
                    if ((cpsub != "overview" ) &&
                        (cpsub != "network")){

                        var bbx = [
                            cpsub,
                            [
                                cpl1[cpsub].text,
                                size,
                                slots,
                                "primary",
                                cpl1[cpsub].icon,
                                0
                            ]
                        ]
                        //res.recipes.badgeboxes[cp][cpsub] = bbx;
                        res.recipes.badgeboxes[cp].push( bbx );
                    }
                }
            }
            if (typeof res.recipes.collapsepanels_l2[cp] !== "undefined"){
                var cpl2 = res.recipes.collapsepanels_l2;

                res.recipes.badgeboxes[cp] = [];
                var cardinality = Object.keys(cpl2[cp]).length;
                var size = -1;
                var slots = cardinality;
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
                    var bbx = [
                        cpsub,
                        [
                            cpl2[cp][cpsub].text,
                            size,
                            slots,
                            "primary",
                            cpl2[cp][cpsub].icon,
                            0
                        ]
                    ]
                    //res.recipes.badgeboxes[cp][cpsub] = bbx;
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
            if ((cp != "overview" ) &&
                (cp != "network")){
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
        //res.recipes.datatableboxes.headers = {};

        for (var index = 0; index < res.recipes.datatableboxes.list.length; index++){

            var cp = res.recipes.datatableboxes.list[index];

            var f_add = this.wrapAddFunction(cp);
            var f_addb = this.wrapAddBatchFunction(cp);
            var f_shows = this.wrapShowSelectedFunction(cp);
            var f_showa = this.wrapShowAllFunction(cp);
            var f_refresh = this.wrapRefreshFunction(cp);
            var f_erases = this.wrapEraseSelectedFunction(cp);
            var f_erasea = this.wrapEraseAllFunction(cp);

            switch(cp){
                case "active":
                case "marketplace":
                case "lvap":
            res.recipes.datatableboxes.buttonboxes[cp] = [
                        {   "tag": "show", "left": true,
                            "params": [ null, "fa-search", "primary", "show selected " + cp.toUpperCase(), f_shows ]
                },
                        {   "tag": "showAll", "left": true,
                            "params": [ null, "fa-file-text", "primary", "show all " + cp.toUpperCase(), f_showa ]
                },
                        {   "tag": "refresh", "left": true,
                            "params": [ null, "fa-refresh", "primary", "force " + cp.toUpperCase() + " table refresh", f_refresh ]
                        }
                    ]
                break;
                default:
                    res.recipes.datatableboxes.buttonboxes[cp] = [
                        {   "tag": "add", "left": true,
                            "params": [ null, "fa-plus-circle", "primary", "add new "+cp.toUpperCase(), f_add ]
                },
                        {   "tag": "addb", "left": true,
                            "params": [ null, "fa-upload", "primary", "batch add new "+cp.toUpperCase(), f_addb ]
                },
                        {   "tag": "show", "left": true,
                            "params": [ null, "fa-search", "primary",  "show selected "+cp.toUpperCase(), f_shows ]
                    },
                        {   "tag": "showAll", "left": true,
                            "params": [ null, "fa-file-text", "primary", "show all "+cp.toUpperCase(), f_showa ]
                    },
                        {   "tag": "refresh", "left": true,
                            "params": [ null, "fa-refresh", "primary", "force table refresh "+cp.toUpperCase(), f_refresh ]
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
        var ps = res.pagestruct;
        var rr = res.recipes;
        // For each CP..
        ps.cps = {};
        var pscps = ps.cps;
        for (var cp in rr.collapsepanels_l1){
            var cp_desc = rr.collapsepanels_l1[cp];
            // .. define a sub section
            pscps[cp] = {};
            // .. define keys
            var cp_keys = this.keys.concat([cp]);
            // .. and then instantiate the CP
            pscps[cp].collapsepanel = {};
            pscps[cp].collapsepanel.instance = new EmpCollapsePanel(cp_keys);
            pscps[cp].collapsepanel.parent = null;
            pscps[cp].collapsepanel.children = [];

            if (typeof rr.badgeboxes[cp] !== "undefined"){
                pscps[cp].badgebox = new EmpBadgeBox(cp_keys);
            }

            for (var cpsub in rr.collapsepanels_l2[cp]){
                var cp_desc = rr.collapsepanels_l2[cp][cpsub];
                // .. define a sub section
                pscps[cpsub] = {};
                // .. define keys
                var cp_keys = this.keys.concat([cpsub]);
                // .. and then instantiate the CP
                pscps[cpsub].collapsepanel = {};
                pscps[cpsub].collapsepanel.instance = new EmpCollapsePanel(cp_keys);
                pscps[cpsub].collapsepanel.parent = cp;
                pscps[cpsub].collapsepanel.children = [];
                // .. and update parent cp's children list
                pscps[cp].collapsepanel.children.push(pscps[cpsub].collapsepanel.instance);

            }

            ps.floatingnavmenu = new EmpFloatingNavMenu("menu");
        }

        for (var i = 0; i < rr.datatableboxes.list.length; i++){
            // Get tag
            var tag = rr.datatableboxes.list[i];
            // Define DTB c_keys
            var keys = this.keys.concat([tag]);
            // Instance DTB
            if( this.qe.targets[tag.toUpperCase()] ){
                pscps[tag].datatablebox = new EmpDataTableBox(keys);
            }
        }

//        console.log(res);

    }

    create(){

        this.initPageResources();
        var tr = this.resources;

        var trp = tr.pagestruct.cps;
        var trr = tr.recipes;

        $( "#adminpage" ).append(tr.pagestruct.floatingnavmenu.create());

        var pwrapper = createPageWrapper();
        $( "#adminpage" ).append(pwrapper);

        // Start deploying CPs
        for (var cp in trp){
            //console.log("NOW Processing CP "+cp)
            // Create the BB according to the associated recipe
            var p = trp[cp].collapsepanel.parent;
            var tag = this.hb.mapName(cp);

            var cpblock = null
            if ( p === null){
                cpblock = trp[cp].collapsepanel.instance.create(
                    trr.collapsepanels_l1[cp].text,
                    trr.collapsepanels_l1[cp].color,
                    trr.collapsepanels_l1[cp].icon
                )
                $( pwrapper ).append(cpblock);
            }
            else{
                cpblock = trp[cp].collapsepanel.instance.create(
                    trr.collapsepanels_l2[p][cp].text,
                    trr.collapsepanels_l2[p][cp].color,
                    trr.collapsepanels_l2[p][cp].icon
                )
                var cpid = trp[p].collapsepanel.instance.getID_COLLAPSINGPANEL();
                $( "#"+cpid ).append(cpblock);
                trp[cp].collapsepanel.instance.setL2Panel();
            }
            // Deploy the CP
            // $( pwrapper ).append(cpblock);

            // Retrieve the ID of the collapsing panel of CP
            var cpid = trp[cp].collapsepanel.instance.getID_COLLAPSINGPANEL();

            // Create and deploy DataTableBoxes (if any) into CP
            if (typeof trp[cp].datatablebox !== "undefined"){
                //console.log(trp[cp].datatablebox);
                //console.log(cp, trr.datatableboxes.buttonboxes[cp]);

                    // Create the DTB according to the specified type
                var dt = trp[cp].datatablebox.create(
                        cp, // get headers descriptor
                        trr.datatableboxes.buttonboxes[cp] // get associated buttons recipes
                    )
                $( "#"+cpid ).append( dt );
                this.cache.DTlist[ tag ] = trp[cp].datatablebox.datatable;

                //console.log("Added DataTableBox "+dtb_type+" to "+cp);

                // Hide DTB
                //trp[cp].datatablebox[cp].show(false);
                // Make DataTable associated to DTB responsive
                trp[cp].datatablebox.makeResponsive();
                // Keep a DataTable instance for faster reference and data handling
                // trp[cp].datatable[dtb_type] = $("#"+trp[cp].datatablebox[dtb_type].datatable.getID()).DataTable();

            }

            // Create and deploy BadgeBox (if any) into CP
            if (typeof trp[cp].badgebox !== "undefined"){
                    // Create the BB according to the recipe given for current CP
                var bb = trp[cp].badgebox.create(trr.badgeboxes[cp]);
                // Deploy BB into CP
                $( "#"+cpid ).append( bb );
                //console.log("Added BadgeBox to "+cp);
            }
            else{
                //console.log("NO BADGEBOX", cp)
            }

            var menu = (trp[cp].collapsepanel.children.length > 0);
            var label = "DEFAULT_LABEL";
            var icon = "fa-frown-o";
            var l1code = null;
            var p = trp[cp].collapsepanel.parent;
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

//             console.log(
//                 null, //keys
//                 menu, //menu
//                 label, //label
//                 icon, //icon
//                 color, //color
//                 ref, //ref
//                 f,  //function
//                 l1code //l1code
//             );
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

            if(cp === "network"){
                var netGraphBox = new EmpNetGraphBox(this.keys);
                var ng = netGraphBox.create();
                $( "#"+cpid ).append( ng );
                netGraphBox.addGraph("topology", [])
            }

        }

        // Update BadgeBox functions
        for (var cp in trp){
            if (typeof trp[cp].badgebox !== "undefined"){
                if (cp === "overview"){
                    for (var cpsub in this.resources.recipes.collapsepanels_l1){
                        if ((cpsub != "overview" ) &&
                            (cpsub != "network")){

                            var f = this.hb.wrapFunction(this.switchTo.bind(this), [cpsub]);
                            trp[cp].badgebox.updateBadge(cpsub,[
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
                        trp[cp].badgebox.updateBadge(cpsub,[
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
        var targets = [
                            this.qe.targets.TENANT,
                            this.qe.targets.WTP,
                            this.qe.targets.CPP,
                            this.qe.targets.VBS,
                            this.qe.targets.LVAP,
                            this.qe.targets.UE,
                            this.qe.targets.ACL,
                            this.qe.targets.ACTIVE,
                            this.qe.targets.MARKETPLACE,
                            this.qe.targets.ACCOUNT,
                        ];
//        $.when( this.qe.scheduleQuery("GET", targets, null, null, console.log) ).then( function(){ console.log( "done", new Date() )} );
        this.qe.scheduleQuery("GET", targets, null, null, this.cache.update.bind(this.cache));

//var t = this
//var d1 = $.Deferred();
//d1.resolve( this.qe.scheduleQuery("GET", targets, null, null, this.cache.update.bind(this.cache) ) )
//$.when( d1 ).done(function(){console.log("done", t.cache.c)} )

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
        if( cp === "overview" ){
            this.uncollapseAll();
        }
        else if( cp in this.resources.recipes.collapsepanels_l2 ){
            var first = Object.keys( this.resources.recipes.collapsepanels_l2[cp] )[0];
            this.switchTo([first])
        }
        else{
            this.uncollapseOne(cp);
        }
    }

    wrapAddFunction(cp){
        var f = function(){
            var tag = this.hb.mapName(cp);
            var cp_keys = this.keys.concat([tag]);
            var mdl = new EmpAddModalBox( cp_keys );
            var args = mdl.initResources(cp);
            var m = mdl.create(args[0], args[1], args[2], args[3]);
            $( m ).modal({backdrop: 'static'});
        };

        return f.bind(this);
    }

    wrapAddBatchFunction(cp){
        var f = function(){
            var tag = this.hb.mapName(cp);
            var cp_keys = this.keys.concat([tag]);
            var mdl = new EmpBatchModalBox( cp_keys );
            var args = mdl.initResources(cp);
            var m = mdl.create(args[0], args[1], args[2], args[3]);
            $( m ).modal({backdrop: 'static'});
        };

        return f.bind(this);
    }

    wrapShowAllFunction(cp){
        var f = function(){
            var tag = this.hb.mapName(cp);
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
            var tag = this.hb.mapName(cp);
            var cp_keys = this.keys.concat([tag]);
            var mdl = new EmpUpdateModalBox( cp_keys );
            var args = mdl.initResources(cp);
            var m = mdl.create(args[0], args[1], args[2], args[3]);
            $( m ).modal({backdrop: 'static'});
        };

        return f.bind(this);
    }

    wrapEraseSelectedFunction(cp){
        var f = function(){
            var tag = this.hb.mapName(cp);
            var f_YES = function(){
                var dt = this.cache.DTlist[ tag ];
                var datatable = $( "#"+ dt.getID() ).DataTable();
                var key = this.hb.getDTKeyFields(datatable.row('.selected').data());
                var input = this.hb.getKeyValue( tag , key);
//                console.log(key, input)
                var fff = function(){
                            if( tag === this.qe.targets.TENANT)
                                this.qe.scheduleQuery("GET", [tag], null, null, this.cache.update.bind(this.cache));
                            else
                                this.qe.scheduleQuery("GET", [tag, this.qe.targets.TENANT], null, null, this.cache.update.bind(this.cache));
                        }
                this.qe.scheduleQuery("DELETE", [ tag ],null, input, fff.bind(this) );

                $( m ).modal('hide');
            };
            var m = generateWarningModal("Remove selected " + cp.toUpperCase(), f_YES.bind(this));
            $( m ).modal();
        };

        return f.bind(this);
    };

    wrapEraseAllFunction(cp){
        var f = function(){
            var tag = this.hb.mapName(cp);
            var f_YES = function(){
                var dt = this.cache.DTlist[ tag ];
                var datatable = $( "#"+ dt.getID() ).DataTable();
                for( var i=0; i<datatable.rows().data().length; i++){
                    var key = this.hb.getDTKeyFields(datatable.rows().data()[i]);
                    var input = this.hb.getKeyValue( tag , key);
//                    console.log(key, input)

                    var fff = function(){
                                if( tag === this.qe.targets.TENANT)
                                    this.qe.scheduleQuery("GET", [tag], null, null, this.cache.update.bind(this.cache));
                                else
                                    this.qe.scheduleQuery("GET", [tag, this.qe.targets.TENANT], null, null, this.cache.update.bind(this.cache));
                            }
                    this.qe.scheduleQuery("DELETE", [ tag ],null, input, fff.bind(this));

                }
                $( m ).modal('hide');
            };
            var m = generateWarningModal("Remove ALL " + tag.toUpperCase(), f_YES.bind(this));
            $( m ).modal();
        };

        return f.bind(this);
    };

    wrapRefreshFunction(cp){
        var f = function(){
            var tag = this.hb.mapName(cp);
            this.qe.scheduleQuery("GET", [tag], null, null, this.cache.update.bind(this.cache));
        };

        return f.bind(this);
    }

}
