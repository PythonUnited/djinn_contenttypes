djinn_contenttypes
===================

This module provides the content type framework for Djinn. Content
types are the 'things' that a user of the system can create, delete,
edit and view.


Views
-----

Djinn uses generic views for content types. The following views
normally apply:

 - Creation: either create or JSON create
   Creation can either use a temporary object, in case the add screen already
   provides some means of relating things to the new object, or simply use the
   standard add view, that doesn't create anything untill a commit.
   JSON create is used for inline adding of content.
   The default templates for creation are:
     


 - Update: either update or JSON update
 - Delete: delete or JSON delete
 - View: base view or modal view
   Templates: if modal=1 is passed as a GET parameter, the template is:
     <content type module>/snippets/<content type name>_modal_detail.html
   otherwise it is:
     <content type module>/<content type name>_detail.html