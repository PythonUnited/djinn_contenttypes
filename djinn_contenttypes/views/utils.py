import logging
from importlib import import_module
from django.db import models
from django.db.models import get_model
from django.conf.urls import url, patterns
from django.conf import settings
from djinn_core.utils import extends
from djinn_contenttypes.models.base import FKContentMixin
from base import DetailView, CreateView, UpdateView, DeleteView


LOGGER = logging.getLogger("djinn_contenttypes")


def generate_model_urls(*models, **kwargs):

    """ Generate the urls for a view, given the conventions used by
    Djinn.  To be able to find specific views and forms, these need to
    be imported.  Best do this in urls.py where you'll most likely
    call this function to generate your urls.  You may provide 'name'
    in kwargs, to override the naming convention for view names
    <modulename>_<mode>_<model>. This is handy for dynamic models, for
    instance djinn_profiles.UserProfile. Provide name as a tuple of
    (<module prefix>, <model>), i.e. name=("djinn_profiles", "userprofile")
    """

    views = []
    name = kwargs.get("name", None)

    for model in models:

        modelname = model.__name__.lower()
        modulename = model.__module__.split(".")[0]

        if kwargs.get("view", True):
            if name:
                viewname = "%s_view_%s" % name
            else:
                viewname = None
            views.append(generate_view_url(model, modelname, modulename,
                                           name=viewname))
        if kwargs.get("edit", True):
            if name:
                editname = "%s_edit_%s" % name
            else:
                editname = None
            views.append(generate_edit_url(model, modelname, modulename,
                                           name=editname))
        if kwargs.get("add", True):
            if name:
                addname = "%s_add_%s" % name
            else:
                addname = None
            views.append(generate_add_url(model, modelname, modulename,
                                          name=addname))
        if kwargs.get("delete", True):
            if name:
                delname = "%s_delete_%s" % name
            else:
                delname = None
            views.append(generate_delete_url(model, modelname, modulename,
                                             name=delname))

    return patterns("", *views)


def generate_view_url(model, modelname, modulename, name=None):

    if model._meta.swapped:
        real_model = get_model(*model._meta.swapped.split("."))
    else:
        real_model = model

    if hasattr(real_model, "slug"):
        expr = r"^%s/(?P<pk>[\d]+)/(?P<slug>[^\/]+)/?$" % modelname
    else:
        expr = r"^%s/(?P<pk>[\d]+)/?$" % modelname

    name = name or "%s_view_%s" % (modulename, modelname)
    view = find_view(model, modulename)

    return url(expr, view, name=name)


def generate_delete_url(model, modelname, modulename, name=None):

    expr = r"^delete/%s/(?P<pk>[\d]+)/?$" % modelname
    name = name or "%s_delete_%s" % (modulename, modelname)
    view = find_view(model, modulename, suffix="DeleteView",
                     default=DeleteView)

    return url(expr, view, name=name)


def generate_add_url(model, modelname, modulename, name=None):

    expr = r"^add/%s/?$" % modelname
    name = name or "%s_add_%s" % (modulename, modelname)
    form_class = find_form_class(model, modulename)

    kwargs = {}

    if form_class:
        kwargs["form_class"] = form_class

    if extends(model, FKContentMixin):

        kwargs['fk_fields'] = [f.name for f in model._meta.fields if
                               isinstance(f, models.ForeignKey)]
        expr = r"^add/%s" % modelname

        for fk_field in kwargs['fk_fields']:
            expr += "/(?P<%s>.+)" % fk_field
        expr += "/?$"

    view = find_view(model, modulename, suffix="CreateView",
                     default=CreateView,
                     **kwargs)

    return url(expr, view, name=name)


def generate_edit_url(model, modelname, modulename, name=None):

    """ Generate edit URL. Override name by providing it in the
    keyword arguments """

    expr = r"^edit/%s/(?P<pk>[\d]+)/?$" % modelname
    name = name or "%s_edit_%s" % (modulename, modelname)
    form_class = find_form_class(model, modulename)

    kwargs = {}

    if form_class:
        kwargs["form_class"] = form_class

    view = find_view(model, modulename, suffix="UpdateView",
                     default=UpdateView,
                     **kwargs)

    return url(expr, view, name=name)


def find_view(model, modulename, suffix="View", default=DetailView, **kwargs):

    """ Try to find the view for the model. This checks the views.py
    of the model's module, and also views.<modelname>.py """

    viewclassname = "%s%s" % (model.__name__, suffix)
    modelname = model.__name__.lower()
    view_class = module = None

    if model._meta.swapped:
        modulename, modelname = model._meta.swapped.lower().split(".")

    try:
        module = import_module("%s.views.%s" % (modulename, modelname))
    except ImportError:
        try:
            module = import_module("%s.views" % modulename)
        except ImportError:
            LOGGER.info("No views module found for %s" % modulename)

    if module:
        try:
            view_class = getattr(module, viewclassname)
        except AttributeError:
            LOGGER.info("No view found for %s" % modelname)

    if not view_class:
        view_class = default
        kwargs.update({"model": model})

    return view_class.as_view(**kwargs)


def find_form_class(model, modulename):

    """ Try to find form class either in forms.py or in a separate file
    within forms named after the lower case model class. """

    formclassname = "%sForm" % model.__name__
    modelname = model.__name__.lower()
    form_class = module = None
    setting_attr = "%s_%s_FORM" % (modulename.upper(), modelname.upper())

    if getattr(settings, setting_attr, None):

        parts = getattr(settings, setting_attr).split(".")

        module = import_module(".".join(parts[:-1]))
        form_class = getattr(module, parts[-1])

        return form_class

    if model._meta.swapped:
        modulename, modelname = model._meta.swapped.split(".")
        modelname = modelname.lower()

    try:
        module = import_module("%s.forms.%s" % (modulename, modelname))
    except ImportError:
        try:
            module = import_module("%s.forms" % modulename)
        except ImportError:
            LOGGER.info("No forms module found for %s" % modulename)

    if module:
        try:
            form_class = getattr(module, formclassname)
        except AttributeError:
            LOGGER.info("No form found for %s" % modelname)

    return form_class
