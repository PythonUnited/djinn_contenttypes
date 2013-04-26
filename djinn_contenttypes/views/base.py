from django.http import QueryDict
from django.views.generic.detail import DetailView as BaseDetailView
from django.views.generic.edit import UpdateView as BaseUpdateView
from django.views.generic.edit import DeleteView as BaseDeleteView
from django.views.generic.edit import CreateView as BaseCreateView
from django.http import HttpResponseRedirect
from django.db import models
from django.core.urlresolvers import reverse
from pgutils.exception_handlers import Http403
from pgcontent.registry import CTRegistry


VIEW = 'contenttypes.view'
EDIT = 'contenttypes.change_contenttype'


class DetailView(BaseDetailView):

    """ Detail view for simple content, not related, etc. All intranet
    views should extend this view.
    """

    def get_template_names(self):

        if self.request.GET.get("modal", False):
            ["%s/snippets/%s_modal_detail.html" % (self.model.__module__.split(".")[0],
                                             self.model.__name__.lower())]
        else:
            return ["%s/%s_detail.html" % (self.model.__module__.split(".")[0],
                                           self.model.__name__.lower())]

    def get_object(self, queryset=None):

        obj = super(DetailView, self).get_object(queryset=queryset)

        info = CTRegistry.get(obj.ct_name)

        if not self.request.user.has_perm(info.get("view_permission", VIEW), 
                                          obj=obj):
            raise Http403()

        return obj
    
    def get_context_data(self, **kwargs):

        """ Always add self as "view" so as to be able to call methods
        and properties on view """

        ctx = super(DetailView, self).get_context_data(**kwargs)

        ctx.update({"view": self})

        return ctx    


class CreateView(BaseCreateView):

    def get_form_kwargs(self):

        """ Allow for missing input values for owner, ... """

        kwargs = super(CreateView, self).get_form_kwargs()

        if self.request.method == "POST":

            del kwargs['data']

            data = QueryDict("", mutable=True)

            for key in self.request.POST.keys():
                data[key] = self.request.POST[key]

            if not data.has_key("owner"):
                data["owner"] = "userprofile:%s" % self.request.user.id

            data['changed_by'] = data["creator"] = self.request.user.id

            kwargs.update({"data": data})

        return kwargs

    def get_template_names(self):

        return ["%s/%s_edit.html" % (self.model.__module__.split(".")[0],
                                       self.model.__name__.lower())]

class UpdateView(BaseUpdateView):

    def get_initial(self):
        
        initial = super(CreateView, self).get_initial()

        initial.update({"changed_by": self.request.user})        

        return initial

    def get_template_names(self):

        return ["%s/%s_edit.html" % (self.model.__module__.split(".")[0],
                                       self.model.__name__.lower()),
                "%s_edit.html" % self.object.ct_name]

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

        if self.request.POST.get('action', None) == "Afbreken" or \
                self.request.POST.get('action', None) == "Annuleren":
            
            if self.object.is_initiated:
                self.object.delete()
                
                url = self.request.user.profile.get_absolute_url()
                return HttpResponseRedirect(url)
            else:
                return HttpResponseRedirect(self.object.get_absolute_url())
        else:

            form_class = self.get_form_class()
            form = self.get_form(form_class)

            created = self.object.is_initiated

            if form.is_valid():
                self.object.is_initiated = False
                self.form_valid(form)
                self.post_save(form, created=created)
                
                return HttpResponseRedirect(self.get_success_url())
            else:
                return self.form_invalid(form)

    def form_valid(self, form):

        form.instance.changed_by=self.request.user

        self.object = form.save(commit=True)
        

class DeleteView(BaseDeleteView):

    template_name = "djinn_contenttypes/snippets/delete.html"

    def delete(self, request, *args, **kwargs):

        self.object = self.get_object()

        try:
            self.object.delete()
        
            return HttpResponseRedirect(self.get_success_url())        
        except:
            context = super(BaseDeleteView, self).get_context_data(**kwargs)
            context['message'] = "Het verwijderen is mislukt."
            context['object'] = self.object

            # TODO: return to detail view
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
