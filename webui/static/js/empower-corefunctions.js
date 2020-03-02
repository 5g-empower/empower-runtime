/**
 * Class WEBUI_CoreFunctions is a support class for importing into extending 
 * classes a set of common functions that can be useful for managing the 
 * activity over the WEBUI
 * 
 * @requires js/support/empower-globals.js
 */
class WEBUI_CoreFunctions{
 
  /**
   * This method checks if candidate argument is null
   * @param {*} candidate 
   * 
   * @return true if is null, false otherwise
   */
  _is_null(candidate) {
    if (candidate === null) {
      return true
    }
    return false
  }

  /**
   * This method checks if candidate argument is undefined
   * @param {*} candidate 
   * 
   * @return true if is undefined, false otherwise
   */
  _is_undefined(candidate) {
    if (candidate === undefined) {
      return true
    }
    return false
  }

  /**
   * This method checks if candidate argument is null OR undefined
   * @param {*} candidate 
   * 
   * @return true if is null OR undefined, false otherwise
   */
  _is_there(candidate) {
    return (!(this._is_null(candidate) || this._is_undefined(candidate)))
  }

  /**
   * This method checks if candidate argument is an array
   * @param {*} candidate 
   * 
   * @return true if is an array, false otherwise
   */
  _is_array(candidate) {
    return (candidate instanceof Array)
  }

  /**
   * This method checks if candidate argument is string
   * @param {*} candidate 
   * 
   * @return true if is string, false otherwise
   */
  _is_string(candidate) {
    return (typeof candidate === 'string')
  }

  /**
   * This method checks if candidate argument is string ""
   * @param {*} candidate 
   * 
   * @return true if candidate is "" string, false otherwise
   */
  _is_void_string(candidate) {
    return (this._is_string(candidate) && (candidate===""))
  }

  /**
     * This function checks if candidate param is a JS Object
     * @param {*} candidate - candidate
     * @return {boolean} true if it is a JS Object, false otherwise
     */
  _is_object(candidate={}){
      return (typeof candidate === 'object')
  }

  /**
     * This function creates the HTML element specified by tagname
     * @param {string} tagname - tag name of the desired element
     * @return {Element} the Element instance
     */
  _create_element(tagname){
    return  document.createElement(tagname)
  }

  /**
   * This functions converts an Element class into a JQuery object
   * @param {Element} element - the element to be converted
   * @return {Object} the jQuery Object
   */
  _element2jq(element){
    return $( element )
  }

  /**
   * This functions disables a JQuery object
   * @param {Object} jqobj - the jQuery Object to be disabled
   * @return {boolean} returns always true
   */
  _disable(jqobj){
    jqobj.prop("disabled", true)
  }

  /**
   * This functions enables a JQuery object
   * @param {Object} jqobj - the jQuery Object to be enabled
   * @return {boolean} returns always true
   */
  _enable(jqobj){
    jqobj.prop("disabled", false)
  }

  /**
   * This functions hides a JQuery object
   * @param {Object} jqobj - the jQuery Object to be hidden
   * @return {boolean} returns always true
   */
  _hide(jqobj){
    jqobj.addClass("d-none")
  }

  /**
   * This functions shows a JQuery object
   * @param {Object} jqobj - the jQuery Object to be shown
   * @return {boolean} returns always true
   */
  _show(jqobj){
    jqobj.removeClass("d-none")
  }


  /**
   * This functions wraps a string into html tag and adds attributes (if provided) to the resulting element.
   * NB: no check performed over data types, tag/attributes consistency and to_be_wrapped content
   * @param {string} to_be_wrapped - string to be wrapped
   * @param {!string} tag - the wrapping HTML tag
   * @param {?string} attributes - sequence of attributes to  be applied to the resulting element
   * @return {string} the HTML-wrapped string
   */
  _wrap_in_html(to_be_wrapped, tag = 'DIV', attributes = null) {
    let _a = ''
    if (this._is_there(attributes)) {
      if (this._is_object(attributes)) {
        Object.keys(attributes).forEach(function (key) {
          _a += " " + key + "=\"" + attributes[key] + "\""
        })
      }
    }
    return "<" + tag + _a + ">" + to_be_wrapped + "</" + tag + ">"
  }

  /**
   * This function converts an HTML code string into a jQuery object
   * @param {string} html_str - the HTML code string to be converted 
   * @return {object|null} jQuery object if conversion succeded, null otherwise
   */
  _convert_html_to_jquery(html_str = '<DIV></DIV>') {
    try {
      return $($.parseHTML(html_str))
    }
    catch (error) {
      return null
    }
  }
}

/**
 * An istance of WEBUI_CoreFunctions class is made available globally through 
 * the global variable __EMPOWER_WEBUI (to avoid reinstanciating it every time 
 * to access its provided functions)
 * 
 * @global
 */

 __EMPOWER_WEBUI.CORE_FUNCTIONS = new WEBUI_CoreFunctions()