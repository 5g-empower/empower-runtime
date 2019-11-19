$('#devices').removeClass('collapsed');
$('#collapseTwo').addClass('show');
$('#devices_vbses').addClass('active');

console.log("__EMPOWER_WEBUI",__EMPOWER_WEBUI)

$(document).ready(function() {

  ENTITY = __EMPOWER_WEBUI.ENTITY.DEVICE.VBS

  let fields = {
    address: {
      type: "TEXT"
    },
    desc: {
      type: "TEXT"
    },
  }

  ADD_MODAL = new WEBUI_Modal_Entity(
    __EMPOWER_WEBUI.MODAL.TYPE.ADD,
    ENTITY
  ).add_fields(fields)

  EDIT_MODAL = new WEBUI_Modal_Entity(
    __EMPOWER_WEBUI.MODAL.TYPE.EDIT,
    ENTITY
  ).add_fields(fields)

  REMOVE_MODAL = new WEBUI_Modal_Entity(
    __EMPOWER_WEBUI.MODAL.TYPE.REMOVE,
    ENTITY
  ).add_fields(fields)

  aoColumns = [
    { "sTitle": "Address" },
    { "sTitle": "Description" },
    { "sTitle": "Last seen" },
    { "sTitle": "Address" },
  ]

  if ( __EMPOWER_WEBUI.USER.USERNAME == "root" ) {
  aoColumns.push({ "sTitle": "Actions", "sClass": "text-center" })
  }

  DATATABLE = $('#dataTable').DataTable({
  "aoColumns": aoColumns
  });

  refresh_datatable();
});

ENTITY = null

function add() {

  let data = {
    "version":"1.0",
    "addr": ADD_MODAL.address.get(),
    "desc": ADD_MODAL.desc.get()
  }

  console.log("data: ",data)
  
  add_reset = ADD_MODAL.reset.bind(ADD_MODAL)

  REST_REQ(ENTITY).configure_POST({
    data: data,
    success: [ empower_log_response, empower_alert_generate_success, 
      add_reset, refresh_datatable ],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()

}

function trigger_edit_modal( vbs_key ) {

  show_edit_modal = function(data){

    EDIT_MODAL.address.set(data.addr)
    EDIT_MODAL.desc.set(data.desc)

    EDIT_MODAL.get_$instance().modal({show:true})
  }

  REST_REQ(ENTITY).configure_GET({
    key: vbs_key,
    success: [ empower_log_response, show_edit_modal],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()
}

function edit(){

  let data = {
    "version":"1.0",
    "addr": EDIT_MODAL.address.get(),
    "desc": EDIT_MODAL.desc.get()
  }
  
  edit_reset = EDIT_MODAL.reset.bind(EDIT_MODAL)

  REST_REQ(ENTITY).configure_PUT({
    data: data,
    key: data.addr,
    success: [ empower_log_response, empower_alert_generate_success, 
      edit_reset, refresh_datatable ],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function trigger_remove_modal( vbs_key ) {

  show_remove_modal = function(data){

    REMOVE_MODAL.address.set(data.addr)
    REMOVE_MODAL.desc.set(data.desc)

    REMOVE_MODAL.get_$instance().modal({show:true})
  }

  REST_REQ(ENTITY).configure_GET({
    key: vbs_key,
    success: [ empower_log_response, show_remove_modal],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function remove(){

  let key = REMOVE_MODAL.address.get()
  
  REMOVE_MODAL.reset()

  REST_REQ(ENTITY).configure_DELETE({
    key: key,
    success: [
      empower_log_response, empower_alert_generate_success, refresh_datatable ],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function format_datatable_data( data ) {

  connected = 0
  offline = 0
  online = 0

  $.each( data, function( key, val ) {

    if ( val['state'] == "online" ) {
      online += 1
    } else if ( val['state'] == "connected") {
      connected += 1
    } else {
      offline += 1
    }

    actions = "-"

    if ( __USERNAME == "root" ) {
      actions = ""+
      '<button class="btn btn-sm btn-warning shadow-sm mr-xl-1 mb-md-1 m-1" '+
      'onclick="trigger_edit_modal(\''+val['addr']+'\')">'+
      '<i class="fas fa-edit fa-sm fa-fw text-white-50 mr-xl-1 m-1"></i><span class="d-none d-xl-inline">Edit</span></button>'+
      '<button class="btn btn-sm btn-danger shadow-sm mb-xl-1 m-1" '+
      'onclick="trigger_remove_modal(\''+val['addr']+'\')">'+
      '<i class="fas fa-trash fa-sm fa-fw text-white-50 mr-xl-1 m-1"></i><span class="d-none d-xl-inline">Remove</span></button>'
    }

    connection = "-"
    last_seen = "-"

    if ( val['state'] == "online" ) {
        connection = val['connection']['addr']
        last_seen = val['last_seen']
    }

    DATATABLE.row.add([
        val['addr'],
        val['desc'],
        last_seen,
        connection,
        actions
    ] )

  });

  DATATABLE.draw(true)

  $("#offline").html(offline)
  $("#online").html(online)
  $("#connected").html(connected)
}

function refresh_datatable() {

  DATATABLE.clear();

  REST_REQ(ENTITY).configure_GET({
      success: [ empower_log_response, format_datatable_data],
      error: [ empower_log_response,  empower_alert_generate_error ]
    })
    .perform()
}