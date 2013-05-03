from django.http import QueryDict
from django.views.generic.detail import DetailView as BaseDetailView
from django.views.generic.edit import UpdateView as BaseUpdateView
from django.views.generic.edit import DeleteView as BaseDeleteView
from django.views.generic.edit import CreateView as BaseCreateView
from django.http import HttpResponseRedirect
from django.db import models
from django.core.urlresolvers import reverse
from pgutils.exception_handlers import Http403
from djinn_contenttypes.registry import CTRegistry


class TemplateResolverMixin(object):

    def get_template_names(self):

        if self.request.GET.get("modal", False):
            modal = "_modal"
        else:
            modal = ""

        return ["%s/%s_%s%s.html" % (
                self.model.__module__.split(".")[0],
                self.model.__name__.lower(),
                self.mode,
                modal),
                "djinn_contenttypes/base_%s.html" % self.mode
                ]


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

    def get_object(self, queryset=None):

        obj = super(DetailView, self).get_object(queryset=queryset)

        perm = CTRegistry.get(obj.ct_name).get("view_permission", 
                                               'contenttypes.view')

        if not self.request.user.has_perm(perm, obj=obj):
            raise Http403()

        return obj


class CreateView(TemplateResolverMixin, ViewContextMixin, BaseCreateView):

    mode = "add"

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instanciating the form.
        """

        kwargs = super(CreateView, self).get_form_kwargs()

        if self.request.method == "POST":
    
            del kwargs['data']

            data = QueryDict("", mutable=True)

            for key in self.request.POST.keys():
                data[key] = self.request.POST[key]

            data['creator'] = data['owner'] = self.request.user.id

            kwargs.update({"data": data})

        return kwargs

    def get_context_data(self, **kwargs):

        ctx = super(CreateView, self).get_context_data(**kwargs)
        ctx.update({"ct_name": self.model.__name__.lower()})

        return ctx

    def post(self, request, *args, **kwargs):

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
        self.object = form.save()
        self.object.is_tmp = False
        
        return HttpResponseRedirect(self.get_success_url())


class UpdateView(TemplateResolverMixin, ViewContextMixin, BaseUpdateView):

    mode = "edit"

    def get_object(self, queryset=None):

        obj = super(DetailView, self).get_object(queryset=queryset)

        perm = CTRegistry.get(obj.ct_name).get(
            "edit_permission", 
            'contenttypes.change_contenttype')

        if not self.request.user.has_perm(perm, obj=obj):
            raise Http403()

        return obj

    @property
    def delete_url(self):

        return reverse("%s_delete_%s" % (self.object.app_label,
                                         self.object.ct_name),
                       kwargs={'pk': self.object.id}),

    @models.permalink
    def get_success_url(self):

        """ Return the URL to which the edit/create action should
        return upon success"""

        obj = self.get_object()

        return ('%s_view_%s' % (obj.app_label, obj.ct_name), (), 
                {"slug":obj.slug, "pk": str(obj.id)})

    def post(self, request, *args, **kwargs):

        """ Check whether the user wants to cancel the whole
        operation. If so, we need to check whether is was an edit, or
        initial object. If the latter is the case, delete the 'tmp'
        object."""

        self.object = self.get_object()

        if self.request.POST.get('action', None) == "cancel":            
            return HttpResponseRedirect(self.object.get_absolute_url())
        else:
            return super(UpdateView, self).post(request, *args, **kwargs)


class DeleteView(BaseDeleteView):

    template_name = "djinn_contenttypes/snippets/confirm_delete.html"

    def delete(self, request, *args, **kwargs):

        self.object = self.get_object()

        try:
            self.object.delete()
        
            return HttpResponseRedirect(self.get_success_url())        
        except:
            return HttpResponseRedirect(self.get_success_url())        

    def get_success_url(self):

        """ Return the URL to which the edit/create action should
        return upon success"""

        return self.request.user.profile.get_absolute_url()

    def get_context_data(self, **kwargs):

        context = super(DeleteView, self).get_context_data(**kwargs)

        data = {"url": reverse("%s_delete_%s" % (context['object'].app_label,
                                                 context['object'].ct_name),
                               kwargs={'pk': context['object'].id})}

        context.update(data)

        return context

    def get(self, request, *args, **kwargs):

        """ Make sure that the confirm delete is sent as text/plain """

        self.object = self.get_object()
        context = self.get_context_data(object=self.object, **kwargs)
        return self.render_to_response(context, mimetype="text/plain")
