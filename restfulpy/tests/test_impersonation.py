import sys
import unittest

from nanohttp.contexts import context, Context

from restfulpy.principal import ImpersonateAs, DummyIdentity


class ImpersonationTest(unittest.TestCase):
    def setUp(self):
        self.http_context = Context({})
        self.http_context.__enter__()

    def tearDown(self):
        self.http_context.__exit__(*sys.exc_info())

    def test_impersonation(self):
        role1 = 'role-1'
        role2 = 'role-2'
        role3 = 'role-3'
        role4 = 'role-4'

        # Simple test
        role_1_principal = DummyIdentity(role1)
        with ImpersonateAs(role_1_principal):
            self.assertEqual(context.identity, role_1_principal)
            self.assertTrue(context.identity.is_in_roles(role1))

            # Now we change the role
            role_2_principal = DummyIdentity(role2)
            with ImpersonateAs(role_2_principal):
                self.assertFalse(context.identity.is_in_roles(role1))
                self.assertTrue(context.identity.is_in_roles(role2))

        # Multiple roles
        role_3_4_principal = DummyIdentity(role3, role4)
        with ImpersonateAs(role_3_4_principal):
            self.assertTrue(context.identity.is_in_roles(role3))
            self.assertTrue(context.identity.is_in_roles(role4))

            self.assertFalse(context.identity.is_in_roles(role1))
            self.assertFalse(context.identity.is_in_roles(role2))


if __name__ == '__main__':
    unittest.main()
