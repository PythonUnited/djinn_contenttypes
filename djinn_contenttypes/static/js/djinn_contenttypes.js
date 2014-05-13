if (djinn === undefined) {
    var djinn = {};
}


if (djinn.contenttypes === undefined) {
  djinn.contenttypes = {};
}


/**
 * Show given data as modal. This assumes the data is actually the
 * correct HTML for a bootstrap modal box. Since the modal data
 * @param data modal box as HTML
 * @param args Extra event arguments as list.
 */
djinn.contenttypes.show_modal = function(data, args) {

  if (!args) {
    args = [];
  }

  var styling = {"z-index": "5000"};

  var modal = $(data).modal({'show': false}).css(styling);

  modal.on('hidden', function () { $(this).remove(); });
  modal.on('shown', function() { $(this).trigger("modal_action_show", args); });

  modal.modal('show');
};


$(document).ready(function() {

  $('input').placehold();
  $('textarea').placehold();

  $(document).on("click", ".modal .cancel", function(e) {

    e.preventDefault();

    $(e.currentTarget).parents(".modal").modal('hide');
  });

  $(document).on("click", "#sharecontent :radio", function(e) {

    var input = $(e.target);

    $("#sharecontent .collapsed").hide();

    input.parents(".radio").next().show();
  });

  $(document).on("modal_action_show", function(e) {

    var modal = $(e.target);

    modal.find('input,textarea').placehold();
  });

  $(document).on("modal_action_show", "#sharecontent", function(e) {

    var modal = $(e.target);

    modal.find(".relate").each(function() {

      djinn.forms.initRelateWidget($(this));
    });
  });

  $(document).on("click", "a.modal-action", function(e) {

    e.preventDefault();

    var link = $(e.currentTarget);

    $.get(link.attr("href"), function(data) {

      djinn.contenttypes.show_modal(data);
    });
  });

  /*
   * The behavior of a modal form is: on success (status code 200)
   * the modal is closed, on failure (status 202) the received data is
   * assumed to be a new modal, to replace the current one.
   */
  $(document).on("submit", ".modal-submit", function(e) {

    e.preventDefault();    

    var form = $(e.target);
    
    $.ajax(form.attr("action"),
           {type: form.attr("method") || "POST",
            data: form.serialize(),
            success: function(data, status, xhr) {

              form.parents(".modal").modal("hide");
           
              if (xhr.status == 202) {
                djinn.contenttypes.show_modal(data);
              }
            }
           });    
  });
  
});
