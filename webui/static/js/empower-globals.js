/**
 * WEBUI GLOBAL VARIABLES
 */


/**
 * GLOBAL VARIABLES DEFINED ELSEWHERE
 * 
 * @ templates/base.html
 * 
 * __USERNAME: currently logged user's username
 * __PASSWORD: currently logged user's password
 * __BASIC_AUTH: currently logged user's basic authentication
 * __PROJECT_ID: currently selected project's identifier
 *  
 */

/**
 * __EMPOWER_WEBUI is the reference dictionary for the whole WEBUI
 * Each other WEBUI classes may integrate it with their own global variables,
 * thus implementing a single reference variable for the whole solution, 
 * reducing the chance for collision with other constants defined in external / 
 * vendor modules
 * 
 * @global
 */
__EMPOWER_WEBUI= {}

/**
 * Integrating the previously defined global vars
 */

 __EMPOWER_WEBUI.USER={
   USERNAME: __USERNAME,
   PASSWORD: __PASSWORD,
   BASIC_AUTH: __BASIC,
   ROOT: "root"
 }

 __EMPOWER_WEBUI.PROJECT={
  ID: __PROJECT_ID
}

__EMPOWER_WEBUI.SSID={
  TYPE:{
    UNIQUE: "unique",
    SHARED: "shared",
  }
}