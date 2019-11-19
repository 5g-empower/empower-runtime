/**
 * Support global variable for storing the "alerts in EMPOWER and referring them 
 * and their property univocally in the WEBUI
 */

__EMPOWER_WEBUI.ALERT={
  ALERT_BOX_ID: "alert_box",
  MAX_NUMBER: 1,
  COUNTER: 0,
  TYPES: {
    ERROR: "ERROR",
    WARNING: "WARNING",
    SUCCESS: "SUCCESS"
  }
}

/**
 * Class WEBUI_Alert allows generation and management of alert messages in the 
 * webui. Alerts are success, warning or error notifications for HTTP Requests 
 * performed through the webui, diplaying additional information about the 
 * occurred event. Color code (GREEN-YELLOW-RED) is used to characterize the 
 * different alert types.
 * It relies on a "alert box" DIV element with specific id in the HTML page, 
 * which  is used as a container for all the generated alerts
 * 
 * @requires js/support/empower-global.js 
 * @requires js/support/empower-corefunctions.js
 * 
 * @extends {WEBUI_CoreFunctions}
 */
class WEBUI_Alert extends WEBUI_CoreFunctions{

  /**
   * Constructor: configures the alert according to the passed arguments
   * 
   * @param {string} alert_id - the ID of the to-be-generated alert.
   * @param {string} type - the type of alert. Refer __EMPOWER_WEBUI.ALERT.TYPES  
   *                        for valid values
   * @param {string} strong_text  - the main text of the alert.
   * @param {string} text -the secondary text of the alert.
   */
  constructor(alert_id, type=__EMPOWER_WEBUI.ALERT.TYPES.ERROR, strong_text="", 
              text=""){

    super()

    this._$MAIN = this.get_$main(alert_id, type)

    this._$STRONG = this.get_$strong_text(strong_text)

    this._$TEXT = this.get_$text(text)
    
    this._$BUTTON = this.get_$button(alert_id)

  }
  
  /**
   * This method assembles the alert into a jQuery object referencing the 
   * element into the HTML page
   * 
   * @return {Object} this instance of WEBUI_Alert class (i.e., this)
   */
  generate(){
    let div = this._wrap_in_html("","DIV", {})

    let $div = this._convert_html_to_jquery(div)

    this._$MAIN.append($div)

    $div.append(this._$STRONG)

    $div.append(this._$TEXT)

    this._$MAIN.append(this._$BUTTON)
    
    return this
  }

  /**
   * This method assigns the value to alert's main text 
   * 
   * @param {string} text 
   * 
   * @return {Object} this instance of WEBUI_Alert class (i.e., this)
   * 
   */
  set_strong_text(text){
    this._$STRONG.text(text)

    return this
  }

  /**
   * This method assigns the value to alert's secondary text 
   * 
   * @param {string} text 
   * 
   * @return {Object} this instance of WEBUI_Alert class (i.e., this)
   * 
   */
  set_text(text){
    this._$TEXT.text(text)

    return this
  }

  /**
   * This method assigns the alert ID 
   * 
   * @param {string} alert_id
   * 
   * @return {Object} this instance of WEBUI_Alert class (i.e., this)
   * 
   */
  set_id(alert_id){
    if (this._is_there(this.get_id())){
      console.warn("ALERT ID  already assigned: ", 
                    this._$MAIN.id, "(replaced by:" + 
                    alert_id+")")
    }
    this._$MAIN.id = alert_id

    return this
  }

  /**
   * This method retieves the alert ID 
   * 
   * @return {string} this instance alert ID
   * 
   */
  get_id(){
    return this._$MAIN.attr('id')
  }

  /**
   * This method generates the jQuery object associated to the alert main 
   * element (i.e., the one with the identifier containing all other components)
   * 
   * @param {string} alert_id - the ID of the to-be-generated alert.
   * @param {string} type - the type of alert. Refer __EMPOWER_WEBUI.ALERT.TYPES 
   *                        for valid values
   * 
   * @return {Object} the instance of the main element
   */
  get_$main(alert_id=null, type=__EMPOWER_WEBUI.ALERT.TYPES.ERROR){
    let alert_type = "alert-error"
    switch(type){
      case __EMPOWER_WEBUI.ALERT.TYPES.SUCCESS:
        alert_type = "alert-success"
        break
      case __EMPOWER_WEBUI.ALERT.TYPES.WARNING:
        alert_type = "alert-warning"
        break
      default:
        alert_type = "alert-danger"
    }
    let attributes = {
      class: "alert alert-dismissible " + alert_type + 
             " fade collapse d-block mb-1",
      role: "alert"
    }
    if (this._is_there(alert_id)){
      attributes.id = alert_id
    }
    let wrapper = this._wrap_in_html("","DIV", attributes)

    return this._convert_html_to_jquery(wrapper)
  }

  /**
   * This method generates the jQuery object associated to the alert main text
   * element
   * 
   * @param {string} text 
   * 
   * @return {Object} the instance of the main text element
   */
  get_$strong_text(text=""){
    let strong = this._wrap_in_html(text, "STRONG",{class:"mr-2"})

    return this._convert_html_to_jquery(strong)
  }

  /**
   * This method generates the jQuery object associated to the alert secondary
   *  text element
   * 
   * @param {string} text 
   * 
   * @return {Object} the instance of the secondary text element
   */
  get_$text(text=""){
    let txt = this._wrap_in_html(text, "SPAN",{})

    return this._convert_html_to_jquery(txt)
  }

  /**
   * This method generates the jQuery object associated to the alert close 
   * button element
   * 
   * @param {string} alert_id
   * 
   * @return {Object} the instance of the close button element
   */
  get_$button(alert_id){
    
    let attributes = {
      type: "button",
      class: "close",
    }

    if (!this._is_there(alert_id)){
      console.error("NO alert id provided: button won't work")
    }
    else{
      attributes.onclick= "$('#"+alert_id+"').remove()"    
    }

    let span = this._wrap_in_html('x', "SPAN",{})

    let $span = this._convert_html_to_jquery(span)

    let button = this._wrap_in_html("", "BUTTON",attributes)

    let $button = this._convert_html_to_jquery(button)

    $button.append($span)

    return $button
  }

  /**
   * This method returns the jQuery object of current instance of the alert 
   * element
   * 
   * @return {Object} the instance of alert
   */
  get_$instance(){
    return this._$MAIN
  }

  /**
   * This method add instance alert into the alert box, at the top or bottom of 
   * the existing alert list, depending on the value of top argument
   * 
   * @param {boolean} top - if true, alert will be inserted at the top of the 
   *                      alert list in the alert box, at the bottom otherwise
   * 
   * @return {Object} this instance of WEBUI_Alert class (i.e., this)
   */

  publish(top=true, destroy_overlapping=true){
    if (destroy_overlapping){
      // console.warn("OVERLAPPING, id:",this.get_id())
      $("#"+this.get_id()).remove()
    }
    if (top){
      $("#"+__EMPOWER_WEBUI.ALERT.ALERT_BOX_ID).prepend(this.get_$instance())
    }
    else{
      $("#"+__EMPOWER_WEBUI.ALERT.ALERT_BOX_ID).append(this.get_$instance())
    }

    return this
  }

  /**
   * This method publishes the alert into the alert box and makes it visible
   * 
   * @return {Object} this instance of WEBUI_Alert class (i.e., this)
   */
  show(){
    
    this.publish()
        .get_$instance().addClass("show")

    return this
  }

  /**
   * This method hides instance associated alert
   * 
   * @return {Object} this instance of WEBUI_Alert class (i.e., this)
   */
  hide(){
    this.get_$instance().removeClass("show")

    return this
  }

}


/**
 * Class WEBUI_Alert_Success extends WEBUI_Alert to manage in an easier way 
 * success alerts
 * 
 * @extends {WEBUI_Alert}
 */
class WEBUI_Alert_Success extends WEBUI_Alert{
  constructor(alert_id, strong_text="", text=""){
     
    super(alert_id, "SUCCESS", strong_text, text)

  }
}


/**
 * Class WEBUI_Alert_Warning extends WEBUI_Alert to manage in an easier way 
 * warning alerts
 * 
 * @extends {WEBUI_Alert}
 */
class WEBUI_Alert_Warning extends WEBUI_Alert{
  constructor(alert_id, strong_text="", text=""){
     
    super(alert_id, "WARNING", strong_text, text)

  }
}


/**
 * Class WEBUI_Alert_Error extends WEBUI_Alert to manage in an easier way 
 * error alerts
 * 
 * @extends {WEBUI_Alert}
 */
class WEBUI_Alert_Error extends WEBUI_Alert{
  constructor(alert_id, strong_text="", text=""){
     
    super(alert_id, "ERROR", strong_text, text)

  }
}

/**
 * Support function for formatting the main and secondary text of an alert 
 * according to what returned by the HTTP Response
 * 
 * @param  {...any} args - arguments returned by the HTTP response
 * 
 * @return {Object} a dictionary with two keys: strong_text and text, for the 
 *                  main and secondary alert text, respectively
 */
function empower_alert_format_content(args){
  let jQxhr = null
  let detail = args[1]
  
  args.forEach(function(arg, index){
    // console.log("args["+index+"] (type:",(typeof arg),"): ",arg)
    if ((arg != null) && (arg != undefined)){
      if ((arg.empower != null) && (arg.empower != undefined)){
        jQxhr = arg
      }
    }
  })

  // console.log("jQxhr", jQxhr)
  // console.log("detail", detail)

  if (detail != "success"){
    detail = detail+"<br>"
    let rt = jQxhr.responseText
    // console.log("rt", rt)
    if (( rt != null) && (rt != undefined) && (rt != "")){
      let response_json = JSON.parse(rt)
      // console.log("response_json", response_json)
      if (( response_json.detail != null) && 
          (response_json.detail != undefined)){
        // eval('var value = '+response_json.detail)
        // console.log("value", value)
        // console.log("value str", JSON.stringify(value, null, 2))
        let detail_text = response_json.detail
        detail = detail +"<pre class='mb-0'>" +
                    JSON.stringify(detail_text, null, 2) + "</pre>"
                //  JSON.stringify(JSON.parse(response_json.detail), null, 2)
      }
    }
  }
  else{
    detail = detail+"<br>"
  }

  let strong_text = jQxhr.status+": "+jQxhr.statusText
  let text = detail
  if (jQxhr != null){
    text = text + "<em class='text-xs'>" +
                  jQxhr.empower.method + " : " + jQxhr.empower.url +
                  " [@" + jQxhr.empower.time.substring(11) + "]</em>"
  }

  return {
    strong_text: strong_text,
    text: text
  }
}

/**
 * Support function for generating an alert following a "success" response
 * 
 * @param  {...any} args - arguments returned by the HTTP response
 */
function empower_alert_generate_success(...args) {

  let alert_content= empower_alert_format_content(args)

  new WEBUI_Alert_Success("alert_" + empower_alert_assign_id_number(),
                          alert_content.strong_text,
                          alert_content.text)
    .generate().show()

}

/**
 * Support function for generating an alert following an "error" response
 * 
 * @param  {...any} args - arguments returned by the HTTP response
 */
function empower_alert_generate_error(...args) {

  let alert_content= empower_alert_format_content(args)

  new WEBUI_Alert_Error("alert_" + empower_alert_assign_id_number(),
                        alert_content.strong_text,
                        alert_content.text)
    .generate().show()
}

/**
 * Support function for generating sequential align id number
 * 
 * @return {number} aling id number
 */
function empower_alert_assign_id_number(){
  __EMPOWER_WEBUI.ALERT.COUNTER = 
    (__EMPOWER_WEBUI.ALERT.COUNTER + 1) % __EMPOWER_WEBUI.ALERT.MAX_NUMBER
  
  return __EMPOWER_WEBUI.ALERT.COUNTER
}

