/**
 * @requires js/support/empower-global.js 
 * @requires js/support/empower-corefunctions.js
 * 
 * @extends {WEBUI_CoreFunctions}
 */
class WEBUI_Card extends WEBUI_CoreFunctions{

  constructor(card_id){

    super()

    // <div class="col-xl-4 col-md-6 mb-4">
    //   <div class="card border-left-primary shadow h-100 py-2">
    //     <div class="card-body">
    //       <div class="row no-gutters align-items-center">
    //         <div class="col-xl-8">
    //           <div class="h5 mb-2 font-weight-bold text-gray-800">SDN@Play</div>
    //           <div class="text-xs font-weight-bold text-primary text-uppercase mb-2">This application makes white bunnies happy even if watched by many people.</div>
    //         </div>
    //         <div class="col-xl-4 text-right">
    //           <button class="btn btn-sm btn-warning shadow-sm"><i class="fas fa-edit fa-sm text-white-50"></i></button>
    //           <button class="btn btn-sm btn-danger shadow-sm"><i class="fas fa-stop fa-sm text-white-50"></i></button>
    //         </div>
    //       </div>
    //     </div>
    //   </div>
    // </div>

    this._$MAIN = this.get_$main(card_id)
    this._$LABELS = this.get_$labels()
    this._$BUTTONS = this.get_$buttons()
  }

  generate(){
    
    let $card = this._convert_html_to_jquery(
      this._wrap_in_html(
        "", 
        "DIV",
        {class:"card border-left-primary shadow h-100 py-2"})
    )
    let $card_body = this._convert_html_to_jquery(
      this._wrap_in_html(
        "", 
        "DIV",
        {class:"card-body py-1 px-3"})
    )
    let $row_wrapper = this._convert_html_to_jquery(
      this._wrap_in_html(
        "", 
        "DIV",
        {class:"row no-gutters align-items-center"})
    )

    let $bw = this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "DIV", 
        {class: "col-1 d-flex"}
      )
    )

    this._$MAIN.append($card)
      $card.append($card_body)
        $card_body.append($row_wrapper)
          $row_wrapper.append(this._$LABELS)
          $row_wrapper.append($bw)
          $bw.append(this._$BUTTONS)

    return this

  }

  get_$main(card_id){
    let attributes = {
      class: "col-xl-4 col-md-6 mb-4"
    }
    if (this._is_there(card_id)){
      attributes.id = card_id
    }
    let wrapper = this._wrap_in_html("","DIV", attributes)

    return this._convert_html_to_jquery(wrapper)
  }

  get_$labels(){
    let attributes = {
      class: "col-11 pr-2"
    }
    let label_wrapper = this._wrap_in_html("","DIV", attributes)

    return this._convert_html_to_jquery(label_wrapper)
  }

  get_$buttons(){
    let attributes = {
      class: "col-1 p-0"
    }
    let button_wrapper = this._wrap_in_html("","DIV", attributes)

    return this._convert_html_to_jquery(button_wrapper)
  }

  add_label($label, append=true){
    if (append){
      this._$LABELS.append($label)
    }
    else{
      this._$LABELS.prepend($label)
    }

    return this
  }

  add_button($button, append=true){
    if (append){
      this._$BUTTONS.append($button)
    }
    else{
      this._$BUTTONS.prepend($button)
    }

    return this
  }

  get_$instance(){
    return this._$MAIN
  }

}

class WEBUI_Card_Worker extends WEBUI_Card{

  BUTTON={
    TYPE:{
      PLAY: "PLAY",
      EDIT: "EDIT",
      STOP: "STOP",
      INFO: "INFO",
    }
  }

  // <div class="col-xl-4 col-md-6 mb-4">
  //   <div class="card border-left-primary shadow h-100 py-2">
  //     <div class="card-body">
  //       <div class="row no-gutters align-items-center">
  //         <div class="col-xl-8">
  //           <div class="h5 mb-2 font-weight-bold text-gray-800">SDN@Play</div>
  //           <div class="text-xs font-weight-bold text-primary text-uppercase mb-2">This application makes white bunnies happy even if watched by many people.</div>
  //         </div>
  //         <div class="col-xl-4 text-right">
  //           <button class="btn btn-sm btn-warning shadow-sm"><i class="fas fa-edit fa-sm text-white-50"></i></button>
  //           <button class="btn btn-sm btn-danger shadow-sm"><i class="fas fa-stop fa-sm text-white-50"></i></button>
  //         </div>
  //       </div>
  //     </div>
  //   </div>
  // </div>

  constructor(card_id, title_text, description_text, _package){
    super(card_id)

    this._TITLE = this.get_$title(title_text)
    this._PACKAGE = this.get_$package(_package)
    this._DESCRIPTION = this.get_$description(description_text)
    
  }

  generate(){
    return super.generate()
      .add_label(this._PACKAGE)    
      .add_label(this._TITLE)    
      .add_label(this._DESCRIPTION)    
  }

  get_$title(title_text){
    let attributes = {
      class: "h5 mb-2 font-weight-bold text-gray-800"
    }
    let title = this._wrap_in_html(title_text,"DIV", attributes)

    return this._convert_html_to_jquery(title)
  }

  get_$package(_package){
        
    let $package = this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "DIV", 
        {
          class: "d-flex",
        })
    )

    let $icon_wrapper = this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "DIV", 
        {
          class:"col-auto p-0",
          "data-toggle": "tooltip", 
          "data-placement":"right",
          "title": this.get_package_tree(_package)
        })
    )
    let $icon = this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "I", 
        {class:"fas fa-cubes fa-fw mr-1"})
    )
    let $text_wrapper = this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "DIV", 
        {class:"col p-0"})
    )
    let $text = this._convert_html_to_jquery(
      this._wrap_in_html(
        this.compress_package_text(_package),
        "SPAN", 
        {class: "text-xs text-gray my-1 font-italic text-gray-500"})
    )

    $icon_wrapper.append($icon)
    $text_wrapper.append($text)
    $package.append($icon_wrapper)
    $package.append($text_wrapper)

    return $package
    // return this.get_package_tree(_package)
  }

  compress_package_text(_package){
    let parray = _package.split(".")
    parray.forEach(function(element, index, arr){
      if ((index === 0) && (element === "empower")){
        arr[index] = "E"
      }
      // else if ((index === 1) && (element === "workers")){
      //   arr[index] = "W"
      // }
      else if (index === (arr.length-1)){
        arr[index] = arr[index]
      }
      else{
        arr[index] = arr[index].charAt(0)
      }
    }.bind(this))
    // if (parray[0] === "empower"){
    //   parray[0] = "E"
    // }
    // if (parray[1] === "workers"){
    //   parray[1] = "W"
    // }

    return parray.join(".")
  }
  
  get_package_tree(_package){
    let $tree = this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "DIV", 
        {class: "text-xs bg-white text-gray-900 rounded p-0 m-0"} )
    )
    let parray = _package.split(".")
    parray.forEach(function(element, index){
      let $line = this._convert_html_to_jquery(
        this._wrap_in_html(
          "",
          "DIV", 
          {class: "col-12 d-flex"})
      )
      for (let i = 0; i < index; i++){
        let $icon_slot = this._convert_html_to_jquery(
          this._wrap_in_html(
            "",
            "DIV", 
            {class:"col-auto p-0"})
        )
        let icon_class = "fas text-white fa-square-full fa-fw p-0 m-0"
        if (i === (index-1)){
          icon_class = "fas fa-long-arrow-alt-right fa-fw mr-1"
        }
        // if (i === (index - 1)){
        //   icon_class = "fas fa-plus fa-fw"
        // }
        let $icon = this._convert_html_to_jquery(
          this._wrap_in_html(
            "",
            "I", 
            {class: icon_class})
        )
        $icon_slot.append($icon)
        $line.append($icon_slot)
      }
      let $text_wrapper = this._convert_html_to_jquery(
        this._wrap_in_html(
          "",
          "DIV", 
          {class:"col-auto p-0"})
      )
      let text_class = "text-gray font-italic text-gray-900"
      if  (index === (parray.length-1)){
        text_class = "text-gray font-italic font-weight-bold text-gray-900"
      }
      let $text = this._convert_html_to_jquery(
        this._wrap_in_html(
          element,
          "SPAN", 
          {class: text_class})
      )
      $text_wrapper.append($text)
      $line.append($text_wrapper)
      $tree.append($line)
    }.bind(this))

    let $wrapper = this._convert_html_to_jquery(
      this._wrap_in_html(
        "",
        "DIV", 
        {} )
    )
    $wrapper.append($tree)

    return $wrapper.html().replace(/"/g,"'")
  }

  get_$description(description_text){
    let attributes = {
      class: "text-xs font-weight-bold text-primary text-uppercase mb-2"
    }
    let description = this._wrap_in_html(description_text,"DIV", attributes)

    return this._convert_html_to_jquery(description)
  }

  get_$button(type, extra_params={}){

    let button_params = extra_params

    let button_class = this.get_button_class(type)

    if (this._is_there(button_params.class)){
      button_params.class = button_params.class + " " + button_class
    }
    else{
      button_params.class = button_class
    }

    let button = this._wrap_in_html(
      "",
      "BUTTON",
      // {class:this.get_button_class(type)}
      button_params
    )
    let $button = this._convert_html_to_jquery(button)

    let icon = this._wrap_in_html(
      "",
      "I",
      {class: this.get_button_icon_class(type)}
    )
    let $icon = this._convert_html_to_jquery(icon)

    $button.append($icon)

    return $button
  }

  get_button_class(type){
    let btn_type = "btn-info"
    switch(type){
      case this.BUTTON.TYPE.PLAY:
        btn_type = "btn-success my-1"
        break
      case this.BUTTON.TYPE.INFO:
        btn_type = "btn-info my-1"
        break
      case this.BUTTON.TYPE.EDIT:
        btn_type = "btn-warning mb-1"
        break
      case this.BUTTON.TYPE.STOP:
        btn_type = "btn-danger mb-1"
        break
      default:
        console.warn("UNKNOWN button type:", type)
    }
    // return "btn btn-sm "+btn_type+" shadow-sm my-1"
    return "btn btn-sm "+btn_type+" shadow-sm px-1 py-0"
  }

  get_button_icon_class(type){
    let btn_icon = "fas fa-icons"
    switch(type){
      case this.BUTTON.TYPE.PLAY:
        btn_icon = "fas fa-play"
        break
      case this.BUTTON.TYPE.EDIT:
        btn_icon = "fas fa-edit"
        break
      case this.BUTTON.TYPE.STOP:
        btn_icon = "fas fa-stop"
        break
      case this.BUTTON.TYPE.INFO:
        btn_icon = "fas fa-search"
        break
      default:
        console.warn("UNKNOWN button type:", type)
    }
    return btn_icon+" fa-sm fa-fw text-white-50"
  }
}

class WEBUI_Card_Application extends WEBUI_Card_Worker{
}

class WEBUI_Card_Worker_Active extends WEBUI_Card_Worker{
  constructor(card_id, title_text, description_text, _package, extra={}){
    super(card_id, title_text, description_text, _package)


    if (!this._is_there(extra.info)){
      extra.info = {}
    }
    this._INFO_BUTTON = this.get_$button(this.BUTTON.TYPE.INFO, extra.info)
    this._EDIT_BUTTON = this.get_$button(this.BUTTON.TYPE.EDIT)
    this._STOP_BUTTON = this.get_$button(this.BUTTON.TYPE.STOP)
  }

  generate(){

    // console.log(this._EDIT_BUTTON)
    return super.generate()
      .add_button(this._INFO_BUTTON)    
      .add_button(this._EDIT_BUTTON)    
      .add_button(this._STOP_BUTTON)    
  }

  retrieve_$info_button(){
    return this._INFO_BUTTON
  }

  retrieve_$edit_button(){
    return this._EDIT_BUTTON
  }

  retrieve_$stop_button(){
    return this._STOP_BUTTON
  }
}

class WEBUI_Card_Application_Active extends WEBUI_Card_Application{
  constructor(card_id, title_text, description_text, _package, extra={}){
    super(card_id, title_text, description_text, _package)


    if (!this._is_there(extra.info)){
      extra.info = {}
    }
    this._INFO_BUTTON = this.get_$button(this.BUTTON.TYPE.INFO, extra.info)
    this._EDIT_BUTTON = this.get_$button(this.BUTTON.TYPE.EDIT)
    this._STOP_BUTTON = this.get_$button(this.BUTTON.TYPE.STOP)
  }

  generate(){

    // console.log(this._EDIT_BUTTON)
    return super.generate()
      .add_button(this._INFO_BUTTON)    
      .add_button(this._EDIT_BUTTON)    
      .add_button(this._STOP_BUTTON)    
  }

  retrieve_$info_button(){
    return this._INFO_BUTTON
  }

  retrieve_$edit_button(){
    return this._EDIT_BUTTON
  }

  retrieve_$stop_button(){
    return this._STOP_BUTTON
  }
}

class WEBUI_Card_Worker_Catalog extends WEBUI_Card_Worker{
  constructor(card_id, title_text, description_text, worker_name, running_instances=0){
    super(card_id, title_text, description_text, worker_name)

    this._INSTANCES = this.get_$running_instances(running_instances)

    this._PLAY_BUTTON = this.get_$button(this.BUTTON.TYPE.PLAY)
  }

  get_$running_instances(running_instances){

    let $icon = this._convert_html_to_jquery(this._wrap_in_html(
      "","I", {class:"fas fa-cog fa-spin fa-fw mr-1"}))
    
    let $value = this._convert_html_to_jquery(this._wrap_in_html(
      running_instances,
      "SPAN", 
      {class:"font-weight-bold text-uppercase mr-1"}))

    let $text = this._convert_html_to_jquery(this._wrap_in_html(
        "instances",
        "SPAN", 
        {class:"small font-italic"}))
    
    let $wrapper = this._convert_html_to_jquery(this._wrap_in_html(
      "",
      "DIV", 
      {class:"small text-success "}))

    

    $wrapper.append($icon)
    $wrapper.append($value)
    $wrapper.append($text)

    return $wrapper
  }

  generate(){
    return super.generate()
      .add_label(this._INSTANCES)
      .add_button(this._PLAY_BUTTON)    
  }

  retrieve_$play_button(){
    return this._PLAY_BUTTON
  }
}

class WEBUI_Card_Application_Catalog extends WEBUI_Card_Application{
  constructor(card_id, title_text, description_text, worker_name, running_instances=0){
    super(card_id, title_text, description_text, worker_name)

    this._INSTANCES = this.get_$running_instances(running_instances)

    this._PLAY_BUTTON = this.get_$button(this.BUTTON.TYPE.PLAY)
  }

  get_$running_instances(running_instances){

    let $icon = this._convert_html_to_jquery(this._wrap_in_html(
      "","I", {class:"fas fa-cog fa-spin fa-fw mr-1"}))
    
    let $value = this._convert_html_to_jquery(this._wrap_in_html(
      running_instances,
      "SPAN", 
      {class:"font-weight-bold text-uppercase mr-1"}))

    let $text = this._convert_html_to_jquery(this._wrap_in_html(
        "instances",
        "SPAN", 
        {class:"small font-italic"}))
    
    let $wrapper = this._convert_html_to_jquery(this._wrap_in_html(
      "",
      "DIV", 
      {class:"small text-success "}))

    

    $wrapper.append($icon)
    $wrapper.append($value)
    $wrapper.append($text)

    return $wrapper
  }

  generate(){
    return super.generate()
      .add_label(this._INSTANCES)
      .add_button(this._PLAY_BUTTON)    
  }

  retrieve_$play_button(){
    return this._PLAY_BUTTON
  }
}