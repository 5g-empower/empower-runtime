$('#workers').removeClass('collapsed');
$('#collapseThree').addClass('show');
$('#workers_catalog').addClass('active');

// console.warn("THIS PAGE IS A WORK IN PROGRESS!")

$(document).ready(function() {

  refresh_worker_catalog()

})

function refresh_worker_catalog(){

  get_catalog_workers = function(data){

    let running_instances= {}

    $.each(data, function(key, val){
      if (val.name in running_instances){
        running_instances[val.name] = running_instances[val.name] + 1
      }
      else{
        running_instances[val.name] = 1
      }
    })

    show_workers = function(data){
      clear_worker_catalog()
      WORKER_COUNTER = 0
      $.each(data, function(key, val){
        if (!(val.name in running_instances)){
          running_instances[val.name] = 0
        }
        // console.log("ADDING worker: ",val)
        let worker = new WEBUI_Card_Worker_Catalog(
          "worker_"+WORKER_COUNTER++,
          val.label,
          val.desc,
          val.name,
          running_instances[val.name]
        ).generate()
        let $worker= worker.get_$instance()
        $("#worker_box").append($worker)
        let f = function(){
          alter_modal(key, val)
        }
        worker.retrieve_$play_button().click(f)
      })

      $(document).ready(function(){
        $('[data-toggle="tooltip"]').tooltip({html:true});   
      });
    }

    REST_REQ(__EMPOWER_WEBUI.ENTITY.WORKER.CATALOG).configure_GET({
      success: [ empower_log_response, show_workers ],
      error: [ empower_log_response, empower_alert_generate_error ]
    })
    .perform()
  }

  REST_REQ(__EMPOWER_WEBUI.ENTITY.WORKER.WORKER).configure_GET({
    success: [ empower_log_response, get_catalog_workers ],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()
}

function clear_worker_catalog(){
  $("#worker_box").empty()
}

function alter_modal(key, descriptor){
  console.log("ALTER MODAL",key, descriptor)
  let modal_hacker = new WEBUI_Modal_Hacker_Worker("worker_modal")
  modal_hacker.regenerate_title(descriptor.label)
  modal_hacker.configure_from_descriptor(key,descriptor)
  modal_hacker.show()
  modal_hacker.retrieve_footer().empty()
  modal_hacker.retrieve_footer().append(
    modal_hacker.generate_footer_button_CANCEL()
  )
  let run_button = modal_hacker.generate_footer_button_RUN()
  let f= function(){

    let fields = {}
    $.each(descriptor.params, function(key, val){
      fields[key] = {
        type: "TEXT"
      }
    })
    let modal= new WEBUI_Modal(__EMPOWER_WEBUI.MODAL.TYPE.GENERIC,"worker_modal")
      .add_fields(fields)
    run_worker(key, modal)
  }
  run_button.click(f)
  modal_hacker.retrieve_footer().append(
    run_button
  )
}

function run_worker(name, modal){
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

  REST_REQ(__EMPOWER_WEBUI.ENTITY.WORKER.WORKER).configure_POST({
    data: data,
    success: [ empower_log_response, empower_alert_generate_success,
       refresh_worker_catalog ],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()
}

