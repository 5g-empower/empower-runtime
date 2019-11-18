/**
 * Class WEBUI_Log is a support class for logging
 * 
 * @requires js/support/empower-globals.js
 */


__EMPOWER_WEBUI.LOG={
  INSTANCE: null,
  ENABLED:{
    HTTP_RESPONSE: true
  }
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
  if (__EMPOWER_WEBUI.LOG.ENABLED.HTTP_RESPONSE){
    console.log("HTTP_RESPONSE LOG: ")
    args.forEach(function(arg, index){
      console.log("args["+index+"] (type:",(typeof arg),"): ",arg)
    })
  }
}