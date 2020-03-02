$('#apps').removeClass('collapsed');
$('#collapseThree').addClass('show');
$('#apps_catalog').addClass('active');

$(document).ready(function() {

  refresh_application_catalog()

})

function refresh_application_catalog(){

  let CF = __EMPOWER_WEBUI.CORE_FUNCTIONS
  if (!CF._is_there(__EMPOWER_WEBUI.PROJECT.ID)){
    $("#application_box").html("<div class='h4 col-12 text-center'><span class='border border-dark rounded text-dark font-weight-bold py-3 px-5'> NO PROJECT SELECTED: please go to Dahboard and select a project</div></div>")
    return
  }

  get_catalog_applications = function(data){

    let running_instances= {}

    $.each(data, function(key, val){
      if (val.name in running_instances){
        running_instances[val.name] = running_instances[val.name] + 1
      }
      else{
        running_instances[val.name] = 1
      }
    })

    show_applications = function(data){
      clear_application_catalog()
      APPLICATION_COUNTER = 0
      $.each(data, function(key, val){
        if (!(val.name in running_instances)){
          running_instances[val.name] = 0
        }
        // console.log("ADDING application: ",val)
        let application = new WEBUI_Card_Application_Catalog(
          "application_"+APPLICATION_COUNTER++,
          val.label,
          val.desc,
          val.name,
          running_instances[val.name]
        ).generate()
        let $application= application.get_$instance()
        $("#application_box").append($application)
        let f = function(){
          alter_modal(key, val)
        }
        application.retrieve_$play_button().click(f)
      })

      $(document).ready(function(){
        $('[data-toggle="tooltip"]').tooltip({html:true});   
      });
    }

    REST_REQ(__EMPOWER_WEBUI.ENTITY.APPLICATION.CATALOG).configure_GET({
      success: [ empower_log_response, show_applications ],
      error: [ empower_log_response, empower_alert_generate_error ]
    })
    .perform()
  }

  REST_REQ(__EMPOWER_WEBUI.ENTITY.APPLICATION.APPLICATION,).configure_GET({
    success: [ empower_log_response, get_catalog_applications ],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()
}

function clear_application_catalog(){
  $("#application_box").empty()
}

function alter_modal(key, descriptor){
  console.log("ALTER MODAL",key, descriptor)
  let modal_hacker = new WEBUI_Modal_Hacker_Application("application_modal")
  modal_hacker.regenerate_title(descriptor.label)
  modal_hacker.configure_from_descriptor(key,descriptor)
  modal_hacker.show()
  modal_hacker.retrieve_footer().empty()
  modal_hacker.retrieve_footer().append(
    modal_hacker.generate_footer_button_CANCEL()
  )
  let run_button = modal_hacker.generate_footer_button_RUN()
  let f= function(){
    console.log("f")
    let fields = {}
    $.each(descriptor.params, function(key, val){
      console.log("alter_modal:",key,val)
      fields[key] = {
        type: "TEXT"
      }
    })
    let modal= new WEBUI_Modal(__EMPOWER_WEBUI.MODAL.TYPE.GENERIC,"application_modal")
      .add_fields(fields)
    run_application(key, modal)
  }
  run_button.click(f)
  modal_hacker.retrieve_footer().append(
    run_button
  )
}

function run_application(name, modal){
  console.log('name', name)

  let data = {
    "version":"1.0",
    "name": name,
    params: {}
  }

  $.each(modal._FIELDS, function(k, field){
    data.params[k] = field.get_value()
    if (data.params[k] === ""){
      data.params[k] = field.get_default()
    }
    console.log(k, ":", data.params[k])
  })

  console.log("data:", data)

  REST_REQ(__EMPOWER_WEBUI.ENTITY.APPLICATION.APPLICATION).configure_POST({
    data: data,
    success: [ empower_log_response, empower_alert_generate_success,
       refresh_application_catalog ],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()
}

