from django.core.cache import cache
from django.views.generic.detail import DetailView as BaseDetailView
from django.views.generic.edit import UpdateView as BaseUpdateView
from django.views.generic.edit import DeleteView as BaseDeleteView
from django.views.generic.edit import CreateView as BaseCreateView
from django.views.generic.base import TemplateResponseMixin
from django.http import HttpResponseRedirect, HttpResponse, \
    HttpResponseForbidden
from django.apps import apps
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
import json

from djinn_contenttypes.settings import WYSIWYG_SIZE_NAMES, \
    IMAGESIZES_CHECKING_INTERVAL_SECS
from djinn_core.utils import implements
from djinn_contenttypes.registry import CTRegistry
from djinn_contenttypes.utils import (
    get_object_by_ctype_id, has_permission, check_get_url)
from djinn_contenttypes.models.base import BaseContent, LocalRoleMixin
from djinn_contenttypes.utils import json_serializer
from djinn_workflow.utils import get_state
from pgauth.models import UserGroup
from django.core.exceptions import ImproperlyConfigured
from djinn_search.utils import update_index_for_instance


def forbidden_page(request):

    return '<html>No permission for %s</html>' % request.path


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
    def allow_saveandedit(self):
        return CTRegistry.get(self.ct_name).get("allow_saveandedit", False) \
               and self.request.user.has_perm('auth.manage_feeds')

    @property
    def view_url(self):

        if not self.object:
            return "/"

        if self.allow_saveandedit and \
                self.request_data.get('action', None) == 'saveandedit':
            return self.edit_url

        kwargs = {"pk": self.object.id}

        if hasattr(self.object, "slug"):
            kwargs.update({"slug": self.object.slug})

        return reverse('%s_view_%s' % (self.app_label, self.ct_name),
                       kwargs=kwargs)


class MimeTypeMixin(object):

    """ Mixin class to set mimetype. Make sure this is the first class in the
    line of extended classes that do render_to_response... """

    content_type = "text/html"
    mimetype = "text/html"

    def render_to_response(self, context, **response_kwargs):

        """ Override so as to add mimetype """

        #MJB mimetype was removed in django 1.7:
        # response_kwargs['mimetype'] = self.mimetype
        response_kwargs['content_type'] = self.content_type

        return super(MimeTypeMixin, self).render_to_response(
            context, **response_kwargs)


class CTMixin(object):

    """ Detailview that applies to any content, determined by the url parts """

    def get_object(self, queryset=None):

        """ Retrieve context from URL parts app, ctype and id."""

        return get_object_by_ctype_id(
            self.kwargs['ctype'],
            self.kwargs.get('id', self.kwargs.get('pk', None)))


class RequestDataMixin(object):

    """ get data from request.GET or request.POST """

    @property
    def request_data(self):

        if self.request.method in ['POST', 'PUT']:
            return self.request.POST

        return self.request.GET



class SwappableMixin(object):

    """ Allow for swapped models. This is an undocumented feature of
    the meta class for now, that enables user defined overrides for
    models (i.e. contrib.auth.User)"""

    @property
    def real_model(self):

        if not hasattr(self.model._meta, 'swapped') or \
                not self.model._meta.swapped:
            return self.model
        else:
            module, model = self.model._meta.swapped.split(".")
            return apps.get_model(module, model)

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

        # for url in []: # self.request.session.get('history', []):
        # MJB even kijken hoe dit bevalt...
        for url in self.request.session.get('history', []):

            # if self.request.path != url:
            #     absolute_url = self.request.build_absolute_uri(url)
            #     # history url testing ONLY agains local server
            #     # absolute_url = "http://%s%s" % (settings.HTTP_HOST, url)
            #     # absolute_url = iri_to_uri(absolute_url)
            #     cookies = self.request.COOKIES
            #
            #     # DEZE BLOKKEERT. PAK DE EERSTE MAAR
            #     try:
            #         statuscode = check_get_url(absolute_url,
            #                                    cookies=cookies, **{"timeout": 2.0})
            #
            #         if statuscode == 200:
            #             success_url = url
            #             break
            #     except Exception as exc:
            #         # may be timeout or invalid request.
            #         # try the next one
            #         pass
            if isinstance(self, DeleteView):
                if f"/{self.kwargs[self.pk_url_kwarg]}/" in url:
                    continue

            if self.request.path != url:
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
                not self.request.GET.get("modal", False):
            templates = ["%s/snippets/%s.html" %
                         (self.app_label, self.ct_name)] \
                + templates

        return templates

    @property
    def state(self):

        return get_state(self.object)

    @property
    def created(self):

        return (hasattr(self.object, 'publish_from') and
                self.object.publish_from) or self.object.created

    def get(self, request, *args, **kwargs):

        """ We need our own implementation of GET, to be able to do permission
        checks on the object """

        self.object = self.get_object()

        perm = CTRegistry.get(self.ct_name).get("view_permission",
                                                'contenttypes.view')

        if not has_permission(perm, self.request.user, self.object):
            return HttpResponseForbidden(forbidden_page(request))

        context = self.get_context_data(object=self.object)
        content_type = self._determine_content_type()

        if content_type == "text/html":
            self.add_to_history()

        if hasattr(self.object, 'images'):
            '''
            20191121
            This section takes care of re-generating images at sizes that 
            are used in the intranet's wysiwygs. Since the URLS are stored in 
            the wysiwyg content, the images-library does not see them missing 
            from the images cache folder.
            So, we periodically check them here, as users try to access them.
            But not too often, since checking results in a number of queries 
            and filesystem checks. 
            '''

            img_cache_key = "imgsizes_checked_%s_%d" % (
                self.ct_name, self.object.id)
            if not cache.get(img_cache_key):
                # If the key is not in the cache, it is time to check the
                # images (again)
                # print("checking image sizes...")
                for photologue_image in self.object.images.all():
                    # check if image cache is up to date
                    # This proved to be a problem with image_urls stored hard in
                    # wysiwyg content.
                    for sizename in WYSIWYG_SIZE_NAMES:
                        # this will try to get the url from cache.
                        # if the cached file doesn't exist anymore, it is created again
                        the_url = photologue_image._get_SIZE_url(sizename)
                        # print(the_url)
                # After the check/regenerate, show other users check has been
                # done recently.
                cache.set(img_cache_key, 'no need to check now',
                          IMAGESIZES_CHECKING_INTERVAL_SECS)
            # else:
            #     print("no need to check")

        return self.render_to_response(context, content_type=content_type)


class CTDetailView(CTMixin, DetailView):

    """Detailview that applies to any content, determined by the url
    parts. This means that the model is really variable! """

    @property
    def model(self):

        return self.get_object().__class__


class CreateView(TemplateResolverMixin, SwappableMixin, AcceptMixin,
                 RequestDataMixin, BaseCreateView, HistoryMixin):

    mode = "add"
    fk_fields = []

    def get_form_class(self):

        # if self.__class__ == CreateView:
        #     self.fields = '__all__'
        return super(CreateView, self).get_form_class()

    def get_initial(self):

        initial = {}

        for fld in self.request_data.keys():
            initial[fld] = self.request_data[fld]

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
            if self.request_data.get("tmp_id"):
                obj = self.real_model.objects.get(
                    id=self.request_data.get("tmp_id"))
            else:
                obj = self.real_model.objects.create(
                    creator=self.request.user,
                    is_tmp=True,
                    changed_by=self.request.user
                    )

                # Set any data that is available, i.e. through initial data
                #
                initial_data = self.get_initial()
                if initial_data:
                    form_class = self.get_form_class()

                    kwargs = self.get_form_kwargs()
                    kwargs['data'] = initial_data
                    kwargs['instance'] = obj

                    form = form_class(**kwargs)
                    form.cleaned_data = {}

                    for field in initial_data.keys():
                        if field in form.data and field in form.fields:
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
            return HttpResponseForbidden(forbidden_page(request))

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
            return HttpResponseForbidden(forbidden_page(request))

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
            if self.request.POST.get('action', 'create') == 'saveandedit':
                self.object.is_tmp = True
            else:
                self.object.is_tmp = False
        except:
            pass

        if 'owner' in form.cleaned_data.keys():
            # Het opslaan van owner in de form-save komt te laat voor het
            # versturen van de timeline berichten.
            # Dus de owner-aanpassing moet daarvoor al gedaan worden
            new_owner = form.cleaned_data['owner']
            if implements(self.object, BaseContent) and new_owner and\
                    new_owner != self.object.get_owner():
                self.object.set_owner(new_owner.user)

        self.object = form.save()

        # owner nog steeds leeg, dan maar dit:
        if not self.object.get_owner() and \
                implements(self.object, BaseContent):
            self.object.set_owner(self.request.user)

        update_index_for_instance(self.object)

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
                 RequestDataMixin, BaseUpdateView, HistoryMixin):

    mode = "edit"

    def get_success_url(self):

        return self.view_url

    @property
    def partial(self):

        """ Allow partial update """

        return self.request.POST.get('partial', False) or \
               self.request.GET.get('partial', False)

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
            return HttpResponseForbidden(forbidden_page(request))

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
            return HttpResponseForbidden(forbidden_page(request))

        if self.request.POST.get('action', None) == "cancel":

            return self.handle_cancel()
        else:
            return super(UpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):

        if implements(self.object, LocalRoleMixin):
            orig_owner = form.instance.get_owner()

        if hasattr(form, "update") and self.partial:
            self.object = form.update()
        else:
            self.object = form.save()

        if implements(self.object, BaseContent):
            self.object.changed_by = self.request.user

        if implements(self.object, LocalRoleMixin) and \
                        'owner' in form.changed_data and \
                        form.cleaned_data['owner'] and \
                        orig_owner != form.cleaned_data['owner']:
            self.object.set_owner(form.cleaned_data['owner'].user)

        try:
            if self.request.POST.get('action', 'save') == 'saveandedit':
                self.object.is_tmp = True
            else:
                self.object.is_tmp = False
        except:
            pass

        self.object.save()

        if self.request.POST.get('action', 'save') == 'saveandedit':
            return self.render_to_response(self.get_context_data(form=form),
                                           status=202)

        if not self.partial:
            # Translators: edit form status message
            messages.success(self.request, _("Saved changes"))

        # call once after all save's
        update_index_for_instance(self.object)

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form),
                                       status=202)

    def handle_cancel(self):

        if self.object and getattr(self.object, "is_tmp", False):
            # MJB 20200114
            # We used to delete on cancel, but now let the nightly
            # pg_purge_empty_content job do this
            # self.object.delete()
            pass

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
            return HttpResponseForbidden(forbidden_page(request))

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


class FeedViewMixin(object):

    def get_queryset(self, queryset):

        if self.kwargs.get('for_rssfeed', False):

            return queryset.filter(publish_for_feed=True)

        return queryset

    @property
    def for_rssfeed(self):
        return self.kwargs.get('for_rssfeed', False)


class DesignVersionMixin(object):
    """
    Allows a view to switch between the old and the new template
    (new: template_path starting with 'gronet_v3')

    NOTE: In case of new templates, Diazo is fully bypassed!

    add parameter to URL:
    ?olddesign=1
    """

    def get_template_names(self):

        if self.template_name:
            if 'olddesign' in self.request.GET:
                return self.template_name.replace("gronet_v3/", "")

            template_name_tmp = self.template_name
            if 'tprefix' in self.request.GET and not template_name_tmp.startswith('gronet_'):
                template_name_tmp = f"gronet_{self.request.GET['tprefix']}/{template_name_tmp}"

            if 'tpostfix' in self.request.GET:
                template_name_tmp = template_name_tmp.replace(".html", f"_{self.request.GET['tpostfix']}.html")

            return template_name_tmp

        return super().get_template_names()


    def dispatch(self, request, *args, **kwargs):

        response = super().dispatch(request, *args, **kwargs)

        if 'olddesign' not in self.request.GET:
            # disallow Diazo to modify anything.
            # So, not even touch the outgoing html doctype, xmlns, etcetera
            response['X-Diazo-Off'] = 'true'

        return response