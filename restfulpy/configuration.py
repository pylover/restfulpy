from os import path

from nanohttp import configure as nanohttp_configure, settings


__builtin_config = """

debug: true
timestamp: false
# Default timezone.
# empty for local time
# 0, utc, UTC, z or Z for the UTC,
# UTC±HH:MM for specify timezone. ie. +3:30 for tehran
# An instance of datetime.tzinfo is also acceptable
# Example:
# timezone: !!python/object/apply:datetime.timezone
#   - !!python/object/apply:datetime.timedelta [0, 7200, 0]
#   - myzone
timezone:

db:
  # The main uri
  url: postgresql://postgres:postgres@localhost/restfulpy_demo

  # Will be used to create and drop database(s).
  administrative_url: postgresql://postgres:postgres@localhost/postgres

  # Will be used to run tests
  test_url: postgresql://postgres:postgres@localhost/restfulpy_test

  # Redirect all SQL Queries to std-out
  echo: false

migration:
  directory: migration
  ini: alembic.ini

jwt:
  secret: JWT-SECRET
  algorithm: HS256
  max_age: 86400  # 24 Hours
  refresh_token:
    secret: JWT-REFRESH-SECRET
    algorithm: HS256
    max_age: 2678400  # 30 Days
    secure: true
    httponly: false
    # path: optional
    #path: /

messaging:
  # default_messenger: restfulpy.messaging.providers.SmtpProvider
  default_messenger: restfulpy.messaging.ConsoleMessenger
  default_sender: restfulpy
  mako_modules_directory:
  template_dirs:
    - %(restfulpy_root)s/messaging/templates

templates:
  directories: []

authentication:
  redis:
    host: localhost
    port: 6379
    password: ~
    db: 0

worker:
  gap: .5
  number_of_threads: 1

jobs:
  interval: .5 # Seconds
  number_of_threads: 1

smtp:
  host: smtp.example.com
  port: 587
  username: user@example.com
  password: password
  local_hostname: localhost
  tls: true
  auth: true
  ssl: false

"""


def configure(context=None, force=False):

    context = context or {}
    context['restfulpy_root'] = path.dirname(__file__)

    nanohttp_configure(
        context=context,
        force=force
    )
    settings.merge(__builtin_config)

