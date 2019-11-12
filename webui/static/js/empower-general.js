/**
 * TODO: WORTH BEING REWRITED?
 * @param {*} url 
 */
function empower_ajax_delete(url) {
  $.ajax({
    url: url,
    type: 'DELETE',
    headers: {
      "Authorization": __BASIC
    },
    dataType: 'json',
    success: function(response) {
      refresh_accounts();
      message = "<strong>200: Success."
      $('#alert').removeClass('collapse');
      $("#alert").addClass('alert-success')
      $("#alert").addClass('show')
      $("#alert").show()
      $("#alert div").html(message);
    },
    error: function(response) {
      title = response.responseJSON['title']
      status_code = response.responseJSON['status_code']
      detail = response.responseJSON['detail']
      message = "<strong>" + status_code + ": " + title + ".</strong>&nbsp;" + detail
      $('#alert').removeClass('collapse');
      $("#alert").addClass('alert-danger')
      $("#alert").addClass('show')
      $("#alert").show()
      $("#alert div").html(message);
    },
  });
}

/**
 * This function is just printing out all its arguments.
 * Can be useful for debugging purposes if added among the success / error / 
 * complete functions in a jQuery ajax request, to display what returned by the 
 * request
 * 
 * @param  {...any} args - argument of the function (kept generic in order to 
 *                         process them dinamically inside the function)
 */
function empower_log_response(...args) {
  console.log("RESPONSE: ")
  args.forEach(function(arg, index){
    console.log("args["+index+"] (type:",(typeof arg),"): ",arg)
  })
}

/**
 * Class WEBUI_CoreFunctions is a support class for importing into extending 
 * classes a set of common functions that can be useful for managing the 
 * activity over the WEBUI
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
   * This method checks if candidate argument is string
   * @param {*} candidate 
   * 
   * @return true if is string, false otherwise
   */
  _is_string(candidate) {
    return (typeof candidate === 'string')
  }
}


/**
 * Class WEBUI_Credentials can be used for keeping current user credentials and 
 * generating the Basic Authentication required by many of the queries of the
 * WEBUI REST API
 * 
 * @extends WEBUI_CoreFunctions
 * 
 */
class WEBUI_Credentials extends WEBUI_CoreFunctions{

  constructor(basic_auth, username=null, password=null){

    super()

    if (this._is_there(username) && this._is_there(password)){
      this.basic_auth = "Basic " + btoa(username + ":" + password)
    }
    else if (this._is_there(basic_auth)){
      this.basic_auth = function(){return basic_auth}
    }
    else if (this._is_there(__BASIC)){
      this.basic_auth = __BASIC
    }
    else{
      console.error("BASIC_AUTH CANNOT BE EVALUATED")
    }
  }
}

/**
 * Class WEBUI_Request provides a manager for HTTP asynchronous requests for the 
 * WEBUI.
 * 
 * @extends WEBUI_CoreFunctions
 * 
 */
class WEBUI_Request extends WEBUI_CoreFunctions{

  _ENTRY_POINT = '/api/v1/'
  _REQ_TIMEOUT_INTERVAL = 2000 //ms

  /**
   * Constructor: accept a WEBUI_Credentials instance as input.
   * IF credentials are NOT provided, it checks for global variable __BASIC and
   * uses directly it as Basic Authentication.
   * IF also __BASIC is missing, an error message is sent to the console.
   * 
   * @param {Object} credentials
   */
  constructor(credentials=null) {

    super()

    this._CLASSNAME = this.constructor.name

    if(!this._is_there(credentials)){
      if (this._is_there(__BASIC)){
        this._BASIC_AUTH = __BASIC
      }
      else{
        console.error("NO BASIC_AUTH PROVIDED "+
        "(NO __BASIC global variable defined): MOST queries are going to FAIL")
      }
    }
    else{
      this._BASIC_AUTH = credentials.basic_auth()
    }
    // console.log("username:", credentials.username(), 
    //             "password:", credentials.password())
    
    this.REQUEST = null

  }

  /**
   * This method returns the Basic authentication value to be inserted in 
   * the request header
   * 
   * @param {?string} username - current user's username
   * @param {?string} password - current user's password
   * 
   * @return {string} Basic Authentication
   */

  basic_auth(username=null , password=null) {

    // if (this._is_there(username) &&
    //   this._is_there(password)) {

    //   try {
    //     this._BASIC_AUTH = "Basic " + btoa(username + ':' + password);
    //   }
    //   catch (e) {
    //     console.error(e)
    //     this._BASIC_AUTH = ""
    //   }
    // }

    return this._BASIC_AUTH
  }

  /**
   * This method configures the asynchronous HTTP request (ajax) according 
   * to the params passed
   * 
   * @param {Object} options - All the configuration options.
   * @param {?string} options.method - The HTTP method to use for the request.
   * @param {?string} options.dataType - The type of data that expected back 
   *                                     from the server.
   * @param {?(Object|string)} options.data - Data to be sent to the server.
   * @param {?boolean} options.cache - If set to false, it will force requested 
   *                                   pages not to be cached by the browser.
   * @param {?function[]} options.success - A sequence of functions to be called
   *                                        if the request succeeds.
   * @param {?function[]} options.complete - A sequence of functions to be 
   *                                        called when the request finishes 
   *                                        (after success and error callbacks 
   *                                        are executed).
   * @param {?function[]} options.error - A sequence of functions to be called 
   *                                      if the request fails.
   * @param {?number} options.timeout - Set a timeout (in milliseconds) for the 
   *                                    request. A value of 0 means there will 
   *                                    be no timeout.
   * @param {?boolean} options.auth_requested - true if authentication is 
   *                                            required, false otherwise.
   * @param {?Object|string} options.key - a parameter identifying the specific 
   *                                      target of the request
   * 
   * @return {Object} current WEBUI_Request instance
   */
  configure({ method = "GET",
    dataType = "json", data = {},
    cache = false,
    success = [], error = [], complete = [],
    timeout = this._REQ_TIMEOUT_INTERVAL,
    need_auth = true,
    key = null
  }) {

    this.REQUEST = {
      method: method,
      url: this.get_URL(method, key),
      dataType: dataType,
      data: this.get_formatted_data(data, method),
      cache: cache,
      timeout: timeout,
      success: success,
      error: error,
      complete: complete
    }

    if (need_auth) {
      this.REQUEST.beforeSend = function (req) {
        req.setRequestHeader("Authorization", this.basic_auth());
      }.bind(this)
    }

    console.log(this._CLASSNAME, " req:", this.REQUEST)

    return this
  }

  /**
   * This method returns the data properly formatted for the associated HTML
   *  Request type
   * 
   * @param {?(Object|string)} data 
   * @param {string} method 
   * 
   * @return {string} data formatted for request
   */
  get_formatted_data(data, method = GET) {
    if (!this._is_there(data)) {
      return ""
    }
    else if (this._is_string(data)) {
      return data
    }
    else {
      return JSON.stringify(data)
    }
  }

  /**
   * 
   * @param {string} method 
   * @param {Object|string} key 
   */
  get_URL(method, key) {
    return this._ENTRY_POINT
  }

  /**
   * This method configures the asynchronous GET HTTP request (ajax) 
   * according to the params passed
   * 
   * @param {Object} options - All the configuration options.
   * @param {?function[]} options.success - A sequence of functions to be called
   *                                        if the request succeeds.
   * @param {?function[]} options.complete - A sequence of functions to be 
   *                                        called when the request finishes 
   *                                        (after success and error callbacks 
   *                                        are executed).
   * @param {?function[]} options.error - A sequence of functions to be called 
   *                                      if the request fails.
   * @param {?number} options.timeout - Set a timeout (in milliseconds) for the 
   *                                    request. A value of 0 means there will 
   *                                    be no timeout.
   * @param {?Object|string} options.key - a parameter identifying the specific 
   *                                      target of the request
   * 
   * @return {Object} current WEBUI_Request instance
   */
  configure_GET({ cache = false,
    success = [], error = [], complete = [],
    timeout = this._REQ_TIMEOUT_INTERVAL,
    key = null
  }) {
    return this.configure({
      method: "GET",
      dataType: "json", data: "",
      cache: cache,
      success: success, error: error, complete: complete,
      timeout: timeout,
      need_auth: true,
      key: key
    })
  }

  /**
   * This method configures the asynchronous POST HTTP request (ajax) 
   * according to the params passed
   * 
   * @param {Object} options - All the configuration options.
   * @param {?(Object|string)} options.data - Data to be sent to the server.
   * @param {?boolean} options.cache - If set to false, it will force requested 
   *                                   pages not to be cached by the browser.
   * @param {?function[]} options.success - A sequence of functions to be called
   *                                        if the request succeeds.
   * @param {?function[]} options.complete - A sequence of functions to be 
   *                                        called when the request finishes 
   *                                        (after success and error callbacks 
   *                                        are executed).
   * @param {?function[]} options.error - A sequence of functions to be called 
   *                                      if the request fails.
   * @param {?number} options.timeout - Set a timeout (in milliseconds) for the 
   *                                    request. A value of 0 means there will 
   *                                    be no timeout.
   * 
   * @return {Object} current WEBUI_Request instance
   */
  configure_POST({ cache = false,
    data = {},
    success = [], error = [], complete = [],
    timeout = this._REQ_TIMEOUT_INTERVAL
  }) {
    return this.configure({
      method: "POST",
      dataType: "text", data: data,
      cache: cache,
      success: success, error: error, complete: complete,
      timeout: timeout,
      need_auth: true
    })
  }

  /**
   * This method configures the asynchronous PUT HTTP request (ajax) 
   * according to the params passed
   * 
   * @param {Object} options - All the configuration options.
   * @param {?(Object|string)} options.data - Data to be sent to the server.
   * @param {?boolean} options.cache - If set to false, it will force requested 
   *                                   pages not to be cached by the browser.
   * @param {?function[]} options.success - A sequence of functions to be called
   *                                        if the request succeeds.
   * @param {?function[]} options.complete - A sequence of functions to be 
   *                                        called when the request finishes 
   *                                        (after success and error callbacks 
   *                                        are executed).
   * @param {?function[]} options.error - A sequence of functions to be called 
   *                                      if the request fails.
   * @param {?number} options.timeout - Set a timeout (in milliseconds) for the 
   *                                    request. A value of 0 means there will 
   *                                    be no timeout.
   * @param {?Object|string} options.key - a parameter identifying the specific 
   *                                      target of the request
   * 
   * @return {Object} current WEBUI_Request instance
   */
  configure_PUT({ cache = false,
    data = {},
    success = [], error = [], complete = [],
    timeout = this._REQ_TIMEOUT_INTERVAL,
    key = null
  }) {

    return this.configure({
      method: "PUT",
      dataType: "text", data: data,
      cache: cache,
      success: success, error: error, complete: complete,
      timeout: timeout,
      need_auth: true,
      key: key
    })
  }

  /**
   * This method configures the asynchronous DELETE HTTP request (ajax) 
   * according to the params passed
   * 
   * @param {Object} options - All the configuration options.
   * @param {?boolean} options.cache - If set to false, it will force requested 
   *                                   pages not to be cached by the browser.
   * @param {?function[]} options.success - A sequence of functions to be called
   *                                        if the request succeeds.
   * @param {?function[]} options.complete - A sequence of functions to be 
   *                                        called when the request finishes 
   *                                        (after success and error callbacks 
   *                                        are executed).
   * @param {?function[]} options.error - A sequence of functions to be called 
   *                                      if the request fails.
   * @param {?number} options.timeout - Set a timeout (in milliseconds) for the 
   *                                    request. A value of 0 means there will 
   *                                    be no timeout.
   * @param {?Object|string} options.key - a parameter identifying the specific 
   *                                      target of the request
   * 
   * @return {Object} current WEBUI_Request instance
   */
  configure_DELETE({ cache = false,
    success = [], error = [], complete = [],
    timeout = this._REQ_TIMEOUT_INTERVAL,
    key = null
  }) {
    return this.configure({
      method: "DELETE",
      dataType: "json", data: "",
      cache: cache,
      success: success, error: error, complete: complete,
      timeout: timeout,
      need_auth: true,
      key: key
    })
  }

  /**
   * This method performs the currently configured (this._REQUEST) 
   * asynchronous HTTP request
   */
  perform() {
    $.ajax(this.REQUEST)
  }
}

/**
 * Class WEBUI_Request_DEVICE extends WEBUI_Request to the DEVICE specific case
 * 
 * @extends {WEBUI_Request}
 */
class WEBUI_Request_DEVICE extends WEBUI_Request {

  /**
   * @override
   */
  get_formatted_data(data, method = "GET") {

    if ((method === "POST") ||
      (method === "PUT")) {
      if (!this._is_string(data)) {
        data = JSON.stringify(data)
      }
    }
    else {
      data = ""
    }

    return super.get_formatted_data(data, method)
  }
}

/**
 * Support global variable for storing the "entities" of EMPOWER and refer them 
 * univocally in the WEBUI
 */
EMPOWER_ENTITIES={
  DEVICE:{
    WTP: "WTP",
    VBS: "VBS"
  }
}

/**
 * Class WEBUI_Request_WTP extends WEBUI_Request_DEVICE to the WTP specific 
 * case. It is actually just an alias of the extended class
 * 
 * @extends {WEBUI_Request_DEVICE}
 */
class WEBUI_Request_WTP extends WEBUI_Request_DEVICE {

  /**
   * @override
   */
  get_URL(method = "GET", key = null) {
    if (this._is_there(key)) {
      if ((method === "GET") ||
        (method === "PUT") ||
        (method === "DELETE")) {
        return this._ENTRY_POINT + "wtps/" + key
      }
    }
    return this._ENTRY_POINT + "wtps"
  }

}

/**
 * Class WEBUI_Request_VBS extends WEBUI_Request_DEVICE to the VBS specific 
 * case. It is actually just an alias of the extended class
 * 
 * @extends {WEBUI_Request_DEVICE}
 */
class WEBUI_Request_VBS extends WEBUI_Request_DEVICE {

  /**
   * @override
   */
  get_URL(method = "GET", key = null) {
    if (this._is_there(key)) {
      if ((method === "GET") ||
        (method === "PUT") ||
        (method === "DELETE")) {
        return this._ENTRY_POINT + "vbses/" + key
      }
    }
    return this._ENTRY_POINT + "vbses"
  }

}

/**
 * Support factory for providing the proper WEBUI_Request_XXX class for the 
 * specified entity
 * 
 * @param {string} entity - identifier of the entity
 */
function REST_REQ(entity){
  switch(entity){
    case EMPOWER_ENTITIES.DEVICE.WTP:
      return new WEBUI_Request_WTP()
    case EMPOWER_ENTITIES.DEVICE.VBS:
      return new WEBUI_Request_VBS()
    default:
      console.warn("Entity", 
        entity, 
        "unknown, default WEBUI_Request instance returned")
      return new WEBUI_Request()
  }
}