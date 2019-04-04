class EmpDescriptor{

    constructor(){

        this.dt = {};   // datatypes
        this.dt.STR = {     "unknwn": {"type_id": "unknown", "validation": null, }, // unknown data type
                            "work": {"type_id": "work", "validation": null, }, // internal working dt - are not shown
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
                            "band": {"type_id": "band", "validation": null, },
//                          "url": {"type_id": "url", "validation": null, },
                            "tmsi": {"type_id": "tmsi", "validation": null, },
                            "tenantid": {"type_id": "tenantid", "validation": null, },
                            "ueid": {"type_id": "ueid", "validation": null, },
                         };
        this.dt.NUM = {  "intgr": {"type_id": "integer", "validation": null, },
                         "bool": {"type_id": "boolean", "validation": null, },
                         };
        this.dt.LIST = { "a": {"type_id": "arry", "validation": null, },
                            "d":  {"type_id": "dict", "validation": null, },
                          };
        this.dt.OBJ = {  "lvap": {"type_id": "lvap", "validation": null, },
                            "wtp":  {"type_id": "wtp", "validation": null, },
                            "cpp":  {"type_id": "cpp", "validation": null, },
                            "img":  {"type_id": "image", "validation": null, },
                            "datapath":  {"type_id": "datapath", "validation": null, },
                            "connection":  {"type_id": "connection", "validation": null, },
                            "ssids":  {"type_id": "ssids", "validation": null, },
                            "networks":  {"type_id": "networks", "validation": null, },
                            "dscp":  {"type_id": "dscp", "validation": null, },
                            "match":  {"type_id": "match", "validation": null, },
                            "tID":  {"type_id": "tID", "validation": null, },  // selector version!
                            "slice":  {"type_id": "slice", "validation": null, }, 
                            "vbs":  {"type_id": "vbs", "validation": null, },  
                            "uemeasurements":  {"type_id": "ue_measurements", "validation": null, },  
                            "cell":  {"type_id": "cell", "validation": null, },  
                          };

        this.add = {
            "M" : "mandatory",   // the value is mandatory for add operation
            "O" : "optional",    // the value is optional for add operation
            "E" : "empty",       // the value is not used for add operation
        }

        // Tenant
        this.d = {};
        var targets = __QE.targets;

        this.d[targets.TENANT] = { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.TENANT].attr["bssid_type"]    =  {"name": "BSSIS type", "isKey": false,   "add": this.add.M,  "update": false,  "type": this.dt.STR.bssid_type };
            this.d[targets.TENANT].attr["tenant_id"]     =  {"name": "Tenant ID", "isKey": true,    "add": this.add.E,  "update": false,  "type": this.dt.STR.uuid};
            this.d[targets.TENANT].attr["tenant_name"]   =  {"name": "Name", "isKey": false,   "add": this.add.M,  "update": false,  "type": this.dt.STR.def };
            this.d[targets.TENANT].attr["components"]    =  {"name": "Components", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["cpps"]          =  {"name": "CPPs", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["desc"]          =  {"name": "Description", "isKey": false,   "add": this.add.M,  "update": false,  "type": this.dt.STR.def };
            this.d[targets.TENANT].attr["endpoints"]    =  {"name": "Endpoints", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["lvaps"]         =  {"name": "LVAPs", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["lvnfs"]         =  {"name": "LVNFs", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["owner"]         =  {"name": "Owner", "isKey": false,   "add": this.add.M,  "update": false,  "type": this.dt.STR.owner };
            this.d[targets.TENANT].attr["plmn_id"]       =  {"name": "PLMN id", "isKey": false,   "add": this.add.O,  "update": false,  "type": this.dt.STR.plmnid };
            this.d[targets.TENANT].attr["slices"] =  {"name": "Network Slices", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["traffic_rules"] =  {"name": "Traffic Rules", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["ues"]           =  {"name": "UEs", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["vbses"]         =  {"name": "VBSes", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.TENANT].attr["wtps"]          =  {"name": "WTPs", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d };

            this.d[targets.TENANT].ff.TBL = ff_Tenant_Table;
//            this.d[targets.TENANT].ff.GET = ff_Tenant_Get;
//            this.d[targets.TENANT].ff.SET = ff_Tenant_Set;
//            this.d[targets.TENANT].ff.UPD = ff_Tenant_Update;


        // WTP
        this.d[targets.WTP] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
        this.d["wtp"] = this.d[targets.WTP];
            this.d[targets.WTP].attr["label"]        =  {"name": "Name", "isKey": false,   "add": this.add.M,  "update": false,  "type": this.dt.STR.def };
            this.d[targets.WTP].attr["addr"]         =  {"name": "MAC Address", "isKey": true,    "add": this.add.M,  "update": false,  "type": this.dt.STR.mac };
            this.d[targets.WTP].attr["connection"]   =  {"name": "Connection", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.connection  };
            this.d[targets.WTP].attr["datapath"]     =  {"name": "Datapath", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.datapath };
            this.d[targets.WTP].attr["last_seen"]    =  {"name": "Last Seen", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.WTP].attr["last_seen_ts"] =  {"name": "Last Seen (ts)", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.data };
            this.d[targets.WTP].attr["period"]       =  {"name": "Period", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.WTP].attr["state"]        =  {"name": "State", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.state  };  // "disconnected" - "connected" - "online"
            this.d[targets.WTP].attr["supports"]     =  {"name": "Supports", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.a };

            this.d[targets.WTP].ff.TBL = ff_Wtp_Table;
//            this.d[targets.WTP].ff.GET = ff_Wtp_Get;
//            this.d[targets.WTP].ff.SET = ff_Wtp_Set;
//            this.d[targets.WTP].ff.UPD = ff_Wtp_Update;


        // CPP
        this.d[targets.CPP] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.CPP].attr["label"]        =  {"name": "Name", "isKey": false,   "add": this.add.M,  "update": false,  "type": this.dt.STR.def };
            this.d[targets.CPP].attr["addr"]         =  {"name": "MAC Address", "isKey": true,    "add": this.add.M,  "update": false,  "type": this.dt.STR.mac };
            this.d[targets.CPP].attr["connection"]   =  {"name": "Connection", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.connection };
            this.d[targets.CPP].attr["datapath"]     =  {"name": "Datapath", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.datapath };
            this.d[targets.CPP].attr["last_seen"]    =  {"name": "Last Seen", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.CPP].attr["last_seen_ts"] =  {"name": "Last Seen (ts)", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.data };
            this.d[targets.CPP].attr["period"]       =  {"name": "Period", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.CPP].attr["state"]        =  {"name": "State", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.state  };  // "disconnected" - "connected" - "online"

            this.d[targets.CPP].ff.TBL = ff_Cpp_Table;
//            this.d[targets.CPP].ff.GET = ff_Cpp_Get;
//            this.d[targets.CPP].ff.SET = ff_Cpp_Set;
//            this.d[targets.CPP].ff.UPD = ff_Cpp_Update;


        // VBS
        this.d[targets.VBS] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
        this.d["vbs"] = this.d[targets.VBS];
            this.d[targets.VBS].attr["label"]       =  {"name": "Name", "isKey": false,   "add": this.add.M,  "update": false,  "type": this.dt.STR.def };
            this.d[targets.VBS].attr["addr"]        =  {"name": "MAC Address", "isKey": true,    "add": this.add.M,  "update": false,  "type": this.dt.STR.mac };
            this.d[targets.VBS].attr["cells"]       =  {"name": "Cells", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d  };
            this.d[targets.VBS].attr["connection"]  =  {"name": "Connection", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.connection };
            this.d[targets.VBS].attr["datapath"]    =  {"name": "Datapath", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.datapath };
            this.d[targets.VBS].attr["last_seen"]   =  {"name": "Last Seen", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.VBS].attr["last_seen_ts"]=  {"name": "Last Seen (ts)", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.data };
            this.d[targets.VBS].attr["period"]      =  {"name": "Period", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.VBS].attr["state"]       =  {"name": "State", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.state  };  // "disconnected" - "connected" - "online"

            this.d[targets.VBS].ff.TBL = ff_Vbs_Table;
//            this.d[targets.VBS].ff.GET = ff_Vbs_Get;
//            this.d[targets.VBS].ff.SET = ff_Vbs_Set;
//            this.d[targets.VBS].ff.UPD = ff_Vbs_Update;


        // COMPONENT ACTIVE    // Gli attributi cambiano in base al servizio/componente, come fare???
        this.d[targets.COMPONENT] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.COMPONENT].attr["name"]     =  {"name": "Name", "isKey": true,    "add": this.add.M,  "update": false,  "type": this.dt.STR.def};
            this.d[targets.COMPONENT].attr["active"]   =  {"name": "Status", "isKey": false,    "add": this.add.E,  "update": false,  "type": this.dt.NUM.bool};
            this.d[targets.COMPONENT].attr["desc"]     =  {"name": "Description", "isKey": false,    "add": this.add.E,  "update": false,  "type": this.dt.STR.def};

            this.d[targets.COMPONENT].ff.TBL = ff_Component_Table;
//            this.d[targets.COMPONENT].ff.GET = ff_Component_Get;
//            this.d[targets.COMPONENT].ff.SET = ff_Component_Set;
//            this.d[targets.COMPONENT].ff.UPD = ff_Component_Update;


        // ACCOUNT
        this.d[targets.ACCOUNT] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.ACCOUNT].attr["username"]   =  {"name": "Username", "isKey": true,    "add": this.add.M,  "update": false,  "type": this.dt.STR.def };
            this.d[targets.ACCOUNT].attr["name"]       =  {"name": "Name", "isKey": false,   "add": this.add.M,  "update": true,  "type": this.dt.STR.def };
            this.d[targets.ACCOUNT].attr["surname"]    =  {"name": "Surname", "isKey": false,   "add": this.add.M,  "update": true,  "type": this.dt.STR.def };
            this.d[targets.ACCOUNT].attr["role"]       =  {"name": "Role", "isKey": false,   "add": this.add.M,  "update": false,  "type": this.dt.STR.role };
            this.d[targets.ACCOUNT].attr["email"]      =  {"name": "Mail", "isKey": false,   "add": this.add.M,  "update": true,  "type": this.dt.STR.def };
            this.d[targets.ACCOUNT].attr["password"]   =  {"name": "Password", "isKey": false,   "add": this.add.M,  "update": true,  "type": this.dt.STR.def };
            this.d[targets.ACCOUNT].attr["new_password"]   =  {"name": "New Password", "isKey": false,   "add": this.add.E,  "update": true,  "type": this.dt.STR.def };
            this.d[targets.ACCOUNT].attr["new_password_confirm"]   =  {"name": "Confirm Password", "isKey": false,   "add": this.add.E,  "update": true,  "type": this.dt.STR.def };

            this.d[targets.ACCOUNT].ff.TBL = ff_Account_Table;
//            this.d[targets.ACCOUNT].ff.GET = ff_Account_Get;
//            this.d[targets.ACCOUNT].ff.SET = ff_Account_Set;
//            this.d[targets.ACCOUNT].ff.UPD = ff_Account_Update;


        // UE   // TODO EMP_if: controllare
        this.d[targets.UE] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.UE].attr["imsi"]    =  {"name": "IMSI", "isKey": false,    "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.UE].attr["rnti"]    =  {"name": "RNTI", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.UE].attr["plmn_id"] =  {"name": "PLMN ID", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.plmnid};
            this.d[targets.UE].attr["cell"]    =  {"name": "Cell", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.cell };
            this.d[targets.UE].attr["vbs"]     =  {"name": "VBS", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.vbs };
            this.d[targets.UE].attr["state"]   =  {"name": "State", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.state };    // "active" - "ho_in_progress_removing" - "ho_in_progress_adding"
            
            this.d[targets.UE].attr["slice"]   =  {"name": "Slice", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.slice };
            this.d[targets.UE].attr["ue_id"]   =  {"name": "UE ID", "isKey": true,   "add": this.add.E,  "update": false,  "type": this.dt.STR.ueid };
            this.d[targets.UE].attr["tmsi"]   =  {"name": "TMSI", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.tmsi };
            this.d[targets.UE].attr["tenant_id"]   =  {"name": "tenant ID", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.tenantid };
            this.d[targets.UE].attr["ue_measurements"]   =  {"name": "Measurements", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.uemeasurements };

            this.d[targets.UE].ff.TBL = ff_Ue_Table;
//            this.d[targets.UE].ff.GET = ff_Ue_Get;
//            this.d[targets.UE].ff.SET = ff_Ue_Set;
//            this.d[targets.UE].ff.UPD = ff_Ue_Update;


        // LVAP  // TODO EMP_if: controllare
        this.d[targets.LVAP] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.LVAP].attr["addr"]                   =  {"name": "MAC Address", "isKey": true,    "add": this.add.E,  "update": false,  "type": this.dt.STR.mac};
            this.d[targets.LVAP].attr["assoc_id"]               =  {"name": "Association ID", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr};
            this.d[targets.LVAP].attr["association_state"]      =  {"name": "Association State", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.bool};
            this.d[targets.LVAP].attr["authentication_state"]   =  {"name": "Authentication State", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.bool};
            this.d[targets.LVAP].attr["blocks"]                 =  {"name": "Blocks", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.a };
            this.d[targets.LVAP].attr["bssid"]                  =  {"name": "BSSID", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.mac};
            this.d[targets.LVAP].attr["encap"]                  =  {"name": "Encapsulation", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.mac};
            this.d[targets.LVAP].attr["networks"]               =  {"name": "Networks", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.networks };
            this.d[targets.LVAP].attr["pending"]                =  {"name": "Pending", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.work }; // Runtime working attribute
            this.d[targets.LVAP].attr["ssid"]                   =  {"name": "SSID", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.def};
            this.d[targets.LVAP].attr["state"]                  =  {"name": "State", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.state };    // "running" - "spawning" - "removing"
            this.d[targets.LVAP].attr["supported_band"]         =  {"name": "Supported Band", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr};
            this.d[targets.LVAP].attr["wtp"]                    =  {"name": "WTP", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.wtp};

            this.d[targets.LVAP].ff.TBL = ff_Lvap_Table;
//            this.d[targets.LVAP].ff.GET = ff_Lvap_Get;
//            this.d[targets.LVAP].ff.SET = ff_Lvap_Set;
//            this.d[targets.LVAP].ff.UPD = ff_Lvap_Update;


        // LVNF
        this.d[targets.LVNF] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.LVNF].attr["lvnf_id"]   =  {"name": "LVNF ID", "isKey": true,   "add": this.add.E,  "update": false,  "type": this.dt.STR.uuid};
            this.d[targets.LVNF].attr["image"]     =  {"name": "Image", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.img};
            this.d[targets.LVNF].attr["tenant_id"] =  {"name": "Tenant ID", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.uuid};
            this.d[targets.LVNF].attr["cpp"]       =  {"name": "CPP", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.OBJ.cpp};
            this.d[targets.LVNF].attr["state"]     =  {"name": "State", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.state };  // "spawning" - "running" - "stopping" - "stopped" - "migrating_stop" - "migrating_start"
            this.d[targets.LVNF].attr["returncode"]=  {"name": "Return code", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr};
            this.d[targets.LVNF].attr["ports"]     =  {"name": "Ports", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d };

            this.d[targets.LVNF].ff.TBL = ff_Lvnf_Table;
//            this.d[targets.LVNF].ff.GET = ff_Lvnf_Get;
//            this.d[targets.LVNF].ff.SET = ff_Lvnf_Set;
//            this.d[targets.LVNF].ff.UPD = ff_Lvnf_Update;


        // UE_MEASUREMENT  // TODO EMP_if: da controllare
        this.d[targets.UE_MEASUREMENT] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.UE_MEASUREMENT].attr["id"]             =  {"name": "ID", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr};
            this.d[targets.UE_MEASUREMENT].attr["module_type"]    =  {"name": "Module Type", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.unknwn};
            this.d[targets.UE_MEASUREMENT].attr["tenant_id"]      =  {"name": "Tenant ID", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.uuid};
            this.d[targets.UE_MEASUREMENT].attr["callback"]       =  {"name": "Callback", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.unknwn};
            this.d[targets.UE_MEASUREMENT].attr["imsi"]           =  {"name": "IMSI", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr };
            this.d[targets.UE_MEASUREMENT].attr["measurements"]   =  {"name": "Measurements", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d };
            this.d[targets.UE_MEASUREMENT].attr["results"]        =  {"name": "Results", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d };

//            this.d[targets.UE_MEASUREMENT].ff.TBL = ff_Rrc_Table;
//            this.d[targets.UE_MEASUREMENT].ff.GET = ff_Rrc_Get;
//            this.d[targets.UE_MEASUREMENT].ff.SET = ff_Rrc_Set;
//            this.d[targets.UE_MEASUREMENT].ff.UPD = ff_Rrc_Update;


        // ACL
        this.d[targets.ACL] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.ACL].attr["label"]    =  {"name": "Name", "isKey": false,   "add": this.add.M,  "update": false,  "type": this.dt.STR.def};
            this.d[targets.ACL].attr["addr"]     =  {"name": "MAC address", "isKey": true,    "add": this.add.M,  "update": false,  "type": this.dt.STR.mac};

            this.d[targets.ACL].ff.TBL = ff_Acl_Table;
//            this.d[targets.ACL].ff.GET = ff_Acl_Get;
//            this.d[targets.ACL].ff.SET = ff_Acl_Set;
//            this.d[targets.ACL].ff.UPD = ff_Acl_Update;


        // TRAFFIC RULE
        this.d[targets.TR] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.TR].attr["dscp"]     =  {"name": "Tag", "isKey": false,    "add": this.add.M,  "update": false,  "type": this.dt.OBJ.dscp};
            this.d[targets.TR].attr["tenant_id"]    =  {"name": "Tenant ID", "isKey": false,   "add": this.add.M,  "update": false,  "type": this.dt.OBJ.tID};
            this.d[targets.TR].attr["label"]    =  {"name": "Description", "isKey": false,   "add": this.add.M,  "update": false,  "type": this.dt.STR.def};
            this.d[targets.TR].attr["match"]    =  {"name": "Match rules", "isKey": true,   "add": this.add.M,  "update": false,  "type": this.dt.OBJ.match};
            this.d[targets.TR].attr["priority"] =  {"name": "Priority", "isKey": false,   "add": this.add.O,  "update": false,  "type": this.dt.NUM.intgr};

            this.d[targets.TR].ff.TBL = ff_TR_Table;
//            this.d[targets.TR].ff.GET = ff_TR_Get;
//            this.d[targets.TR].ff.SET = ff_TR_Set;
//            this.d[targets.TR].ff.UPD = ff_TR_Update;


        // SLICE
        this.d[targets.SLICE] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d[targets.SLICE].attr["tenant_id"] =  {"name": "Tenant ID", "isKey": true,    "add": this.add.E,  "update": false,  "type": this.dt.STR.def};
            this.d[targets.SLICE].attr["dscp"]    =  {"name": "Tag", "isKey": true,   "add": this.add.E,  "update": false,  "type": this.dt.STR.def};
            this.d[targets.SLICE].attr["wifi"]    =  {"name": "Wi-Fi", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d};
            this.d[targets.SLICE].attr["lte"]     =  {"name": "LTE", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d};

            this.d[targets.SLICE].ff.TBL = ff_Slice_Table;
//            this.d[targets.SLICE].ff.GET = ff_Slice_Get;
//            this.d[targets.SLICE].ff.SET = ff_Slice_Set;
//            this.d[targets.SLICE].ff.UPD = ff_Slice_Update;



// OTHER ------------------------------------------------------------------------

        // DATAPATH
        this.d["datapath"] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d["datapath"].attr["dpid"]          =  {"name": "DPID", "isKey": true,    "add": this.add.E,  "update": false,  "type": this.dt.STR.dpid};
            this.d["datapath"].attr["hosts"]         =  {"name": "Hosts", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d};
            this.d["datapath"].attr["ip_addr"]       =  {"name": "IP Address", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.ip_addr};
            this.d["datapath"].attr["network_ports"] =  {"name": "Network Ports", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d};

        // NETWORK PORTS
        this.d["network_ports"] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d["network_ports"].attr["dpid"]      =  {"name": "DPID", "isKey": false,    "add": this.add.E,  "update": false,  "type": this.dt.STR.dpid};
            this.d["network_ports"].attr["hwaddr"]    =  {"name": "Hardware Address", "isKey": true,   "add": this.add.E,  "update": false,  "type": this.dt.STR.mac};
            this.d["network_ports"].attr["iface"]     =  {"name": "Interface", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.def};
            this.d["network_ports"].attr["neighbour"] =  {"name": "Neighbour", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.def};
            this.d["network_ports"].attr["port_id"]   =  {"name": "Port ID", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr};

        // SUPPORTS
        this.d["supports"] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d["supports"].attr["addr"]                 =  {"name": "MAC Address", "isKey": false,    "add": this.add.E,  "update": false,  "type": this.dt.STR.mac};
            this.d["supports"].attr["band"]                 =  {"name": "Band", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.band};
            this.d["supports"].attr["channel"]              =  {"name": "Channel", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr};
            this.d["supports"].attr["ht_supports"]          =  {"name": "HT Supports", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.work};
            this.d["supports"].attr["hwaddr"]               =  {"name": "Hardware Address", "isKey": true,   "add": this.add.E,  "update": false,  "type": this.dt.STR.mac};
            this.d["supports"].attr["ncqm"]                 =  {"name": "NCQM", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.unknwn};
            this.d["supports"].attr["supports"]             =  {"name": "Supports", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.work};
            this.d["supports"].attr["tx_policies"]          =  {"name": "TX Policies", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d};
            this.d["supports"].attr["ucqm"]                 =  {"name": "UCQM", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.unknwn};
            this.d["supports"].attr["wifi_stats"]           =  {"name": "Wi-Fi Statistic", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.LIST.d};

        this.d["blocks"] = this.d["supports"];

        // CELLS

        this.d["cells"] =  { "attr" : {},    // attributes
                        "ff" : {},      // format functions
                        };
            this.d["cells"].attr["addr"]                =  {"name": "Address", "isKey": false,    "add": this.add.E,  "update": false,  "type": this.dt.STR.mac};
            this.d["cells"].attr["max_ues"]             =  {"name": "Max UEs", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.STR.def};
            this.d["cells"].attr["pci"]                 =  {"name": "PCI", "isKey": true,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr};
            this.d["cells"].attr["dl_bandwidth"]        =  {"name": "DL Bandwidth", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr};
            this.d["cells"].attr["dl_earfcn"]           =  {"name": "DL EARFCN", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr};
            this.d["cells"].attr["ul_bandwidth"]        =  {"name": "UL Bandwidth", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr};
            this.d["cells"].attr["ul_earfcn"]           =  {"name": "UL EARFCN", "isKey": false,   "add": this.add.E,  "update": false,  "type": this.dt.NUM.intgr};


    }
}
