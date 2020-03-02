$('#workers').removeClass('collapsed');
$('#collapseThree').addClass('show');
$('#workers_active').addClass('active');

console.warn("THIS PAGE IS A WORK IN PROGRESS!")

$(document).ready(function() {

  show_active_workers()

})

WORKER_MODAL = {
  EDIT: "EDIT",
  STOP: "STOP"
}

function show_active_workers(){

  show_workers = function(data){
    clear_active_worker_list()

    if (Object.keys(data).length === 0){
      $("#worker_box").html(
        '<div class="col-12 my-3 d-flex justify-content-center ">'+
          '<div class="col-auto border border-dark rounded text-center p-3">'+
            '<div class="h4 text-dark font-weight-bold px-5"> NO ACTIVE workers </div>'+
            '<div class="text-dark font-italic px-5"> You can run them in CATALOG section </div>'+
          '</div>'+
        '</div>')
      return
    }

    WORKER_COUNTER = 0
    $.each(data, function(key, val){

      let worker = new WEBUI_Card_Worker_Active(
        "worker_"+WORKER_COUNTER++,
        val.manifest.label,
        val.manifest.desc,
        val.name,
        {
          info:{
            "data-toggle": "tooltip", 
            "data-placement":"left",
            "title": ""+generate_tooltip_params(val)
          }
        }
      ).generate()
      let $worker= worker.get_$instance()
      $("#worker_box").append($worker)

      let f_edit = function(){
        alter_modal(WORKER_MODAL.EDIT, key, val)
      }
      worker.retrieve_$edit_button().click(f_edit)

      let f_stop = function(){
        alter_modal(WORKER_MODAL.STOP, key, val)
      }
      worker.retrieve_$stop_button().click(f_stop)

      $(document).ready(function(){
        $('[data-toggle="tooltip"]').tooltip({html:true});   
      });

    })
  }

  REST_REQ(__EMPOWER_WEBUI.ENTITY.WORKER.WORKER).configure_GET({
    success: [ empower_log_response, show_workers ],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()
}

function clear_active_worker_list(){
  $("#worker_box").empty()
}

function alter_modal(type, key, descriptor){
  console.log("ALTER MODAL",type, key, descriptor)
  let modal_hacker = new WEBUI_Modal_Hacker_Worker("worker_modal")

  // let title = "Default title"
  let worker_button = null
  let worker_function = null
  let fields_disabled = false

  switch(type){
    case WORKER_MODAL.EDIT:
      // title = "EDIT worker"
      worker_button = modal_hacker.generate_footer_button_EDIT()
      worker_function = edit_worker
      fields_disabled = false
      break
    case WORKER_MODAL.STOP:
      // title = "STOP worker"
      worker_button = modal_hacker.generate_footer_button_STOP()
      worker_function = stop_worker
      fields_disabled = true
      break
    default:
      console.warn("Invalid modal type: ", type)
  }

  modal_hacker.regenerate_title(descriptor.manifest.label)
  modal_hacker.configure_from_descriptor(key,descriptor.manifest)
  modal_hacker.show()
  modal_hacker.retrieve_footer().empty()
  modal_hacker.retrieve_footer().append(
    modal_hacker.generate_footer_button_CANCEL()
  )

  let fields = {}
    $.each(descriptor.params, function(key, val){
      fields[key] = {
        type: "TEXT"
      }
    })

  let modal= new WEBUI_Modal(__EMPOWER_WEBUI.MODAL.TYPE.GENERIC,"worker_modal")
    .add_fields(fields)

  $.each(modal._FIELDS, function(k, field){
    console.log("Setting field ", k, " to ", descriptor.params[k])
    field.set_value(descriptor.params[k])
    if (fields_disabled){
      field.disable()
    }
  })

  let f= function(){
    
    worker_function(key, modal)
  }

  worker_button.click(f)
  modal_hacker.retrieve_footer().append(
    worker_button
  )
}

function edit_worker(uuid, modal){

  modal.hide()

  // console.log('EDIT -> uuid', uuid)
  // console.log('EDIT -> modal', modal)

  let data = {
    "version":"1.0",
    params: {}
  }

  // $.each(modal._FIELDS, function(k, field){
  //   data.params[k] = field.get_value()
  // })
  $.each(modal._FIELDS, function(k, field){
    data.params[k] = field.get_value()
    if (data.params[k] === ""){
      data.params[k] = field.get_default()
    }
    console.log(k, ":", data.params[k])
  })

  // console.log("data:", data)

  REST_REQ(__EMPOWER_WEBUI.ENTITY.WORKER.WORKER).configure_PUT({
    key: uuid,
    data: data,
    success: [ empower_log_response, empower_alert_generate_success, 
      show_active_workers ],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()
}

function stop_worker(uuid, modal){

  modal.hide()

  // console.log('STOP -> uuid', uuid)
  // console.log('STOP -> modal', modal)
  
  REST_REQ(__EMPOWER_WEBUI.ENTITY.WORKER.WORKER).configure_DELETE({
    key: uuid,
    success: [ empower_log_response, empower_alert_generate_success, 
      show_active_workers ],
    error: [ empower_log_response, empower_alert_generate_error ]
  })
  .perform()
}

function enable_tooltips($button){
  $button.tooltip({html:true})
}

function generate_tooltip_params(service={}){

  let cf = __EMPOWER_WEBUI.CORE_FUNCTIONS
  if (cf._is_there(service)){
    if (cf._is_there(service.params)){

      let $wrapper= cf._convert_html_to_jquery(cf._wrap_in_html(
        "", "DIV", {}
      ))
      let $title = cf._convert_html_to_jquery(cf._wrap_in_html(
        "Instance parameters",
        "DIV",
        {class:"text-center h5 text-weight-bolder text-info mb-1"}
      ))

      $wrapper.append($title)


      // let $wrapper= cf._convert_html_to_jquery(cf._wrap_in_html(
      //   "", "DIV", {}
      // ))
      // let $table =cf._convert_html_to_jquery(cf._wrap_in_html(
      //   "", "TABLE", {}
      // ))
      // let $tbody =cf._convert_html_to_jquery(cf._wrap_in_html(
      //   "", "TBODY", {}
      // ))

      // $wrapper.append($table)
      // $table.append($tbody)

      // let $title = cf._convert_html_to_jquery(cf._wrap_in_html(
      //   "Instance parameters",
      //   "DIV",
      //   {class:"text-center text-weight-bold mb-1"}
      // ))
      // let $td = cf._convert_html_to_jquery(cf._wrap_in_html(
      //   "", "TD", {colspan:3}
      // ))
      // let $tr =cf._convert_html_to_jquery(cf._wrap_in_html(
      //   "", "TR", {}
      // ))

      // $td.append($title)
      // $tr.append($td)
      // $tbody.append($tr)

      $.each(service.params, function(key, val){
        $tr =cf._convert_html_to_jquery(cf._wrap_in_html(
          "", "DIV", {class:"text-left rounded bg-info text-gray-900 mb-1"}
        ))
        

        let $icon = cf._convert_html_to_jquery(cf._wrap_in_html(
          "", "I", {class:"fas fa-arrow-right fa-xs fa-fw mr-1 ml-1"}
        ))
        $tr.append($icon)

        let $key = cf._convert_html_to_jquery(cf._wrap_in_html(
          key+":", "span", {class:"mr-1 font-weight-bold"}
        ))
        $tr.append($key)

        let $val = cf._convert_html_to_jquery(cf._wrap_in_html(
          val, "span", {}
        ))
        $tr.append($val)

        $wrapper.append($tr)

        // $tr =cf._convert_html_to_jquery(cf._wrap_in_html(
        //   "", "TR", {class:"small"}
        // ))
        
        // let $td1 = cf._convert_html_to_jquery(cf._wrap_in_html(
        //   "", "TD", {}
        // ))
        // let $icon = cf._convert_html_to_jquery(cf._wrap_in_html(
        //   "", "I", {class:"fas fa-arrow-right fa-xs fa-fw mr-1"}
        // ))
        // $td1.append($icon)

        // let $td2 = cf._convert_html_to_jquery(cf._wrap_in_html(
        //   "", "TD", {}
        // ))
        // let $key = cf._convert_html_to_jquery(cf._wrap_in_html(
        //   key+":", "span", {class:"mr-1 font-weight-bold"}
        // ))
        // $td2.append($key)

        // let $td3 = cf._convert_html_to_jquery(cf._wrap_in_html(
        //   "", "TD", {}
        // ))
        // let $val = cf._convert_html_to_jquery(cf._wrap_in_html(
        //   val, "span", {}
        // ))
        // $td3.append($val)

        // $tr.append($td1)
        // $tr.append($td2)
        // $tr.append($td3)

        // $tbody.append($tr)
      })

      return $wrapper.html().replace(/"/g,"'")
    }
  }
  return {}
  
}

