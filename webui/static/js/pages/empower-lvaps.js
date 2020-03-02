$('#clients').removeClass('collapsed');
$('#collapseOne').addClass('show');
$('#clients_lvaps').addClass('active');

console.log("__EMPOWER_WEBUI",__EMPOWER_WEBUI)

$(document).ready(function() {

  aoColumns = [
    { "sTitle": "Address" },
    { "sTitle": "BSSID" },
    { "sTitle": "SSID" },
    { "sTitle": "WTP" },
    { "sTitle": "Actions", "sClass": "text-center" }
  ]

  DATATABLE = $('#dataTable').DataTable({
  "aoColumns": aoColumns
  });

  refresh_datatable();
});

ENTITY = null
CF = __EMPOWER_WEBUI.CORE_FUNCTIONS

CURRENT_LVAP = null
CURRENT_WTP = null
WTPS_FOR_HANDOVER = []

OFFLINE_DEBUG = false

function format_datatable_data( data ) {

  if (OFFLINE_DEBUG){
    data = lvap_json
  }

  $.each( data, function( key, val ) {

    actions = "-"

    if ( __USERNAME === "root" ) {
      actions = ""+
      '<button class="btn btn-sm btn-info shadow-sm mr-xl-1 mb-md-1 m-1" '+
      'onclick="trigger_inspect_modal(\''+val['addr']+'\')">'+
      '<i class="fas fa-search fa-sm fa-fw text-white-50 mr-xl-1 m-1"></i><span class="d-none d-xl-inline">Inspect</span></button>'
    }
    else{
      actions = ""+
      '<button class="btn btn-sm btn-warning shadow-sm mr-xl-1 mb-md-1 m-1" '+
      'onclick="trigger_ho_modal(\''+val['addr']+'\')">'+
      '<i class="fas fa-exchange-alt fa-sm fa-fw text-white-50 mr-xl-1 m-1"></i><span class="d-none d-xl-inline">Handover</span></button>'
    }

    let address = val.addr
    let bssid = val.bssid
    let ssid = val.ssid
    let wtp = null
    let wtp_addr = null
    let wtp_desc = null
    let wtp_channel = null
    let wtp_band = null
    if (CF._is_there(val["wtp"])){
      wtp_desc = val.wtp.desc
    }
    if (CF._is_there(val["blocks"])){
      $.each( val["blocks"], function( block_key, block_val ) {
        if(CF._is_there(block_val)){
          wtp_addr = block_val["addr"]
          wtp_channel = block_val["channel"]
          wtp_band = block_val["band"]
        }
      })
    }
    wtp = wtp_addr +"("+wtp_channel+", "+wtp_band+")\n"+wtp_desc

    
    DATATABLE.row.add([
        address,
        bssid,
        ssid,
        wtp,
        actions
    ] )

  });

  DATATABLE.draw(true)

}

function refresh_datatable() {

  ENTITY = __EMPOWER_WEBUI.ENTITY.CLIENT.LVAP

  DATATABLE.clear();

  // format_datatable_data(lvap_json)

  REST_REQ(ENTITY).configure_GET({
      success: [ empower_log_response, format_datatable_data],
      error: [ empower_log_response,  empower_alert_generate_error ]
    })
    .perform()
}

function trigger_ho_modal(lvap_key, inspect_mode=false){

  console.log("trigger_ho_modal:", lvap_key)

  $("#ho_modal_title").text("LVAP Handover")

  show_ho_modal_step_one = function(lvap){
    
    if (OFFLINE_DEBUG){
      lvap = lvap_json[lvap_key]
    }

    CURRENT_LVAP = lvap
    let lvap_addr = lvap.addr

    $("#ho_address").text(lvap_addr)
    $("#ho_bssid").text(lvap.bssid)
    $("#ho_ssid").text(lvap.ssid)

    let wtp_addr = null
    let wtp_hwaddr = null
    let wtp_desc = null
    let wtp_channel = null
    let wtp_band = null
    let wtp_tx_policies = null

    if (CF._is_there(lvap.wtp)){
      wtp_addr = lvap.wtp.addr
      wtp_desc = lvap.wtp.desc
    }
    if (CF._is_there(lvap.blocks)){
      $.each( lvap.blocks, function( block_key, block_val ) {
        wtp_hwaddr = block_val.hwaddr
        wtp_channel = block_val.channel
        wtp_band = block_val.band
        wtp_tx_policies = block_val.tx_policies[lvap_addr]
      })
    }

    $("#ho_current_wtp_addr").text(wtp_addr)
    $("#ho_current_wtp_hwaddr").text(wtp_hwaddr)
    $("#ho_current_wtp_channel").text(wtp_channel)
    $("#ho_current_wtp_band").text(wtp_band)
    $("#ho_current_wtp_desc").text(wtp_desc)

    CURRENT_WTP = {
      addr: wtp_addr,
      desc :wtp_desc,
      hwaddr: wtp_hwaddr,
      channel: wtp_channel,
      band: wtp_band,
    }

    show_ho_modal_step_two = function(wtps){

      if (OFFLINE_DEBUG){
        wtps = wtps_json
      }
    
      let wtp_select = $("#edit_wtp")
      wtp_select.empty()
      $.each(wtps, function(key, value){
        if (CF._is_there(value["state"])){
          if (value["state"] === "online"){
            let addr = value.addr
            let desc = value.desc
            let blocks = {}
            if (CF._is_there(value["blocks"])){
              $.each(value["blocks"], function(block_key, block_value){
                let block = {
                  hwaddr: block_value.hwaddr,
                  channel: block_value.channel,
                  band: block_value.band
                }
                blocks[block_key] = block
              })
            }
            let wtp = {
              addr: addr,
              desc: desc,
              blocks: blocks
            }

            let option_index = WTPS_FOR_HANDOVER.push(wtp) -1

            let option_text = wtp.addr

            let opt = null
            if (CURRENT_WTP.addr === wtp.addr){
              // wtp is CURRENT WTP
              option_text = "* " + option_text

              opt = new Option(option_text, option_index, true, true)

            }
            else{
              opt = new Option(option_text, option_index)
            }
            
            wtp_select.append(opt)
          }
        }
      })

      let block_select = $("#edit_block")

      if (inspect_mode){
        CF._hide($("#ho_handover_section"))
      }
      else{
        CF._show($("#ho_handover_section"))
      }

      update_wtp_selection()

      let instance = $("#ho_modal")

      instance.modal("show")
    }

    ENTITY = __EMPOWER_WEBUI.ENTITY.DEVICE.WTP

    REST_REQ(ENTITY).configure_GET({
        success: [ empower_log_response, show_ho_modal_step_two],
        error: [ empower_log_response,  empower_alert_generate_error ]
      })
      .perform()
  }

  ENTITY = __EMPOWER_WEBUI.ENTITY.CLIENT.LVAP

  let key = lvap_key

  if (OFFLINE_DEBUG){
    key = ""
  }

  REST_REQ(ENTITY).configure_GET({
      key: key,
      success: [ empower_log_response, show_ho_modal_step_one],
      error: [ empower_log_response,  empower_alert_generate_error ]
    })
    .perform()
  
}

function update_wtp_selection(){
  let wtp_select = $("#edit_wtp")
  let index = wtp_select.val()
  console.log("selected wtp:", index)

  let wtp = WTPS_FOR_HANDOVER[index]
  $("#ho_wtp_addr").text(wtp.addr)
  $("#ho_wtp_desc").text(wtp.desc)

  let perform_button = $("#ho_perform_btn")

  if (CURRENT_WTP.addr === wtp.addr){
    $("#ho_wtp_title").text("Current WTP")
    CF._hide(perform_button)
  }
  else{
    $("#ho_wtp_title").text("NEW WTP")
    CF._show(perform_button)
  }

  let block_select = $("#edit_block")
  block_select.empty()
  update_block_selection()
}

function update_block_selection(){

  let block_select = $("#edit_block")
  let wtp_select = $("#edit_wtp")

  let wtp_index = wtp_select.val()

  let wtp = WTPS_FOR_HANDOVER[wtp_index]
  console.log("block_select:", block_select)
  console.log("block_select.length:", block_select.length)

  let block_select_options_count = $("#edit_block option").length
  
  if (block_select_options_count === 0){

    // any block
    let opt = new Option("-", "any", true, true)
    block_select.append(opt)

    $.each(wtp.blocks, function(key, block){
      
      let option_text = block.hwaddr+" ("+block.channel+", "+block.band+")"

      let opt = null
      if (CURRENT_WTP.addr === wtp.addr){
        if ((CURRENT_WTP.hwaddr === block.hwaddr) &&
            (CURRENT_WTP.channel === block.channel) &&
            (CURRENT_WTP.band === block.band)){

          option_text = "* " + option_text
          opt = new Option(option_text, key, true, true)
        }
        else{
          opt = new Option(option_text, key)
        }
      }
      else{
        opt = new Option(option_text, key)
      }
      
      block_select.append(opt)
    })

  }

  let block_index = block_select.val()
  let block = wtp.blocks[block_index]

  let perform_button = $("#ho_perform_btn")

  if (block_select.val() === "any"){
    CF._hide($("#ho_block_summary"))
    CF._show(perform_button)
  }
  else {
    CF._show($("#ho_block_summary"))
    if ((CURRENT_WTP.addr === wtp.addr) &&
        (CURRENT_WTP.hwaddr === block.hwaddr) &&
        (CURRENT_WTP.channel === block.channel) &&
        (CURRENT_WTP.band === block.band)){
      $("#ho_block_title").text("Current Block")
      CF._hide(perform_button)
    }
    else{
      $("#ho_block_title").text("NEW Block")
      CF._show(perform_button)
    }

    $("#ho_wtp_hwaddr").text(block.hwaddr)
    $("#ho_wtp_channel").text(block.channel)
    $("#ho_wtp_band").text(block.band)
  }

}

function trigger_inspect_modal(lvap_key){

  console.log("trigger_inspect_modal:", lvap_key)
  trigger_ho_modal(lvap_key, true)
  $("#ho_modal_title").text("Inspect LVAP")

}

function perform_handover(){
  let key = $("#ho_address").text()
  let data = {
    version: "1.0",
    wtp: $("#ho_wtp_addr").text()
  }
  let block_id = $("#edit_block").val()
  if (block_id !== "any"){
    data.blocks = [parseInt(block_id)]
  }

  ENTITY = __EMPOWER_WEBUI.ENTITY.CLIENT.LVAP

  REST_REQ(ENTITY).configure_PUT({
    data: data,
    key: key,
    success: [ empower_log_response, empower_alert_generate_success ],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

// let wtps_json = {
//   "00:0D:B9:3F:8A:E8": {
//       "addr": "00:0D:B9:3F:8A:E8",
//       "desc": "Generic device",
//       "last_seen": 39033,
//       "last_seen_ts": "2020-01-16T13:48:13.633402Z",
//       "period": 0,
//       "state": "online",
//       "connection": {
//           "proto": "empower.managers.ranmanager.lvapp",
//           "addr": "192.168.0.130"
//       },
//       "blocks": {
//           "0": {
//               "addr": "00:0D:B9:3F:8A:E8",
//               "hwaddr": "04:F0:21:14:CA:8E",
//               "channel": 36,
//               "supports": [
//                   6,
//                   9,
//                   12,
//                   18,
//                   24,
//                   36,
//                   48,
//                   54
//               ],
//               "ht_supports": [
//                   0,
//                   1,
//                   2,
//                   3,
//                   4,
//                   5,
//                   6,
//                   7,
//                   8,
//                   9,
//                   10,
//                   11,
//                   12,
//                   13,
//                   14,
//                   15
//               ],
//               "tx_policies": {
//                   "C4:86:E9:4B:1B:3F": {
//                       "addr": "C4:86:E9:4B:1B:3F",
//                       "no_ack": false,
//                       "rts_cts": 2436,
//                       "max_amsdu_len": 7935,
//                       "mcast": "legacy",
//                       "mcs": [
//                           6.0,
//                           9.0,
//                           12.0,
//                           18.0,
//                           24.0,
//                           36.0,
//                           48.0,
//                           54.0
//                       ],
//                       "ht_mcs": [
//                           0,
//                           1,
//                           2,
//                           3,
//                           4,
//                           5,
//                           6,
//                           7,
//                           8,
//                           9,
//                           10,
//                           11,
//                           12,
//                           13,
//                           14,
//                           15
//                       ],
//                       "ur_count": 3
//                   }
//               },
//               "band": "HT20"
//           },
//           "1": {
//               "addr": "00:0D:B9:3F:8A:E8",
//               "hwaddr": "04:F0:21:1E:58:EC",
//               "channel": 6,
//               "supports": [
//                   1,
//                   2,
//                   5,
//                   6,
//                   9,
//                   11,
//                   12,
//                   18,
//                   24,
//                   36,
//                   48,
//                   54
//               ],
//               "ht_supports": [
//                   0,
//                   1,
//                   2,
//                   3,
//                   4,
//                   5,
//                   6,
//                   7,
//                   8,
//                   9,
//                   10,
//                   11,
//                   12,
//                   13,
//                   14,
//                   15
//               ],
//               "tx_policies": {},
//               "band": "HT20"
//           }
//       }
//   }
// }

// let lvap_json = {
//   "C4:86:E9:4B:1B:3F": {
//       "addr": "C4:86:E9:4B:1B:3F",
//       "bssid": "D6:2B:74:4B:1B:3F",
//       "ssid": "myproject",
//       "wtp": {
//           "addr": "00:0D:B9:3F:8A:E8",
//           "desc": "Generic device",
//           "last_seen": 39121,
//           "last_seen_ts": "2020-01-16T13:48:41.635651Z",
//           "period": 0,
//           "state": "online",
//           "connection": {
//               "proto": "empower.managers.ranmanager.lvapp",
//               "addr": "192.168.0.130"
//           },
//           "blocks": {
//               "0": {
//                   "addr": "00:0D:B9:3F:8A:E8",
//                   "hwaddr": "04:F0:21:14:CA:8E",
//                   "channel": 36,
//                   "supports": [
//                       6,
//                       9,
//                       12,
//                       18,
//                       24,
//                       36,
//                       48,
//                       54
//                   ],
//                   "ht_supports": [
//                       0,
//                       1,
//                       2,
//                       3,
//                       4,
//                       5,
//                       6,
//                       7,
//                       8,
//                       9,
//                       10,
//                       11,
//                       12,
//                       13,
//                       14,
//                       15
//                   ],
//                   "tx_policies": {
//                       "C4:86:E9:4B:1B:3F": {
//                           "addr": "C4:86:E9:4B:1B:3F",
//                           "no_ack": false,
//                           "rts_cts": 2436,
//                           "max_amsdu_len": 7935,
//                           "mcast": "legacy",
//                           "mcs": [
//                               6.0,
//                               9.0,
//                               12.0,
//                               18.0,
//                               24.0,
//                               36.0,
//                               48.0,
//                               54.0
//                           ],
//                           "ht_mcs": [
//                               0,
//                               1,
//                               2,
//                               3,
//                               4,
//                               5,
//                               6,
//                               7,
//                               8,
//                               9,
//                               10,
//                               11,
//                               12,
//                               13,
//                               14,
//                               15
//                           ],
//                           "ur_count": 3
//                       }
//                   },
//                   "band": "HT20"
//               },
//               "1": {
//                   "addr": "00:0D:B9:3F:8A:E8",
//                   "hwaddr": "04:F0:21:1E:58:EC",
//                   "channel": 6,
//                   "supports": [
//                       1,
//                       2,
//                       5,
//                       6,
//                       9,
//                       11,
//                       12,
//                       18,
//                       24,
//                       36,
//                       48,
//                       54
//                   ],
//                   "ht_supports": [
//                       0,
//                       1,
//                       2,
//                       3,
//                       4,
//                       5,
//                       6,
//                       7,
//                       8,
//                       9,
//                       10,
//                       11,
//                       12,
//                       13,
//                       14,
//                       15
//                   ],
//                   "tx_policies": {},
//                   "band": "HT20"
//               }
//           }
//       },
//       "blocks": [
//           {
//               "addr": "00:0D:B9:3F:8A:E8",
//               "hwaddr": "04:F0:21:14:CA:8E",
//               "channel": 36,
//               "supports": [
//                   6,
//                   9,
//                   12,
//                   18,
//                   24,
//                   36,
//                   48,
//                   54
//               ],
//               "ht_supports": [
//                   0,
//                   1,
//                   2,
//                   3,
//                   4,
//                   5,
//                   6,
//                   7,
//                   8,
//                   9,
//                   10,
//                   11,
//                   12,
//                   13,
//                   14,
//                   15
//               ],
//               "tx_policies": {
//                   "C4:86:E9:4B:1B:3F": {
//                       "addr": "C4:86:E9:4B:1B:3F",
//                       "no_ack": false,
//                       "rts_cts": 2436,
//                       "max_amsdu_len": 7935,
//                       "mcast": "legacy",
//                       "mcs": [
//                           6.0,
//                           9.0,
//                           12.0,
//                           18.0,
//                           24.0,
//                           36.0,
//                           48.0,
//                           54.0
//                       ],
//                       "ht_mcs": [
//                           0,
//                           1,
//                           2,
//                           3,
//                           4,
//                           5,
//                           6,
//                           7,
//                           8,
//                           9,
//                           10,
//                           11,
//                           12,
//                           13,
//                           14,
//                           15
//                       ],
//                       "ur_count": 3
//                   }
//               },
//               "band": "HT20"
//           }
//       ],
//       "state": "running",
//       "ht_caps": true,
//       "ht_caps_info": {
//           "L_SIG_TXOP_Protection_Support": false,
//           "Forty_MHz_Intolerant": false,
//           "Reserved": false,
//           "DSSS_CCK_Mode_in_40_MHz": false,
//           "Maximum_AMSDU_Length": false,
//           "HT_Delayed_Block_Ack": false,
//           "Rx_STBC": 1,
//           "Tx_STBC": true,
//           "Short_GI_for_40_MHz": true,
//           "Short_GI_for_20_MHz": true,
//           "HT_Greenfield": false,
//           "SM_Power_Save": 3,
//           "Supported_Channel_Width_Set": true,
//           "LDPC_Coding_Capability": true
//       },
//       "assoc_id": 1822,
//       "pending": [],
//       "encap": "00:00:00:00:00:00",
//       "networks": [
//           [
//               "D6:2B:74:4B:1B:3F",
//               "myproject"
//           ]
//       ],
//       "authentication_state": true,
//       "association_state": true
//   }
// }