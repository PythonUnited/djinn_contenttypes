djinn_contenttypes
===================

This module provides the content type framework for Djinn. Content
types are the 'things' that a user of the system can create, delete,
edit and view.


Views
-----

Djinn uses generic views for content types. Views behave differently
according to how they are called: when called Ajax style or when
modal=1 is passed as parameter, the template rendered will be 'modal',
otherwise a complete HTML page will be rendered. Successfull add and
edit views will return a 'record' like snippet, assuming that they
were called to return an inline template view of the object.

The following views normally apply:

 - Creation:
   Creation can either use a temporary object, in case the add screen already
   provides some means of relating things to the new object, or simply use the
   standard add view, that doesn't create anything untill a commit.
   The default templates for creation are:
      <app label>/<content type name>_add.html
      <app label>/<content type name>_add_modal.html
      djinn_contenttypes/base_add.html
      djinn_contenttypes/base_add_modal.html

 - Update: either update or JSON update
      <app label>/<content type name>_edit.html
      <app label>/<content type name>_edit_modal.html
      djinn_contenttypes/base_edit.html
      djinn_contenttypes/base_edit_modal.html

 - Delete: delete or JSON delete

 - View: base view or modal view
     <content type module>/<content type name>_modal_detail.html
     <content type module>/<content type name>_detail.html
      djinn_contenttypes/base_detail.html
      djinn_contenttypes/base_detail_modal.html