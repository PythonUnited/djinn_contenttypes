from django.http import QueryDict
from django.views.generic.detail import DetailView as BaseDetailView
from django.views.generic.edit import UpdateView as BaseUpdateView
from django.views.generic.edit import DeleteView as BaseDeleteView
from django.views.generic.edit import CreateView as BaseCreateView
from django.http import HttpResponseRedirect, HttpResponse
from django.db import models
from django.core.urlresolvers import reverse
from pgutils.exception_handlers import Http403
from djinn_contenttypes.registry import CTRegistry
from djinn_contenttypes.utils import get_object_by_ctype_id


class TemplateResolverMixin(object):

    @property
    def app_label(self):
        try:
            return self.object.app_label
        except:
            return self.model.__module__.split(".")[0]

    @property
    def ct_name(self):
        try:
            return self.object.ct_name
        except:
            return self.model.__name__.lower()            

    def get_template_names(self):

        if self.request.GET.get("modal", False) or self.request.is_ajax():
            modal = "_modal"
        else:
            modal = ""

        return ["%s/%s_%s%s.html" % (self.app_label, self.ct_name, self.mode,
                modal),
                "djinn_contenttypes/base_%s%s.html" % (self.mode, modal)
                ]

    @property
    def delete_url(self):

        return reverse("%s_delete_%s" % (self.app_label, self.ct_name),
                       kwargs={'pk': self.object.id})

    @property
    def add_url(self):

        return reverse("%s_add_%s" % (self.app_label, self.ct_name))

    @property
    def edit_url(self):

        return reverse("%s_edit_%s" % (self.app_label, self.ct_name),
                       kwargs={'pk': self.object.id})

    @property
    def view_url(self):

        return reverse("%s_detail_%s" % (self.app_label, self.ct_name),
                       kwargs={'pk': self.object.id})


class ViewContextMixin(object):

    def get_context_data(self, **kwargs):

        """ Always add self as "view" so as to be able to call methods
        and properties on view """

        ctx = kwargs
        ctx.update({"view": self, "object": self.object})

        return ctx


class DetailView(TemplateResolverMixin, ViewContextMixin, BaseDetailView):

    """ Detail view for simple content, not related, etc. All intranet
    views should extend this view.
    """

    mode = "detail"

    def get_template_names(self):

        """ If the request is Ajax, and no one asked for a modal view,
        assume that we need to return a record like view"""

        templates = super(DetailView, self).get_template_names()

        if self.request.is_ajax() and \
                not self.request.REQUEST.get("modal", False):
            templates = ["%s/snippets/%s.html" % 
                         (self.app_label, self.ct_name)] \
                + templates

        return templates


    def get(self, request, *args, **kwargs):

        """ We need our own implementation of GET, to be able to do permission
        checks on the object """

        self.object = self.get_object()

        perm = CTRegistry.get(self.ct_name).get("view_permission", 
                                                'contenttypes.view')

        if not self.request.user.has_perm(perm, obj=self.object):
            raise Http403()

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class CTDetailView(DetailView):
    
    """ Detailview that applies to any content, determined by the url parts """

    def get_object(self, queryset=None):

        """ Retrieve context from URL parts app, ctype and id."""

        return get_object_by_ctype_id(
            self.kwargs['ctype'], 
            self.kwargs.get('id', self.kwargs.get('pk', None)))


class CreateView(TemplateResolverMixin, ViewContextMixin, BaseCreateView):

    mode = "add"
    create_tmp_object = False

    @models.permalink
    def get_success_url(self):

        """ Return the URL to which the edit/create action should
        return upon success"""

        return ('%s_view_%s' % (self.app_label, self.ct_name), (), 
                {"slug":self.object.slug, "pk": str(self.object.id)})

    def get_object(self, queryset=None):

        if not self.create_tmp_object:
            return None
        else:
            return self.model.objects.create(creator=self.request.user,
                                             changed_by=self.request.user,
                                             )

    def get(self, request, *args, **kwargs):

        """ Override get so as to be able to check permissions """

        perm = CTRegistry.get(self.ct_name).get("add_permission", 
                                                'contenttypes.add_contenttype')

        if not self.request.user.has_perm(perm):
            raise Http403()
        
        self.object = self.get_object()

        if self.create_tmp_object:
            return HttpResponseRedirect(self.edit_url)
        else:
            return super(CreateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        perm = CTRegistry.get(self.ct_name).get("add_permission", 
                                                'contenttypes.add_contenttype')

        if not self.request.user.has_perm(perm):
            raise Http403()

        if self.request.POST.get('action', None) == "cancel":

            # There may be a temporary object...
            try:
                self.object = self.get_object()

                if getattr(self.object, "is_tmp", False):
                    self.object.delete()
            except:
                pass

            return HttpResponseRedirect(
                request.user.profile.get_absolute_url())
        else:
            return super(CreateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):

        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.changed_by = self.request.user
        self.object.is_tmp = False
        self.object.save()

        try:
            self.object.set_owner(self.request.user)
        except:
            pass
            
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form),
                                       status=202)


class UpdateView(TemplateResolverMixin, ViewContextMixin, BaseUpdateView):

    mode = "edit"

    @models.permalink
    def get_success_url(self):

        """ Return the URL to which the edit/create action should
        return upon success"""

        return ('%s_view_%s' % (self.app_label, self.ct_name), (), 
                {"slug":self.object.slug, "pk": str(self.object.id)})

    def get(self, request, *args, **kwargs):

        """ Check permissions for editing """

        self.object = self.get_object()

        perm = CTRegistry.get(self.ct_name).get(
            "edit_permission", 
            'contenttypes.change_contenttype')

        if not self.request.user.has_perm(perm, obj=self.object):
            raise Http403()

        return super(UpdateView, self).post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        """ Check whether the user wants to cancel the whole
        operation. If so, we need to check whether is was an edit, or
        initial object. If the latter is the case, delete the 'tmp'
        object."""

        self.object = self.get_object()

        perm = CTRegistry.get(self.ct_name).get(
            "edit_permission", 
            'contenttypes.change_contenttype')

        if not self.request.user.has_perm(perm, obj=self.object):
            raise Http403()

        if self.request.POST.get('action', None) == "cancel":            
            return HttpResponseRedirect(self.object.get_absolute_url())
        else:
            return super(UpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.update(commit=False)
        self.object.changed_by = self.request.user
        self.object.save()

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form),
                                       status=202)


class DeleteView(TemplateResolverMixin, ViewContextMixin, BaseDeleteView):

    mode = "delete"

    def delete(self, request, *args, **kwargs):

        self.object = self.get_object()

        perm = CTRegistry.get(self.ct_name).get(
            "delete_permission", 
            'contenttypes.delete_contenttype')

        if not self.request.user.has_perm(perm, obj=self.object):
            raise Http403()

        try:
            # enable signal handlers to access last change info
            #
            self.object.changed_by = self.request.user
            self.object.delete()
        except:
            return HttpResponseRedirect(self.view_url)

        if self.request.is_ajax():
            return HttpResponse("Bye bye", content_type='text/plain')
        else:
            return HttpResponseRedirect(self.get_success_url())        
        
    def get_success_url(self):

        """ Return the URL to which the edit/create action should
        return upon success"""

        return self.request.user.profile.get_absolute_url()

    def get(self, request, *args, **kwargs):

        """ Make sure that the confirm delete is sent as text/plain """

        self.object = self.get_object()
        context = self.get_context_data(object=self.object, **kwargs)

        return self.render_to_response(context, mimetype="text/plain")
