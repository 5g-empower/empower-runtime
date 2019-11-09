$(document).ready(function() {
  refresh_projects();
  refresh_owners();
});

function create_project() {

  address = $("#address")[0].value
  desc = $("#desc")[0].value

  console.log(address)
  console.log(desc)

}

function refresh_projects() {

  $("#projects").html("")

  $.getJSON( "/api/v1/projects", function( data ) {

    projects = ""

    $.each( data, function( key, val ) {

      if ( __USERNAME == "root" ) {

        cmd = '<a href="/auth/switch_project" class="d-none d-sm-inline-block btn btn-sm btn-danger shadow-sm"><i class="fas fa-trash fa-sm text-white-50"></i>&nbsp; Remove</a>'

      } else {

        if ( __PROJECT_ID != key ) {

          cmd = '<a href="/auth/switch_project?project_id=' + key + '" class="d-none d-sm-inline-block btn btn-sm btn-success shadow-sm"><i class="fas fa-flag fa-sm text-white-50"></i>&nbsp;Select</a>'

        } else {

          cmd = '<a href="/auth/switch_project" class="d-none d-sm-inline-block btn btn-sm btn-secondary shadow-sm"><i class="fas fa-times fa-sm text-white-50"></i> Deselect</a>'

        }

      }

      projects += '<div class="col-xl-5 col-md-6 mb-4"><div class="card border-left-primary shadow h-100 py-2"><div class="card-body"><div class="row no-gutters align-items-center"><div class="col mr-2"><div class="text-xs font-weight-bold text-primary text-uppercase mb-1">' + key + '</div><div class="h5 mb-0 font-weight-bold text-gray-800">' + val['desc'] + '</div></div><div class="col-auto">' + cmd + '</div></div></div></div></div>'

    });

    $("#projects").html(projects)

  });

}

function refresh_owners() {
  $("#owner").empty()
  $.getJSON( "/api/v1/accounts", function( data ) {
    $.each( data, function( key, val ) {
      if ( key != 'root' ) {
        $('#owner').append(new Option(val['name'] + ' (' + val['email'] + ')', key))
      }
    });
  });
}
