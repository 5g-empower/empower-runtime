$('#clients').addClass('collapsed');
$('#devices').addClass('collapsed');
$('#workers').addClass('collapsed');
$('#apps').addClass('collapsed');


$(document).ready(function() {

  ENTITY = __EMPOWER_WEBUI.ENTITY.ACCOUNT

  let fields = {
    username: {
      type: "TEXT"
    },
    name: {
      type: "TEXT"
    },
    email: {
      type: "TEXT"
    },
    password: {
      type: "TEXT"
    },
    password_confirm: {
      type: "TEXT"
    },
  }

  ADD_MODAL = new WEBUI_Modal_Entity(
    __EMPOWER_WEBUI.MODAL.TYPE.ADD,
    ENTITY
  ).add_fields(fields)

  add_password_consistency_check = function(){
    console.log ("password_consistency_check")
    check_input_consistency(
      ADD_MODAL.password.$instance,
      ADD_MODAL.password_confirm.$instance,
      $('#add_ACCOUNT_button')
    )
  }

  add_password_consistency_check()  

  ADD_MODAL.password.on_change(add_password_consistency_check)
  ADD_MODAL.password_confirm.on_change(add_password_consistency_check)

  EDIT_MODAL = new WEBUI_Modal_Entity(
    __EMPOWER_WEBUI.MODAL.TYPE.EDIT,
    ENTITY
  ).add_fields(fields)

  edit_password_consistency_check = function(){
    console.log ("password_consistency_check")
    check_input_consistency(
      EDIT_MODAL.password.$instance,
      EDIT_MODAL.password_confirm.$instance,
      $('#edit_ACCOUNT_button'),
      true
    )
  }

  EDIT_MODAL.password.on_change(edit_password_consistency_check)
  EDIT_MODAL.password_confirm.on_change(edit_password_consistency_check)

  fields = {
    username: {
      type: "TEXT"
    },
    name: {
      type: "TEXT"
    },
    email: {
      type: "TEXT"
    }
  }

  REMOVE_MODAL = new WEBUI_Modal_Entity(
    __EMPOWER_WEBUI.MODAL.TYPE.REMOVE,
    ENTITY
  ).add_fields(fields)

  ID_NOTIFY_PWD_ERR_MODAL = "notifyPasswordErrorModal"

  aoColumns = [
    { "sTitle": "Username" },
    { "sTitle": "Name" },
    { "sTitle": "E-Mail" },
    { "sTitle": "Actions", "sClass": "text-center" }
  ]

  DATATABLE = $('#dataTable').DataTable({
      "aoColumns": aoColumns
  });

  refresh_datatable();

});

ENTITY = null

function add() {

  // if (ADD_MODAL.password.get() != ADD_MODAL.password_confirm.get()){

  //   $error_notification = $("#"+ID_NOTIFY_PWD_ERR_MODAL) 
  //   $error_notification.modal({show:true})

  //   return 
  // }

  let data = {
    "version":"1.0",
    "username": ADD_MODAL.username.get(),
    "name": ADD_MODAL.name.get(),
    "email": ADD_MODAL.email.get(),
    "password": ADD_MODAL.password.get(),
  }
  
  add_reset = function(){
    ADD_MODAL.reset()
    // ADD_MODAL.hide()
  }.bind(ADD_MODAL)


  REST_REQ(ENTITY).configure_POST({
    data: data,
    success: [ empower_log_response, empower_alert_generate_success, 
      add_reset, refresh_datatable ],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()

}

/**
 * This function triggers the edit modal for modifying current user's profile 
 * settings
 * 
 * @param {string} account_key 
 */
function trigger_edit_modal( account_key ) {

  show_edit_modal = function(data){

    EDIT_MODAL.username.set(data.username)
    EDIT_MODAL.name.set(data.name)
    EDIT_MODAL.email.set(data.email)

    EDIT_MODAL.show()
  }

  REST_REQ(ENTITY).configure_GET({
    key: account_key,
    success: [ empower_log_response, show_edit_modal],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()
}

/**
 * This function requests via REST API the modification of current user's 
 * profile settings
 * 
 */
function edit(){

  let data = {
    "version":"1.0",
    "username": EDIT_MODAL.username.get(),
    "name": EDIT_MODAL.name.get(),
    "email": EDIT_MODAL.email.get(),
  }

  let cf = __EMPOWER_WEBUI.CORE_FUNCTIONS
  let pwd = EDIT_MODAL.password.get()
  let cpwd = EDIT_MODAL.password_confirm.get()
  if (cf._is_there(pwd) && (!cf._is_void_string(pwd))){
    data.new_password = pwd
    data.new_password_confirm = cpwd
  }
  
  edit_reset = EDIT_MODAL.reset.bind(EDIT_MODAL)

  REST_REQ(ENTITY).configure_PUT({
    data: data,
    key: data.username,
    success: [ empower_log_response, edit_reset, 
      empower_alert_generate_success, refresh_datatable ],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function trigger_remove_modal( account_key ) {

  show_remove_modal = function(data){

    REMOVE_MODAL.username.set(data.username)
    REMOVE_MODAL.name.set(data.name)
    REMOVE_MODAL.email.set(data.email)

    REMOVE_MODAL.show()
  }

  REST_REQ(ENTITY).configure_GET({
    key: account_key,
    success: [ empower_log_response, show_remove_modal],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function remove(){

  let account_key = REMOVE_MODAL.username.get()
  
  REMOVE_MODAL.reset()

  REST_REQ(ENTITY).configure_DELETE({
    key: account_key,
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


    actions = ""+
      '<button class="btn btn-sm btn-warning shadow-sm mr-xl-1 mb-md-1 m-1" '+
      'onclick="trigger_edit_modal(\''+val['username']+'\')">'+
      '<i class="fas fa-edit fa-sm fa-fw text-white-50 mr-xl-1 m-1"></i><span class="d-none d-xl-inline">Edit</span></button>'
    if (val['username'] !== 'root'){
      actions = actions +
      '<button class="btn btn-sm btn-danger shadow-sm mr-xl-1 mb-md-1 m-1" '+
      'onclick="trigger_remove_modal(\''+val['username']+'\')">'+
      '<i class="fas fa-trash fa-sm fa-fw text-white-50 mr-xl-1 m-1"></i><span class="d-none d-xl-inline">Remove</span></button>'
    }

    DATATABLE.row.add([
        val['username'],
        val['name'],
        val['email'],
        actions
    ] )

  });

  DATATABLE.draw(true)
}

function refresh_datatable() {

  DATATABLE.clear();

  REST_REQ(ENTITY).configure_GET({
    success: [ empower_log_response, format_datatable_data],
    error: [ empower_log_response,  empower_alert_generate_error ]
    })
    .perform()
}

function check_input_consistency($input, $confirm_input, $button, nullable=false){
  console.log ("check_input_consistency")
  if (!nullable){
    let cf = __EMPOWER_WEBUI.CORE_FUNCTIONS
    let value = $input.val()
    if (cf._is_undefined(value) || 
        cf._is_null(value) || 
        cf._is_void_string(value)){
      $button.prop('disabled', true);
      $input.addClass("text-danger bg-dark font-weight-bold")
      $confirm_input.addClass("text-danger bg-dark font-weight-bold")

      return
    }
  }

  if ($input.val() === $confirm_input.val()){
    $button.prop('disabled', false);
    $input.removeClass("text-danger bg-dark font-weight-bold")
    $confirm_input.removeClass("text-danger bg-dark font-weight-bold")
  }
  else{
    $button.prop('disabled', true);
    $input.addClass("text-danger bg-dark font-weight-bold")
    $confirm_input.addClass("text-danger bg-dark font-weight-bold")
  }
}



