
import unittest

from nanohttp import configure

from restfulpy.principal import JwtPrincipal


class PrincipalTestCase(unittest.TestCase):
    __configuration__ = '''
    jwt:
      secret: JWT-SECRET
      algorithm: HS256
      max_age: 86400  # 24 Hours
      refresh_token:
        secret: JWT-REFRESH-SECRET
        algorithm: HS256
        max_age: 2678400  # 30 Days
    '''

    @classmethod
    def setUpClass(cls):
        configure(init_value=cls.__configuration__, force=True)

    def test_principal(self):
        principal = JwtPrincipal(dict(
            email='test@example.com',
            id=1,
            sessionId=1,
            roles=['admin']
        ))

        self.assertEqual(principal.email, 'test@example.com')
        self.assertEqual(principal.id, 1)
        self.assertEqual(principal.session_id, 1)
        self.assertEqual(principal.roles, ['admin'])
        self.assertTrue(principal.is_in_roles('admin'))
        self.assertTrue(principal.is_in_roles('admin', 'god'))

        encoded = principal.dump()

        principal = JwtPrincipal.load(encoded.decode())
        self.assertEqual(principal.email, 'test@example.com')
        self.assertEqual(principal.id, 1)
        self.assertEqual(principal.session_id, 1)
        self.assertEqual(principal.roles, ['admin'])
        self.assertTrue(principal.is_in_roles('admin'))
        self.assertTrue(principal.is_in_roles('admin', 'god'))

        principal = JwtPrincipal.load(encoded.decode(), force=True)
        self.assertEqual(principal.email, 'test@example.com')
        self.assertEqual(principal.id, 1)
        self.assertEqual(principal.session_id, 1)
        self.assertEqual(principal.roles, ['admin'])
        self.assertTrue(principal.is_in_roles('admin'))
        self.assertTrue(principal.is_in_roles('admin', 'god'))

        principal = JwtPrincipal.load((b'Bearer %s' % encoded).decode(), force=True)
        self.assertEqual(principal.email, 'test@example.com')
        self.assertEqual(principal.id, 1)
        self.assertEqual(principal.session_id, 1)
        self.assertEqual(principal.roles, ['admin'])
        self.assertTrue(principal.is_in_roles('admin'))
        self.assertTrue(principal.is_in_roles('admin', 'god'))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
