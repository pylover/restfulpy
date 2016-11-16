
from mako.lookup import TemplateLookup, Template
from wheezy.core.descriptors import attribute
from restfulpy.http import SingletonPerContext

from old.configuration import settings


class Messenger(object, metaclass=SingletonPerContext):
    """
    The abstract base class for everyone messaging operations
    """

    def render_body(self, body, template_string=None, template_filename=None):
        if template_string:
            mako_template = Template(template_string)
        elif template_filename:
            mako_template = self.lookup.get_template(template_filename)
        else:
            mako_template = None

        if mako_template:
            return mako_template.render(**body)
        else:
            return body

    @attribute
    def lookup(self):
        return TemplateLookup(directories=settings.messaging.template_dirs, input_encoding='utf8')

    def send(self, *args, **kwargs):
        self.send_from(settings.messaging.default_sender, *args, **kwargs)

    def send_from(self, from_, to, subject, body, cc=None, bcc=None, template_string=None, template_filename=None):
        raise NotImplementedError
