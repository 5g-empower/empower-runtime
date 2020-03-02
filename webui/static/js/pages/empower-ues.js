$('#clients').removeClass('collapsed');
$('#collapseOne').addClass('show');
$('#clients_ues').addClass('active');

console.log("__EMPOWER_WEBUI",__EMPOWER_WEBUI)

$(document).ready(function() {

  aoColumns = [
    { "sTitle": "Address" },
    { "sTitle": "IMSI" },
    { "sTitle": "TIMSI" },
    { "sTitle": "VBS" },
    { "sTitle": "Actions", "sClass": "text-center" }
  ]

  DATATABLE = $('#dataTable').DataTable({
  "aoColumns": aoColumns
  });

  refresh_datatable();
});

ENTITY = null
CF = __EMPOWER_WEBUI.CORE_FUNCTIONS

CURRENT_LVAP = null
CURRENT_WTP = null
WTPS_FOR_HANDOVER = []

OFFLINE_DEBUG = false

function format_datatable_data( data ) {

}

function refresh_datatable() {

  DATATABLE.clear();
  DATATABLE.draw(true)

}

