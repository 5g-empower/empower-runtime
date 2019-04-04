class EmpCache{

    constructor(){

        this.hb = __HB;
        this.qe = __QE;
        this.desc = __DESC;

        this.DTlist = {};
        this.BBlist = {};

        this.c = {};
        for( var obj in this.qe.targets ){
            this.c[ this.qe.targets[obj] ] = [];
        }

    }

    update(){
        var args = arguments[0];
        for( var tag in args ){
            var results = null;
            if( tag === "accounts" ){
                var tmp = [];
                for( var user in args[tag] ){
                    tmp.push( args[tag][user] )
                }
                results = tmp;
            }
            else if( tag === "components" ){
                var tmp = [];
                for( var user in args[tag] ){
                    tmp.push( args[tag][user] )
                }
                results = tmp;
            }
            // else if (tag == "ues"){
			// 	results = test_ues
			// 	console.log("Added fake test_ues");
			// }
			// else if (tag == "lvaps"){
			// 	results = test_lvaps;
			// 	console.log("Added fake test_lvaps");
			// }
			// else if (tag === "vbses"){
			// 	results = args[tag];
			// 	results.push(test_vbs);
			// 	console.log("Added fake test_vbs");
			// }
            else{
                results = args[tag]
            }
//          console.log(tag, results );
            this.updateCache(tag, results);
        }

    }

    updateCache(tag, results){
        this.c[tag] = results;

        this.updateBB(tag);
        this.updateDT(tag);
    }

    updateDT(tag){
        if( this.DTlist[tag] ){
            var dt = this.DTlist[ tag ];
            var datatable = $( "#"+ dt.getID() ).DataTable();

            var DTdata = dt.ceDtBody(tag);

            datatable.clear();
            datatable.rows.add(DTdata);
            datatable.draw();
            }
        else{
            console.log("EmpCache.updateDT: DTlist[" + tag + "] not exists.")
        }
    }

    updateBB(tag){

        var n = this.checkCardinality(tag);
        var obj = this.hb.mapName2Obj(tag);
//        console.log( obj, this.BBlist[obj] )
        if( this.BBlist[obj] ){
            $( "#" + this.BBlist[obj] ).text(n)
        }
        else{
            console.log("EmpCache.updateBB: BBlist[" + obj + "] not exists.")
        }
    }

    checkCardinality(tag){
        var n = 0;
        switch(tag){
            case this.qe.targets.WTP:
            case this.qe.targets.CPP:
            case this.qe.targets.VBS:
                this.updateBB("devices");
                n = this.c[tag].length;
                break;
            case "devices":
                n = this.c[this.qe.targets.WTP].length + this.c[this.qe.targets.CPP].length + this.c[this.qe.targets.VBS].length ;
                break;
            case this.qe.targets.LVAP:
            case this.qe.targets.UE:
                this.updateBB("clients");
                n = this.c[tag].length;
                break;
            case "clients":
                n = this.c[this.qe.targets.LVAP].length + this.c[this.qe.targets.UE].length;
                break;
            default:
                n = this.c[tag].length;
        }
//        console.log(tag,n);
        return n;

    }

}




// // TO BE DELETED

// test_vbs = {
// 	"addr": "00:00:00:00:BA:C0",
// 	"cells": {
// 		"3": {
// 			"addr": "00:00:00:00:BA:C0",
// 			"cell_measurements": {},
// 			"dl_bandwidth": 25,
// 			"dl_earfcn": 3400,
// 			"features": {
// 				"cell_measure": 1,
// 				"handover": 0,
// 				"ue_measure": 1,
// 				"ue_report": 1
// 			},
// 			"max_ues": 2,
// 			"pci": 3,
// 			"ran_features": {
// 				"layer1": {},
// 				"layer2": {
// 					"prb_slicing": 0,
// 					"rbg_slicing": 1
// 				},
// 				"layer3": {},
// 				"mac_sched": 1,
// 				"max_slices": 8
// 			},
// 			"ue_measurements": {},
// 			"ul_bandwidth": 25,
// 			"ul_earfcn": 21400
// 		}
// 	},
// 	"connection": [
// 		"10.244.5.177",
// 		41524
// 	],
// 	"datapath": null,
// 	"label": "debug_vbs",
// 	"last_seen": 751,
// 	"last_seen_ts": "2019-02-12T15:29:49.872198Z",
// 	"period": 2000,
// 	"state": "online"
// };

// test_ues= [
// 	{
// 		"cell": {
// 			"addr": "00:00:00:00:01:9B",
// 			"cell_measurements": {},
// 			"dl_bandwidth": 25,
// 			"dl_earfcn": 3400,
// 			"features": {
// 				"cell_measure": 1,
// 				"handover": 0,
// 				"ue_measure": 1,
// 				"ue_report": 1
// 			},
// 			"max_ues": 2,
// 			"pci": 3,
// 			"ran_features": {
// 				"layer1": {},
// 				"layer2": {
// 					"prb_slicing": 0,
// 					"rbg_slicing": 1
// 				},
// 				"layer3": {},
// 				"mac_sched": 1,
// 				"max_slices": 8
// 			},
// 			"ue_measurements": {},
// 			"ul_bandwidth": 25,
// 			"ul_earfcn": 21400
// 		},
// 		"imsi": 222930000000001,
// 		"plmn_id": "222f93",
// 		"rnti": 79,
// 		"state": "running",
// 		"tenant_id": "e1cc2da1-3012-48b9-946d-e8ea9848a60d",
// 		"tmsi": 1,
// 		"ue_id": "8c99af0f-bedb-4cb1-9f19-ef39e2b7cc29",
// 		"ue_measurements": {},
// 		"vbs": {
// 			"addr": "00:00:00:00:01:9B",
// 			"cells": {
// 				"3": {
// 					"addr": "00:00:00:00:01:9B",
// 					"cell_measurements": {},
// 					"dl_bandwidth": 25,
// 					"dl_earfcn": 3400,
// 					"features": {
// 						"cell_measure": 1,
// 						"handover": 0,
// 						"ue_measure": 1,
// 						"ue_report": 1
// 					},
// 					"max_ues": 2,
// 					"pci": 3,
// 					"ran_features": {
// 						"layer1": {},
// 						"layer2": {
// 							"prb_slicing": 0,
// 							"rbg_slicing": 1
// 						},
// 						"layer3": {},
// 						"mac_sched": 1,
// 						"max_slices": 8
// 					},
// 					"ue_measurements": {},
// 					"ul_bandwidth": 25,
// 					"ul_earfcn": 21400
// 				}
// 			},
// 			"connection": ["10.244.5.177", 41524],
// 			"datapath": null,
// 			"label": "myvbs",
// 			"last_seen": 751,
// 			"last_seen_ts": "2019-02-12T15:29:49.872198Z",
// 			"period": 2000,
// 			"state": "online"
// 		}
// 	}, {
// 		"cell": {
// 			"addr": "00:00:00:00:01:9B",
// 			"cell_measurements": {},
// 			"dl_bandwidth": 25,
// 			"dl_earfcn": 3400,
// 			"features": {
// 				"cell_measure": 1,
// 				"handover": 0,
// 				"ue_measure": 1,
// 				"ue_report": 1
// 			},
// 			"max_ues": 2,
// 			"pci": 3,
// 			"ran_features": {
// 				"layer1": {},
// 				"layer2": {
// 					"prb_slicing": 0,
// 					"rbg_slicing": 1
// 				},
// 				"layer3": {},
// 				"mac_sched": 1,
// 				"max_slices": 8
// 			},
// 			"ue_measurements": {},
// 			"ul_bandwidth": 25,
// 			"ul_earfcn": 21400
// 		},
// 		"imsi": 222930000000001,
// 		"plmn_id": "222f93",
// 		"rnti": 82,
// 		"state": "running",
// 		"tenant_id": "e1cc2da1-3012-48b9-946d-e8ea9848a60d",
// 		"tmsi": 1,
// 		"ue_id": "91cb5379-7768-4635-9729-8917e9c95fda",
// 		"ue_measurements": {},
// 		"vbs": {
// 			"addr": "00:00:00:00:01:9B",
// 			"cells": {
// 				"3": {
// 					"addr": "00:00:00:00:01:9B",
// 					"cell_measurements": {},
// 					"dl_bandwidth": 25,
// 					"dl_earfcn": 3400,
// 					"features": {
// 						"cell_measure": 1,
// 						"handover": 0,
// 						"ue_measure": 1,
// 						"ue_report": 1
// 					},
// 					"max_ues": 2,
// 					"pci": 3,
// 					"ran_features": {
// 						"layer1": {},
// 						"layer2": {
// 							"prb_slicing": 0,
// 							"rbg_slicing": 1
// 						},
// 						"layer3": {},
// 						"mac_sched": 1,
// 						"max_slices": 8
// 					},
// 					"ue_measurements": {},
// 					"ul_bandwidth": 25,
// 					"ul_earfcn": 21400
// 				}
// 			},
// 			"connection": ["10.244.5.177", 41524],
// 			"datapath": null,
// 			"label": "myvbs",
// 			"last_seen": 751,
// 			"last_seen_ts": "2019-02-12T15:29:49.872198Z",
// 			"period": 2000,
// 			"state": "online"
// 		}
// 	}
// ]


// test_lvaps= [{
// 	"addr": "00:24:D7:7B:B0:7C",
// 	"assoc_id": 746,
// 	"association_state": true,
// 	"authentication_state": true,
// 	"blocks": [{
// 			"addr": "00:0D:B9:2F:63:84",
// 			"band": "HT20",
// 			"channel": 6,
// 			"ht_supports": [
// 				0,
// 				1,
// 				2,
// 				3,
// 				4,
// 				5,
// 				6,
// 				7,
// 				8,
// 				9,
// 				10,
// 				11,
// 				12,
// 				13,
// 				14,
// 				15
// 			],
// 			"hwaddr": "D4:CA:6D:14:C2:07",
// 			"ncqm": {},
// 			"supports": [
// 				1,
// 				2,
// 				5,
// 				6,
// 				9,
// 				11,
// 				12,
// 				18,
// 				24,
// 				36,
// 				48,
// 				54
// 			],
// 			"tx_policies": {
// 				"00:24:D7:7B:B0:7C": {
// 					"ht_mcs": [
// 						0,
// 						1,
// 						2,
// 						3,
// 						4,
// 						5,
// 						6,
// 						7,
// 						8,
// 						9,
// 						10,
// 						11,
// 						12,
// 						13,
// 						14,
// 						15
// 					],
// 					"mcast": "legacy",
// 					"mcs": [
// 						1,
// 						2,
// 						6,
// 						9,
// 						11,
// 						12,
// 						18,
// 						24,
// 						36,
// 						48,
// 						54
// 					],
// 					"no_ack": false,
// 					"rts_cts": 2436,
// 					"ur_count": 3
// 				}
// 			},
// 			"ucqm": {},
// 			"wifi_stats": {}
// 		}
// 	],
// 	"bssid": "B6:4F:E6:7B:B0:7C",
// 	"encap": "00:00:00:00:00:00",
// 	"networks": [
// 		[
// 			"B6:4F:E6:7B:B0:7C",
// 			"tenant_1"
// 		],
// 		[
// 			"0E:D9:5C:7B:B0:7C",
// 			"tenant_2"
// 		]
// 	],
// 	"pending": [],
// 	"ssid": "tenant_1",
// 	"state": "running",
// 	"supported_band": "HT20",
// 	"wtp": {
// 		"addr": "00:0D:B9:2F:55:CC",
// 		"connection": [
// 			"10.244.0.0",
// 			48570
// 		],
// 		"datapath": {
// 			"dpid": "00:00:00:0D:B9:2F:55:CC",
// 			"hosts": {},
// 			"ip_addr": null,
// 			"network_ports": {
// 				"1": {
// 					"dpid": "00:00:00:0D:B9:2F:55:CC",
// 					"hwaddr": "00:0D:B9:2F:55:CC",
// 					"iface": "eth0",
// 					"neighbour": null,
// 					"port_id": 1
// 				},
// 				"2": {
// 					"dpid": "00:00:00:0D:B9:2F:55:CC",
// 					"hwaddr": "DA:E2:77:F5:67:87",
// 					"iface": "empower0",
// 					"neighbour": null,
// 					"port_id": 2
// 				}
// 			}
// 		},
// 		"label": "WTP_1_lab_hallway",
// 		"last_seen": 64464,
// 		"last_seen_ts": "2019-02-14T15:57:41.306571Z",
// 		"period": 5000,
// 		"state": "online",
// 		"supports": [{
// 				"addr": "00:0D:B9:2F:55:CC",
// 				"band": "HT20",
// 				"channel": 6,
// 				"ht_supports": [
// 					0,
// 					1,
// 					2,
// 					3,
// 					4,
// 					5,
// 					6,
// 					7,
// 					8,
// 					9,
// 					10,
// 					11,
// 					12,
// 					13,
// 					14,
// 					15
// 				],
// 				"hwaddr": "D4:CA:6D:14:C2:07",
// 				"ncqm": {},
// 				"supports": [
// 					1,
// 					2,
// 					5,
// 					6,
// 					9,
// 					11,
// 					12,
// 					18,
// 					24,
// 					36,
// 					48,
// 					54
// 				],
// 				"tx_policies": {
// 					"00:24:D7:7B:B0:7C": {
// 						"ht_mcs": [
// 							0,
// 							1,
// 							2,
// 							3,
// 							4,
// 							5,
// 							6,
// 							7,
// 							8,
// 							9,
// 							10,
// 							11,
// 							12,
// 							13,
// 							14,
// 							15
// 						],
// 						"mcast": "legacy",
// 						"mcs": [
// 							1,
// 							2,
// 							6,
// 							9,
// 							11,
// 							12,
// 							18,
// 							24,
// 							36,
// 							48,
// 							54
// 						],
// 						"no_ack": false,
// 						"rts_cts": 2436,
// 						"ur_count": 3
// 					}
// 				},
// 				"ucqm": {},
// 				"wifi_stats": {}
// 			}, {
// 				"addr": "00:0D:B9:2F:55:CC",
// 				"band": "HT20",
// 				"channel": 36,
// 				"ht_supports": [
// 					0,
// 					1,
// 					2,
// 					3,
// 					4,
// 					5,
// 					6,
// 					7,
// 					8,
// 					9,
// 					10,
// 					11,
// 					12,
// 					13,
// 					14,
// 					15
// 				],
// 				"hwaddr": "04:F0:21:09:F9:97",
// 				"ncqm": {},
// 				"supports": [
// 					6,
// 					9,
// 					12,
// 					18,
// 					24,
// 					36,
// 					48,
// 					54
// 				],
// 				"tx_policies": {},
// 				"ucqm": {},
// 				"wifi_stats": {}
// 			}
// 		]
// 	}
// }, {
// 	"addr": "00:24:D7:72:AB:BC",
// 	"assoc_id": 1877,
// 	"association_state": true,
// 	"authentication_state": true,
// 	"blocks": [{
// 			"addr": "00:0D:B9:2F:63:E0",
// 			"band": "HT20",
// 			"channel": 6,
// 			"ht_supports": [
// 				0,
// 				1,
// 				2,
// 				3,
// 				4,
// 				5,
// 				6,
// 				7,
// 				8,
// 				9,
// 				10,
// 				11,
// 				12,
// 				13,
// 				14,
// 				15
// 			],
// 			"hwaddr": "D4:CA:6D:14:C1:AF",
// 			"ncqm": {},
// 			"supports": [
// 				1,
// 				2,
// 				5,
// 				6,
// 				9,
// 				11,
// 				12,
// 				18,
// 				24,
// 				36,
// 				48,
// 				54
// 			],
// 			"tx_policies": {
// 				"00:24:D7:72:AB:BC": {
// 					"ht_mcs": [
// 						0,
// 						1,
// 						2,
// 						3,
// 						4,
// 						5,
// 						6,
// 						7,
// 						8,
// 						9,
// 						10,
// 						11,
// 						12,
// 						13,
// 						14,
// 						15
// 					],
// 					"mcast": "legacy",
// 					"mcs": [
// 						1,
// 						2,
// 						6,
// 						9,
// 						11,
// 						12,
// 						18,
// 						24,
// 						36,
// 						48,
// 						54
// 					],
// 					"no_ack": false,
// 					"rts_cts": 2436,
// 					"ur_count": 3
// 				}
// 			},
// 			"ucqm": {},
// 			"wifi_stats": {}
// 		}
// 	],
// 	"bssid": "B6:4F:E6:72:AB:BC",
// 	"encap": "00:00:00:00:00:00",
// 	"networks": [
// 		[
// 			"B6:4F:E6:72:AB:BC",
// 			"tenant_1"
// 		],
// 		[
// 			"0E:D9:5C:72:AB:BC",
// 			"tenant_2"
// 		]
// 	],
// 	"pending": [],
// 	"ssid": "tenant_1",
// 	"state": "running",
// 	"supported_band": "HT20",
// 	"wtp": {
// 		"addr": "00:0D:B9:2F:63:E0",
// 		"connection": [
// 			"10.244.0.0",
// 			60976
// 		],
// 		"datapath": {
// 			"dpid": "00:00:00:0D:B9:2F:63:E0",
// 			"hosts": {},
// 			"ip_addr": null,
// 			"network_ports": {
// 				"1": {
// 					"dpid": "00:00:00:0D:B9:2F:63:E0",
// 					"hwaddr": "00:0D:B9:2F:63:E0",
// 					"iface": "eth0",
// 					"neighbour": null,
// 					"port_id": 1
// 				},
// 				"2": {
// 					"dpid": "00:00:00:0D:B9:2F:63:E0",
// 					"hwaddr": "5A:65:B4:BD:7E:BF",
// 					"iface": "empower0",
// 					"neighbour": null,
// 					"port_id": 2
// 				},
// 				"5": {
// 					"dpid": "00:00:00:0D:B9:2F:63:E0",
// 					"hwaddr": "6A:33:A9:9C:50:E9",
// 					"iface": "empower0",
// 					"neighbour": null,
// 					"port_id": 5
// 				}
// 			}
// 		},
// 		"label": "WTP_10_D2_stairs",
// 		"last_seen": 87103,
// 		"last_seen_ts": "2019-02-14T15:57:42.055204Z",
// 		"period": 5000,
// 		"state": "online",
// 		"supports": [{
// 				"addr": "00:0D:B9:2F:63:E0",
// 				"band": "HT20",
// 				"channel": 6,
// 				"ht_supports": [
// 					0,
// 					1,
// 					2,
// 					3,
// 					4,
// 					5,
// 					6,
// 					7,
// 					8,
// 					9,
// 					10,
// 					11,
// 					12,
// 					13,
// 					14,
// 					15
// 				],
// 				"hwaddr": "D4:CA:6D:14:C1:AF",
// 				"ncqm": {},
// 				"supports": [
// 					1,
// 					2,
// 					5,
// 					6,
// 					9,
// 					11,
// 					12,
// 					18,
// 					24,
// 					36,
// 					48,
// 					54
// 				],
// 				"tx_policies": {
// 					"00:24:D7:72:AB:BC": {
// 						"ht_mcs": [
// 							0,
// 							1,
// 							2,
// 							3,
// 							4,
// 							5,
// 							6,
// 							7,
// 							8,
// 							9,
// 							10,
// 							11,
// 							12,
// 							13,
// 							14,
// 							15
// 						],
// 						"mcast": "legacy",
// 						"mcs": [
// 							1,
// 							2,
// 							6,
// 							9,
// 							11,
// 							12,
// 							18,
// 							24,
// 							36,
// 							48,
// 							54
// 						],
// 						"no_ack": false,
// 						"rts_cts": 2436,
// 						"ur_count": 3
// 					}
// 				},
// 				"ucqm": {},
// 				"wifi_stats": {}
// 			}, {
// 				"addr": "00:0D:B9:2F:63:E0",
// 				"band": "HT20",
// 				"channel": 36,
// 				"ht_supports": [
// 					0,
// 					1,
// 					2,
// 					3,
// 					4,
// 					5,
// 					6,
// 					7,
// 					8,
// 					9,
// 					10,
// 					11,
// 					12,
// 					13,
// 					14,
// 					15
// 				],
// 				"hwaddr": "04:F0:21:09:F9:8D",
// 				"ncqm": {},
// 				"supports": [
// 					6,
// 					9,
// 					12,
// 					18,
// 					24,
// 					36,
// 					48,
// 					54
// 				],
// 				"tx_policies": {},
// 				"ucqm": {},
// 				"wifi_stats": {}
// 			}
// 		]
// 	}
// }
// ]