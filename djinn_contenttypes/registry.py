class CTRegistry(object):

    """ Global registry for content types

    The registry can take any attrivutes per content type, but the following
    attributes have active use so far:

      class            Actual class for ct
      app              App id
      label            Front end name of CT
      global_add       Whether the ct should show in the add menu
      global_filter    Whether the ct should show in the search filters
      add_permission   Permission to determine whether a user can add the CT
      view_permission  Permission to determine whether a user can use the CT in
                       search filters.
      del_permission   Permission to determine whether a user can delete the CT
      edit_permission  Permission to check whether a user can edit the CT
      name_plural      well...
      filter_label     Label to show in filter. If empty, not shown at all.
      group_add        Whether the CT can be added to group context

    """

    content_types = {}

    @staticmethod
    def register(name, register_dict):

        CTRegistry.content_types[name] = register_dict

        # Also register with full name e.g. app.ctname
        CTRegistry.content_types["%s.%s" % (register_dict['app'], name)] = \
            register_dict

    @staticmethod
    def get(name):

        """
        Fetch all details for contenttype with name as a dict.
        """

        return CTRegistry.content_types.get(name, {})

    @staticmethod
    def get_attr(name, attr, default=None):

        """ Fetch given attr. Return default if not set"""

        return CTRegistry.content_types.get(name, {}).get(attr, default)

    @staticmethod
    def list_types(excludes=[]):

        """ Only list the 'full' keys: those with the app id and model id """

        return filter(lambda x: x not in excludes and "." in x,
                      CTRegistry.content_types.keys())
