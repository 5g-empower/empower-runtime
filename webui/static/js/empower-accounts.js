$(document).ready(function() {

  aoColumns = [
          { "sTitle": "Username" },
          { "sTitle": "Name" },
          { "sTitle": "E-Mail" },
          { "sTitle": "Actions", "sClass": "text-center" }
  ]

  t = $('#dataTable').DataTable({
      "aoColumns": aoColumns
  });

  refresh_accounts();

});

function create_account() {

  username = $("#username")[0].value
  name = $("#name")[0].value
  password = $("#email")[0].value

  console.log(username)
  console.log(name)
  console.log(password)

}

function remove_account(username) {

  empower_ajax_delete( "/api/v1/accounts/" + username );

}

function refresh_accounts() {

  $("#alert").hide();

  t.clear();

  $.getJSON( "/api/v1/accounts", function( data ) {

    $.each( data, function( key, val ) {

      actions = '<a href="" class="d-none d-sm-inline-block btn btn-sm btn-warning shadow-sm"><i class="fas fa-edit fa-sm text-white-50"></i>&nbsp;Edit</a>&nbsp;<a href="#" onclick="remove_account(\''+val['username']+'\')" class="d-none d-sm-inline-block btn btn-sm btn-danger shadow-sm"><i class="fas fa-trash fa-sm text-white-50"></i>&nbsp;Remove</a>'

      t.row.add([
          val['username'],
          val['name'],
          val['email'],
          actions
      ] ).draw( true );

    });

  });

}
