class EmpQueryEngine{

    constructor(username, password, role){

        this.username = username;
        this.role  = role;
        this.roles = {};

        this.roles.ADMIN = "admin";
        this.roles.USER = "user";
        this.BASE_AUTH = "Basic " + btoa( this.username + ':' + password);
        this.targets = {};
        this.targets.FEED = "feeds";
        this.targets.ACTIVE = "active";
        this.targets.MARKETPLACE = "marketplace";
        this.targets.TENANT = "tenants";
        this.targets.ACCOUNT = "accounts";
        this.targets.CPP = "cpps";
        this.targets.WTP = "wtps";
        this.targets.VBS = "vbses";
        this.targets.UE = "ues";
        this.targets.LVAP = "lvaps";
        this.targets.LVNF = "lvnfs";
        this.targets.ACL = "acl";
        this.targets.RRC_MEASUREMENT = "rrc_measurements";

        this.queryqueue = [];
        this.querystatus = 0;

    }

    isAdmin(){
        if (this.role === this.roles.ADMIN)
            return true;
        return false;
    }

    scheduleQuery(type="GET", targets, tenant_id=null, values=null, cb=null){
        var data = [type, targets, tenant_id, values, cb];
        this.queryqueue.push(data);
        this.processQueryQueue.bind(this)();
    }

    processQueryQueue(){
        var t = this
        //console.log("processQueryQueue");
        if (t.queryqueue.length > 0){
            // console.log("processQueryQueue: length = ",t.queryqueue.length);
            if (t.querystatus === 0){
                // console.log("processQueryQueue: qstatus ", t.querystatus);
                t.querystatus = 1;
                var data = t.queryqueue.shift();
                return t.runQuery.bind(this).apply(null, data).promise().then(
                    function(){
                        t.querystatus = t.querystatus - 1;
                        // console.log("processQueryQueue: DONE qstatus ", t.querystatus);
                        return t.processQueryQueue(t);
                    }
                )
            }
            else if (this.querystatus === 1){
                // console.log("processQueryQueue: qstatus ", this.querystatus);
            }
        }
        else{
            // console.log("processQueryQueue: queryqueue is VOID");
        }
        return;
    }

    runQuery( type="GET", targets, tenant_id, values, cb){
        var t = this;
        $( "#navbar_pendingQuery" ).removeClass("hide");
        var params = [];
        for (var i = 0; i < targets.length; i++){
            params.push(t.performQuery(type, targets[i], tenant_id, values) );
        }
        if ( cb !== null){
            return  ($.when.apply(null, params)).then(
                function(){
//                    console.log(cb);
                    $( "#navbar_pendingQuery" ).addClass("hide");
                    var args = {};
                    if (targets.length === 1){
                        args[targets[0]] = arguments[0];
                    }
                    else{
                        for (var i = 0; i < targets.length; i++){
                            args[targets[i]] = arguments[i][0];
                        }
                    }
                    cb.apply(null, [args]);
                }
            )
        }
    }

    performQuery(type="GET",target,  tenant_id, values){
                return $.ajax(this.getRequestParams(type, target, tenant_id, values));
    }

    getRequestParams(type, target, tenant_id, values){
        var url = this.GETQueryURL(target, tenant_id);
        var data = '';
        var dataType = 'json';

        switch(target){
//                case this.targets.FEED:
//                case this.targets.UE:
//                case this.targets.LVAP:
//                case this.targets.LVNF:
//                case this.targets.RRC_MEASUREMENT:
//                case this.targets.ACTIVE:
            case this.targets.TENANT:
                if( type === "POST" ){
                    url = this.POSTQueryURL(target, tenant_id);
                    dataType = "text";
                    data = '{ "version" : "1.0", "owner" : "' + values.owner + '", "tenant_name" : "' + values.tenant_name + '",';
                    data += ' "desc" : "' + values.desc + '", "bssid_type" : "' + values.bssid_type + '"';
                    if( values.plmn_id ) data += ', "plmn_id" : "' + values.plmn_id + '"';
                    if( tenant_id ) data += ', "tenant_id" : "' + tenant_id + '"';
                    data += ' }'
                }
                else if( type === "DELETE"){
                    url = this.DELETEQueryURL(target, tenant_id) + values.tenant_id;
                }
                break;
            case this.targets.ACCOUNT:
                if( type === "POST"){
                    url = this.POSTQueryURL(target, tenant_id);
                    dataType = "text";
                    data = '{ "version" : "1.0", "username" : "' + values.username + '", "password" : "' + values.password + '", "role" : "' + values.role + '",'
                    data += ' "name" : "' + values.name + '", "surname" : "' + values.surname + '", "email" : "' + values.email + '" }';
                }
                else if( type === "PUT"){
                    url = this.PUTQueryURL(target, tenant_id) + values.username;
                    dataType = "text";
                    data = '{ "version" : "1.0",'
                    data += ' "name" : "' + values.name + '", "surname" : "' + values.surname + '", "email" : "' + values.email + '" }';
                        }
                else if( type === "DELETE"){
                    url = this.DELETEQueryURL(target, tenant_id) + values.username;
                }
                break;
            case this.targets.ACL:
                if( type === "POST" ){
                    url = this.POSTQueryURL(target, tenant_id);
                    dataType = "text";
                    data = '{  "version": "1.0", "sta" : "' + values.addr + '", "label" : "' + values.label + '"  }';
                        }
                else if( type === "DELETE"){
                    url = this.DELETEQueryURL(target, tenant_id) + values.addr;
                        }
                break;
            case this.targets.LVAP:
                if( type === "PUT" ){
                    url = this.PUTQueryURL(target, tenant_id)+ values[0];
                    dataType = "text";
                    data = '{  "version": "1.0", "wtp" : "' + values[1].addr + '"  }';
                        }
                break;
            case this.targets.CPP:
            case this.targets.VBS:
            case this.targets.WTP:
                if( type === "POST"){
                    url = this.POSTQueryURL(target, tenant_id);
                    dataType = "text";
                    data = '{  "version": "1.0", "addr" : "' + values.addr + '", "label" : "' + values.label + '"  }';
                }
                else if( type === "DELETE"){
                    url = this.DELETEQueryURL(target, tenant_id) + values.addr;
                }
                else if( type === "ADD" ){
                    type = "POST";
                    url = this.ADDQueryURL(target, tenant_id) + values.addr;
                }
                break;
    }

        var t = this
        var request = {
            url: url,
            type: type,
            dataType: dataType,
            data: data,
            cache: false,
            beforeSend: function (request) {
                request.setRequestHeader("Authorization", t.BASE_AUTH);
            },
            error: console.log,
            success: function(){}
            };

//        console.log("request", request)
        return request;
    }

    GETQueryURL(target, tenant_id){
        var url = "";
        switch(target){
            case this.targets.ACCOUNT:
            case this.targets.FEED:
                url = "/api/v1/" + target;
                break;
            case this.targets.WTP:
            case this.targets.CPP:
            case this.targets.VBS:
            case this.targets.UE:
            case this.targets.LVAP:
                if( tenant_id ) {
                    url = "/api/v1/tenants/" + tenant_id + "/" + target;
                        } else {
                    url = "/api/v1/" + target;
                }
                break;
            case this.targets.MARKETPLACE:
            case this.targets.TENANT:
                if( this.isAdmin() ){
                    url = "/api/v1/" + target;
                }
                else{
                    url = "/api/v1/"  + target +"?user=" + this.username;
                            }
                break;
            case this.targets.LVNF:
            case this.targets.RRC_MEASUREMENT:
                if( tenant_id ){
                    url = "/api/v1/tenants/" + tenant_id + "/" + target;
                        }
                        else{
                    console.error("EmpQueryEngine.GETQueryURL: missing tenant ID parameter in "+target+" request");
                        }
                break;
            case this.targets.ACTIVE:
                if( tenant_id ) {
                    url = "/api/v1/tenants/" + tenant_id + "/components";
                } else {
                    url = "/api/v1/components";
                }
                break;

            case this.targets.ACL:
                url = "/api/v1/allow";
                break;
            default: console.log("EmpQueryEngine.GETQueryURL: no URL for "+target+" request");
                        }

        return url;
                }

    POSTQueryURL(target, tenant_id){
        var url = "";
        switch(target){
            case this.targets.TENANT:
            case this.targets.ACCOUNT:
                url = "/api/v1/" + target
                break;
            case this.targets.CPP:
            case this.targets.VBS:
            case this.targets.WTP:
                        if (tenant_id) {
                    url = "/api/v1/tenants/" + tenant_id + "/" + target
                        } else {
                    url = "/api/v1/" + target
                }
                break;
            case this.targets.ACL:
                url = "/api/v1/allow"
                break;
            default: console.log("EmpQueryEngine.POSTQueryURL: no URL for "+target+" request");
                        }

        return url;
                }

    DELETEQueryURL(target, tenant_id){
        var url = "";
        switch(target){
            case this.targets.ACCOUNT:
            case this.targets.CPP:
            case this.targets.VBS:
            case this.targets.WTP:
                        if (tenant_id) {
                    url = "/api/v1/tenants/" + tenant_id + "/" + target  + "/"
                        } else {
                    url = "/api/v1/" + target + "/"
                }
                break;
            case this.targets.TENANT:
                url = "/api/v1/" + target + "/"
                break;
            case this.targets.ACL:
                url = "/api/v1/allow/"
                break;
            default: console.log("EmpQueryEngine.DELETEQueryURL: no URL for "+target+" request");
                        }

        return url;
                }

    ADDQueryURL(target, tenant_id){
        var url = "";
        switch(target){
            case this.targets.CPP:
            case this.targets.VBS:
            case this.targets.WTP:
                if (tenant_id) {
                    url = "/api/v1/tenants/" + tenant_id + "/" + target  + "/"
                } else {
                    console.log("EmpQueryEngine.ADDQueryURL: no tenant id for "+target+" request");
                }
                break;
            default: console.log("EmpQueryEngine.ADDQueryURL: no URL for "+target+" request");
                        }

        return url;
                }

    PUTQueryURL(target, tenant_id){
        var url = "";
        switch(target){
            case this.targets.ACCOUNT:
            case this.targets.LVAP:
                if (tenant_id) {
                    url = "/api/v1/tenants/" + tenant_id + "/" + target  + "/"
                } else {
                    url = "/api/v1/" + target  + "/"
                }
                break;
            default: console.log("EmpQueryEngine.PUTQueryURL: no URL for "+target+" request");
                        }

        return url;
                }

//    retrieveDataSet(selection){
//        $( "#navbar_pendingQuery" ).removeClass("hide");
//        var params = [];
//        for (var i = 0; i < selection.length; i++){
////            console.log(selection[i]);
//            params.push(this.performQuery("GET", selection[i], null, null,
//                            function(){
//                                $( "#navbar_pendingQuery" ).addClass("hide");
//                            }
//                        ));
//        }
//        //console.log(params);
//
//        return ($.when.apply(null, params))
//        // ($.when.apply(null, params)).then(
//        //     function(){//, lvnfs, acls){
//        //         for (var i = 0; i < arguments.length; i++){
//        //             console.log(arguments[i][0]);
//        //         }
//        //     }
//        // );
//    }

//    showAll(){
//        //this.retrieveAllData().then(
//        var queryList = [
//                            this.targets.TENANT,
//                            this.targets.WTP,
//                            this.targets.CPP,
//                            this.targets.VBS,
//                            this.targets.LVAP,
//                            this.targets.UE,
//                            this.targets.ACL,
//                            this.targets.ACTIVE,
//                            this.targets.MARKETPLACE,
//                            this.targets.ACCOUNT,
//                        ];
//        this.retrieveDataSet( queryList
//        ).then(
//            function(){
//                var results = {};
//                for (var i = 0; i < queryList.length; i++){
//                    results[ queryList[i] ] = arguments[i][0];
//                }
//                __CACHE.update(results);
//            }
//        ).fail(
//            function(){
//                console.error("EmpQueryEngine.showAll: failure happened! Data not loaded.");
//            }
//        )
//                    }

//    retrieveTenantGeneric(){
//        return $.when(
//            this.performQuery(this.targets.IMSIMAC),
//            this.performQuery(this.targets.ACLALL),
//            this.performQuery(this.targets.ACLDEN)
//        );
//    }
//
//    retrieveTenant(tenant_id){
//        return $.when(
//            this.performQuery(this.targets.TENANT,tenant_id)
//        );
//    }

}
