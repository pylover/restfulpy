from nanohttp import configure

from restfulpy.principal import JwtPrincipal


def test_principal():
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
    configure(init_value=__configuration__, force=True)

    principal = JwtPrincipal(dict(
        email='test@example.com',
        id=1,
        sessionId=1,
        roles=['admin']
    ))

    assert principal.email == 'test@example.com'
    assert principal.id == 1
    assert principal.session_id == 1
    assert principal.roles == ['admin']
    assert principal.is_in_roles('admin') is True
    assert principal.is_in_roles('admin', 'god') is True

    encoded = principal.dump()

    principal = JwtPrincipal.load(encoded.decode())
    assert principal.email == 'test@example.com'
    assert principal.id == 1
    assert principal.session_id == 1
    assert principal.roles == ['admin']
    assert principal.is_in_roles('admin') is True
    assert principal.is_in_roles('admin', 'god') is True

    principal = JwtPrincipal.load(encoded.decode(), force=True)
    assert principal.email == 'test@example.com'
    assert principal.id == 1
    assert principal.session_id == 1
    assert principal.roles == ['admin']
    assert principal.is_in_roles('admin') is True
    assert principal.is_in_roles('admin', 'god') is True

    principal =\
        JwtPrincipal.load((b'Bearer %s' % encoded).decode(), force=True)
    assert principal.email == 'test@example.com'
    assert principal.id == 1
    assert principal.session_id == 1
    assert principal.roles == ['admin']
    assert principal.is_in_roles('admin') is True
    assert principal.is_in_roles('admin', 'god') is True

