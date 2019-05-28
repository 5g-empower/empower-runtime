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
        this.targets.UE = "ues";
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
                try{
                    return t.runQuery.bind(this).apply(null, data).promise().then(
                        function(){
                            t.querystatus = t.querystatus - 1;
                            // console.log("processQueryQueue: DONE qstatus ", t.querystatus);
                            return t.processQueryQueue(t);
                        }
                    )
                }
                catch(e){
                    console.log (e);
                    t.querystatus = t.querystatus - 1;
                    // console.log("processQueryQueue: DONE qstatus ", t.querystatus);
                    $( "#navbar_pendingQuery" ).text("Last query FAILED!");
                    return t.processQueryQueue(t);
                }
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
            params.push( t.performQuery(type, targets[i], tenant_id, values) );
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
                },
                function(){
                        $( "#navbar_pendingQuery" ).text(" ");
                        var error = JSON.parse(arguments[0].responseText);
                        var txt = error["code"] + ": " + error["reason"] + "\n";
                        if( error["message"] ) txt += error["message"];
                        alert(txt)
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
                    data = values;
                    data.version = "1.0";
                    data = JSON.stringify(data);
                }
                else if( type === "PUT"){
                    url = this.PUTQueryURL(target, values.tenant_id) + values.dscp;
                    dataType = "text";
                    data = values;
                    data.version = "1.0";
                    data = JSON.stringify(data);
                }
                else if( type === "DELETE"){
                    console.log(values);
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
                    data = '{ "version" : "1.0", "username" : "' + values.username + '", "role" : "' + values.role + '",'
                    if( values.password ) data += '"password" : "' + values.password + '", "new_password" : "' + values.new_password + '", "new_password_confirm" : "' + values.new_password_confirm + '",'
                    data += ' "name" : "' + values.name + '", "surname" : "' + values.surname + '", "email" : "' + values.email + '" }';
                }
                else if( type === "PUT"){
                    url = this.PUTQueryURL(target, tenant_id) + values.username;
                    dataType = "text";
                    data = '{ "version" : "1.0", "username" : "' + values.username + '", "role" : "' + values.role + '",'
                    if( values.password ) data += '"password" : "' + values.password + '", "new_password" : "' + values.new_password + '", "new_password_confirm" : "' + values.new_password_confirm + '",'
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
                    console.warn("VALUES: ",values);

                    data = {
                        version: "1.0"
                    }
                    if (values.wtp)
                        data.wtp =  values.wtp.addr;
                    
                    if (values.block){
                        if (values.block !== null){
                            data.blocks = [];
                            var block = {}
                            if (values.wtp)
                                block.wtp = values.wtp.addr;
                            else
                                console.warn("NO WTP provided for LVAP WTP block update")
                            block.hwaddr = values.block.hwaddr;
                            block.channel = values.block.channel;
                            block.band = values.block.band;

                            // console.log(data);
                            // console.log(data.blocks);
                            data.blocks.push(block);
                        }
                    }

                    data = JSON.stringify(data);

                    console.log(data);

                    if (values.lvap === null){
                        console.error("Missing LVAP params");
                    }

                    url = this.PUTQueryURL(target, tenant_id)+values.lvap.addr; 

                    console.log(url);
                    
                    dataType = "text";                   
                }
                break;
            case this.targets.UE:
                if( type === "PUT" ){

                    console.warn("VALUES: ",values);

                    data = {
                        version: "1.0"
                    }

                    if (values.vbs)
                        data.vbs =  values.vbs.addr;
                    
                    if (values.cell)
                        data.cell = values.cell;

                    if (values.slice)
                        data.slice = values.slice.dscp;

                    data = JSON.stringify(data);

                    console.log(data);

                    if (values.ue === null){
                        console.error("Missing UE params");
                    }

                    url = this.PUTQueryURL(target, tenant_id)+values.ue.ue_id; 

                    console.log(url);
                    
                    dataType = "text";
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
            success: function(){},
            error: function(){}
            };

        console.log("request", request)
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
            case this.targets.UE:
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
