console.warn("THIS PAGE IS A WORK IN PROGRESS!")


CARD__ACLS = "acls_card"
CARD__WIFI_SLICES = "wifi_slices_card"
CARD__LTE_SLICES = "lte_slices_card"

VALUE__ACLS = "acls_value"
VALUE__WIFI_SLICES = "wifi_slices_value"
VALUE__LTE_SLICES = "lte_slices_value"

BOX__ACLS = "acls_box"
BOX__WIFI_SLICES = "wifi_slices_box"
BOX__LTE_SLICES = "lte_slices_box"

BODY__PROPERTIES = "properties_body"

DEFAULT_QUANTUM_VALUE = "5000"
DEFAULT_STA_SCHEDULER_VALUE = "0"
DEFAULT_AMSDU_AGGREGATION_VALUE = false
DEFAULT_RBGS_VALUE = "5"
DEFAULT_UE_SCHEDULER_VALUE = "0"

LAST_QUANTUM_VALUE = DEFAULT_QUANTUM_VALUE
LAST_STA_SCHEDULER_VALUE = DEFAULT_STA_SCHEDULER_VALUE
LAST_AMSDU_AGGREGATION_VALUE = DEFAULT_AMSDU_AGGREGATION_VALUE
LAST_RBGS_VALUE = DEFAULT_RBGS_VALUE
LAST_UE_SCHEDULER_VALUE = DEFAULT_UE_SCHEDULER_VALUE

OPTIONS_STA_SCHEDULER_WIFI = [
  {
    value: 0, label: "ROUND-ROBIN"
  },
  {
    value: 1, label: "DEFICIT ROUND-ROBIN"
  },
  {
    value: 2, label: "AIRTIME DEFICIT ROUND-ROBIN"
  },
]

OPTIONS_UE_SCHEDULER_LTE = [
  {
    value: 0, label: "ROUND-ROBIN"
  }
]

DCSP_ALLOWED_VALUES = [
  0x00,
  0x01,
  0x02,
  0x03,
  0x04,
  0x08,
  0x0A,
  0x0C,
  0x0E,
  0x10,
  0x12,
  0x14,
  0x16,
  0x18,
  0x1A,
  0x1C,
  0x1E,
  0x20,
  0x22,
  0x24,
  0x26,
  0x28,
  0x2C,
  0x2E,
  0x30,
  0x38
]

$(document).ready(function() {

  console.log("__EMPOWER_WEBUI: ", __EMPOWER_WEBUI)
  
  let fields = {
    address: {
      type: "TEXT"
    },
    desc: {
      type: "TEXT"
    },
  }

  ENTITY = __EMPOWER_WEBUI.ENTITY.ACL

  ADD_ACL_MODAL = new WEBUI_Modal_Entity(
    __EMPOWER_WEBUI.MODAL.TYPE.ADD,
    ENTITY
  ).add_fields(fields)

  EDIT_ACL_MODAL = new WEBUI_Modal_Entity(
    __EMPOWER_WEBUI.MODAL.TYPE.EDIT,
    ENTITY
  ).add_fields(fields)

  REMOVE_ACL_MODAL = new WEBUI_Modal_Entity(
    __EMPOWER_WEBUI.MODAL.TYPE.REMOVE,
    ENTITY
  ).add_fields(fields)

  aoColumns_ACLS = [
    { "sTitle": "Address" },
    { "sTitle": "Description" },
    { "sTitle": "Actions", "sClass": "text-center"  },
  ]

  DATATABLE_ACLS = $('#dataTable_ACLS').DataTable({
    "aoColumns": aoColumns_ACLS
  });

  aoColumns_WIFI_SLICES = [
    { "sTitle": "ID", "sClass": "text-center"  },
    // { "sTitle": "Properties" },
    { "sTitle": "AMSDU Aggr.", "sClass": "text-center"  },
    { "sTitle": "Quantum", "sClass": "text-center"  },
    { "sTitle": "STA Scheduler", "sClass": "text-center"  },
    { "sTitle": "Devices", "sClass": "text-center"  },
    { "sTitle": "Actions", "sClass": "text-center"  },
  ]

  DATATABLE_WIFI_SLICES = $('#dataTable_WIFI_SLICES').DataTable({
    "aoColumns": aoColumns_WIFI_SLICES
  });

  aoColumns_LTE_SLICES = [
    { "sTitle": "ID", "sClass": "text-center"  },
    // { "sTitle": "Properties" },
    { "sTitle": "RBGS", "sClass": "text-center"  },
    { "sTitle": "UE Scheduler", "sClass": "text-center"  },
    { "sTitle": "Devices", "sClass": "text-center"  },
    { "sTitle": "Actions", "sClass": "text-center"  },
  ]

  DATATABLE_LTE_SLICES = $('#dataTable_LTE_SLICES').DataTable({
    "aoColumns": aoColumns_LTE_SLICES
  });

  aoColumns_MNG_WIFI_SLICE = [
    { "sTitle": "Select", "sClass": "text-center pl-4" },
    { "sTitle": "Description" },
    { "sTitle": "Properties" },
  ]

  DATATABLE_MNG_WIFI_SLICE_MODAL = $('#dataTable_MNG_WIFI_SLICE_Modal').DataTable({
    "aoColumns": aoColumns_MNG_WIFI_SLICE
  });

  aoColumns_MNG_LTE_SLICE = [
    { "sTitle": "Select", "sClass": "text-center pl-4" },
    { "sTitle": "Description" },
    { "sTitle": "Properties" },
  ]

  DATATABLE_MNG_LTE_SLICE_MODAL = $('#dataTable_MNG_LTE_SLICE_Modal').DataTable({
    "aoColumns": aoColumns_MNG_LTE_SLICE
  });

  MNG_SLICE_MODAL = $('#MNG_SLICE_Modal')

  // ENTITY = __EMPOWER_WEBUI.ENTITY.PROJECT
  
  // REST_REQ(ENTITY).configure_GET({
  //   key: project_id,
  //   success: [ empower_log_response, build_and_set_properties_body, refresh_datatable_acls ],
  //   error: [ empower_log_response,  empower_alert_generate_error ]
  // })
  // .perform()



  refresh_all()

})

ENTITY = null
CF = __EMPOWER_WEBUI.CORE_FUNCTIONS

function set_card_values(acls, wifi_slices, lte_slices){
  set_acls_number(acls)
  set_wifi_slices_number(wifi_slices)
  set_lte_slices_number(lte_slices)
}

function set_acls_number(value){
  $("#" + VALUE__ACLS).text(value)
}

function set_wifi_slices_number(value){
  $("#" + VALUE__WIFI_SLICES).text(value)
}

function set_lte_slices_number(value){
  $("#" + VALUE__LTE_SLICES).text(value)
}


function toggle_acls_card(){
  $("#" + CARD__ACLS).toggleClass('d-none')
}

function toggle_wifi_slices_card(){
  $("#" + CARD__WIFI_SLICES).toggle('d-none')
}

function toggle_lte_slices_card(){
  $("#" + CARD__LTE_SLICES).toggle('d-none')
}

function set_properties_body(html=null){
  $("#" + BODY__PROPERTIES).html(html)
}

function build_properties_body(data){

  let spacing = "<i class='fas fa-icons fa-fw fa-1x invisible mr-1'></i>"
  let html = ""+
  "<p class='py-2 my-0'><i class='fas fa-tag fa-fw fa-1x mr-1 '></i><b class='pr-1 text-lg'>Project Id:</b>"+ data.project_id + "</p>"
  if (CF._is_there(data.wifi_props)){
    html += "<p class='py-2 my-0'><i class='fas fa-wifi fa-fw fa-1x mr-1'></i><b class='text-lg'>WiFi</b></p>"
    html += "<p class='py-1 my-0'>"+spacing+"<b class='pr-1'>SSID:</b>"+ data.wifi_props.ssid + "</p>"
    html += "<p class='py-1 my-0'>"+spacing+"<b class='pr-1'>BSSID type:</b>"+ data.wifi_props.bssid_type + "</p>"
  }
  else{
    // html += "<p class='py-2 my-0 text-danger'>"
    // html += "<span class='fa-stack fa-1x'>"
    // html +=   "<i class='fas fa-wifi fa-stack-1x'></i>"
    // html +=   "<i class='fas fa-ban fa-stack-2x'></i>"
    // html += "</span>"
    // html += "<b class='text-lg'> NO WiFi</b></p>"
    html += "<p class='py-2 my-0'><i class='fas fa-ban fa-fw fa-1x mr-1'></i><b class='text-lg'>NO WiFi</b></p>"
  }
  if (CF._is_there(data.lte_props)){
    html += "<p class='py-2 my-0'><i class='fas fa-wifi fa-fw fa-1x mr-1'></i><b class='text-lg'>LTE</b></p>"
    html += "<p class='py-1 my-0'>"+spacing+"<b class='pr-1'>PLMNID (MCC/MNC):</b>"+ data.lte_props.plmnid.mcc + "/"+ data.lte_props.plmnid.mnc+"</p>"
  }
  else{
    // html += "<p class='py-2 my-0 text-danger'>"
    // html += "<span class='fa-stack fa-1x'>"
    // html +=   "<i class='fas fa-wifi fa-stack-1x'></i>"
    // html +=   "<i class='fas fa-ban fa-stack-2x'></i>"
    // html += "</span>"
    // html += "<b class='text-lg'> NO LTE</b></p>"
    html += "<p class='py-2 my-0'><i class='fas fa-ban fa-fw fa-1x mr-1'></i><b class='text-lg'>NO LTE</b></p>"
  }

  return html
}

function build_and_set_properties_body(data){

  set_properties_body(build_properties_body(data))
}

function set_what_is_visible(project_data){
  if (CF._is_there(project_data.wifi_props)){
    $( "#" + CARD__ACLS).removeClass("d-none")
    $( "#" + CARD__WIFI_SLICES).removeClass("d-none")
    $( "#" + BOX__ACLS).removeClass("d-none")
    $( "#" + BOX__WIFI_SLICES).removeClass("d-none")
  }
  else{

  }
  if (CF._is_there(project_data.lte_props)){
    $( "#" + CARD__LTE_SLICES).removeClass("d-none")
    $( "#" + BOX__LTE_SLICES).removeClass("d-none")
  }
  else{
    
  }
}

function format_datatable_acls_data( data ) {
  let acls = {}
  if (CF._is_there(data.wifi_props)){
    if (CF._is_there(data.wifi_props.allowed)){
      acls = data.wifi_props.allowed
      // acls = {
      //   123:{
      //     addr: 123,
      //     desc: "1 2 e 3"
      //   },
      //   456:{
      //     addr: 456,
      //     desc: "4 5 e 6"
      //   }
      // }
    }
  }

  $.each( acls, function( key, val ) {

    let actions = ""+
      '<button class="btn btn-sm btn-warning shadow-sm mr-xl-1 mb-md-1 m-1" '+
      'onclick="trigger_edit_acl_modal(\''+val['addr']+'\')">'+
      '<i class="fas fa-edit fa-sm fa-fw text-white-50 mr-xl-1 m-1"></i><span class="d-none d-xl-inline">Edit</span></button>'+
      '<button class="btn btn-sm btn-danger shadow-sm mb-xl-1 m-1" '+
      'onclick="trigger_remove_acl_modal(\''+val['addr']+'\')">'+
      '<i class="fas fa-trash fa-sm fa-fw text-white-50 mr-xl-1 m-1"></i><span class="d-none d-xl-inline">Remove</span></button>'

    DATATABLE_ACLS.row.add([
        val['addr'],
        val['desc'],
        actions
    ] )

  });

  DATATABLE_ACLS.draw(true)

  $( "#" + VALUE__ACLS).text(Object.keys(acls).length)

}

function refresh_datatable_acls(data=null) {

  DATATABLE_ACLS.clear();

  if (CF._is_there(data)){
    format_datatable_acls_data(data)
  }
  else{

    ENTITY = __EMPOWER_WEBUI.ENTITY.PROJECT

    REST_REQ(ENTITY).configure_GET({
      key: __EMPOWER_WEBUI.PROJECT.ID,
      success: [ empower_log_response, format_datatable_acls_data],
      error: [ empower_log_response,  empower_alert_generate_error ]
    })
    .perform()
  }
}

function add_ACL() {

  let data = {
    "version":"1.0",
    "addr": ADD_ACL_MODAL.address.get(),
    "desc": ADD_ACL_MODAL.desc.get()
  }

  console.log("data: ",data)

  let rda = function(){
    refresh_datatable_acls()
  }
  
  add_reset = ADD_ACL_MODAL.reset.bind(ADD_ACL_MODAL)

  ENTITY = __EMPOWER_WEBUI.ENTITY.ACL

  REST_REQ(ENTITY).configure_POST({
    data: data,
    success: [ empower_log_response, empower_alert_generate_success, 
      add_reset, rda ],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()

}

function trigger_edit_acl_modal( acl_key ) {

  show_edit_modal = function(data){

    EDIT_ACL_MODAL.address.set(data.addr)
    EDIT_ACL_MODAL.desc.set(data.desc)

    EDIT_ACL_MODAL.get_$instance().modal({show:true})
  }

  ENTITY = __EMPOWER_WEBUI.ENTITY.ACL

  REST_REQ(ENTITY).configure_GET({
    key: acl_key,
    success: [ empower_log_response, show_edit_modal],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()
}

function edit_ACL(){

  let data = {
    "version":"1.0",
    "addr": EDIT_ACL_MODAL.address.get(),
    "desc": EDIT_ACL_MODAL.desc.get()
  }
  
  edit_reset = EDIT_ACL_MODAL.reset.bind(EDIT_ACL_MODAL)

  let rda = function(){
    refresh_datatable_acls()
  }

  ENTITY = __EMPOWER_WEBUI.ENTITY.ACL

  REST_REQ(ENTITY).configure_PUT({
    data: data,
    key: data.addr,
    success: [ empower_log_response, empower_alert_generate_success, 
      edit_reset, rda ],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function trigger_remove_acl_modal( acl_key ) {

  show_remove_modal = function(data){

    REMOVE_ACL_MODAL.address.set(data.addr)
    REMOVE_ACL_MODAL.desc.set(data.desc)

    REMOVE_ACL_MODAL.get_$instance().modal({show:true})
  }

  ENTITY = __EMPOWER_WEBUI.ENTITY.ACL

  REST_REQ(ENTITY).configure_GET({
    key: acl_key,
    success: [ empower_log_response, show_remove_modal],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function remove_ACL(){

  let key = REMOVE_ACL_MODAL.address.get()
  
  REMOVE_ACL_MODAL.reset()

  let rda = function(){
    refresh_datatable_acls()
  }

  ENTITY = __EMPOWER_WEBUI.ENTITY.ACL

  REST_REQ(ENTITY).configure_DELETE({
    key: key,
    success: [
      empower_log_response, empower_alert_generate_success, rda ],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function remove_ALL_ACLs(){

  let rda = function(){
    refresh_datatable_acls()
  }

  ENTITY = __EMPOWER_WEBUI.ENTITY.ACL

  REST_REQ(ENTITY).configure_DELETE({
    success: [
      empower_log_response, empower_alert_generate_success, rda ],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function format_datatable_wifi_slices_data( data ) {

  let wifi_slices = {}
  if (CF._is_there(data.wifi_slices)){

    wifi_slices = data.wifi_slices
    
  }

  $.each( wifi_slices, function( key, val ) {

    let amsdu_aggregation = "-"
    let quantum = "-"
    let sta_scheduler = "-"
    if (CF._is_there(val.properties)){
      let prop = val.properties
      amsdu_aggregation = prop.amsdu_aggregation
      quantum = prop.quantum
      sta_scheduler = prop.sta_scheduler
      OPTIONS_STA_SCHEDULER_WIFI.forEach(function(option){
        if (parseInt(option.value) === parseInt(sta_scheduler)){
          sta_scheduler = sta_scheduler + "<br><span class='font-italic text-sm'>" + option.label + "</span>"
        }
      })
    }
    
    // let properties = "-"
    // if (CF._is_there(val.properties)){
    //   properties = ""
    //   let counter = 0
    //   $.each(val.properties, function(prop_key, prop_value){
    //     if (prop_key === "sta_scheduler"){
    //       let value = prop_value
    //       OPTIONS_STA_SCHEDULER_WIFI.forEach(function(option){
    //         if (parseInt(option.value) === parseInt(value)){
    //           prop_value = prop_value+', <span class="font-italic">'+option.label+'<span>'
    //         }
    //       })
    //     }
    //     properties += ""+
    //     "<p class='py-1 my-0'><b class='pr-1'>"+prop_key+":</b>"+ prop_value + "</p>"
    //     counter++
    //   })
    //   if (counter === 0){
    //     properties = "-"
    //   }
    // }

    let devices = "-"
    if (CF._is_there(val.devices)){
      devices = ""
      let counter = 0
      $.each(val.devices, function(dev_key, dev_data){
        devices += ""+
        "<p class='pt-2 my-0'><i class='fas fa-hashtag fa-x1 fa-fw mr-1'></i><b class='pr-1'>"+dev_key+"</b></p>"
        counter++
        $.each(val.devices[dev_key], function(prop_key, prop_value){
          if (val.devices[dev_key][prop_key] != val.properties[prop_key]){
            if (prop_key === "sta_scheduler"){
              let value = prop_value
              OPTIONS_STA_SCHEDULER_WIFI.forEach(function(option){
                if (parseInt(option.value) === parseInt(value)){
                  prop_value = prop_value+', <span class="font-italic">'+option.label+'<span>'
                }
              })
            }
            devices += ""+
            "<p class='my-0 small'><b class='pr-1'>"+prop_key+":</b>"+ prop_value + "</p>"
          }
        })
      })
      if (counter === 0){
        devices = "-"
      }
    }

    let actions = ""+
      '<button class="btn btn-sm btn-warning shadow-sm mr-xl-1 mb-md-1 m-1" '+
      'onclick="trigger_mng_slice_modal(\'EDIT\',\'WIFI\',\''+val['slice_id']+'\')">'+
      '<i class="fas fa-edit fa-sm fa-fw text-white-50 mr-xl-1 m-1"></i><span class="d-none d-xl-inline">Edit</span></button>'+
      '<button class="btn btn-sm btn-danger shadow-sm mb-xl-1 m-1" '+
      'onclick="trigger_mng_slice_modal(\'DELETE\',\'WIFI\',\''+val['slice_id']+'\')">'+
      '<i class="fas fa-trash fa-sm fa-fw text-white-50 mr-xl-1 m-1"></i><span class="d-none d-xl-inline">Remove</span></button>'

    DATATABLE_WIFI_SLICES.row.add([
        val['slice_id'],
        // properties,
        amsdu_aggregation,
        quantum,
        sta_scheduler,
        devices,
        actions
    ] )

  });

  DATATABLE_WIFI_SLICES.draw(true)

  $( "#" + VALUE__WIFI_SLICES).text(Object.keys(wifi_slices).length)

}

function refresh_datatable_wifi_slices(data=null) {

  // console.log("refresh_datatable_wifi_slices, data: ", data)

  DATATABLE_WIFI_SLICES.clear();

  if (CF._is_there(data)){
    format_datatable_wifi_slices_data(data)
  }
  else{

    ENTITY = __EMPOWER_WEBUI.ENTITY.PROJECT

    REST_REQ(ENTITY).configure_GET({
      key: __EMPOWER_WEBUI.PROJECT.ID,
      success: [ empower_log_response, format_datatable_wifi_slices_data],
      error: [ empower_log_response,  empower_alert_generate_error ]
    })
    .perform()
  }
}

// function trigger_edit_wifi_slice_modal( ws_key ) {

//   not_yet_implemented("trigger_edit_wifi_slice_modal")
// }

function trigger_remove_wifi_slice_modal( ws_key ) {

  // not_yet_implemented("trigger_remove_wifi_slice_modal")

  ENTITY = __EMPOWER_WEBUI.ENTITY.SLICE.WIFI_SLICE

  let refresh_datatable_wifi_slices_no_data = function(){
    refresh_datatable_wifi_slices()
  }

  REST_REQ(ENTITY).configure_DELETE({
    key: ws_key,
    success: [ empower_log_response, empower_alert_generate_success,
               refresh_datatable_wifi_slices_no_data],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function format_datatable_lte_slices_data( data ) {

  let lte_slices = {}
  if (CF._is_there(data.lte_slices)){

    lte_slices = data.lte_slices
    
  }

  $.each( lte_slices, function( key, val ) {

    

    let rbgs = "-"
    let ue_scheduler = "-"
    if (CF._is_there(val.properties)){
      let prop = val.properties
      rbgs = prop.rbgs
      ue_scheduler = prop.ue_scheduler
      OPTIONS_UE_SCHEDULER_LTE.forEach(function(option){
        if (parseInt(option.value) === parseInt(ue_scheduler)){
          ue_scheduler = ue_scheduler + "<br><span class='font-italic text-sm'>" + option.label + "</span>"
        }
      })
    }

    // let properties = "-"
    // if (CF._is_there(val.properties)){
    //   properties = ""
    //   let counter = 0
    //   $.each(val.properties, function(prop_key, prop_value){
    //     if (prop_key === "ue_scheduler"){
    //       let value = prop_value
    //       OPTIONS_UE_SCHEDULER_LTE.forEach(function(option){
    //         if (parseInt(option.value) === parseInt(value)){
    //           prop_value = prop_value+', <span class="font-italic">'+option.label+'<span>'
    //         }
    //       })
    //     }
    //     properties += ""+
    //     "<p class='py-1 my-0'><b class='pr-1'>"+prop_key+":</b>"+ prop_value + "</p>"
    //     counter++
    //   })
    //   if (counter === 0){
    //     properties = "-"
    //   }
    // }

    let devices = "-"
    if (CF._is_there(val.devices)){
      devices = ""
      let counter = 0
      $.each(val.devices, function(dev_key, dev_data){
        devices += ""+
        "<p class='pt-2 my-0'><i class='fas fa-hashtag fa-x1 fa-fw mr-1'></i><b class='pr-1'>"+dev_key+"</b></p>"
        counter++
        $.each(val.devices[dev_key], function(prop_key, prop_value){
          if (val.devices[dev_key][prop_key] != val.properties[prop_key]){
            if (prop_key === "sta_scheduler"){
              let value = prop_value
              OPTIONS_UE_SCHEDULER_LTE.forEach(function(option){
                if (parseInt(option.value) === parseInt(value)){
                  prop_value = prop_value+', <span class="font-italic">'+option.label+'<span>'
                }
              })
            }
            devices += ""+
            "<p class='my-0 small'><b class='pr-1'>"+prop_key+":</b>"+ prop_value + "</p>"
          }
        })
      })
      if (counter === 0){
        devices = "-"
      }
    }

    let actions = ""+
      '<button class="btn btn-sm btn-warning shadow-sm mr-xl-1 mb-md-1 m-1" '+
      'onclick="trigger_mng_slice_modal(\'EDIT\',\'LTE\',\''+val['slice_id']+'\')">'+
      '<i class="fas fa-edit fa-sm fa-fw text-white-50 mr-xl-1 m-1"></i><span class="d-none d-xl-inline">Edit</span></button>'+
      '<button class="btn btn-sm btn-danger shadow-sm mb-xl-1 m-1" '+
      'onclick="trigger_mng_slice_modal(\'DELETE\',\'LTE\',\''+val['slice_id']+'\')">'+
      '<i class="fas fa-trash fa-sm fa-fw text-white-50 mr-xl-1 m-1"></i><span class="d-none d-xl-inline">Remove</span></button>'

    DATATABLE_LTE_SLICES.row.add([
        val['slice_id'],
        // properties,
        rbgs,
        ue_scheduler,
        devices,
        actions
    ] )

  });

  DATATABLE_LTE_SLICES.draw(true)

  $( "#" + VALUE__LTE_SLICES).text(Object.keys(lte_slices).length)

}

function refresh_datatable_lte_slices(data=null) {

  // console.log("refresh_datatable_lte_slices, data: ", data)

  DATATABLE_LTE_SLICES.clear();

  if (CF._is_there(data)){
    format_datatable_lte_slices_data(data)
  }
  else{

    ENTITY = __EMPOWER_WEBUI.ENTITY.PROJECT

    REST_REQ(ENTITY).configure_GET({
      key: __EMPOWER_WEBUI.PROJECT.ID,
      success: [ empower_log_response, format_datatable_lte_slices_data],
      error: [ empower_log_response,  empower_alert_generate_error ]
    })
    .perform()
  }
}

function trigger_edit_lte_slice_modal( ls_key ) {

  not_yet_implemented("trigger_edit_lte_slice_modal")
}

function trigger_remove_lte_slice_modal( ls_key ) {

  not_yet_implemented("trigger_remove_lte_slice_modal")
}

function refresh_all(){

  let project_id = __EMPOWER_WEBUI.PROJECT.ID
  
  ENTITY = __EMPOWER_WEBUI.ENTITY.PROJECT
  
  REST_REQ(ENTITY).configure_GET({
    key: project_id,
    success: [ empower_log_response, build_and_set_properties_body,
      set_what_is_visible, 
      refresh_datatable_acls, 
      refresh_datatable_wifi_slices, 
      refresh_datatable_lte_slices ],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function not_yet_implemented(what=null){
  let message = "NOT IMPLEMENTED, yet" 
  if (CF._is_there(what)){
    message = "'" + what + "' "+ message
  }
  console.warn(message)
}






function fill_with_slice_id_options(){
  let select = $("#mng_slice_id")
  select.empty()
  DCSP_ALLOWED_VALUES.forEach(function(dscp){
    select.append(new Option(dscp, parseInt(dscp)))
  })
}

function fill_with_scheduler_options(select, tech){
  select.empty()
  let arr = []
  switch(tech){
    case "LTE":
      arr = OPTIONS_UE_SCHEDULER_LTE
      break;

    case "WIFI":
      arr = OPTIONS_STA_SCHEDULER_WIFI
      break;

  }
  arr.forEach(function(option){
    select.append(new Option(option.label, option.value))
  })
}

function adjust_mng_slice_modal_buttons_and_tables(tech, op){
  
  CF._hide($("#mng_wifi_slc_create_btn"))
  CF._hide($("#mng_wifi_slc_edit_btn"))
  CF._hide($("#mng_wifi_slc_delete_btn"))
  CF._hide($("#mng_lte_slc_create_btn"))
  CF._hide($("#mng_lte_slc_edit_btn"))
  CF._hide($("#mng_lte_slc_delete_btn"))
  CF._hide($("#dataTable_MNG_WIFI_SLICE_Modal_wrapper"))
  // console.log("HIDE WIFI SLICE DATATABLE")
  DATATABLE_MNG_WIFI_SLICE_MODAL.clear()
  DATATABLE_MNG_WIFI_SLICE_MODAL.draw()
  CF._hide($("#dataTable_MNG_LTE_SLICE_Modal_wrapper"))
  // console.log("HIDE LTE SLICE DATATABLE")
  DATATABLE_MNG_LTE_SLICE_MODAL.clear()
  DATATABLE_MNG_LTE_SLICE_MODAL.draw()

  CF._hide($("#mng_wifi_default_props"))
  CF._hide($("#mng_lte_default_props"))


  let t = ""
  switch(tech){
    case "LTE":
      t = "lte"
      CF._show($("#dataTable_MNG_LTE_SLICE_Modal_wrapper"))
      // console.log("SHOW LTE SLICE DATATABLE")
      CF._show($("#mng_lte_default_props"))
      break
    case "WIFI":
      t = "wifi"
      CF._show($("#dataTable_MNG_WIFI_SLICE_Modal_wrapper"))
      // console.log("SHOW WIFI SLICE DATATABLE")
      CF._show($("#mng_wifi_default_props"))
      break
  }
  switch(op){
    case "CREATE":
      CF._show($("#mng_"+ t +"_slc_create_btn"))
      break
    case "EDIT":
      CF._show($("#mng_"+ t +"_slc_edit_btn"))
      break
    case "DELETE":
      CF._show($("#mng_"+ t +"_slc_delete_btn"))
      break
  }
}

function refresh_mng_slice_modal_datatable(tech, op="CREATE", reference_device=null){
  ENTITY = null

  switch(tech){
    case "LTE":
      ENTITY = __EMPOWER_WEBUI.ENTITY.DEVICE.VBS
      break;
    case "WIFI":
      ENTITY = __EMPOWER_WEBUI.ENTITY.DEVICE.WTP    
      break;
      default:
        console.log("Unknown tech: ", tech)
  }

  let show_mng_slice_modal = function(data){
    format_mng_slice_modal_datatable(tech, data, op, reference_device)
    MNG_SLICE_MODAL.modal({show:true})
  }
 

  REST_REQ(ENTITY).configure_GET({
    success: [ empower_log_response, show_mng_slice_modal],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function format_mng_slice_modal_datatable( tech, data, op, reference_device) {

  console.log("format_mng_slice_modal_datatable[", tech, ",", op,",",reference_device,"] data: ", data)

  let device_list = {}

  if (CF._is_there(data)){

    device_list = data
    
  }

  let dt = null
  switch(tech){
    case "LTE":
      dt = DATATABLE_MNG_LTE_SLICE_MODAL
      break;
    case "WIFI":
      dt = DATATABLE_MNG_WIFI_SLICE_MODAL
      break;
  }

  dt.clear()

  index = 0

  $.each( device_list, function( key, val ) {

    let add_row = true
    
    let checkbox = null
    if (tech === "WIFI"){
      checkbox = '<input type="checkbox" class="form-check-input position-static" id="checkbox_' + index + 
                    '" onclick="toggle_properties(\'WIFI\',\''+index+'\')"></input>'
    }
    else if  (tech === "LTE"){
      checkbox = '<input type="checkbox" class="form-check-input position-static" id="checkbox_' + index + 
                    '" onclick="toggle_properties(\'LTE\',\''+index+'\')"></input>'
    }

    let description = '<div><b id="device_id_'+index+'">'+key+'</b><br><span class="font-italic">'+val.desc+'</i></span>'

    let properties = ''

    if (tech === "WIFI"){
      properties = '<div class="form-group pr-2 d-none" id="properties_device_'+index+'">' +
            
        '<div class="form-group row pr-2">'+
          '<label class="col-5 my-auto pl-4 font-italic text-right pr-4">'+
            '<i class="fas fa-hourglass fa-1x fa-fw d-none"></i>'+
            '<span>Quantum</span>'+
          '</label>'+
          '<input class="form-control col-6" id="mng_quantum_device_'+index+'" placeholder="Quantum">'+
        '</div>'+

        '<div class="form-group row pr-2">'+
          '<label class="col-5 my-auto pl-4 font-italic text-right pr-4">'+
            '<i class="fas fa-clipboard-list fa-x1 fa-fw d-none"></i>'+
            '<span>STA Scheduler</span></label>'+
          '<select class="form-control col-6" id="mng_sta_scheduler_device_'+index+'">'+
          '</select>'+
        '</div>'+

        '<div class="form-group row pr-2">'+
          '<label class="col-5 my-auto pl-4 font-italic text-right pr-4">'+
            '<i class="far fa-plus-square fa-x1 fa-fw d-none"></i>'+
            '<span class="small">A-MSDU Aggr.</span></label>'+
          '<div class="custom-control custom-switch col-6">'+
            '<input type="checkbox" class="custom-control-input" id="mng_amsdu_aggregation_device_'+index+'">'+
            '<label class="custom-control-label" for="mng_amsdu_aggregation_device_'+index+'"></label>'+
          '</div>'+
        '</div>'+
      '</div>'
    }
    else if  (tech === "LTE"){
      properties = '<div class="form-group pr-2 d-none" id="properties_device_'+index+'">' +
            
        '<div class="form-group row pr-2">'+
          '<label class="col-5 my-auto pl-4 font-italic text-right pr-4">'+
            '<i class="fas fa-hourglass fa-1x fa-fw d-none"></i>'+
            '<span>RBGS</span>'+
          '</label>'+
          '<input class="form-control col-6" id="mng_rbgs_device_'+index+'" placeholder="RBGS">'+
        '</div>'+

        '<div class="form-group row pr-2">'+
          '<label class="col-5 my-auto pl-4 font-italic text-right pr-4">'+
            '<i class="fas fa-clipboard-list fa-x1 fa-fw d-none"></i>'+
            '<span>UE Scheduler</span></label>'+
          '<select class="form-control col-6" id="mng_ue_scheduler_device_'+index+'">'+
          '</select>'+
        '</div>'+
      '</div>'
      // console.log("properties for ",tech,":", properties)
    }

    if (CF._is_there(reference_device)){
      if (op === 'DELETE'){
        let params = reference_device.devices[key]
        if (!CF._is_there(params)){
          add_row = false
        }
      }
    }

    if (add_row){
      dt.row.add([
          checkbox,
          description,
          properties
      ] )

      index += 1
    }

  });

  dt.draw(true)

  $(document).ready(function() {
    if (CF._is_there(reference_device)){
      if (tech === "WIFI"){
        let table_length = DATATABLE_MNG_WIFI_SLICE_MODAL.rows().count()
        console.log("Table length:", table_length)
        for(let index = 0; index < table_length; index++){
          let device_id = $("#device_id_"+index).text()
          let params = reference_device.devices[device_id]
          if (CF._is_there(params)){
            $("#checkbox_"+index).prop("checked", true)
            $("#mng_quantum_device_"+index).val(params.quantum)
            let select = $("#mng_sta_scheduler_device_"+index)
            fill_with_scheduler_options(select, tech)
            select.val(params.sta_scheduler)
            $("#mng_amsdu_aggregation_device_"+index).prop("checked",params.amsdu_aggregation)
            CF._show($("#properties_device_"+index))
            if (op === 'DELETE'){
              CF._disable($("#checkbox_"+index))
              CF._disable($("#mng_quantum_device_"+index))
              CF._disable(select)
              CF._disable($("#mng_amsdu_aggregation_device_"+index))
            }
          }
        }
      }
      else if (tech === "LTE"){
        let table_length = DATATABLE_MNG_LTE_SLICE_MODAL.rows().count()
        console.log("Table length:", table_length)
        for(let index = 0; index < table_length; index++){
          let device_id = $("#device_id_"+index).text()
          let params = reference_device.devices[device_id]
          if (CF._is_there(params)){
            $("#checkbox_"+index).prop("checked", true)
            $("#mng_rbgs_device_"+index).val(params.rbgs)
            let select = $("#mng_ue_scheduler_device_"+index)
            fill_with_scheduler_options(select, tech)
            select.val(params.ue_scheduler)
            CF._show($("#properties_device_"+index))
            if (op === 'DELETE'){
              CF._disable($("#checkbox_"+index))
              CF._disable($("#mng_rbgs_device_"+index))
              CF._disable(select)
            }
          }
        }
      }
    }
  })
}

function trigger_mng_slice_modal(op, tech, key=null){

  adjust_mng_slice_modal_buttons_and_tables(tech, op)

  fill_with_slice_id_options()

  let select = null
  let configure_modal = null

  switch(tech){
    case "LTE":
      switch(op){
        case "CREATE":

          console.log("trigger_mng_slice_modal: ", tech, op)

          $('#MNG_SLICE_Modal_title').text("Create LTE Slice")
          $('#mng_table_title').html("<b>Custom Configurations</b>")

          select = $('#mng_ue_scheduler')
          fill_with_scheduler_options(select, "LTE")
    
          $('#mng_slice_id').val("")
          CF._enable($('#mng_slice_id'))
          $('#mng_rbgs').val(DEFAULT_RBGS_VALUE)
          CF._enable($('#mng_rbgs'))
          $('#mng_ue_scheduler').val(DEFAULT_UE_SCHEDULER_VALUE)
          CF._enable($('#mng_ue_scheduler'))
          
          refresh_mng_slice_modal_datatable(tech)
          
          break
        case "EDIT":

          console.log("trigger_mng_slice_modal: ", tech, op)

          ENTITY = __EMPOWER_WEBUI.ENTITY.SLICE.LTE_SLICE

          configure_modal = function(data){
            $('#MNG_SLICE_Modal_title').text("Edit LTE Slice")
            $('#mng_table_title').html("<b>Custom Configurations</b>")

            select = $('#mng_ue_scheduler')
            fill_with_scheduler_options(select, "LTE")
      
            $('#mng_slice_id').val(key)
            CF._disable($('#mng_slice_id'))
            $('#mng_rbgs').val(data.properties.rbgs)
            CF._enable($('#mng_rgbs'))
            $('#mng_ue_scheduler').val(data.properties.ue_scheduler)
            CF._enable($('#ue_scheduler'))

            refresh_mng_slice_modal_datatable(tech, op, data)
          }
    
          REST_REQ(ENTITY).configure_GET({
            key: key,
            success: [ empower_log_response, configure_modal ],
            error: [ empower_log_response,  empower_alert_generate_error ]
          })
          .perform()
          
          break
        case "DELETE":

          console.log("trigger_mng_slice_modal: ", tech, op)

          ENTITY = __EMPOWER_WEBUI.ENTITY.SLICE.LTE_SLICE

          configure_modal = function(data){
            $('#MNG_SLICE_Modal_title').text("Delete LTE Slice")
            $('#mng_table_title').html("<b>Custom Configurations</b>")

            select = $('#mng_ue_scheduler')
            fill_with_scheduler_options(select, "LTE")
      
            $('#mng_slice_id').val(key)
            CF._disable($('#mng_slice_id'))
            $('#mng_rbgs').val(data.properties.rbgs)
            CF._disable($('#mng_rbgs'))
            $('#mng_ue_scheduler').val(data.properties.ue_scheduler)
            CF._disable($('#mng_ue_scheduler'))

            refresh_mng_slice_modal_datatable(tech, op, data)
          }
    
          REST_REQ(ENTITY).configure_GET({
            key: key,
            success: [ empower_log_response, configure_modal ],
            error: [ empower_log_response,  empower_alert_generate_error ]
          })
          .perform()
          
          break
        default:
          console.log("Unknown op", op)
      }
      break
    case "WIFI":
      switch(op){
        
        case "CREATE":

          console.log("trigger_mng_slice_modal: ", tech, op)

          $('#MNG_SLICE_Modal_title').text("Create WiFi Slice")
          $('#mng_table_title').html("<b>Custom Configurations</b>")

          select = $('#mng_sta_scheduler')
          fill_with_scheduler_options(select, "WIFI")
    
          $('#mng_slice_id').val("")
          CF._enable($('#mng_slice_id'))
          $('#mng_quantum').val(DEFAULT_QUANTUM_VALUE)
          CF._enable($('#mng_quantum'))
          $('#mng_sta_scheduler').val(DEFAULT_STA_SCHEDULER_VALUE)
          CF._enable($('#mng_sta_scheduler'))
          $('#mng_amsdu_aggregation').val(DEFAULT_AMSDU_AGGREGATION_VALUE)
          CF._enable($('#mng_amsdu_aggregation'))
          
          refresh_mng_slice_modal_datatable(tech)
    
          break
        case "EDIT":

          console.log("trigger_mng_slice_modal: ", tech, op, key)

          ENTITY = __EMPOWER_WEBUI.ENTITY.SLICE.WIFI_SLICE

          configure_modal = function(data){
            $('#MNG_SLICE_Modal_title').text("Edit WiFi Slice")
            $('#mng_table_title').html("<b>Custom Configurations</b>")

            select = $('#mng_sta_scheduler')
            fill_with_scheduler_options(select, "WIFI")
      
            $('#mng_slice_id').val(key)
            CF._disable($('#mng_slice_id'))
            $('#mng_quantum').val(data.properties.quantum)
            CF._enable($('#mng_quantum'))
            $('#mng_sta_scheduler').val(data.properties.sta_scheduler)
            CF._enable($('#sta_scheduler'))
            $('#mng_amsdu_aggregation').val(data.properties.amsdu_aggregation)
            CF._enable($('#amsdu_aggregation'))

            refresh_mng_slice_modal_datatable(tech, op, data)
          }
    
          REST_REQ(ENTITY).configure_GET({
            key: key,
            success: [ empower_log_response, configure_modal ],
            error: [ empower_log_response,  empower_alert_generate_error ]
          })
          .perform()

          break
        case "DELETE":

          console.log("trigger_mng_slice_modal: ", tech, op)

          ENTITY = __EMPOWER_WEBUI.ENTITY.SLICE.WIFI_SLICE

          configure_modal = function(data){
            $('#MNG_SLICE_Modal_title').text("Delete WiFi Slice")
            $('#mng_table_title').html("<b>Custom Configurations</b>")

            select = $('#mng_sta_scheduler')
            fill_with_scheduler_options(select, "WIFI")
      
            $('#mng_slice_id').val(key)
            CF._disable($('#mng_slice_id'))
            $('#mng_quantum').val(data.properties.quantum)
            CF._disable($('#mng_quantum'))
            $('#mng_sta_scheduler').val(data.properties.sta_scheduler)
            CF._disable($('#mng_sta_scheduler'))
            $('#mng_amsdu_aggregation').val(data.properties.amsdu_aggregation)
            CF._disable($('#mng_amsdu_aggregation'))

            refresh_mng_slice_modal_datatable(tech, op, data)
          }
    
          REST_REQ(ENTITY).configure_GET({
            key: key,
            success: [ empower_log_response, configure_modal ],
            error: [ empower_log_response,  empower_alert_generate_error ]
          })
          .perform()
          break
        default:
          console.log("Unknown op", op)
      }
      break;
    default:
      console.log("Unknown tech", tech)
      break;
  }
}


function mng_WIFI_SLICE(op){
  let data = {}
  let table_length = 0
  let refresh_datatable_wifi_slices_no_data = function(){
    refresh_datatable_wifi_slices()
  }
  switch(op){
    case "CREATE":
      data = {}
  
      data.version = "1.0"

      data.slice_id = parseInt($("#mng_slice_id").val())

      data.properties ={}
      data.properties.quantum = parseInt($("#mng_quantum").val())
      data.properties.sta_scheduler = parseInt($("#mng_sta_scheduler").val())
      data.properties.amsdu_aggregation = $("#mng_amsdu_aggregation").prop("checked")

      data.devices = {}
      table_length = DATATABLE_MNG_WIFI_SLICE_MODAL.rows().count()
      for(let key = 0; key < table_length; key++){

        let checkbox = $("#checkbox_"+key)
        if (checkbox.prop("checked")){
          let q = $("#mng_quantum_device_"+key).val()
          let ss = $("#mng_sta_scheduler_device_"+key).val()
          let aa = $("#mng_amsdu_aggregation_device_"+key).prop("checked")
          let device_id = $("#device_id_"+key).text()
          data.devices[device_id] = {}
          // if ((q != data.properties.quantum) ||
          //     (ss != data.properties.sta_scheduler) ||
          //     (aa != data.properties.amsdu_aggregation)){
            let dev_prop = data.devices[device_id]
            // if (q != data.properties.quantum){
              dev_prop.quantum = parseInt(q)
            // }
            // if (ss != data.properties.sta_scheduler){
              dev_prop.sta_scheduler = parseInt(ss)
            // }
            // if (aa != data.properties.amsdu_aggregation){
              dev_prop.amsdu_aggregation = aa
          //   }
          // }
        }
      }

      console.log("slice data: ",data)

      ENTITY = __EMPOWER_WEBUI.ENTITY.SLICE.WIFI_SLICE

      REST_REQ(ENTITY).configure_POST({
        data: JSON.stringify(data),
        success: [ empower_log_response, empower_alert_generate_success,
                  refresh_datatable_wifi_slices_no_data],
        error: [ empower_log_response,  empower_alert_generate_error ]
      })
      .perform()
      break
    case "EDIT":

      data = {}
  
      data.version = "1.0"

      data.slice_id = parseInt($("#mng_slice_id").val())

      data.properties ={}
      data.properties.quantum = parseInt($("#mng_quantum").val())
      data.properties.sta_scheduler = parseInt($("#mng_sta_scheduler").val())
      data.properties.amsdu_aggregation = $("#mng_amsdu_aggregation").prop("checked")

      data.devices = {}
      table_length = DATATABLE_MNG_WIFI_SLICE_MODAL.rows().count()
      for(let key = 0; key < table_length; key++){

        let checkbox = $("#checkbox_"+key)
        if (checkbox.prop("checked")){
          let q = $("#mng_quantum_device_"+key).val()
          let ss = $("#mng_sta_scheduler_device_"+key).val()
          let aa = $("#mng_amsdu_aggregation_device_"+key).prop("checked")
          let device_id = $("#device_id_"+key).text()
          data.devices[device_id] = {}
          // if ((q != data.properties.quantum) ||
          //     (ss != data.properties.sta_scheduler) ||
          //     (aa != data.properties.amsdu_aggregation)){
            let dev_prop = data.devices[device_id]
            // if (q != data.properties.quantum){
              dev_prop.quantum = parseInt(q)
            // }
            // if (ss != data.properties.sta_scheduler){
              dev_prop.sta_scheduler = parseInt(ss)
            // }
            // if (aa != data.properties.amsdu_aggregation){
              dev_prop.amsdu_aggregation = aa
          //   }
          // }
        }
      }

      console.log("slice data: ",data)

      ENTITY = __EMPOWER_WEBUI.ENTITY.SLICE.WIFI_SLICE

      REST_REQ(ENTITY).configure_PUT({
        key: data.slice_id,
        data: JSON.stringify(data),
        success: [ empower_log_response, empower_alert_generate_success,
                  refresh_datatable_wifi_slices_no_data],
        error: [ empower_log_response,  empower_alert_generate_error ]
      })
      .perform()
      break

    case "DELETE":

      ENTITY = __EMPOWER_WEBUI.ENTITY.SLICE.WIFI_SLICE

      REST_REQ(ENTITY).configure_DELETE({
        key: parseInt($("#mng_slice_id").val()),
        success: [ empower_log_response, empower_alert_generate_success,
                  refresh_datatable_wifi_slices_no_data],
        error: [ empower_log_response,  empower_alert_generate_error ]
      })
      .perform()
      break

    default:
      console.log("Unknown op", op)
  }
}

function mng_LTE_SLICE(op){
  let data = {}
  let table_length = 0
  let refresh_datatable_lte_slices_no_data = function(){
    refresh_datatable_lte_slices()
  }
  switch(op){
    case "CREATE":
      data = {}
  
      data.version = "1.0"

      data.slice_id = parseInt($("#mng_slice_id").val())

      data.properties ={}
      data.properties.rbgs = parseInt($("#mng_rbgs").val())
      data.properties.ue_scheduler = parseInt($("#mng_ue_scheduler").val())

      data.devices = {}
      table_length = DATATABLE_MNG_LTE_SLICE_MODAL.rows().count()
      for(let key = 0; key < table_length; key++){

        let checkbox = $("#checkbox_"+key)
        if (checkbox.prop("checked")){
          let r = $("#mng_rbgs_device_"+key).val()
          let us = $("#mng_ue_scheduler_device_"+key).val()
          let device_id = $("#device_id_"+key).text()
          data.devices[device_id] = {}
          // if ((r != data.properties.rbgs) ||
          //     (us != data.properties.ue_scheduler)){
            let dev_prop = data.devices[device_id]
            // if (r != data.properties.rbgs){
              dev_prop.rbgs = parseInt(r)
            // }
            // if (us != data.properties.ue_scheduler){
              dev_prop.ue_scheduler = parseInt(us)
          //   }
          // }
        }
      }

      console.log("slice data: ",data)

      ENTITY = __EMPOWER_WEBUI.ENTITY.SLICE.LTE_SLICE

      REST_REQ(ENTITY).configure_POST({
        data: JSON.stringify(data),
        success: [ empower_log_response, empower_alert_generate_success,
                  refresh_datatable_lte_slices_no_data],
        error: [ empower_log_response,  empower_alert_generate_error ]
      })
      .perform()
      break
    case "EDIT":
      data = {}

      data.version = "1.0"

      data.slice_id = parseInt($("#mng_slice_id").val())

      data.properties ={}
      data.properties.rbgs = parseInt($("#mng_rbgs").val())
      data.properties.ue_scheduler = parseInt($("#mng_ue_scheduler").val())

      data.devices = {}
      table_length = DATATABLE_MNG_LTE_SLICE_MODAL.rows().count()
      for(let key = 0; key < table_length; key++){

        let checkbox = $("#checkbox_"+key)
        if (checkbox.prop("checked")){
          let r = $("#mng_rbgs_device_"+key).val()
          let us = $("#mng_ue_scheduler_device_"+key).val()
          let device_id = $("#device_id_"+key).text()
          data.devices[device_id] = {}
          // if ((r != data.properties.rbgs) ||
          //     (us != data.properties.ue_scheduler)){
            let dev_prop = data.devices[device_id]
            // if (r != data.properties.rbgs){
              dev_prop.rbgs = parseInt(r)
            // }
            // if (us != data.properties.ue_scheduler){
              dev_prop.ue_scheduler = parseInt(us)
          //   }
          // }
        }
      }

      console.log("slice data: ",data)

      ENTITY = __EMPOWER_WEBUI.ENTITY.SLICE.LTE_SLICE

      REST_REQ(ENTITY).configure_PUT({
        key: data.slice_id,
        data: JSON.stringify(data),
        success: [ empower_log_response, empower_alert_generate_success,
                  refresh_datatable_lte_slices_no_data],
        error: [ empower_log_response,  empower_alert_generate_error ]
      })
      .perform()
      break

    case "DELETE":

      ENTITY = __EMPOWER_WEBUI.ENTITY.SLICE.LTE_SLICE

      REST_REQ(ENTITY).configure_DELETE({
        key: parseInt($("#mng_slice_id").val()),
        success: [ empower_log_response, empower_alert_generate_success,
                  refresh_datatable_lte_slices_no_data],
        error: [ empower_log_response,  empower_alert_generate_error ]
      })
      .perform()
      break

    default:
      console.log("Unknown op", op)
  }
}


function toggle_properties(tech, key){
  // console.log("toggle_properties", tech, key)
  let checkbox = $("#checkbox_"+key)
  if (checkbox.is(":checked")){
    if (tech === 'WIFI'){
      $('#mng_quantum_device_'+key).val($('#mng_quantum').val())
      let select =  $('#mng_sta_scheduler_device_'+key)
      select.empty()
      fill_with_scheduler_options(select, tech)
      select.val($('#mng_sta_scheduler').val())
      $('#mng_amsdu_aggregation_device_'+key).prop("checked", $('#mng_amsdu_aggregation').prop("checked"))
    }
    else if (tech === 'LTE'){
      $('#mng_rbgs_device_'+key).val($('#mng_rbgs').val())
      let select =  $('#mng_ue_scheduler_device_'+key)
      select.empty()
      fill_with_scheduler_options(select, tech)
      select.val($('#mng_ue_scheduler').val())
    }
    // console.log("SHOW",$("#properties_device_"+key))
    CF._show($("#properties_device_"+key))
  }
  else{
    // console.log("HIDE",$("#properties_device_"+key))
    CF._hide($("#properties_device_"+key))
  }
}

function update_quantum_on_cascade(){
  let value = ($('#mng_quantum').val())
  // if (CF._is_null(LAST_QUANTUM_VALUE)){
  //   LAST_QUANTUM_VALUE = value
  // }
  // let length = DATATABLE_MNG_WIFI_SLICE_MODAL.rows().count()
  // for(let key = 0; key < length; key++){
  //   if (LAST_QUANTUM_VALUE === $('#mng_quantum_device_'+key).val()){
  //     $('#mng_quantum_device_'+key).val(value)
  //   }
  // }
  LAST_QUANTUM_VALUE = value
}

function update_sta_scheduler_on_cascade(){
  let value = ($('#mng_sta_scheduler').val())
  // if (CF._is_null(LAST_STA_SCHEDULER_VALUE)){
  //   LAST_STA_SCHEDULER_VALUE = value
  // }
  // let length = DATATABLE_MNG_WIFI_SLICE_MODAL.rows().count()
  // for(let key = 0; key < length; key++){
  //   if (LAST_STA_SCHEDULER_VALUE === $('#mng_sta_scheduler_device_'+key).val()){
  //     $('#mng_sta_scheduler_device_'+key).val(value)
  //   }
  // }
  LAST_STA_SCHEDULER_VALUE = value
}

function update_amsdu_aggregation_on_cascade(){
  let value = ($('#mng_amsdu_aggregation').prop("checked"))
  // if (CF._is_null(LAST_AMSDU_AGGREGATION_VALUE)){
  //   LAST_AMSDU_AGGREGATION_VALUE = value
  // }
  // let length = DATATABLE_MNG_WIFI_SLICE_MODAL.rows().count()
  // for(let key = 0; key < length; key++){
  //   if (LAST_AMSDU_AGGREGATION_VALUE === $('#mng_amsdu_aggregation_device_'+key).prop("checked")){
  //     $('#mng_amsdu_aggregation_device_'+key).prop("checked",value)
  //   }
  // }
  LAST_AMSDU_AGGREGATION_VALUE = value
}

function update_rbgs_on_cascade(){
  let value = ($('#mng_rbgs').val())
  // if (CF._is_null(LAST_RBGS_VALUE)){
  //   LAST_RBGS_VALUE = value
  // }
  // let length = DATATABLE_MNG_LTE_SLICE_MODAL.rows().count()
  // for(let key = 0; key < length; key++){
  //   if (LAST_RBGS_VALUE === $('#mng_rbgs_device_'+key).val()){
  //     $('#mng_rbgs_device_'+key).val(value)
  //   }
  // }
  LAST_RBGS_VALUE = value
}

function update_ue_scheduler_on_cascade(){
  let value = ($('#mng_ue_scheduler').val())
  // if (CF._is_null(LAST_UE_SCHEDULER_VALUE)){
  //   LAST_UE_SCHEDULER_VALUE = value
  // }
  // let length = DATATABLE_MNG_WIFI_SLICE_MODAL.rows().count()
  // for(let key = 0; key < length; key++){
  //   if (LAST_UE_SCHEDULER_VALUE === $('#mng_ue_scheduler_device_'+key).val()){
  //     $('#mng_ue_scheduler_device_'+key).val(value)
  //   }
  // }
  LAST_UE_SCHEDULER_VALUE = value
}

