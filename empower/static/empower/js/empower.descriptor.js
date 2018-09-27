class EmpDescriptor{

    constructor(){

        this.dt = {};   // datatypes
        this.dt.STR = {     "unknwn": {"type_id": "unknown", "validation": null, }, // unknown data type
                            "def": {"type_id": "default", "validation": vf_STR_def, },        // stringa alfanumerica
                            "mac": {"type_id": "mac", "validation": vf_STR_mac, },            // ethernet address
                            "uuid": {"type_id": "uuid", "validation": null, },          // uuid value
                            "data": {"type_id": "data", "validation": null, },          // "%Y-%m-%dT%H:%M:%S.%fZ"
                            "plmnid": {"type_id": "plmnid", "validation": vf_STR_plmnid, },
                            "bssid_type": {"type_id": "bssid_type", "validation": vf_STR_bssid_type, },  // "unique" - "shared"
                            "role": {"type_id": "role", "validation": vf_STR_role, },  // "admin" - "user"
                            "owner": {"type_id": "owner", "validation": vf_STR_owner, },  // "admin" - "user"
                            "state": {"type_id": "state", "validation": null, },
                            "dpid": {"type_id": "dpid", "validation": null, },
                            "ip_addr": {"type_id": "ip_addr", "validation": null, },
//                            "url": {"type_id": "url", "validation": null, },
                         };
        this.dt.NUM = {  "intgr": {"type_id": "integer", "validation": null, },
                         "bool": {"type_id": "boolean", "validation": null, },
                         };
        this.dt.LIST = { "a": {"type_id": "arry", "validation": null, },
                            "d":  {"type_id": "dict", "validation": null, },
                          };
        this.dt.OBJ = {  "lvap": {"type_id": "lvap", "validation": null, },
//                            "ue":  {"type_id": "ue", "validation": null, },
//                            "lvnf":  {"type_id": "lvnf", "validation": null, },
                            "wtp":  {"type_id": "wtp", "validation": null, },
                            "cpp":  {"type_id": "cpp", "validation": null, },
//                            "vbs":  {"type_id": "vbs", "validation": null, },
//                            "component":  {"type_id": "component", "validation": null, },
//                            "traffic_rule":  {"type_id": "traffic_rule", "validation": null, },
//                            "port":  {"type_id": "port", "validation": null, },
//                            "support":  {"type_id": "support", "validation": null, },
//                            "cell":  {"type_id": "cell", "validation": null, },
                            "img":  {"type_id": "image", "validation": null, },
//                            "measurement":  {"type_id": "measurement", "validation": null, },
//                            "result":  {"type_id": "result", "validation": null, },
                            "datapath":  {"type_id": "datapath", "validation": null, },
//                            "network_port":  {"type_id": "network_port", "validation": null, },
                            "connection":  {"type_id": "connection", "validation": null, },
                            "ssids":  {"type_id": "ssids", "validation": null, },
                            "networks":  {"type_id": "networks", "validation": null, },
                          };
        // format function names
        this.ffn= {
            "TBL": "tbl",
            "GET": "get",
            "SET": "set",
            "UPD": "upd",
        }


        // Tenant
        this.d = {};
        var targets = __QE.targets;

        this.d[targets.TENANT] = { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.TENANT].attr["bssid_type"]    =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.STR.bssid_type };
            this.d[targets.TENANT].attr["components"]    =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["cpps"]          =  {"isKey": false,   "set": false,  "update": true,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["desc"]          =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.STR.def };
            this.d[targets.TENANT].attr["lvaps"]         =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["lvnfs"]         =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["owner"]         =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.STR.owner };
            this.d[targets.TENANT].attr["plmn_id"]       =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.STR.plmnid };
            this.d[targets.TENANT].attr["tenant_id"]     =  {"isKey": true,    "set": false,  "update": false,  "type": this.dt.STR.uuid};
            this.d[targets.TENANT].attr["tenant_name"]   =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.STR.def };
            this.d[targets.TENANT].attr["traffic_rules"] =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["ues"]           =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["vbses"]         =  {"isKey": false,   "set": false,  "update": true,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["wtps"]          =  {"isKey": false,   "set": false,  "update": true,  "type": this.dt.LIST.d };

            this.d[targets.TENANT].ff.TBL = ff_Tenant_Table;
//            this.d[targets.TENANT].ff.GET = ff_Tenant_Get;
//            this.d[targets.TENANT].ff.SET = ff_Tenant_Set;
//            this.d[targets.TENANT].ff.UPD = ff_Tenant_Update;


        // WTP
        this.d[targets.WTP] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
        this.d["wtp"] = this.d[targets.WTP];
            this.d[targets.WTP].attr["addr"]         =  {"isKey": true,    "set": true,  "update": false,  "type": this.dt.STR.mac };
            this.d[targets.WTP].attr["connection"]   =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.OBJ.connection  };
            this.d[targets.WTP].attr["datapath"]     =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.OBJ.datapath };
            this.d[targets.WTP].attr["label"]        =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.STR.def };
            this.d[targets.WTP].attr["last_seen"]    =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.WTP].attr["last_seen_ts"] =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.data };
            this.d[targets.WTP].attr["period"]       =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.WTP].attr["state"]        =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.state  };  // "disconnected" - "connected" - "online"
            this.d[targets.WTP].attr["supports"]     =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.a };

            this.d[targets.WTP].ff.TBL = ff_Wtp_Table;
//            this.d[targets.WTP].ff.GET = ff_Wtp_Get;
//            this.d[targets.WTP].ff.SET = ff_Wtp_Set;
//            this.d[targets.WTP].ff.UPD = ff_Wtp_Update;


        // CPP
        this.d[targets.CPP] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.CPP].attr["addr"]         =  {"isKey": true,    "set": true,  "update": false,  "type": this.dt.STR.mac };
            this.d[targets.CPP].attr["connection"]   =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.OBJ.connection };
            this.d[targets.CPP].attr["datapath"]     =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.OBJ.datapath };
            this.d[targets.CPP].attr["label"]        =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.STR.def };
            this.d[targets.CPP].attr["last_seen"]    =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.CPP].attr["last_seen_ts"] =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.data };
            this.d[targets.CPP].attr["period"]       =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.CPP].attr["state"]        =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.state  };  // "disconnected" - "connected" - "online"

            this.d[targets.CPP].ff.TBL = ff_Cpp_Table;
//            this.d[targets.CPP].ff.GET = ff_Cpp_Get;
//            this.d[targets.CPP].ff.SET = ff_Cpp_Set;
//            this.d[targets.CPP].ff.UPD = ff_Cpp_Update;


        // VBS
        this.d[targets.VBS] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
        this.d["vbs"] = this.d[targets.VBS];
            this.d[targets.VBS].attr["addr"]       =  {"isKey": true,    "set": true,  "update": false,  "type": this.dt.STR.mac };
            this.d[targets.VBS].attr["cells"]      =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.a  };
            this.d[targets.VBS].attr["connection"] =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.OBJ.connection };
            this.d[targets.VBS].attr["datapath"]   =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.OBJ.datapath };
            this.d[targets.VBS].attr["label"]      =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.STR.def };
            this.d[targets.VBS].attr["last_seen"]  =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.VBS].attr["last_seen_ts"]=  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.data };
            this.d[targets.VBS].attr["period"]     =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.VBS].attr["state"]      =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.state  };  // "disconnected" - "connected" - "online"

            this.d[targets.VBS].ff.TBL = ff_Vbs_Table;
//            this.d[targets.VBS].ff.GET = ff_Vbs_Get;
//            this.d[targets.VBS].ff.SET = ff_Vbs_Set;
//            this.d[targets.VBS].ff.UPD = ff_Vbs_Update;


        // COMPONENT ACTIVE    // Gli attributi cambiano in base al servizio/componente, come fare???
        this.d[targets.ACTIVE] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.ACTIVE].attr["component_id"] =  {"isKey": true,    "set": true,  "update": false,  "type": this.dt.STR.def};
//            this.d[targets.ACTIVE].attr["every"]        =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.NUM.intgr};
//            this.d[targets.ACTIVE].attr["params"]        =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.STR.unknwn};
//            this.d[targets.ACTIVE].attr["modules"]      =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.STR.unknwn};
//            this.d[targets.ACTIVE].attr["port"]         =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.NUM.intgr};

            this.d[targets.ACTIVE].ff.TBL = ff_Active_Table;
//            this.d[targets.ACTIVE].ff.GET = ff_Active_Get;
//            this.d[targets.ACTIVE].ff.SET = ff_Active_Set;
//            this.d[targets.ACTIVE].ff.UPD = ff_Active_Update;


        // ACCOUNT
        this.d[targets.ACCOUNT] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.ACCOUNT].attr["email"]      =  {"isKey": false,   "set": true,  "update": true,  "type": this.dt.STR.def };
            this.d[targets.ACCOUNT].attr["name"]       =  {"isKey": false,   "set": true,  "update": true,  "type": this.dt.STR.def };
            this.d[targets.ACCOUNT].attr["role"]       =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.STR.role };
            this.d[targets.ACCOUNT].attr["surname"]    =  {"isKey": false,   "set": true,  "update": true,  "type": this.dt.STR.def };
            this.d[targets.ACCOUNT].attr["username"]   =  {"isKey": true,    "set": true,  "update": false,  "type": this.dt.STR.def };
            this.d[targets.ACCOUNT].attr["password"]   =  {"isKey": false,   "set": true,  "update": true,  "type": this.dt.STR.def };

            this.d[targets.ACCOUNT].ff.TBL = ff_Account_Table;
//            this.d[targets.ACCOUNT].ff.GET = ff_Account_Get;
//            this.d[targets.ACCOUNT].ff.SET = ff_Account_Set;
//            this.d[targets.ACCOUNT].ff.UPD = ff_Account_Update;


        // UE   // TODO EMP_if: controllare
        this.d[targets.UE] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.UE].attr["imsi"]    =  {"isKey": true,    "set": false,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.UE].attr["rnti"]    =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.UE].attr["plmn_id"] =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.plmnid};
            this.d[targets.UE].attr["cell"]    =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.UE].attr["vbs"]     =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.UE].attr["state"]   =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.state };    // "active" - "ho_in_progress_removing" - "ho_in_progress_adding"

            this.d[targets.UE].ff.TBL = ff_Ue_Table;
//            this.d[targets.UE].ff.GET = ff_Ue_Get;
//            this.d[targets.UE].ff.SET = ff_Ue_Set;
//            this.d[targets.UE].ff.UPD = ff_Ue_Update;


        // LVAP  // TODO EMP_if: controllare
        this.d[targets.LVAP] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.LVAP].attr["addr"]          =  {"isKey": true,    "set": false,  "update": false,  "type": this.dt.STR.mac};
            this.d[targets.LVAP].attr["assoc_id"]      =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr};
            this.d[targets.LVAP].attr["association_state"]     =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.bool};
            this.d[targets.LVAP].attr["authentication_state"]  =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.bool};
            this.d[targets.LVAP].attr["blocks"]        =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.a };
            this.d[targets.LVAP].attr["bssid"]         =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.mac};
            this.d[targets.LVAP].attr["encap"]         =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.mac};
            this.d[targets.LVAP].attr["networks"]       =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.OBJ.networks };
            this.d[targets.LVAP].attr["pending"]       =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.a };
            this.d[targets.LVAP].attr["ssid"]          =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.def};
            this.d[targets.LVAP].attr["state"]         =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.state };    // "running" - "spawning" - "removing"
            this.d[targets.LVAP].attr["supported_band"]=  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr};
            this.d[targets.LVAP].attr["wtp"]           =  {"isKey": false,   "set": false,  "update": true,  "type": this.dt.OBJ.wtp};

            this.d[targets.LVAP].ff.TBL = ff_Lvap_Table;
//            this.d[targets.LVAP].ff.GET = ff_Lvap_Get;
//            this.d[targets.LVAP].ff.SET = ff_Lvap_Set;
//            this.d[targets.LVAP].ff.UPD = ff_Lvap_Update;


        // LVNF
        this.d[targets.LVNF] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.LVNF].attr["lvnf_id"]   =  {"isKey": true,   "set": false,  "update": false,  "type": this.dt.STR.uuid};
            this.d[targets.LVNF].attr["image"]     =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.OBJ.img};
            this.d[targets.LVNF].attr["tenant_id"] =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.uuid};
            this.d[targets.LVNF].attr["cpp"]       =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.OBJ.cpp};
            this.d[targets.LVNF].attr["state"]     =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.state };  // "spawning" - "running" - "stopping" - "stopped" - "migrating_stop" - "migrating_start"
            this.d[targets.LVNF].attr["returncode"]=  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr};
            this.d[targets.LVNF].attr["ports"]     =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d };

            this.d[targets.LVNF].ff.TBL = ff_Lvnf_Table;
//            this.d[targets.LVNF].ff.GET = ff_Lvnf_Get;
//            this.d[targets.LVNF].ff.SET = ff_Lvnf_Set;
//            this.d[targets.LVNF].ff.UPD = ff_Lvnf_Update;


        // UE_MEASUREMENT  // TODO EMP_if: da controllare
        this.d[targets.UE_MEASUREMENT] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.UE_MEASUREMENT].attr["id"]             =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr};
            this.d[targets.UE_MEASUREMENT].attr["module_type"]    =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.unknwn};
            this.d[targets.UE_MEASUREMENT].attr["tenant_id"]      =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.uuid};
            this.d[targets.UE_MEASUREMENT].attr["callback"]       =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.unknwn};
            this.d[targets.UE_MEASUREMENT].attr["imsi"]           =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.UE_MEASUREMENT].attr["measurements"]   =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.UE_MEASUREMENT].attr["results"]        =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d };

//            this.d[targets.UE_MEASUREMENT].ff.TBL = ff_Rrc_Table;
//            this.d[targets.UE_MEASUREMENT].ff.GET = ff_Rrc_Get;
//            this.d[targets.UE_MEASUREMENT].ff.SET = ff_Rrc_Set;
//            this.d[targets.UE_MEASUREMENT].ff.UPD = ff_Rrc_Update;


        // ACL
        this.d[targets.ACL] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.ACL].attr["addr"]     =  {"isKey": true,    "set": true,  "update": false,  "type": this.dt.STR.mac};
            this.d[targets.ACL].attr["label"]    =  {"isKey": false,   "set": true,  "update": false,  "type": this.dt.STR.def};

            this.d[targets.ACL].ff.TBL = ff_Acl_Table;
//            this.d[targets.ACL].ff.GET = ff_Acl_Get;
//            this.d[targets.ACL].ff.SET = ff_Acl_Set;
//            this.d[targets.ACL].ff.UPD = ff_Acl_Update;

// OTHER ------------------------------------------------------------------------

        // DATAPATH
        this.d["datapath"] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d["datapath"].attr["dpid"]         =  {"isKey": true,    "set": false,  "update": false,  "type": this.dt.STR.dpid};
            this.d["datapath"].attr["hosts"]        =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d};
            this.d["datapath"].attr["ip_addr"]      =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.ip_addr};
            this.d["datapath"].attr["network_ports"]    =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d};

        // NETWORK PORTS
        this.d["network_ports"] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d["network_ports"].attr["dpid"]         =  {"isKey": false,    "set": false,  "update": false,  "type": this.dt.STR.dpid};
            this.d["network_ports"].attr["hwaddr"]        =  {"isKey": true,   "set": false,  "update": false,  "type": this.dt.STR.mac};
            this.d["network_ports"].attr["iface"]      =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.def};
            this.d["network_ports"].attr["neighbour"]    =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.def};
            this.d["network_ports"].attr["port_id"]    =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr};

        // SUPPORTS
        this.d["supports"] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d["supports"].attr["addr"]         =  {"isKey": false,    "set": false,  "update": false,  "type": this.dt.STR.mac};
            this.d["supports"].attr["band"]         =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.STR.band};
            this.d["supports"].attr["channel"]      =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.NUM.intgr};
            this.d["supports"].attr["ht_supports"]  =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.a};
            this.d["supports"].attr["hwaddr"]       =  {"isKey": true,   "set": false,  "update": false,  "type": this.dt.STR.mac};
            this.d["supports"].attr["ncqm"]         =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d};
            this.d["supports"].attr["supports"]     =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.a};
            this.d["supports"].attr["traffic_rule_queues"]    =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d};
            this.d["supports"].attr["tx_policies"]  =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d};
            this.d["supports"].attr["ucqm"]    =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d};
            this.d["supports"].attr["wifi_stats"]   =  {"isKey": false,   "set": false,  "update": false,  "type": this.dt.LIST.d};

        this.d["blocks"] = this.d["supports"];

    }
}