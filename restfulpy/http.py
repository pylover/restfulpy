
from threading import local, get_ident
import mimetypes
import os.path

from wheezy.http import HTTPResponse
from wheezy.web.handlers import BaseHandler
from wheezy.web.handlers.method import MethodHandler
import jwt


_thread_local = local()
HTTP_HEADER_ACCEPT_RANGE_NONE = ('Accept-Ranges', 'none')


class Context(dict):

    def __init__(self, thread_local, *args, **kw):
        super(Context, self).__init__(*args, **kw)
        self.thread_local = thread_local
        self.update({'__id': get_ident()})

    @classmethod
    def current(cls):
        if not hasattr(_thread_local, 'kakapo_context'):
            _thread_local.kakapo_context = cls(_thread_local)
        return _thread_local.kakapo_context

    def destroy(self):
        delattr(self.thread_local, 'kakapo_context')


class SingletonPerContext(type):

    def __call__(cls, *args, **kwargs):
        context_key = '%s' % cls.__name__
        context = Context.current()
        if context_key not in context:
            context[context_key] = super(SingletonPerContext, cls).__call__(*args, **kwargs)
        return context[context_key]


class JwtBasePrincipal(object):
    def __init__(self, **kw):
        object.__setattr__(self, 'items', kw)

    @classmethod
    def _secret(cls):
        raise NotImplementedError

    @classmethod
    def _algorithm(cls):
        raise NotImplementedError

    def dump(self):
        res = jwt.encode(
            self.items,
            self._secret(),
            algorithm=self._algorithm())
        return res

    @classmethod
    def load(cls, s):
        params = jwt.decode(
            s,
            cls._secret(),
            algorithms=cls._algorithm())
        result = cls(**params)
        result.validate()
        return result

    def __getattr__(self, key):
        items = object.__getattribute__(self, 'items')
        if key in items:
            return items[key]
        raise AttributeError(key)

    def __setattr__(self, key, value):
        self.items[key] = value

    def __delattr__(self, key):
        del self.items[key]

    @classmethod
    def current(cls):
        current = Context.current()
        if current:
            return current.get('principal')
        return None

    @classmethod
    def get_current_member_id(cls):
        c = cls.current()
        if c:
            return c.id
        raise ValueError('Invalid principal')

    def validate(self):
        """
        It should be called just after the load method.
        You can include additional criteria to validate the principal.
        :return:
        """
        pass

    def put_into_context(self):
        ctx = Context.current()
        ctx['principal'] = self

    @staticmethod
    def delete_from_context():
        ctx = Context.current()
        ctx.pop('principal')


class JwtPrincipalController(BaseHandler):
    __principal_type__ = JwtBasePrincipal
    __jwt_header_key__ = 'HTTP_X_JWT_TOKEN'

    @property
    def context(self):
        return Context.current()

    def get_principal(self):
        if hasattr(self, '_JwtPrincipalController__principal'):
            return self.__principal

        if self.__jwt_header_key__ in self.request.environ:
            try:
                token_base64 = self.request.environ[self.__jwt_header_key__]
                self.__principal = self.__principal_type__.load(token_base64)
                return self.__principal
            except jwt.exceptions.DecodeError:
                pass

        token = self.request.cookies.get('token')
        if token:
            self.__principal = self.__principal_type__.load(token)
            return self.__principal

        return None

    def set_principal(self, principal):
        self.__principal = principal
        self.context.update({
            'principal': principal
        })

    def del_principal(self):
        self.__principal = None

    principal = property(get_principal, set_principal, del_principal)

    def has_route_args(self, *args):
        for name in args:
            if name not in self.route_args or self.route_args[name] is None:
                return False
        return True


def single_file_handler(filepath):
    abspath = os.path.abspath(filepath)
    assert os.path.exists(abspath)
    assert os.path.isfile(abspath)
    return lambda request: SingleFileHandler(
        request,
        filepath=abspath)


class SingleFileHandler(MethodHandler):

    def __init__(self, request, filepath):
        self.filepath = filepath
        super(SingleFileHandler, self).__init__(request)

    def head(self):
        return self.get(skip_body=True)

    def get(self, skip_body=False):

        mime_type, encoding = mimetypes.guess_type(self.filepath)
        response = HTTPResponse(mime_type or 'plain/text', encoding)
        if not skip_body:
            response.headers.append(HTTP_HEADER_ACCEPT_RANGE_NONE)
            file = open(self.filepath, 'rb')
            try:
                response.write_bytes(file.read())
            finally:
                file.close()
        return response
