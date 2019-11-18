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
  }

  EDIT_MODAL = new WEBUI_Modal_Entity(
    __EMPOWER_WEBUI.MODAL.TYPE.EDIT,
    ENTITY
  ).add_fields(fields)

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
function edit(){

  let data = {
    "version":"1.0",
    "username": EDIT_MODAL.username.get(),
    "name": EDIT_MODAL.name.get(),
    "email": EDIT_MODAL.email.get(),
  }
  
  edit_reset = EDIT_MODAL.reset.bind(EDIT_MODAL)

  REST_REQ(ENTITY).configure_PUT({
    data: data,
    key: data.username,
    success: [ empower_log_response, edit_reset, edit_success ],
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
  location.reload()
}

