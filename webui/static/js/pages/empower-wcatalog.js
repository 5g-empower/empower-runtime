$('#workers').removeClass('collapsed');
$('#collapseThree').addClass('show');
$('#workers_catalog').addClass('active');

$(document).ready(function() {
  console.warn("THIS PAGE IS A WORK IN PROGRESS!")
  refresh_catalog();
});

function refresh_catalog() {

  $("#catalog").html("")

  $.getJSON( "/api/v1/catalog", function( data ) {

    catalog = ""

    $.each( data, function( key, val ) {

      catalog += '<div class="col-xl-4 col-md-6 mb-4"><div class="card border-left-primary shadow h-100 py-2"><div class="card-body"><div class="row no-gutters align-items-center"><div class="col-xl-10"><div class="h5 mb-2 font-weight-bold text-gray-800">' + val['name'] + '</div><div class="text-xs font-weight-bold text-primary text-uppercase mb-2">' + val['desc'] + '</div></div><div class="col-xl-2 text-right"><a href="#" class="btn btn-sm btn-success shadow-sm"><i class="fas fa-play fa-sm text-white-50"></i></a></div></div></div></div></div>'

    });

    $("#catalog").html(catalog)

  });

}
