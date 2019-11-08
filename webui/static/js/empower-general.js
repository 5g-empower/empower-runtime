function empower_ajax_delete(url) {
  $.ajax({
    url: url,
    type: 'DELETE',
    headers: {
      "Authorization": __BASIC
    },
    dataType: 'json',
    success: function(response) {
      refresh_accounts();
      message = "<strong>200: Success."
      $('#alert').removeClass('collapse');
      $("#alert").addClass('alert-success')
      $("#alert").addClass('show')
      $("#alert").show()
      $("#alert div").html(message);
    },
    error: function(response) {
      title = response.responseJSON['title']
      status_code = response.responseJSON['status_code']
      detail = response.responseJSON['detail']
      message = "<strong>" + status_code + ": " + title + ".</strong>&nbsp;" + detail
      $('#alert').removeClass('collapse');
      $("#alert").addClass('alert-danger')
      $("#alert").addClass('show')
      $("#alert").show()
      $("#alert div").html(message);
    },
  });
}
