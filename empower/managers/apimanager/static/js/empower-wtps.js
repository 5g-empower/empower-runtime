$('#devices').removeClass('collapse');
$('#collapseTwo').addClass('show');
$('#devices_wtps').addClass('active');

// Call the dataTables jQuery plugin
$(document).ready(function() {
  $('#dataTable').DataTable();
});
