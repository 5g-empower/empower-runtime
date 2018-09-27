function vf_STR_def(value){
    return true;
}

function vf_STR_mac(value){
    var a = value.split(":");
    if( a.length != 6 )
        return false;
    else{
        for( var i=0; i<6; i++){
            var n = parseInt(a[i],16);
            var nS = "0" + n.toString(16);
            nS = nS.substring(nS.length-2, nS.length);
            if( !(nS === a[i].toLowerCase()) )
                return false
        }
    }
    return true;
}

function vf_STR_role(value){
    if( value === "admin") return true;
    else if( value === "user") return true;
    else return false;
}

function vf_STR_bssid_type(value){
    if( value === "unique") return true;
    else if( value === "shared") return true;
    else return false;
}

function vf_STR_owner(value){
    for( var a in __CACHE.c[ __QE.targets.ACCOUNT ] ){
        if( __CACHE.c[ __QE.targets.ACCOUNT ][a].username === value ) return true
    }
    return false;
}

function vf_STR_plmnid(value){
    return true;
}