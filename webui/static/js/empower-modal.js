__EMPOWER_WEBUI.MODAL={
  TYPE:{
    ADD: "ADD",
    EDIT: "EDIT",
    REMOVE: "REMOVE",
    GENERIC: "GENERIC"
  },
  PREFIX:{
    ADD: "add_",
    EDIT: "edit_",
    REMOVE: "remove_",
    GENERIC: ""
  },
  SUFFIX:{
    MODAL: "_Modal",
  },
  FIELD:{
    TYPE:{
      TEXT: "TEXT",
      CHECKBOX: "CHECKBOX",
      SELECT: "SELECT",
      SELECT_OWNER: "SELECT_OWNER"
    }
  }
}

class WEBUI_Modal extends WEBUI_CoreFunctions{
  constructor(modal_type, modal_id){
    super()
    if (!this.verify_modal_type(modal_type)){
      console.error("INVALID Modal Type: potential issues")
    }
    this._TYPE = modal_type
    this._ID = modal_id
    this._$INSTANCE = $("#"+modal_id)
    if (!this.check_consistency()){
      console.error("CONSISTENCY CHECK FAILED: potential issues")
    }
  }

  get_modal_id(){
    return this._ID
  }

  get_modal_type(){
    return this._TYPE
  }
  get_$instance(){
    return this._$INSTANCE
  }

  verify_modal_type(modal_type){
    switch(modal_type){
      case __EMPOWER_WEBUI.MODAL.TYPE.ADD:
      case __EMPOWER_WEBUI.MODAL.TYPE.EDIT:
      case __EMPOWER_WEBUI.MODAL.TYPE.REMOVE:
      case __EMPOWER_WEBUI.MODAL.TYPE.GENERIC:
        return true
    }
    console.error("UNKNOWN Modal Type: ", modal_type)
    return false
  }

  check_consistency(){
    if (this._is_there(this.get_$instance())){
      if (this.get_$instance().length > 0){
        if(this.get_$instance().length === 1){
          return true
        }
        else{
          console.error("MORE THAN 1 elements with modal identifier found! (",
          this.get_modal_id(),")" )
        }
      }
      else{
        console.error("NO elements with modal identifier found! (",
                      this.get_modal_id(),")" )
      }
    }
    else{
      console.error("$INSTANCE NOT SET")
    }
    return false
  }

  add_fields(field_dictionary, apply_modal_type_prefix=true){
    this._FIELDS = {}
    if (this._is_object(field_dictionary)){
      $.each(field_dictionary, function( key, val ) {
        let fkey = key
        if (apply_modal_type_prefix){
          fkey = this.apply_field_prefix(key)
          // console.log("fkey", fkey)
        }

        this._FIELDS[fkey]= this.retrieve_modal_field(val.type, fkey)
        if(this._is_there(val.default)){
          this._FIELDS[fkey].set_value(val.default)
        }

        this.configure_field_dedicated_methods(key, fkey)

      }.bind(this))
    }

    return this
  }

  apply_field_prefix(key, modal_type=null){
    if (!this._is_there(modal_type)){
      modal_type = this.get_modal_type()
    }
    switch(modal_type){
      case __EMPOWER_WEBUI.MODAL.TYPE.ADD:
        return __EMPOWER_WEBUI.MODAL.PREFIX.ADD + key
      case __EMPOWER_WEBUI.MODAL.TYPE.EDIT:
        return __EMPOWER_WEBUI.MODAL.PREFIX.EDIT + key
      case __EMPOWER_WEBUI.MODAL.TYPE.REMOVE:
        return __EMPOWER_WEBUI.MODAL.PREFIX.REMOVE + key
      case __EMPOWER_WEBUI.MODAL.TYPE.GENERIC:
        return __EMPOWER_WEBUI.MODAL.PREFIX.GENERIC + key
    }
    console.warn("NO PREFIX FOUND for modal type:", modal_type)
    return key
  }

  retrieve_modal_field(field_type, field_id){
    switch(field_type){
      case __EMPOWER_WEBUI.MODAL.FIELD.TYPE.TEXT:
        return new WEBUI_ModalField_Text(field_id)
      case __EMPOWER_WEBUI.MODAL.FIELD.TYPE.CHECKBOX:
        return new WEBUI_ModalField_CheckBox(field_id)
      case __EMPOWER_WEBUI.MODAL.FIELD.TYPE.SELECT:
        return new WEBUI_ModalField_Select(field_id)
      case __EMPOWER_WEBUI.MODAL.FIELD.TYPE.SELECT_OWNER:
        return new WEBUI_ModalField_SelectOwner(field_id)
      default:
        console.error("UNKNOWN Modal field type: ", field_type)
        return null
    }
  }

  configure_field_dedicated_methods(key, fkey){
    if (this._is_there(this[key])){
      console.error("CONFLICT with existent method with key: ", key,
                    "\nDisruptive malfunctionings may occur!")
    }
    else{
      this[key] = {}
      this[key].get = this._FIELDS[fkey].get_value.bind(this._FIELDS[fkey])
      this[key].set = this._FIELDS[fkey].set_value.bind(this._FIELDS[fkey])
      this[key].reset = this._FIELDS[fkey].reset.bind(this._FIELDS[fkey])
      this[key].$instance = this._FIELDS[fkey].get_$instance()
      this[key].on_change = this[key].$instance.change.bind(this[key].$instance)
    }
    return this
  }

  reset(defaults={}){
    $.each(this._FIELDS, function( key, val ) {
      if (this._is_there(defaults) &&
          this._is_there(defaults[key])){
        val.reset(defaults[key])
      }
      else{
        val.reset()
      }
    })
  }

  show(){
    // this.get_$instance().modal({show:true})
    this.get_$instance().modal('show')

    return this
  }

  hide(){
    this.get_$instance().modal('hide')

    return this
  }

}

class WEBUI_Modal_Entity extends WEBUI_Modal{
  constructor( modal_type, entity){
    let modal_id = __EMPOWER_WEBUI.MODAL.PREFIX[modal_type] +
                   entity +
                   __EMPOWER_WEBUI.MODAL.SUFFIX.MODAL

    // console.log("modal_id= ", modal_id)
    super(modal_type, modal_id)

  }
}

class WEBUI_Modal_Hacker extends WEBUI_Modal{

  retrieve(parent, match){
    let $item = parent.find(match)
    if (!this.check_singularity($item)){
      console.error("ISSUE while retrieveing '"+ match +"' from parent ", parent)
      return null
    }
    return $item
  }

  check_singularity($item){
    if (this._is_there($item)){
      if ($item.length > 0){
        if($item.length === 1){
          return true
        }
        else{
          console.error("MORE THAN 1 element found!")
        }
      }
      else{
        console.error("NO element found!")
      }
    }
    else{
      console.error("INVALID $item")
    }
    return false
  }

  retrieve_header(){
    return this.retrieve(this.get_$instance(), ".modal-header")
  }

  retrieve_title(){
    return this.retrieve(this.retrieve_header(), ".modal-title")
  }

  regenerate_title(text){
    this.retrieve_title().remove()
    let $title = this._convert_html_to_jquery(
      this._wrap_in_html(
        text,
        "DIV",
        {class:"h5 modal-title"}
      )
    )
    this.retrieve_header().prepend($title)
  }

  retrieve_header_close_button(){
    return this.retrieve(this.retrieve_header(), ".close")
  }

  retrieve_body(){
    return this.retrieve(this.get_$instance(), ".modal-body")
  }

  clear_body(){
    this.retrieve_body().empty()
  }

  retrieve_footer(){
    return this.retrieve(this.get_$instance(), ".modal-footer")
  }

  clear_footer(){
    this.retrieve_footer().empty()
  }

  generate_footer_button({ attributes={}, icon_class= null, text="",
                        text_class={} }){
    let $button = this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "BUTTON",
        attributes
      )
    )

    if (this._is_there(icon_class)){
      let $icon = this._convert_html_to_jquery(
        this._wrap_in_html(
          "",
          "I",
          icon_class
        )
      )

      $button.append($icon)
    }

    if (this._is_there(text)){
      let $text = this._convert_html_to_jquery(
        this._wrap_in_html(
          text,
          "SPAN",
          text_class
        )
      )

      $button.append($text)
    }

    return $button
  }

  generate_footer_button_CANCEL(){

    let params={
      attributes:{
        "data-dismiss": "modal" ,
        class: "btn btn-sm btn-secondary shadow-sm"
      },
      icon_class: "fas fa-times fa-fw text-white-50 mr-1",
      text: "Cancel",
      text_class: {}
    }

    return this.generate_footer_button(params)

  }

  generate_footer_button_ADD(toggle_modal=true){

    let params={
      attributes:{
        class: "btn btn-sm btn-primary shadow-sm"
      },
      icon_class: "fas fa-plus fa-fw text-white-50 mr-1",
      text: "Add",
      text_class: {}
    }

    if (toggle_modal){
      params.attributes["data-toggle"] = 'modal'
      params.attributes["data-target"] = '#'+this.get_modal_id
    }

    return this.generate_footer_button(params)

  }

  generate_footer_button_EDIT(toggle_modal=true){

    let params={
      attributes:{
        class: "btn btn-sm btn-primary shadow-sm"
      },
      icon_class: "fas fa-edit fa-fw text-white-50 mr-1",
      text: "Edit",
      text_class: {}
    }

    if (toggle_modal){
      params.attributes["data-toggle"] = 'modal'
      params.attributes["data-target"] = '#'+this.get_modal_id
    }

    return this.generate_footer_button(params)

  }

  generate_footer_button_REMOVE(toggle_modal=true){

    let params={
      attributes:{
        class: "btn btn-sm btn-danger shadow-sm"
      },
      icon_class: "fas fa-trash fa-fw text-white-50 mr-1",
      text: "Remove",
      text_class: {}
    }

    if (toggle_modal){
      params.attributes["data-toggle"] = 'modal'
      params.attributes["data-target"] = '#'+this.get_modal_id
    }

    return this.generate_footer_button(params)

  }

}

class WEBUI_Modal_Hacker_Worker extends WEBUI_Modal_Hacker{


  constructor(modal_id){
    super(__EMPOWER_WEBUI.MODAL.TYPE.GENERIC, modal_id)
  }

  generate_footer_button_RUN(toggle_modal=true){

    let params={
      attributes:{
        class: "btn btn-sm btn-primary shadow-sm"
      },
      icon_class: "fas fa-play fa-fw text-white-50 mr-1",
      text: "Run",
      text_class: {}
    }

    if (toggle_modal){
      params.attributes["data-toggle"] = 'modal'
      params.attributes["data-target"] = '#'+this.get_modal_id()
    }

    return this.generate_footer_button(params)

  }

  generate_footer_button_STOP(toggle_modal=true){

    let params={
      attributes:{
        class: "btn btn-sm btn-danger shadow-sm"
      },
      icon_class: "fas fa-stop fa-fw text-white-50 mr-1",
      text: "Stop",
      text_class: {}
    }

    if (toggle_modal){
      params.attributes["data-toggle"] = 'modal'
      params.attributes["data-target"] = '#'+this.get_modal_id
    }

    return this.generate_footer_button(params)

  }

  generate_form(){
    return this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "FORM",
        {role:"form"}
      )
    )
  }

  generate_worker_name(key){
    return this._convert_html_to_jquery(
      this._wrap_in_html(
        key,
        "DIV",
        {class:"text-xs font-italic text-center mb-1"}
      )
    )
  }

  generate_worker_label(name){
    return this._convert_html_to_jquery(
      this._wrap_in_html(
        name,
        "DIV",
        {class:"h4 text-center font-weight-bold"}
      )
    )
  }

  generate_worker_description(description){
    return this._convert_html_to_jquery(
      this._wrap_in_html(
        description,
        "DIV",
        {class:"text-xs font-weight-bold text-uppercase text-center mb-4"}
      )
    )
  }

  generate_worker_params_frame(){
    return this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "DIV",
        {class:"mx-2 px-3"}// border border-gray rounded"}
      )
    )
  }

  generate_worker_parameter_input_group(key, descriptor){
    // console.log("CIAOOOOO!!!")
    let $form_group = this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "FORM-GROUP",
        {}
      )
    )

    let $label = this._convert_html_to_jquery(
      this._wrap_in_html(
        key,
        "LABEL",
        { class: "font-weight-bold"}
      )
    )
    let $label_icon =  this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "ICON",
        { class: "fas fa-arrow-right fa-xs fa-fw mr-1"}
      )
    )

    $label.prepend($label_icon)

    $form_group.append($label)

    // let param_type = "type: '"+descriptor.type+"'"
    let mandatory = "MANDATORY"
    if (!descriptor.mandatory){
      mandatory = "OPTIONAL"
    }
    let _default = ""
    if (this._is_there(descriptor.default)){
      _default = "default: "+ descriptor.default
    }

    let $input = null
    switch(descriptor.type){
      case "str":
      case "int":
      case "EtherAddress":
        $input = this._convert_html_to_jquery(
          this._wrap_in_html(
            "",
            "INPUT",
            {
              class:"form-control text-xs",
              id: key,
              placeholder: mandatory + ", " + _default +" [ " + descriptor.type  + " ]"
            }
          )
        )
      default:
        if (this._is_array(descriptor.type)){
          $input = this._convert_html_to_jquery(
            this._wrap_in_html(
              "",
              "SELECT",
              {
                class:"form-control text-xs",
                id: key,
                // placeholder: mandatory + ", " + _default +" [ " + param_type  + " ]"
              }
            )
          )
          descriptor.type.forEach(function(option){
            let def = false
            let selected = false
            if (descriptor.default === option){
              def = true
              selected = true
            }
            $input.append(new Option(option, option, def, selected))
          })
        }
    }
    if (!descriptor.mandatory){
      // console.log("Assigning default")
      $input.attr("default",descriptor.default)
    }
    
    $form_group.append($input)

    let description = descriptor.desc
    if (!this._is_there(description)){
      description= "Description not available"
    }

    let $desc = this._convert_html_to_jquery(
      this._wrap_in_html(
        description,
        "DIV",
        {
          class:"text-xs text-gray-500 my-1"
        }
      )
    )

    $form_group.append($desc)

    return $form_group
  }

  configure_from_descriptor(key, descriptor){
    let $form = this.generate_form()

    //$form.append(this.generate_worker_name(key))
    //$form.append(this.generate_worker_label(descriptor.label))
    //$form.append(this.generate_worker_description(descriptor.desc))

    if (this._is_there(descriptor.params)){
      
      let $frame = this.generate_worker_params_frame()
      $.each(descriptor.params, function(key, val){
        // console.log("this",this)
        let $ig = this.generate_worker_parameter_input_group(key, val)
        $frame.append($ig)
      }.bind(this))
      $form.append($frame)
    }

    let $body = this.retrieve_body()
    $body.empty()
    $body.append($form)
  }
}

class WEBUI_Modal_Hacker_Application extends WEBUI_Modal_Hacker{


  constructor(modal_id){
    super(__EMPOWER_WEBUI.MODAL.TYPE.GENERIC, modal_id)
  }

  generate_footer_button_RUN(toggle_modal=true){

    let params={
      attributes:{
        class: "btn btn-sm btn-primary shadow-sm"
      },
      icon_class: "fas fa-play fa-fw text-white-50 mr-1",
      text: "Run",
      text_class: {}
    }

    if (toggle_modal){
      params.attributes["data-toggle"] = 'modal'
      params.attributes["data-target"] = '#'+this.get_modal_id()
    }

    return this.generate_footer_button(params)

  }

  generate_footer_button_STOP(toggle_modal=true){

    let params={
      attributes:{
        class: "btn btn-sm btn-danger shadow-sm"
      },
      icon_class: "fas fa-stop fa-fw text-white-50 mr-1",
      text: "Stop",
      text_class: {}
    }

    if (toggle_modal){
      params.attributes["data-toggle"] = 'modal'
      params.attributes["data-target"] = '#'+this.get_modal_id
    }

    return this.generate_footer_button(params)

  }

  generate_form(){
    return this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "FORM",
        {role:"form"}
      )
    )
  }

  generate_application_name(key){
    return this._convert_html_to_jquery(
      this._wrap_in_html(
        key,
        "DIV",
        {class:"text-xs font-italic text-center mb-1"}
      )
    )
  }

  generate_application_label(name){
    return this._convert_html_to_jquery(
      this._wrap_in_html(
        name,
        "DIV",
        {class:"h4 text-center font-weight-bold"}
      )
    )
  }

  generate_application_description(description){
    return this._convert_html_to_jquery(
      this._wrap_in_html(
        description,
        "DIV",
        {class:"text-xs font-weight-bold text-uppercase text-center mb-4"}
      )
    )
  }

  generate_application_params_frame(){
    return this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "DIV",
        {class:"mx-2 px-3"}// border border-gray rounded"}
      )
    )
  }

  generate_application_parameter_input_group(key, descriptor){
    // console.log("CIAOOOOO!!!")
    let $form_group = this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "FORM-GROUP",
        {}
      )
    )

    let $label = this._convert_html_to_jquery(
      this._wrap_in_html(
        key,
        "LABEL",
        { class: "font-weight-bold"}
      )
    )
    let $label_icon =  this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "ICON",
        { class: "fas fa-arrow-right fa-xs fa-fw mr-1"}
      )
    )

    $label.prepend($label_icon)

    $form_group.append($label)

    let param_type = "type: '"+descriptor.type+"'"
    let mandatory = "MANDATORY"
    if (!descriptor.mandatory){
      mandatory = "OPTIONAL"
    }
    let _default = ""
    if (this._is_there(descriptor.default)){
      _default = "default: "+ descriptor.default
    }
    
    
    let $input = null
    switch(descriptor.type){
      case "str":
      case "int":
      case "EtherAddress":
        $input = this._convert_html_to_jquery(
          this._wrap_in_html(
            "",
            "INPUT",
            {
              class:"form-control text-xs",
              id: key,
              placeholder: mandatory + ", " + _default +" [ " + descriptor.type  + " ]"
            }
          )
        )
      default:
        if (this._is_array(descriptor.type)){
          $input = this._convert_html_to_jquery(
            this._wrap_in_html(
              "",
              "SELECT",
              {
                class:"form-control text-xs",
                id: key,
                // placeholder: mandatory + ", " + _default +" [ " + param_type  + " ]"
              }
            )
          )
          descriptor.type.forEach(function(option){
            let def = false
            let selected = false
            if (descriptor.default === option){
              def = true
              selected = true
            }
            $input.append(new Option(option, option, def, selected))
          })
        }
    }
    if (!descriptor.mandatory){
      // console.log("Assigning default")
      $input.attr("default",descriptor.default)
    }
    
    $form_group.append($input)
    // let $input = this._convert_html_to_jquery(
    //   this._wrap_in_html(
    //     "",
    //     "INPUT",
    //     {
    //       class:"form-control text-xs",
    //       id: key,
    //       placeholder: mandatory + ", " + _default +" [ " + param_type  + " ]"
    //     }
    //   )
    // )
    // if (!descriptor.mandatory){
    //   // console.log("Assigning default")
    //   $input.attr("default",descriptor.default)
    // }

    // $form_group.append($input)

    let description = descriptor.desc
    if (!this._is_there(description)){
      description= "Description not available"
    }

    let $desc = this._convert_html_to_jquery(
      this._wrap_in_html(
        description,
        "DIV",
        {
          class:"text-xs text-gray-500 my-1"
        }
      )
    )

    $form_group.append($desc)

    return $form_group
  }

  configure_from_descriptor(key, descriptor){
    let $form = this.generate_form()

    //$form.append(this.generate_application_name(key))
    //$form.append(this.generate_application_label(descriptor.label))
    //$form.append(this.generate_application_description(descriptor.desc))

    if (this._is_there(descriptor.params)){
      let $frame = this.generate_application_params_frame()
      $.each(descriptor.params, function(key, val){
        console.log("this",this)
        let $ig = this.generate_application_parameter_input_group(key, val)
        $frame.append($ig)
      }.bind(this))
      $form.append($frame)
    }

    this._FIELDS = {}

    let t = this

    $.each(descriptor.params, function(key, val){
      console.log()
      let type = null
      console.log(" HI HI HI val.type:",val.type)
      switch(val.type){
        case "str":
        case "int":
        case "EtherAddress":
          type = __EMPOWER_WEBUI.MODAL.FIELD.TYPE.TEXT
          console.log("found type, type is now: ", type)
          break
        default:

          if (t._is_array(val.type)){
            type = __EMPOWER_WEBUI.MODAL.FIELD.TYPE.SELECT
          }
          console.log("found type, type is now: ", type)
      }
      
      $(document).ready(function(){
        t._FIELDS[key]= t.retrieve_modal_field(type, key)
      });
    })


    let $body = this.retrieve_body()
    $body.empty()
    $body.append($form)
  }
}







class WEBUI_ModalField extends WEBUI_CoreFunctions{
  constructor(field_id){
    super()

    // console.log("field_id:", field_id)

    this._ID = field_id
    this._$INSTANCE = $("#"+field_id)
    if (!this.check_consistency()){
      console.error("CONSISTENCY CHECK FAILED: potential issues")
    }

  }

  get_field_id(){
    return this._ID
  }

  get_$instance(){
    return this._$INSTANCE
  }

  check_consistency(){
    if (this._is_there(this.get_$instance())){
      if (this.get_$instance().length > 0){
        if(this.get_$instance().length === 1){
          return true
        }
        else{
          console.error("MORE THAN 1 elements with field identifier found! (",
                        this.get_field_id(),")" )
        }
      }
      else{
        console.error("NO elements with field identifier found! (",
                      this.get_field_id(),")" )
      }
    }
    else{
    console.error("$INSTANCE NOT SET")
    }
    return false
  }

  set_value(value){
    console.warn("Method  'set_value' to be overridden")
    return this

  }

  get_value(){
    console.warn("Method 'get_value' to be overridden")
    return null
  }

  reset(value){
    console.warn("Method 'reset' to be overridden")
    return this
  }

  disable(){
    this._$INSTANCE.prop("disabled", true)
  }

  get_default(){
    // console.log(this._$INSTANCE)
    return this._$INSTANCE.attr("default")
  }

}

class WEBUI_ModalField_Text extends WEBUI_ModalField{
  constructor(field_id){
    super(field_id)
  }

  set_value(value){
    this.get_$instance().val(value)
  }

  get_value(){
    return this.get_$instance().val()
  }

  reset(value){
    console.log("reset to ", value)
    this.set_value("")
    if (this._is_there(value)){
      this.set_value(value)
    }
    return this
  }
}

class WEBUI_ModalField_CheckBox extends WEBUI_ModalField{
  constructor(field_id){
    super(field_id)
  }

  set_value(value){
    this.get_$instance().prop("checked",value)
  }

  get_value(){
    return this.get_$instance().prop("checked")
  }

  reset(value=false){
    console.log("reset to ", value)
    this.set_value(false)
    if (this._is_there(value)){
      this.set_value(value)
    }
    return this
  }
}

class WEBUI_ModalField_Select extends WEBUI_ModalField{
  constructor(field_id){
    super(field_id)
  }

  set_value(value){
    this.get_$instance().val(value)
  }

  get_value(){
    return this.get_$instance().val()
  }
}

class WEBUI_ModalField_SelectOwner extends WEBUI_ModalField_Select{
  constructor(field_id){
    super(field_id)

    this.reset()
  }

  fill_by_query(){
    let fill = function(data){
      this.empty()
      this.fill_by_response(data)
    }.bind(this)

    REST_REQ(__EMPOWER_WEBUI.ENTITY.ACCOUNT)
      .configure_GET({
        success: [ empower_log_response, fill ],
        error: [ empower_log_response, empower_alert_generate_error ]
      })
      .perform()
  }

  fill_by_response(data){
    $.each( data, function( key, val ) {
      if ( key != 'root' ) {
        this.get_$instance().append(new Option(val['username'] +
          ' ( ' + val['name'] + ", " + val['email'] + ')', key))
      }
    }.bind(this))
  }

  empty(){
    this.get_$instance().empty()
  }

  reset(value=""){
    console.log("reset")
    $.when(this.fill_by_query()).then(function(){
      console.log("reset to ", value)
      this.set_value("")
      if (this._is_there(value)){
        this.set_value(value)
      }
    }.bind(this))
    return this
  }

}






















// class WEBUI_Modal_Generator extends WEBUI_CoreFunctions{
//   constructor(title, buttons){
//     this._$HEADER = this._convert_html_to_jquery(
//       this._wrap_in_html(
//         "",
//         "DIV",
//         {class:"modal-header"}
//       )
//     )

//     let $close_button = this._convert_html_to_jquery(
//       this._wrap_in_html(
//         "x",
//         "BUTTON",
//         {class:"close", type:"button", "data-dismiss":"modal", "aria-label":"Close"}
//       )
//     )

//     this._$HEADER.append($close_button)

//     this._$BODY = this._convert_html_to_jquery(
//       this._wrap_in_html(
//         "",
//         "DIV",
//         {class:"modal-body"}
//       )
//     )
//     this._$FOOTER = this._convert_html_to_jquery(
//       this._wrap_in_html(
//         "",
//         "DIV",
//         {class:"modal-footer"}
//       )
//     )

//     this._MAIN =

//     this._BUTTONS = {}

//     this.add_modal_title(title)
//     this.add_modal_buttons(buttons)
//   }

//   add_modal_title(title){
//     this._$TITLE = this._convert_html_to_jquery(
//       this._wrap_in_html(
//         title,
//         "DIV",
//         {class:"h5"}
//       )
//     )
//     this._$HEADER.prepend(this._$TITLE)
//   }

//   add_modal_buttons(buttons){
//     $.each(buttons, function(key, value){
//       this._BUTTONS[key] = this.add_modal_button(value)
//       this._$FOOTER.append(this._$BUTTONS[key])
//     })
//   }

//   add_modal_button({attributes={}, icon_class= null, text="", text_class={}}){
//     let $button = this._convert_html_to_jquery(
//       this._wrap_in_html(
//         title,
//         "BUTTON",
//         attributes
//       )
//     )

//     if (this._is_there(icon_class)){
//       let $icon = this._convert_html_to_jquery(
//         this._wrap_in_html(
//           "",
//           "I",
//           icon_class
//         )
//       )

//       $button.append($icon)
//     }

//     if (this._is_there(text)){
//       let $text = this._convert_html_to_jquery(
//         this._wrap_in_html(
//           text,
//           "SPAN",
//           text_class
//         )
//       )

//       $button.append($text)
//     }

//     return $button
//   }
// }

// class WEBUI_Modal_Generator_Worker extends WEBUI_Modal_Generator{
//   constructor(title, buttons, worker_descriptor){
//     super(title, buttons)

//   }

//   process_worker_descriptor(descriptor={}){

//     this._$FORM = this._convert_html_to_jquery(
//       this._wrap_in_html(
//         "",
//         "FORM",
//         {role:"form"}
//       )
//     )

//     this._$BODY.append(this._$FORM)

//     if (this._is_there(descriptor.key)){
//       this._$WORKER_ID = this._convert_html_to_jquery(
//         this._wrap_in_html(
//           descriptor.key,
//           "DIV",
//           {class:"text-xs font-italic text-center mb-1"}
//         )
//       )

//       this._$FORM.append(this._$WORKER_ID)
//     }

//     if (this._is_there(descriptor.name)){
//       this._$WORKER_NAME = this._convert_html_to_jquery(
//         this._wrap_in_html(
//           descriptor.name,
//           "DIV",
//           {class:"h4 text-center font-weight-bold"}
//         )
//       )

//       this._$FORM.append(this._$WORKER_NAME)
//     }

//     if (this._is_there(descriptor.desc)){
//       this._$WORKER_DESC = this._convert_html_to_jquery(
//         this._wrap_in_html(
//           descriptor.desc,
//           "DIV",
//           {class:"text-xs font-weight-bold text-uppercase text-center mb-4"}
//         )
//       )

//       this._$FORM.append(this._$WORKER_DESC)
//     }

//     if (this._is_there(descriptor.params)){

//       let $frame = this._convert_html_to_jquery(
//         this._wrap_in_html(
//           "",
//           "DIV",
//           {class:"m-2 border border-gray p-3"}
//         )
//       )
//       this._$FORM.append($frame)

//       this._PARAMETERS = {}
//       $.each(descriptor.params, function(key, val){
//         this._PARAMETERS[key] = this.process_parameter_descriptor(key, val)
//         $frame.append(this._PARAMETERS[key])
//       })
//     }

//   }

//   process_parameter_descriptor(key, descriptor){
//     let $form_group = this._convert_html_to_jquery(
//       this._wrap_in_html(
//         "",
//         "FORM-GROUP",
//         {}
//       )
//     )

//     let $label = this._convert_html_to_jquery(
//       this._wrap_in_html(
//         key,
//         "LABEL",
//         {}
//       )
//     )

//     $form_group.append($label)

//     let param_type = "type: '"+descriptor.type+"'"
//     let mandatory = ", MANDATORY"
//     if (!descriptor.mandatory){
//       mandatory = ", OPTIONAL"
//     }
//     let _default = ""
//     if (this._is_there(descriptor.default)){
//       _default = ", default: "+ descriptor.default
//     }
//     let $input = this._convert_html_to_jquery(
//       this._wrap_in_html(
//         "",
//         "INPUT",
//         {
//           class:"form-control",
//           id: key,
//           placeholder: "[" + param_type + mandatory + _default + "]"
//         }
//       )
//     )

//     $form_group.append($input)

//     let $desc = this._convert_html_to_jquery(
//       this._wrap_in_html(
//         descriptor.desc,
//         "DIV",
//         {
//           class:"text-xs text-gray-500 "
//         }
//       )
//     )

//     $form_group.append($desc)

//     return $form_group
//   }
// }

