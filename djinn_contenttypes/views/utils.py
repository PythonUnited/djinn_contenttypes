import sys
from django.db import models 
from django.conf.urls.defaults import url, patterns
from djinn_core.utils import extends
from djinn_contenttypes.models.base import FKContentMixin
from base import DetailView, CreateView, UpdateView, DeleteView


def generate_model_urls(*models, **kwargs):

    """ Generate the urls for a view, given the conventions used by
    Djinn.  To be able to find specific views and forms, these need to
    be imported.  Best do this in urls.py where you'll most likely
    call this function to generate your urls.
    """

    views = []

    for model in models:
        modelname = model.__name__.lower()
        modulename = model.__module__.split(".")[0]

        if kwargs.get("view", True):
            views.append(generate_view_url(model, modelname, modulename))
        if kwargs.get("edit", True):
            views.append(generate_edit_url(model, modelname, modulename))
        if kwargs.get("add", True):
            views.append(generate_add_url(model, modelname, modulename))
        if kwargs.get("delete", True):
            views.append(generate_delete_url(model, modelname, modulename))

    return patterns("", *views)


def generate_view_url(model, modelname, modulename):

    if hasattr(model, "slug"):
        expr = r"^%s/(?P<pk>[\d]+)/(?P<slug>[^\/]+)/?$" % modelname
    else:
        expr = r"^%s/(?P<pk>[\d]+)/?$" % modelname

    name = "%s_view_%s" % (modulename, modelname)
    view = find_view(model, modulename)

    return url(expr, view, name=name)


def generate_delete_url(model, modelname, modulename):

    expr = r"^delete/%s/(?P<pk>[\d]+)/?$" % modelname
    name = "%s_delete_%s" % (modulename, modelname)
    view = find_view(model, modulename, suffix="DeleteView", default=DeleteView)

    return url(expr, view, name=name)


def generate_add_url(model, modelname, modulename):

    expr = r"^add/%s/?$" % modelname
    name = "%s_add_%s" % (modulename, modelname)
    form_class = find_form_class(model, modulename)

    kwargs = {}

    if form_class:
        kwargs["form_class"] = form_class

    if extends(model, FKContentMixin):

        kwargs['fk_fields'] = [f.name for f in model._meta.fields if \
                                   isinstance(f, models.ForeignKey)]
        expr = r"^add/%s" % modelname

        for fk_field in kwargs['fk_fields']:
            expr += "/(?P<%s>.+)" % fk_field
        expr += "/?$"

    view = find_view(model, modulename, suffix="CreateView", default=CreateView,
                     **kwargs)

    return url(expr, view, name=name)


def generate_edit_url(model, modelname, modulename):

    expr = r"^edit/%s/(?P<pk>[\d]+)/?$" % modelname
    name = "%s_edit_%s" % (modulename, modelname)
    form_class = find_form_class(model, modulename)

    kwargs = {}

    if form_class:
        kwargs["form_class"] = form_class

    view = find_view(model, modulename, suffix="UpdateView", default=UpdateView,
                     **kwargs)

    return url(expr, view, name=name)


def find_view(model, modulename, suffix="View", default=DetailView, **kwargs):

    viewclassname = "%s%s" % (model.__name__, suffix)
    modelname = model.__name__.lower()

    try:
        module = __import__("%s.views.%s" % (modulename, modelname))
    except ImportError:
        try:
            module = __import__("%s.views" % modulename)
        except ImportError:
            pass

    try:
        view_class = getattr(getattr(getattr(module, "views"), modelname),
                             viewclassname)
    except:
        view_class = default
        kwargs.update({"model": model})

    return view_class.as_view(**kwargs)


def find_form_class(model, modulename):

    """ Try to find form class either in forms.py or in a separate file
    within forms named after the lower case model class """

    formclassname = "%sForm" % model.__name__
    modelname = model.__name__.lower()
    form_class = None

    try:
        module = __import__("%s.forms.%s" % (modulename, modelname))
    except ImportError:
        try:
            module = __import__("%s.forms" % modulename)
        except ImportError:
            pass

    try:
        form_class = getattr(getattr(getattr(module, "forms"), modelname),
                             formclassname)
    except:
        try:
            form_class = getattr(getattr(module, "forms"), formclassname)
        except:
            pass

    return form_class
