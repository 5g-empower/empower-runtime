$(document).ready(function() {

  ENTITY = EMPOWER_ENTITIES.ACCOUNT

  ID_EDIT_MODAL = "edit"+ENTITY+"Modal"

  ID_USERNAME = "username"
  ID_NAME = "name"
  ID_EMAIL = "email"

  ID_EDIT_USERNAME = "edit_username"
  ID_EDIT_NAME = "edit_name"
  ID_EDIT_EMAIL = "edit_email"


});

/**
 * This function triggers the edit modal for modifying current user's profile 
 * settings
 * 
 * @param {string} account_key 
 */
function trigger_edit_modal( account_key ) {

  $edit_modal = $("#"+ID_EDIT_MODAL) 

  show_edit_modal = function(data){
    
    $username = $("#"+ID_EDIT_USERNAME) 
    $name = $("#"+ID_EDIT_NAME)
    $email = $("#"+ID_EDIT_EMAIL)

    $username.val(data.username)
    $name.val(data.name)
    $email.val(data.email)

    $edit_modal.modal({show:true})
  }

  REST_REQ(ENTITY).configure_GET({
    key: account_key,
    success: [ show_edit_modal],
    error: []
  })
  .perform()
}

/**
 * This function requests via REST API the modification of current user's 
 * profile settings
 * 
 */
function edit(){
  $username = $("#"+ID_EDIT_USERNAME) 
  $name = $("#"+ID_EDIT_NAME)
  $email = $("#"+ID_EDIT_EMAIL)

  let data = {
    "version":"1.0",
    "username": $username.val(),
    "name": $name.val(),
    "email": $email.val()
  }
  $username.val("")
  $name.val("")
  $email.val("")

  REST_REQ(ENTITY).configure_PUT({
    data: data,
    key: data.username,
    success: [ edit_success ],
    error: []
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

