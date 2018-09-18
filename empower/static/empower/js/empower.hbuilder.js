/*******************************************************************************
*
* HTML ELEMENT MANAGER
*
*******************************************************************************/

class HBuilder{

    constructor(conf){
        this.conf = conf;
    }

    // Create element
    ce(element_type){
        return document.createElement(element_type);
    }

    ceCOL(size = -1, number=1){
        var ret = this.ce("DIV");

        if (size === -1){
            $( ret ).attr("style","width: "+(100/parseInt(number) -1)+"% !important; float: left; margin-left: 1%;");
        }
        else{
            $( ret ).addClass("col-"+size+"-"+number);
        }
        return ret;
    }

    ceCLEARFIX(){
        var ret = this.ce("DIV");
        $( ret ).addClass("clearfix");
        return ret;
    }


    // create Font-Awesome icon
    ceFAI(iconname){
        var ret = this.ce("I");
        $( ret ).addClass("fa "+iconname);
        return ret;
    };


    ceROW(){
        var ret = this.ce("DIV");
        $( ret ).addClass("row");
        return ret;
    }

    cePANEL(){
        var ret = this.ce("DIV");
        $( ret ).addClass("panel");
        return ret;
    }

    cePANEL_H(){
        var ret = this.ce("DIV");
        $( ret ).addClass("panel-heading");
        return ret;
    }

    cePANEL_B(){
        var ret = this.ce("DIV");
        $( ret ).addClass("panel-body");
        return ret;
    }

    cePANEL_F(){
        var ret = this.ce("DIV");
        $( ret ).addClass("panel-footer");
        return ret;
    }

    // Get Element
    ge(element_id){
        return document.getElementById(element_id);
    }

    generateID(keys, brand="EMP", separator="_"){
        var ret = brand;
        for (var i = 0; i < keys.length; i++){
            ret+= "_"+keys[i];
        }
        return ret;
    }

    isArray(what) {
        return Object.prototype.toString.call(what) === '[object Array]';
    }

    syntaxHighlight(json) {
        // KUDOS TO:  https://stackoverflow.com/users/27862/user123444555621
        json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
            var cls = 'number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'key';
                } else {
                    cls = 'string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'boolean';
            } else if (/null/.test(match)) {
                cls = 'null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
    }

    fdownload(txt, filename){
        var element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(txt));
        element.setAttribute('download', filename);

        element.style.display = 'none';
        document.body.appendChild(element);

        element.click();

        document.body.removeChild(element);
    };

    wrapFunction(func,params){
        return func.bind(this, params);
    };

    getDTKeyFields(data){
        var key = "";
        for( var i=0; i<data.length; i++){
            if( data[i].indexOf("key") != -1 ){
                var str = data[i].substr(data[i].indexOf("key")+5)
                key = str.substr(0, str.indexOf("\""))
            }
        }
//        console.log(key)
        return key
    }

    getKeyValue(obj, key){
        var keyAttr = null;
        var found = null;
        var tag = this.mapName(obj);

        for( var a in __DESC.d[tag].attr ){
            if( __DESC.d[tag].attr[a].isKey )
                keyAttr = a;
        }
//        console.log(keyAttr, key)
        for( var i=0; i<__CACHE.c[tag].length; i++){
            if( __CACHE.c[tag][i][keyAttr] === key ){
                found = __CACHE.c[tag][i];
            }
        }
        return found;
    }

    mapName(obj){
        var tag = "";
        if( obj === "components" )
            tag = "active";
        else if( __QE.targets[obj.toUpperCase()] )
            tag = __QE.targets[obj.toUpperCase()]
        else
            tag = obj;
        return tag;
    }

    checkDifference(firstList, scndList){ console.log(firstList, scndList)
        var onlyFrst = [];
        var onlyScnd = [];
        var shared = [];
        for( var n in firstList ){
            if( n in scndList ){
                shared.push( firstList[n] );
            }
            else{
                onlyFrst.push( firstList[n] );
            }
        }
        for( var p in scndList ){
            if( !(p in firstList) ){
                onlyScnd.push( scndList[p] );
            }
        }
        return [onlyFrst, onlyScnd, shared];
    }

    checkAllDifferences(firstList, scndList){
        var onlyFrst = [];
        var onlyScnd = [];
        var sharedEqual = [];
        var sharedDiff = [];
        for( var n in firstList ){
            if( n in scndList ){
                if( JSON.stringify(firstList[n]) === JSON.stringify(scndList[n]) ){
                    sharedEqual.push( scndList[n] )
                }
                else{
                    sharedDiff.push( scndList[n] )  // TODO EMP_if: comunque prediligo la seconda!
                }
            }
            else{
                onlyFrst.push( firstList[n] );
            }
        }
        for( var p in scndList ){
            if( !(p in firstList) ){
                onlyScnd.push( scndList[p] );
            }
        }
        return [onlyFrst, onlyScnd, sharedEqual, sharedDiff];
    }

}
