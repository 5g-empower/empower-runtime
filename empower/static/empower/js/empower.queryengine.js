class EmpQueryEngine{

    constructor(username, password, role){

        this.username = username;
        this.role  = role;
        this.roles = {};

        this.roles.ADMIN = "admin";
        this.roles.USER = "user";
        this.BASE_AUTH = "Basic " + btoa( this.username + ':' + password);
        this.targets = {};
        this.targets.COMPONENT = "components";
        this.targets.TENANT = "tenants";
        this.targets.ACCOUNT = "accounts";
        this.targets.CPP = "cpps";
        this.targets.WTP = "wtps";
        this.targets.VBS = "vbses";
        this.targets.UE = "ues";
        this.targets.LVAP = "lvaps";
        this.targets.LVNF = "lvnfs";
        this.targets.ACL = "acl";
        this.targets.UE_MEASUREMENT = "ue_measurements";
        this.targets.TR = "trs";
        this.targets.SLICE = "slices";

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
        $( "#navbar_pendingQuery" ).text("Loading...");
        var params = [];
        for (var i = 0; i < targets.length; i++){
            params.push(t.performQuery(type, targets[i], tenant_id, values) );
        }
        if ( cb !== null){
            return  ($.when.apply(null, params)).then(
                function(){
//                    console.log(cb);
                    $( "#navbar_pendingQuery" ).text(" ");
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
//                case this.targets.UE_MEASUREMENT:
//            case this.targets.TR:
//                if( type === "POST" ){
//                    url = this.POSTQueryURL(target, values.ssid);
//                    dataType = "text";
//                    data = '{ "version" : "1.0", "dscp" : "' + values.dscp + '", "label" : "' + values.label + '",';
//                    data += ' "match" : "' + values.match + '"  }';
//                }
//                break;
            case this.targets.TR:
                if( type === "POST" ){
                    url = this.POSTQueryURL(target, values.tenant_id);
                    dataType = "text";
                    data = '{ "version" : "1.0", "dscp" : "' + values.dscp + '", "label" : "' + values.label + '",';
                    data += ' "match" : "' + values.match + '"';
                    if( values.priority ) data += ', "priority" : "' + values.priority + '"';
                    data += ' }'
                }
                else if( type === "DELETE"){
                    url = this.DELETEQueryURL(target, values.tenant_id) + values.match;
                }
                break;
            case this.targets.SLICE:
                if( type === "POST"){
                    url = this.POSTQueryURL(target, values.tenant_id);
                    dataType = "text";
                    data = '{ "version" : "1.0", "dscp" : "' + values["dscp"] + '",';
                    data += '"lte": { "static-properties": { '
                    if( values["lte"]["static-properties"]["rbgs"] ) data += '"rbgs" : "' + values["lte"]["static-properties"]["rbgs"] + '",';
                    if( values["lte"]["static-properties"]["sched_id"] ) data += '"sched_id" : "' + values["lte"]["static-properties"]["sched_id"] + '",';
                    data = data.substr(0,data.length-1) + ' },'
                    data += '"runtime-properties": { '
                    if( values["lte"]["runtime-properties"]["rntis"] ) data += '"rntis" : ' + values["lte"]["runtime-properties"]["rntis"] + '';
                    data += ' },'
                    data += '"vbses": { ';
                        for( var vbs in values["lte"]["vbses"] ){
                            data += '"' + vbs + '": { "static-properties": { '
                            if( values["lte"]["vbses"][vbs]["static-properties"]["rbgs"] ) data += '"rbgs" : "' + values["lte"]["vbses"][vbs]["static-properties"]["rbgs"] + '",';
                            if( values["lte"]["vbses"][vbs]["static-properties"]["sched_id"] ) data += '"sched_id" : "' + values["lte"]["vbses"][vbs]["static-properties"]["sched_id"] + '",';
                            data = data.substr(0,data.length-1) + ' },'
                            data += '"runtime-properties": {'
                            if( values["lte"]["vbses"][vbs]["runtime-properties"]["rntis"] ) data += '"rntis" : ' + values["lte"]["vbses"][vbs]["runtime-properties"]["rntis"] + '';
                            data += ' },'
                            if( values["lte"]["vbses"][vbs]["cells"] ) data += '"cells" : ' + values["lte"]["vbses"][vbs]["cells"] + ',';
                            data = data.substr(0,data.length-1) + ' },'
                        }
                    data = data.substr(0,data.length-1) + ' }'
                    data += ' },'
                    data += '"wifi": { "static-properties": {'
                    if( values["wifi"]["static-properties"]["quantum"] ) data += '"quantum" : "' + values["wifi"]["static-properties"]["quantum"] + '",';
                    if( values["wifi"]["static-properties"]["amsdu_aggregation"] ) data += '"amsdu_aggregation" : "' + values["wifi"]["static-properties"]["amsdu_aggregation"] + '",';
                    data = data.substr(0,data.length-1) + ' },'
                    data += '"wtps": { ';
                        for( var wtp in values["wifi"]["wtps"] ){
                            data += '"' + wtp + '": { "static-properties": { '
                            if( values["wifi"]["wtps"][wtp]["static-properties"]["quantum"] ) data += '"quantum" : "' + values["wifi"]["wtps"][wtp]["static-properties"]["quantum"] + '",';
                            if( values["wifi"]["wtps"][wtp]["static-properties"]["amsdu_aggregation"] ) data += '"amsdu_aggregation" : "' + values["wifi"]["wtps"][wtp]["static-properties"]["amsdu_aggregation"] + '",';
                            data = data.substr(0,data.length-1) + ' },'
                            if( values["wifi"]["wtps"][wtp]["blocks"] ) data += '"blocks" : ' + values["wifi"]["wtps"][wtp]["blocks"] + ',';
                            data = data.substr(0,data.length-1) + ' },'
                        }
                    data = data.substr(0,data.length-1) + ' }'
                    data += ' }'
                    data += ' }'
                }
                else if( type === "PUT"){
                    url = this.PUTQueryURL(target, values.tenant_id) + values.dscp;
                    dataType = "text";
                    data = '{ "version" : "1.0", ';
                    data += '"lte": { "static-properties": { '
                    if( values["lte"]["static-properties"]["rbgs"] ) data += '"rbgs" : "' + values["lte"]["static-properties"]["rbgs"] + '",';
                    if( values["lte"]["static-properties"]["sched_id"] ) data += '"sched_id" : "' + values["lte"]["static-properties"]["sched_id"] + '",';
                    data = data.substr(0,data.length-1) + ' },'
                    data += '"runtime-properties": { '
                    if( values["lte"]["runtime-properties"]["rntis"] ) data += '"rntis" : ' + values["lte"]["runtime-properties"]["rntis"] + '';
                    data += ' },'
                    data += '"vbses": { ';
                        for( var vbs in values["lte"]["vbses"] ){
                            data += '"' + vbs + '": { "static-properties": { '
                            if( values["lte"]["vbses"][vbs]["static-properties"]["rbgs"] ) data += '"rbgs" : "' + values["lte"]["vbses"][vbs]["static-properties"]["rbgs"] + '",';
                            if( values["lte"]["vbses"][vbs]["static-properties"]["sched_id"] ) data += '"sched_id" : "' + values["lte"]["vbses"][vbs]["static-properties"]["sched_id"] + '",';
                            data = data.substr(0,data.length-1) + ' },'
                            data += '"runtime-properties": {'
                            if( values["lte"]["vbses"][vbs]["runtime-properties"]["rntis"] ) data += '"rntis" : ' + values["lte"]["vbses"][vbs]["runtime-properties"]["rntis"] + '';
                            data += ' },'
                            if( values["lte"]["vbses"][vbs]["cells"] ) data += '"cells" : ' + values["lte"]["vbses"][vbs]["cells"] + ',';
                            data = data.substr(0,data.length-1) + ' },'
                        }
                    data = data.substr(0,data.length-1) + ' }'
                    data += ' },'
                    data += '"wifi": { "static-properties": {'
                    if( values["wifi"]["static-properties"]["quantum"] ) data += '"quantum" : "' + values["wifi"]["static-properties"]["quantum"] + '",';
                    if( values["wifi"]["static-properties"]["amsdu_aggregation"] ) data += '"amsdu_aggregation" : "' + values["wifi"]["static-properties"]["amsdu_aggregation"] + '",';
                    data = data.substr(0,data.length-1) + ' },'
                    data += '"wtps": { ';
                        for( var wtp in values["wifi"]["wtps"] ){
                            data += '"' + wtp + '": { "static-properties": { '
                            if( values["wifi"]["wtps"][wtp]["static-properties"]["quantum"] ) data += '"quantum" : "' + values["wifi"]["wtps"][wtp]["static-properties"]["quantum"] + '",';
                            if( values["wifi"]["wtps"][wtp]["static-properties"]["amsdu_aggregation"] ) data += '"amsdu_aggregation" : "' + values["wifi"]["wtps"][wtp]["static-properties"]["amsdu_aggregation"] + '",';
                            data = data.substr(0,data.length-1) + ' },'; console.log( values["wifi"]["wtps"][wtp]["blocks"] )
                            if( values["wifi"]["wtps"][wtp]["blocks"] ) data += '"blocks" : ' + values["wifi"]["wtps"][wtp]["blocks"] + ',';
                            data = data.substr(0,data.length-1) + ' },'
                        }
                    data = data.substr(0,data.length-1) + ' }'
                    data += ' }'
                    data += ' }'
                }
                else if( type === "DELETE"){
                    url = this.DELETEQueryURL(target, values.tenant_id) + values.dscp;
                }
                break;
            case this.targets.COMPONENT:
                if( type === "POST" ){
                    url = this.POSTQueryURL(target, tenant_id);
                    dataType = "text";
                    data = '{ "version" : "1.0", "component" : "' + values.name + '"  }';
                }
                else if( type === "DELETE"){
                    url = this.DELETEQueryURL(target, tenant_id) + values.name;
                }
                break;
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
                    data = '{ "version" : "1.0", "username" : "' + values.username + '", "password" : "' + values.password + '", "role" : "' + values.role + '",'
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
                if( type === "PUT" ){   // values[ LVAP, new WTP, Block hwaddr ]
                    url = this.PUTQueryURL(target, tenant_id)+ values[0].addr;
                    dataType = "text";
                    if( values[2] )
                        data = '{  "version": "1.0", "wtp" : "' + values[1].addr + '", "blocks" : "' + values[2] + '"  }';
                    else
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
                url = "/api/v1/" + target;
                break;
            case this.targets.WTP:
            case this.targets.CPP:
            case this.targets.VBS:
            case this.targets.UE:
            case this.targets.LVAP:
            case this.targets.TR:
            case this.targets.SLICE:
            case this.targets.COMPONENT:
                if( tenant_id ) {
                    url = "/api/v1/tenants/" + tenant_id + "/" + target;
                        } else {
                    url = "/api/v1/" + target;
                }
                break;
            case this.targets.TENANT:
                if( this.isAdmin() ){
                    url = "/api/v1/" + target;
                }
                else{
                    url = "/api/v1/"  + target +"?user=" + this.username;
                            }
                break;
            case this.targets.LVNF:
            case this.targets.UE_MEASUREMENT:
                if( tenant_id ){
                    url = "/api/v1/tenants/" + tenant_id + "/" + target;
                        }
                        else{
                    console.error("EmpQueryEngine.GETQueryURL: missing tenant ID parameter in "+target+" request");
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
            case this.targets.COMPONENT:
            case this.targets.SLICE:
            case this.targets.TR:
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
            case this.targets.SLICE:
            case this.targets.TR:
            case this.targets.ACCOUNT:
            case this.targets.CPP:
            case this.targets.VBS:
            case this.targets.WTP:
            case this.targets.COMPONENT:
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
            case this.targets.SLICE:
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

}
