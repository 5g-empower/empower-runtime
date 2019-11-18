/**
 * TODO: WORTH BEING REWRITED?
 * @param {*} url 
 */
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

$(document).ready(function() {

  $('.modal').on('hidden.bs.modal', function(event) {
      $(this).removeClass( 'fv-modal-stack' );
      $('body').data( 'fv_open_modals', $('body').data( 'fv_open_modals' ) - 1 );
  });

  $('.modal').on('shown.bs.modal', function (event) {
      // keep track of the number of open modals
      if ( typeof( $('body').data( 'fv_open_modals' ) ) == 'undefined' ) {
          $('body').data( 'fv_open_modals', 0 );
      }

      // if the z-index of this modal has been set, ignore.
      if ($(this).hasClass('fv-modal-stack')) {
          return;
      }

      $(this).addClass('fv-modal-stack');
      $('body').data('fv_open_modals', $('body').data('fv_open_modals' ) + 1 );
      $(this).css('z-index', 1040 + (10 * $('body').data('fv_open_modals' )));
      $('.modal-backdrop').not('.fv-modal-stack').css('z-index', 1039 + (10 * $('body').data('fv_open_modals')));
      $('.modal-backdrop').not('fv-modal-stack').addClass('fv-modal-stack'); 

  });        
});




