$('#clients').addClass('collapsed');
$('#devices').addClass('collapsed');
$('#workers').addClass('collapsed');
$('#apps').addClass('collapsed');

$(document).ready(function() {

  ENTITY = __EMPOWER_WEBUI.ENTITY.PROJECT

  let fields = {
    description: {
      type: __EMPOWER_WEBUI.MODAL.FIELD.TYPE.TEXT
    },
    owner: {
      type: __EMPOWER_WEBUI.MODAL.FIELD.TYPE.SELECT_OWNER
    },
    ssid: {
      type: __EMPOWER_WEBUI.MODAL.FIELD.TYPE.TEXT
    },
    ssidtype: {
      type: __EMPOWER_WEBUI.MODAL.FIELD.TYPE.CHECKBOX
    },
    mcc: {
      type: __EMPOWER_WEBUI.MODAL.FIELD.TYPE.TEXT
    },
    mnc: {
      type: __EMPOWER_WEBUI.MODAL.FIELD.TYPE.TEXT
    },
  }

  ADD_MODAL = new WEBUI_Modal_Entity(
    __EMPOWER_WEBUI.MODAL.TYPE.ADD,
    ENTITY
  ).add_fields(fields)

  console.log("ADD_MODAL", ADD_MODAL)

  // EDIT_MODAL = new WEBUI_Modal_Entity(
  //   __EMPOWER_WEBUI.MODAL.TYPE.EDIT,
  //   ENTITY
  // ).add_fields(fields)

  fields = {
    id: {
      type: __EMPOWER_WEBUI.MODAL.FIELD.TYPE.TEXT
    },
    description: {
      type: __EMPOWER_WEBUI.MODAL.FIELD.TYPE.TEXT
    },
    owner: {
      type: __EMPOWER_WEBUI.MODAL.FIELD.TYPE.TEXT
    },
  }

  REMOVE_MODAL = new WEBUI_Modal_Entity(
    __EMPOWER_WEBUI.MODAL.TYPE.REMOVE,
    ENTITY
  ).add_fields(fields)

  refresh_projects()

})

function add() {

  let last_owner = ADD_MODAL.owner.get()
  ADD_MODAL.owner.reset(last_owner)

  let data = {
    "version":"1.0",
    "desc": ADD_MODAL.description.get(),
    "owner": ADD_MODAL.owner.get(),
  }
  if (ADD_MODAL.ssid.get()){
    if (ADD_MODAL.ssid.get() != ""){
      let bssid_type = __EMPOWER_WEBUI.SSID.TYPE.UNIQUE
      if (ADD_MODAL.ssidtype.get()){
        bssid_type = __EMPOWER_WEBUI.SSID.TYPE.SHARED
      }
      data.wifi_props= {
        ssid: ADD_MODAL.ssid.get(),
        bssid_type: bssid_type
      }
    }
  }
  if (ADD_MODAL.mcc.get() && ADD_MODAL.mnc.get()){
    if ((ADD_MODAL.mcc.get() != "") &&
        (ADD_MODAL.mnc.get() != "")){
      data.lte_props= {
        plmnid:{
          "mcc": ADD_MODAL.mcc.get(),
          "mnc": ADD_MODAL.mnc.get()
        }
      }
    }
  }

  console.log("ADD data:", data)

  add_reset = ADD_MODAL.reset.bind(ADD_MODAL)

  REST_REQ(ENTITY).configure_POST({
    data: data,
    success: [ empower_log_response, empower_alert_generate_success,
      add_reset, refresh_projects],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()

}

function trigger_remove_modal( project_key ) {

  show_remove_modal = function(data){

    REMOVE_MODAL.id.set(data.project_id)
    REMOVE_MODAL.description.set(data.desc)
    REMOVE_MODAL.owner.set(data.owner)

    REMOVE_MODAL.get_$instance().modal({show:true})
  }

  REST_REQ(ENTITY).configure_GET({
    key: project_key,
    success: [ empower_log_response, show_remove_modal],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function remove(){

  let key = REMOVE_MODAL.id.get()

  remove_reset = REMOVE_MODAL.reset.bind(REMOVE_MODAL)

  REST_REQ(ENTITY).configure_DELETE({
    key: key,
    success: [
      empower_log_response, empower_alert_generate_success,
      remove_reset, refresh_projects],
    error: [ empower_log_response,  empower_alert_generate_error ]
  })
  .perform()
}

function refresh_projects() {

  $("#projects").html("")

  $.getJSON( "/api/v1/projects", function( data ) {

    let projects = ""

    $.each( data, function( key, val ) {

      console.log("refresh_projects:",key,val)

      if ((__EMPOWER_WEBUI.USER.USERNAME === __EMPOWER_WEBUI.USER.ROOT) ||
          (__EMPOWER_WEBUI.USER.USERNAME === val.owner)){

        if (__EMPOWER_WEBUI.USER.USERNAME === __EMPOWER_WEBUI.USER.ROOT){
          cmd = '<button class="btn btn-sm btn-danger shadow-sm mb-1" '+
                'onclick="trigger_remove_modal(\''+ key +'\')">'+
                '<i class="fas fa-trash fa-sm"></i></button>'

        }
        else {

          if ( __EMPOWER_WEBUI.PROJECT.ID != key ) {

            cmd = '<a href="/auth/switch_project?project_id=' + key + '" class="btn btn-sm btn-success shadow-sm"><i class="fas fa-flag fa-sm"></i></a>'

          } else {

            cmd = '<a href="/auth/switch_project" class="btn btn-sm btn-secondary shadow-sm"><i class="fas fa-flag fa-sm"></i></a>'

          }

        }

        projects += ''+
        '<div class="col-xl-4 col-md-6 mb-4">'+
          '<div class="card border-left-primary shadow h-100 py-2">'+
            '<div class="card-body">'+
              '<div class="row no-gutters align-items-center">'+
                '<div class="col mr-2">'+
                  '<div class="text-xs">' +
                    '<i class="fas fa-user-cog fa-fw text-dark"></i>'+
                    '<span class="font-italic text-dark">&nbsp;'+ val['owner']+'</span>'+
                  '</div>'+
                  '<div class="text-xs">' +
                    '<span class="font-weight-bold text-primary text-uppercase mb-1">'+ key +'</span>'+
                  '</div>'+
                  '<div class="h5 mb-0 font-weight-bold text-gray-800">' + val['desc'] +
                  '</div>'+
                '</div>'+
                '<div class="col-auto">' + cmd +
                '</div>'+
              '</div>'+
            '</div>'+
          '</div>'+
        '</div>'
      }

    });

    if (projects === ""){
      // $("#projects").html("<div class='h4 col-12 text-center'><span class='border border-dark rounded text-dark font-weight-bold py-3 px-5'> NO projects available </div></div>")
      $("#projects").html(
        '<div class="col-12 my-3 d-flex justify-content-center ">'+
          '<div class="col-auto border border-dark rounded text-center p-3">'+
            '<div class="h4 text-dark font-weight-bold px-5 mb-0"> NO projects available </div>'+
            // '<div class="text-dark font-italic px-5"> You can run them in CATALOG section </div>'+
          '</div>'+
        '</div>')
    }
    else{
      $("#projects").html(projects)
    }

  });

}
