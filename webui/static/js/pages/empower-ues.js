$('#clients').removeClass('collapsed');
$('#collapseOne').addClass('show');
$('#clients_ues').addClass('active');

console.log("__EMPOWER_WEBUI",__EMPOWER_WEBUI)

$(document).ready(function() {

  aoColumns = [
    { "sTitle": "IMSI" },
    { "sTitle": "TMSI" },
    { "sTitle": "RNTI" },
    { "sTitle": "PLMNID" },
    { "sTitle": "PCI" },
    { "sTitle": "VBS" },
  ]

  DATATABLE = $('#dataTable').DataTable({
  "aoColumns": aoColumns
  });

  refresh_datatable();
});

ENTITY = null
CF = __EMPOWER_WEBUI.CORE_FUNCTIONS

CURRENT_UE = null
CURRENT_VBS = null
VBSES_FOR_HANDOVER = []

OFFLINE_DEBUG = false

function format_datatable_data( data ) {

  if (OFFLINE_DEBUG){
    data = lvap_json
  }

  $.each( data, function( key, val ) {

    let imsi = val.imsi
    let tmsi = val.tmsi
    let rnti = val.rnti
    let plmnid = val.plmnid
    let vbs = null
    let pci = null

    if (CF._is_there(val["cell"])){
      pci = val.cell.pci
      vbs = val.cell.addr
    }

    DATATABLE.row.add([
        imsi,
        tmsi,
        rnti,
        plmnid,
        pci,
        vbs
    ] )

  });

  DATATABLE.draw(true)

}

function refresh_datatable() {

  ENTITY = __EMPOWER_WEBUI.ENTITY.CLIENT.UE

  DATATABLE.clear();

  // format_datatable_data(ue_json)

  REST_REQ(ENTITY).configure_GET({
      success: [ empower_log_response, format_datatable_data],
      error: [ empower_log_response,  empower_alert_generate_error ]
    })
    .perform()

}
