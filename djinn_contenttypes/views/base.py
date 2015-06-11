from urlparse import urlparse
from django.views.generic.detail import DetailView as BaseDetailView
from django.views.generic.edit import UpdateView as BaseUpdateView
from django.views.generic.edit import DeleteView as BaseDeleteView
from django.views.generic.edit import CreateView as BaseCreateView
from django.views.generic.base import TemplateResponseMixin
from django.http import HttpResponseRedirect, HttpResponse, \
    HttpResponseForbidden
from django.db.models import get_model
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson as json
from djinn_core.utils import implements
from djinn_contenttypes.registry import CTRegistry
from djinn_contenttypes.utils import (
    get_object_by_ctype_id, has_permission, check_get_url)
from djinn_contenttypes.models.base import BaseContent
from djinn_contenttypes.utils import json_serializer
from djinn_workflow.utils import get_state
from pgauth.models import UserGroup
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import iri_to_uri
from django.conf import settings


class TemplateResolverMixin(object):

    @property
    def app_label(self):
        return self.model.__module__.split(".")[0]

    @property
    def ct_name(self):
        return self.model.__name__.lower()

    @property
    def ct_label(self):

        return _(self.model.__name__)

    def get_template_names(self):

        if self.template_name:
            return [self.template_name]

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

        return reverse("%s_add_%s" % (self.app_label, self.ct_name),
                       kwargs=self.kwargs)

    @property
    def edit_url(self):

        return reverse("%s_edit_%s" % (self.app_label, self.ct_name),
                       kwargs={'pk': self.object.id})

    @property
    def view_url(self):

        kwargs = {"pk": self.object.id}

        if hasattr(self.object, "slug"):
            kwargs.update({"slug": self.object.slug})

        return reverse('%s_view_%s' % (self.app_label, self.ct_name),
                       kwargs=kwargs)


class MimeTypeMixin(object):

    """ Mixin class to set mimetype. Make sure this is the first class in the
    line of extended classes that do render_to_response... """

    mimetype = "text/html"

    def render_to_response(self, context, **response_kwargs):

        """ Override so as to add mimetype """

        response_kwargs['mimetype'] = self.mimetype
        response_kwargs['content_type'] = self.mimetype

        return super(MimeTypeMixin, self).render_to_response(
            context, **response_kwargs)


class CTMixin(object):

    """ Detailview that applies to any content, determined by the url parts """

    def get_object(self, queryset=None):

        """ Retrieve context from URL parts app, ctype and id."""

        return get_object_by_ctype_id(
            self.kwargs['ctype'],
            self.kwargs.get('id', self.kwargs.get('pk', None)))


class SwappableMixin(object):

    """ Allow for swapped models. This is an undocumented feature of
    the meta class for now, that enables user defined overrides for
    models (i.e. contrib.auth.User)"""

    @property
    def real_model(self):

        if not self.model._meta.swapped:
            return self.model
        else:
            module, model = self.model._meta.swapped.split(".")
            return get_model(module, model)

    def get_queryset(self):

        """ Override default get_queryset to allow for swappable models """

        if self.queryset is None:
            if self.model:
                return self.real_model._default_manager.all()
            else:
                raise ImproperlyConfigured(
                    "%(cls)s is missing a queryset. Define "
                    "%(cls)s.model, %(cls)s.queryset, or override "
                    "%(cls)s.get_queryset()." % {
                        'cls': self.__class__.__name__
                    })
        return self.queryset._clone()


class AcceptMixin(object):

    """ Use the accept header to determine the response. Supported are
    text/html, text/plain and application/json. Mixin class should come as
    first extended class... """

    @property
    def is_json(self):

        return "application/json" in self.request.META.get("HTTP_ACCEPT", [])

    @property
    def is_text(self):

        return "text/plain" in self.request.META.get("HTTP_ACCEPT", [])

    def render_to_response(self, context, **response_kwargs):

        if self.is_json:

            try:
                del response_kwargs['mimetype']
            except:
                pass

            response_kwargs["content_type"] = 'application/json'

            return HttpResponse(
                json.dumps(context, skipkeys=True,
                           default=json_serializer),
                **response_kwargs)
        elif self.is_text:
            try:
                del response_kwargs['mimetype']
            except:
                pass

            response_kwargs["content_type"] = 'text/plain'
            return TemplateResponseMixin.render_to_response(self,
                                                            context,
                                                            **response_kwargs)
        else:
            return TemplateResponseMixin.render_to_response(self,
                                                            context,
                                                            **response_kwargs)


class AbstractBaseView(TemplateResolverMixin, SwappableMixin, AcceptMixin):

    def _determine_content_type(self, default="text/html"):

        content_type = default

        if self.request.is_ajax():
            content_type = "text/plain"

        if "application/json" in self.request.META.get("HTTP_ACCEPT", []):
            content_type = "application_json"

        return content_type


class HistoryMixin(object):

    def add_to_history(self, request=None):

        """ Check on session history, and add path if need be """

        if not request:
            request = self.request

        if 'history' not in request.session:
            request.session['history'] = []

        if len(request.session['history']) > 10:
            request.session['history'].pop()

        path = request.path

        if request.META.get('QUERY_STRING'):
            path = "%s?%s" % (path, request.META['QUERY_STRING'])

        request.session['history'].insert(0, path)
        request.session.modified = True

    def get_redir_url(self):

        """ Get last valid url """

        success_url = None

        for url in []: # self.request.session.get('history', []):

            absolute_url = self.request.build_absolute_uri(url)
            # history url testing ONLY agains local server
            # absolute_url = "http://%s%s" % (settings.HTTP_HOST, url)
            # absolute_url = iri_to_uri(absolute_url)
            cookies = self.request.COOKIES

            # if absolute_url == url:
            #    parsed = urlparse(absolute_url)
            #    if parsed.hostname == self.request.

            if check_get_url(absolute_url, cookies=cookies) == 200:

                success_url = url
                break

        if not success_url:
            success_url = self.request.user.profile.get_absolute_url()

        return success_url


class DetailView(AbstractBaseView, BaseDetailView, HistoryMixin):

    """ Detail view for simple content, not related, etc. All intranet
    detail views should extend this view.
    """

    mode = "detail"

    def get_template_names(self):

        """ If the request is Ajax, and no one asked for a modal view,
        assume that we need to return a record like view"""

        if self.template_name:
            return [self.template_name]

        templates = super(DetailView, self).get_template_names()

        if self.request.is_ajax() and \
                not self.request.REQUEST.get("modal", False):
            templates = ["%s/snippets/%s.html" %
                         (self.app_label, self.ct_name)] \
                + templates

        return templates

    @property
    def state(self):

        return get_state(self.object)

    @property
    def created(self):

        return self.object.publish_from or self.object.created

    def get(self, request, *args, **kwargs):

        """ We need our own implementation of GET, to be able to do permission
        checks on the object """

        self.object = self.get_object()

        perm = CTRegistry.get(self.ct_name).get("view_permission",
                                                'contenttypes.view')

        if not has_permission(perm, self.request.user, self.object):
            return HttpResponseForbidden()

        context = self.get_context_data(object=self.object)
        content_type = self._determine_content_type()

        if content_type == "text/html":
            self.add_to_history()

        return self.render_to_response(context, content_type=content_type)


class CTDetailView(CTMixin, DetailView):

    """Detailview that applies to any content, determined by the url
    parts. This means that the model is really variable! """

    @property
    def model(self):

        return self.get_object().__class__


class CreateView(TemplateResolverMixin, SwappableMixin, AcceptMixin,
                 BaseCreateView, HistoryMixin):

    mode = "add"
    fk_fields = []

    def get_initial(self):

        initial = {}

        for fld in self.request.GET.keys():
            initial[fld] = self.request.GET[fld]

        for fld in self.fk_fields:
            initial[fld] = self.kwargs[fld]

        return initial

    def get_form_kwargs(self):

        """ Add user to kwargs for form. """

        kwargs = super(CreateView, self).get_form_kwargs()

        if getattr(self.form_class, "user_support", False):
            kwargs['user'] = self.request.user

        return kwargs

    def get_success_url(self):

        return self.view_url

    def get_object(self, queryset=None):

        if not getattr(self.real_model, "create_tmp_object", False):
            return None
        else:
            if self.request.REQUEST.get("tmp_id"):
                obj = self.real_model.objects.get(
                    id=self.request.REQUEST.get("tmp_id"))
            else:
                obj = self.real_model.objects.create(
                    creator=self.request.user,
                    is_tmp=True,
                    changed_by=self.request.user
                    )

                # Set any data that is available, i.e. through initial data
                #
                if self.get_initial():
                    form_class = self.get_form_class()

                    kwargs = self.get_form_kwargs()
                    kwargs['data'] = self.get_initial()

                    form = form_class(**kwargs)
                    form.cleaned_data = {}

                    for field in self.get_initial().keys():
                        value = form.fields[field].clean(form.data[field])
                        setattr(obj, field, value)

            obj.save()

            return obj

    def get(self, request, *args, **kwargs):

        """ Override get so as to be able to check permissions """

        # Set object. If not set, odd behaviour of the django generic
        # view classes may occur...
        self.object = None

        # TODO: this should be the more specific permission
        perm = CTRegistry.get(self.ct_name).get("add_permission",
                                                'contenttypes.add_contenttype')

        # TODO: check if this still exists...
        ugid = kwargs.get('parentusergroup', None)

        if ugid:
            context = UserGroup.objects.get(id=int(ugid)).profile
        else:
            context = None

        if not self.request.user.has_perm(perm, obj=context):
            return HttpResponseForbidden()

        self.object = self.get_object()

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):

        # Set object. If not set, odd behaviour of the django generic
        # view classes may occur...
        self.object = None

        perm = CTRegistry.get(self.ct_name).get("add_permission",
                                                'contenttypes.add_contenttype')

        pugid = kwargs.get('parentusergroup', None)

        if pugid:
            theobj = UserGroup.objects.get(id=int(pugid)).profile
        else:
            theobj = None
        if not self.request.user.has_perm(perm, obj=theobj):
            return HttpResponseForbidden()

        self.object = self.get_object()

        if self.request.POST.get('action', None) == "cancel":

            return self.handle_cancel()
        else:
            form_class = self.get_form_class()
            form = self.get_form(form_class)

            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

    def form_valid(self, form):

        """ If the form is valid, first let the form.save create the
        object. We can't commit straight away, since essential data for
        the content type is not in the form (creator, changed_by).
        Set those, then commit. """

        self.object = form.save(commit=False)

        # Assume, but not overly, that this is BaseContent...
        #
        try:
            self.object.creator = self.request.user
            self.object.changed_by = self.request.user
            self.object.is_tmp = False
        except:
            pass

        # And now for real!
        #
        self.object = form.save()

        if implements(self.object, BaseContent):
            self.object.set_owner(self.request.user)

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form),
                                       status=202)

    def handle_cancel(self):

        """Default action upon cancel of edit. If we have an object, and it is
        temporary, delete. Go to last successfull url.
        """

        if self.object and getattr(self.object, "is_tmp", False):
            self.object.delete()

        return HttpResponseRedirect(self.get_redir_url())


class UpdateView(TemplateResolverMixin, SwappableMixin, AcceptMixin,
                 BaseUpdateView, HistoryMixin):

    mode = "edit"

    def get_success_url(self):

        return self.view_url

    @property
    def partial(self):

        """ Allow partial update """

        return self.request.REQUEST.get('partial', False)

    def get_form_kwargs(self):

        kwargs = super(UpdateView, self).get_form_kwargs()

        if getattr(self.form_class, "partial_support", False):
            kwargs['partial'] = self.partial

        if getattr(self.form_class, "user_support", False):
            kwargs['user'] = self.request.user

        return kwargs

    def get_initial(self):

        initial = {}

        for fld in self.request.GET.keys():
            initial[fld] = self.request.GET[fld]

        return initial

    def get(self, request, *args, **kwargs):

        """ Check permissions for editing """

        self.object = self.get_object()

        perm = CTRegistry.get(self.ct_name).get(
            "edit_permission",
            'contenttypes.change_contenttype')

        if not has_permission(perm, self.request.user, self.object):
            return HttpResponseForbidden()

        return super(UpdateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        """ Check whether the user wants to cancel the whole
        operation. If so, we need to check whether is was an edit, or
        initial object. If the latter is the case, delete the 'tmp'
        object."""

        self.object = self.get_object()

        perm = CTRegistry.get(self.ct_name).get(
            "edit_permission",
            'contenttypes.change_contenttype')

        if not has_permission(perm, self.request.user, self.object):
            return HttpResponseForbidden()

        if self.request.POST.get('action', None) == "cancel":

            return self.handle_cancel()
        else:
            return super(UpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):

        if hasattr(form, "update") and self.partial:
            self.object = form.update()
        else:
            self.object = form.save()

        if implements(self.object, BaseContent):
            self.object.changed_by = self.request.user

        try:
            self.object.is_tmp = False
        except:
            pass

        self.object.save()

        if not self.partial:
            # Translators: edit form status message
            messages.success(self.request, _("Saved changes"))

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form),
                                       status=202)

    def handle_cancel(self):

        if self.object and getattr(self.object, "is_tmp", False):
            self.object.delete()

        return HttpResponseRedirect(self.get_redir_url())


class DeleteView(TemplateResolverMixin, SwappableMixin, AcceptMixin,
                 BaseDeleteView, HistoryMixin):

    mode = "delete"

    def delete(self, request, *args, **kwargs):

        self.object = self.get_object()

        perm = CTRegistry.get(self.ct_name).get(
            "delete_permission",
            'contenttypes.delete_contenttype')

        if not has_permission(perm, self.request.user, self.object):
            return HttpResponseForbidden()

        deleted = False

        try:
            # enable signal handlers to access last change info
            #
            if implements(self.object, BaseContent):
                self.object.changed_by = self.request.user

            self.object.delete()

            deleted = True
        except Exception:
            pass

        if deleted:
            if self.is_json:
                return HttpResponse(json.dumps({'message': 'bye bye'}),
                                    content_type='application/json')
            elif self.is_text:
                return HttpResponse("Bye bye", content_type='text/plain')
            else:
                return HttpResponseRedirect(self.get_success_url())
        else:
            if self.is_json:
                return HttpResponse(json.dumps({'message': 'error'}),
                                    status=202,
                                    content_type='application/json')
            elif self.is_text:
                return HttpResponse("Error", status=202,
                                    content_type='text/plain', )
            else:
                return HttpResponseRedirect(self.view_url)

    def get_success_url(self):

        """ On delete, the user should be brought back to the last valid url,
        or home... """

        return self.get_redir_url()

    def get(self, request, *args, **kwargs):

        """ Make sure that the confirm delete is sent as text/plain, given that
        it is shown as a modal. """

        self.object = self.get_object()
        context = self.get_context_data(object=self.object, **kwargs)

        self.request.META["HTTP_ACCEPT"] = "text/plain"

        return self.render_to_response(context)
