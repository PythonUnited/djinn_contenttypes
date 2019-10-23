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

  $(document).find(".modal:not(#MyModal)").remove();

  var styling = {"z-index": "5000"};

  var modal = $(data).modal({'show': false}).css(styling);

  modal.on('hidden', function () {
    $(this).remove();
    $(this).trigger("modal_action_hide", args);
    $(".modal-backdrop").remove();
  });

  modal.on('shown', function() {
    $(this).trigger("modal_action_show", args);
  });

  // bind some actions to this modal
  modal.on("click", ".cancel", function(e) {
    e.preventDefault();
    modal.modal('hide');
  });

  /*
   * The behavior of a modal form is: on success (status code 200)
   * the modal is closed, on failure (status 202) the received data is
   * assumed to be a new modal, to replace the current one.
   */
  modal.on("submit", ".modal-submit", function(e) {

    e.preventDefault();

    var form = $(e.target);

    $.ajax(form.attr("action"),
           {type: form.attr("method") || "POST",
            data: form.serialize(),
            success: function(data, status, xhr) {

              if (xhr.status == 202) {
                modal.find(".modal-body").replaceWith($(data).find(
                  ".modal-body"));
                modal.trigger("modal_action_show");
              } else {
                modal.modal('hide');
              }
            }
           });
  });

  return modal.modal('show');
};


$(document).ready(function() {

  $('input').placehold();
  $('textarea').placehold();

  // tooltips
  $('[data-toggle="tooltip"]').tooltip();

  $(document).on("modal_action_show", function(e) {

    var modal = $(e.target);

    modal.find('input,textarea').placehold();
  });


  $(document).on("modal_action_show", "#sharecontent", function(e) {

    var modal = $(e.target);

    modal.find(".relate").each(function() {

      djinn.forms.relate.init($(this));
    });

    modal.on("click", ":radio", function(e) {

      var input = $(e.target);

      $("#sharecontent .collapsed").hide();

      input.parents(".radio").next().show();
    });
  });

  $(document).on("click", "a.modal-action", function(e) {

    e.preventDefault();
    e.stopPropagation();

    var link = $(e.currentTarget);

    $.get(link.attr("href"), function(data) {

      djinn.contenttypes.show_modal(data);
    });
  });

  $(document).on("click", "input[name=publish_for_feed]", function(e) {

    if ($(this).attr("checked") == "checked") {
      $("div.feed-options").show();
    } else {
      $("div.feed-options").hide();
    }
  });

  $(document).on("focusout", ".description_feed_src", function(e) {
    if ($("#id_description_feed").val().length == 0 && $(".description_feed_src").val().length > 0) {

      $("#id_description_feed").val($(".description_feed_src").val())

    }
  });

    $(document).on("click", ".js-copy-orig-url", function(e) {
      // Copies the full URL to an image to the client clipboard

      e.preventDefault();
      e.stopPropagation();

      var hiddenEleForCopy = $('#_hiddenEleForCopy_');
      // Checking Element exists or not
      if(!hiddenEleForCopy.length){
        $('body').append('<input style="position:absolute;top: -9999px;" id="_hiddenEleForCopy_" value=""></input>');
        hiddenEleForCopy = $('#_hiddenEleForCopy_');
      }
      hiddenEleForCopy.val(location.protocol + "//" + location.host + $(e.currentTarget).data('url'));
      hiddenEleForCopy.select();
      document.execCommand('copy');
      document.getSelection().removeAllRanges();

      var copyMsgElem = $('.copyMsg');
      if(!copyMsgElem.length) {
        $(e.currentTarget).append("<div class='copyMsg' style='display:none'>Gekopieerd!</div>\n");
      }
      $(e.currentTarget).find('.copyMsg').fadeIn(400).delay(200).fadeOut(400);
    });

});
