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

  if (sessionStorage.getItem("empower_temporary")){
    console.log("empower_temporary is defined")
    $("#alert_box").html(sessionStorage.getItem("empower_temporary"))
    sessionStorage.removeItem("empower_temporary")
  }
  else{
    console.log("empower_temporary is NOT defined")
  }

});

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

    EDIT_MODAL.get_$instance().modal({show:true})
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
      empower_alert_generate_success, edit_success ],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

/**
 * This function is meant to be performed after a successful response for 
 * current user's profile settings modification.
 * 
 * NB: it RELOADS the page (to avoid misalignment between session parameters and
 * stored user parameters)
 * 
 */
function edit_success(){

  sessionStorage.setItem("empower_temporary", $("#alert_box").html());
  location.reload()
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
