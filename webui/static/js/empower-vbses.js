$('#devices').removeClass('collapse');
$('#collapseTwo').addClass('show');
$('#devices_vbses').addClass('active');

// Call the dataTables jQuery plugin
$(document).ready(function() {
  $('#dataTable').DataTable();
});
