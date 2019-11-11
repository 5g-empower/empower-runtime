$('#devices').removeClass('collapse');
$('#collapseTwo').addClass('show');
$('#devices_wtps').addClass('active');

$(document).ready(function() {

  aoColumns = [
          { "sTitle": "Address" },
          { "sTitle": "Description" },
          { "sTitle": "Last seen" },
          { "sTitle": "Address" },
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
      } else if ( val['state'] == "connected") {
        connected += 1
      } else {
        offline += 1
      }

      actions = "-"

      if ( __USERNAME == "root" ) {
        actions = '<a href="" class="d-none d-sm-inline-block btn btn-sm btn-warning shadow-sm"><i class="fas fa-edit fa-sm text-white-50"></i>&nbsp;Edit</a>&nbsp;<a href="#" class="d-none d-sm-inline-block btn btn-sm btn-danger shadow-sm"><i class="fas fa-trash fa-sm text-white-50"></i>&nbsp;Remove</a>'
      }

      connection = "-"
      last_seen = "-"

      if ( val['state'] == "online" ) {
          connection = val['connection']['addr']
          last_seen = val['last_seen']
      }

      t.row.add([
          val['addr'],
          val['desc'],
          last_seen,
          connection,
          actions
      ] ).draw( true );

    });

    $("#offline").html(offline)
    $("#online").html(online)
    $("#connected").html(connected)

  });

}
