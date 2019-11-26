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
        {class:"card-body"})
    )
    let $row_wrapper = this._convert_html_to_jquery(
      this._wrap_in_html(
        "", 
        "DIV",
        {class:"row no-gutters align-items-center"})
    )

    this._$MAIN.append($card)
      $card.append($card_body)
        $card_body.append($row_wrapper)
          $row_wrapper.append(this._$LABELS)
          $row_wrapper.append(this._$BUTTONS)

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
      class: "col-xl-8"
    }
    let label_wrapper = this._wrap_in_html("","DIV", attributes)

    return this._convert_html_to_jquery(label_wrapper)
  }

  get_$buttons(){
    let attributes = {
      class: "col-xl-4 text-right"
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

  constructor(card_id, title_text, description_text, worker_url){
    super(card_id)

    this._TITLE = this.get_$title(title_text)
    this._WORKER_URL = this.get_$worker_url(worker_url)
    this._DESCRIPTION = this.get_$description(description_text)
    
  }

  generate(){
    return super.generate()
      .add_label(this._WORKER_URL)    
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

  get_$worker_url(worker_url){
    let attributes = {
      class: "text-xs text-gray my-1 font-italic text-gray-500"
    }
    let url = this._wrap_in_html(worker_url,"DIV", attributes)

    return this._convert_html_to_jquery(url)
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
        btn_type = "btn-success"
        break
      case this.BUTTON.TYPE.EDIT:
        btn_type = "btn-warning"
        break
      case this.BUTTON.TYPE.STOP:
        btn_type = "btn-danger"
        break
      case this.BUTTON.TYPE.INFO:
        btn_type = "btn-info"
        break
      default:
        console.warn("UNKNOWN button type:", type)
    }
    return "btn btn-sm "+btn_type+" shadow-sm mr-1 mb-1"
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
    return btn_icon+" fa-sm text-white-50"
  }
}

class WEBUI_Card_Worker_Active extends WEBUI_Card_Worker{
  constructor(card_id, title_text, description_text, worker_url, extra={}){
    super(card_id, title_text, description_text, worker_url)


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