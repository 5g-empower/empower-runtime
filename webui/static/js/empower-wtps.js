$('#devices').removeClass('collapse');
$('#collapseTwo').addClass('show');
$('#devices_wtps').addClass('active');

$(document).ready(function() {

  aoColumns = [
          { "sTitle": "Address" },
          { "sTitle": "Description" },
          { "sTitle": "Last seen" },
          { "sTitle": "Address" },
          { "sTitle": "Status", "sClass": "text-center" }
  ]

  if ( __USERNAME == "root" ) {
    aoColumns.push({ "sTitle": "Actions", "sClass": "text-center" })
  }

  t = $('#dataTable').DataTable({
      "aoColumns": aoColumns
  });

  refresh_devices();

});

function add_wtp() {

  address = $("#address")[0].value
  desc = $("#desc")[0].value

  console.log(address)
  console.log(desc)

}

function refresh_devices() {

  t.clear();

  $.getJSON( "/api/v1/wtps", function( data ) {

    connected = 0
    offline = 0
    online = 0

    $.each( data, function( key, val ) {

      if ( val['state'] == "online" ) {
        online += 1
        state = '<a href="#" class="btn btn-success btn-circle btn-sm" />'
      } else if ( val['state'] == "connected") {
        connected += 1
        state = '<a href="#" class="btn btn-warning btn-circle btn-sm" />'
      } else {
        offline += 1
        state = '<a href="#" class="btn btn-danger btn-circle btn-sm" />'
      }

      actions = "-"

      if ( __USERNAME == "root" ) {
        actions = '<a href="" class="d-none d-sm-inline-block btn btn-sm btn-warning shadow-sm"><i class="fas fa-edit fa-sm text-white-50"></i>&nbsp;Edit</a>&nbsp;<a href="#" class="d-none d-sm-inline-block btn btn-sm btn-danger shadow-sm"><i class="fas fa-trash fa-sm text-white-50"></i>&nbsp;Remove</a>'
      }

      connection = "-"
      last_seen = "-"

      if ( val['state'] == "offline" ) {
          connection = val['connection']['addr']
          last_seen = val['last_seen']
      }

      t.row.add([
          val['addr'],
          val['desc'],
          last_seen,
          connection,
          state,
          actions
      ] ).draw( true );

    });

    $("#offline").html(offline)
    $("#online").html(online)
    $("#connected").html(connected)

  });

}
