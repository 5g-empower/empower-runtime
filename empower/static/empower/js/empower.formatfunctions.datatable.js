// Format Functions
/*
    HEADER ctrl = h
        type: i -> icon
        type: h -> header label
        type: d -> char separator
        type: k -> key header label
    BODY ctrl = d
        type: i -> icon
        type: a -> attribute value
        type: d -> char separator
        type: l -> list
        type: o -> object
*/

// DTable fancy functions

function ff_Tenant_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "h", "value": "Name"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "value": "ID",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "h", "value": "WTPs"},
                         ]);
        params.push( [ { "type": "h", "value": "CPPs"},
                         ]);
        params.push( [ { "type": "h", "value": "VBSes"},
                         ]);
        params.push( [ { "type": "h", "value": "UEs"},
                         ]);
        params.push( [ { "type": "h", "value": "PLMN ID"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "a", "attr": "tenant_name"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "attr": "tenant_id",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "l", "attr": "wtps"},
                         ]);
        params.push( [ { "type": "l", "attr": "cpps"},
                         ]);
        params.push( [ { "type": "l", "attr": "vbses"},
                         ]);
        params.push( [ { "type": "l", "attr": "ues"},
                         ]);
        params.push( [ { "type": "a", "attr": "plmn_id"},
                         ]);
    }
    return params;
};

function ff_Wtp_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "h", "value": "Label"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "value": "MAC Address",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "h", "value": "Last seen (date)"},
                         ]);
        params.push( [ { "type": "h", "value": "Status"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "a", "attr": "label"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "attr": "addr",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "a", "attr": "last_seen_ts"},
                         ]);
        params.push( [ { "type": "i", "icon": "fa-circle",
                            "attr": "state",
                            "color": {"disconnected": RED,
                                        "connected": YELLOW,
                                        "online":GREEN} },
                         ]);
    }
    return params;
};

function ff_Cpp_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "h", "value": "Label"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "value": "MAC Address",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "h", "value": "Last seen (date)"},
                         ]);
        params.push( [ { "type": "h", "value": "Status"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "a", "attr": "label"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "attr": "addr",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "a", "attr": "last_seen_ts"},
                         ]);
        params.push( [ { "type": "i", "attr": "state",
                            "icon": "fa-circle",
                            "color": {"disconnected": RED,
                                        "connected": YELLOW,
                                        "online":GREEN} },
                         ]);
    }
    return params;
};

function ff_Component_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "Name",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "h", "value": "Active"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "k", "attr": "name",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "i", "attr": "active",
                            "icon": "fa-circle",
                            "color": {"false": RED,
                                        "true":GREEN} },
                         ]);
    }
    return params;
};

function ff_Vbs_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "h", "value": "Label"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "value": "MAC Address",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "h", "value": "Last seen (date)"},
                         ]);
        params.push( [ { "type": "h", "value": "Status"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "a", "attr": "label"},
                        { "type": "d", "value": ": "},
                        { "type": "k", "attr": "addr",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "a", "attr": "last_seen_ts"},
                         ]);
        params.push( [ { "type": "i", "attr": "state",
                            "icon": "fa-circle",
                            "color": {"disconnected": RED,
                                        "connected": YELLOW,
                                        "online":GREEN} },
                         ]);
    }
    return params;
};

function ff_Account_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "Username",
                            "style": "color:" + BLUE },
                        { "type": "d", "value": "( "},
                        { "type": "h", "value": "Role"},
                        { "type": "d", "value": " )"},
                         ]);
        params.push( [ { "type": "h", "value": "Email"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "k", "attr": "username",
                            "style": "color:" + BLUE },
                        { "type": "d", "value": "( "},
                        { "type": "a", "attr": "role"},
                        { "type": "d", "value": " )"},
                         ]);
        params.push( [ { "type": "a", "attr": "email"},
                         ]);
    }
    return params;
};

function ff_Ue_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "UE ID",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "h", "value": "IMSI"},
                         ]);
        params.push( [ { "type": "h", "value": "TMSI"},
                        ]);
        params.push( [ { "type": "h", "value": "RNTI"},
                         ]);
        params.push( [ { "type": "h", "value": "PLMN ID"},
                         ]);
        params.push( [ { "type": "h", "value": "VBS"},
                         ]);
        params.push( [ { "type": "h", "value": "Slice"},
                        ]);
        params.push( [ { "type": "h", "value": "State"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "k", "attr": "ue_id",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "a", "attr": "imsi"},
                         ]);
        params.push( [ { "type": "a", "attr": "tmsi"},
                        ]);
        params.push( [ { "type": "a", "attr": "rnti"},
                         ]);
        params.push( [ { "type": "a", "attr": "plmn_id"},
                         ]);
        params.push( [ { "type": "o", "attr": "vbs"},
                        ]);
        params.push( [ { "type": "a", "attr": "slice"},
                        ]);
                        params.push( [ { "type": "i", "attr": "state",
                        "icon": "fa-circle",
                        "color": {  "stopped": RED,
                                    "stopping": YELLOW,
                                    "running": GREEN,
                                    "spawning": BLUE,
                                    "migrating_stop": YELLOW,
                                    "migrating_start": YELLOW} },
                        ]);
    }
    return params;
};

function ff_Lvap_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "MAC Address",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "h", "value": "SSID"},
                         ]);
        params.push( [ { "type": "h", "value": "WTP"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "k", "attr": "addr",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "a", "attr": "ssid"},
                         ]);
        params.push( [ { "type": "o", "attr": "wtp"},
                         ]);
    }
    return params;
};

function ff_Lvnf_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "h", "value": "State"},
                         ]);
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "LVNF ID",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "h", "value": "CPP"},
                         ]);
        params.push( [ { "type": "h", "value": "Tenant ID"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "a", "attr": "state"},
                         ]);
        params.push( [ { "type": "k", "attr": "lvnf_id",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "a", "attr": "cpp"},
                         ]);
        params.push( [ { "type": "a", "attr": "tenant_id"},
                         ]);
    }
    return params;
};

function ff_Acl_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "MAC Address",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "h", "value": "Laptop/Mobile"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "k", "attr": "addr",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "a", "attr": "label"},
                         ]);
    }
    return params;
};

function ff_TR_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "h", "value": "Name"},
                         ]);
        params.push( [ { "type": "h", "value": "Tenant ID"},
                         ]);
        params.push( [ { "type": "h", "value": "Tag"},
                         ]);
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "Match",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "h", "value": "Priority"},
                         ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "a", "attr": "label"},
                         ]);
        params.push( [ { "type": "a", "attr": "tenant_id"},
                         ]);
        params.push( [ { "type": "a", "attr": "dscp"},
                         ]);
        params.push( [ { "type": "k", "attr": "match",
                            "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "a", "attr": "priority"},
                         ]);
    }
    return params;
};

function ff_Slice_Table( ctrl ){ // input param: ctrl = "h" for header table / "d" for data table
    var params = [];
    if( ctrl === "h" ){
        params.push( [ { "type": "i", "value": "fa-key"},
                        { "type": "k", "value": "Tenant ID",
                        "style": "color:" + BLUE }
                         ]);
        params.push( [ { "type": "i", "value": "fa-key"},
                         { "type": "k", "value": "Tag",
                         "style": "color:" + BLUE }
                          ]);
    }
    else if ( ctrl === "d" ){
        params.push( [ { "type": "f", "attr": "tenant_id",
                        "fname": "get_tenant_name" },
                        { "type": "s", "txt": ": "},
                        { "type": "k", "attr": "tenant_id",
                        "style": "color:" + BLUE },
                         ]);
        params.push( [ { "type": "k", "attr": "dscp",
                         "style": "color:" + BLUE }
                         ]);
    }
    return params;
};