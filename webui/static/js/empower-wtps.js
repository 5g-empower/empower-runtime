$('#devices').removeClass('collapse');
$('#collapseTwo').addClass('show');
$('#devices_wtps').addClass('active');

$(document).ready(function() {

  ENTITY = EMPOWER_ENTITIES.DEVICE.WTP

  ID_ADD_MODAL = "add"+ENTITY+"Modal"
  ID_EDIT_MODAL = "edit"+ENTITY+"Modal"
  ID_REMOVE_MODAL = "remove"+ENTITY+"Modal"

  ID_ADD_ADDRESS = "add_address"
  ID_ADD_DESC = "add_desc"

  ID_EDIT_ADDRESS = "edit_address"
  ID_EDIT_DESC = "edit_desc"

  ID_REMOVE_ADDRESS = "remove_address"
  ID_REMOVE_DESC = "remove_desc"

  aoColumns = [
          { "sTitle": "Address" },
          { "sTitle": "Description" },
          { "sTitle": "Last seen" },
          { "sTitle": "Address" },
  ]

  if ( __USERNAME == "root" ) {
    aoColumns.push({ "sTitle": "Actions", "sClass": "text-center" })
  }

  t = $('#dataTable').DataTable({
      "aoColumns": aoColumns
  });

  refresh_devices();

});

ENTITY = null

function add() {

  $address = $("#"+ID_ADD_ADDRESS) 
  $desc = $("#"+ID_ADD_DESC)

  let data = {
    "version":"1.0",
    "addr": $address.val(),
    "desc": $desc.val()
  }
  $address.val("")
  $desc.val("")

  REST_REQ(ENTITY).configure_POST({
    data: data,
    success: [ empower_log_response, empower_alert_generate_success, refresh_devices],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()

}

function trigger_edit_modal( wtp_key ) {

  $edit_modal = $("#"+ID_EDIT_MODAL) 

  show_edit_modal = function(data){
    
    $address = $("#"+ID_EDIT_ADDRESS) 
    $desc = $("#"+ID_EDIT_DESC)

    $address.val(data.addr)
    $desc.val(data.desc)

    $edit_modal.modal({show:true})
  }

  REST_REQ(ENTITY).configure_GET({
    key: wtp_key,
    success: [ empower_log_response, show_edit_modal],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()
}

function edit(){
  $address = $("#"+ID_EDIT_ADDRESS) 
  $desc = $("#"+ID_EDIT_DESC)

  let data = {
    "version":"1.0",
    "addr": $address.val(),
    "desc": $desc.val()
  }
  $address.val("")
  $desc.val("")

  REST_REQ(ENTITY).configure_PUT({
    data: data,
    key: data.addr,
    success: [ empower_log_response, empower_alert_generate_success,refresh_devices],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function trigger_remove_modal( wtp_key ) {

  $remove_modal = $("#"+ID_REMOVE_MODAL) 

  show_remove_modal = function(data){
    
    $address = $("#"+ID_REMOVE_ADDRESS) 
    $desc = $("#"+ID_REMOVE_DESC)

    $address.val(data.addr)
    $desc.val(data.desc)

    $remove_modal.modal({show:true})
  }

  REST_REQ(ENTITY).configure_GET({
    key: wtp_key,
    success: [ empower_log_response, show_remove_modal],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function remove(){
  $address = $("#"+ID_REMOVE_ADDRESS) 

  let key = $address.val()
  
  $address.val("")
  $desc.val("")

  REST_REQ(ENTITY).configure_DELETE({
    key: key,
    success: [ empower_log_response, empower_alert_generate_success,refresh_devices],
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
      '<button class="btn btn-sm btn-warning shadow-sm mr-1 mb-1" '+
      'onclick="trigger_edit_modal(\''+val['addr']+'\')">'+
      '<i class="fas fa-edit fa-sm text-white-50 mr-1"></i>Edit</button>'+
      '<button class="btn btn-sm btn-danger shadow-sm mb-1" '+
      'onclick="trigger_remove_modal(\''+val['addr']+'\')">'+
      '<i class="fas fa-trash fa-sm text-white-50 mr-1 "></i>Remove</button>'
    }

    connection = "-"
    last_seen = "-"

    if ( val['state'] == "online" ) {
        connection = val['connection']['addr']
        last_seen = val['last_seen']
    }

    t.row.add([
        val['addr'],
        val['desc'],
        last_seen,
        connection,
        actions
    ] ).draw( true );

  });

  t.draw(true)

  $("#offline").html(offline)
  $("#online").html(online)
  $("#connected").html(connected)
}

function refresh_devices() {

  t.clear();

  REST_REQ(ENTITY).configure_GET({
      success: [ empower_log_response, format_datatable_data],
      error: [ empower_log_response,  empower_alert_generate_error ]
    })
    .perform()
}

