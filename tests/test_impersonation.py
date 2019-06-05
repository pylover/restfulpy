from nanohttp.contexts import context, Context

from restfulpy.principal import ImpersonateAs, DummyIdentity


def test_impersonation():
    with Context({}) as ctx:
        role1 = 'role-1'
        role2 = 'role-2'
        role3 = 'role-3'
        role4 = 'role-4'

        # Simple test
        role_1_principal = DummyIdentity(role1)
        with ImpersonateAs(role_1_principal):
            assert context.identity == role_1_principal
            assert context.identity.is_in_roles(role1)

            # Now we change the role
            role_2_principal = DummyIdentity(role2)
            with ImpersonateAs(role_2_principal):
                assert not context.identity.is_in_roles(role1)
                assert context.identity.is_in_roles(role2)

        # Multiple roles
        role_3_4_principal = DummyIdentity(role3, role4)
        with ImpersonateAs(role_3_4_principal):
            assert context.identity.is_in_roles(role3)
            assert context.identity.is_in_roles(role4)

            assert not context.identity.is_in_roles(role1)
            assert not context.identity.is_in_roles(role2)

