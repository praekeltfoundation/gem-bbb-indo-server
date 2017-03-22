from __future__ import absolute_import, unicode_literals

from django.forms import MediaDefiningClass
from django.forms.utils import flatatt
from django.template.loader import render_to_string
from django.utils.six import text_type, with_metaclass
from django.utils.text import slugify
from wagtail.wagtailsnippets.permissions import get_permission_name


class ReportMenuItem(with_metaclass(MediaDefiningClass)):
    template = 'wagtailadmin/shared/menu_item.html'

    def __init__(self, label, url, name=None, classnames='', attrs=None, order=1000):
        self.label = label
        self.url = url
        self.classnames = classnames
        self.name = (name or slugify(text_type(label)))
        self.order = order

        if attrs:
            self.attr_string = flatatt(attrs)
        else:
            self.attr_string = ""

    def is_shown(self, request):
        """
        Whether this menu item should be shown for the given request; permission
        checks etc should go here. By default, menu items are shown all the time
        """

        if request.user.has_perm('access_reports'):
            return True

        return False

    def is_active(self, request):
        return request.path.startswith(text_type(self.url))

    def render_html(self, request):
        return render_to_string(self.template, {
            'name': self.name,
            'url': self.url,
            'classnames': self.classnames,
            'attr_string': self.attr_string,
            'label': self.label,
            'active': self.is_active(request)
        }, request=request)