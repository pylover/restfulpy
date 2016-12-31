
from nanohttp import configure as nanohttp_configure, settings


__builtin_config = """

debug: true
pretty_json: true

db:
  uri: sqlite:///%(data_dir)s/devdata.db
  # uri: postgresql://postgres:postgres@localhost/restfulpy_demo_dev
  # administrative_uri: postgresql://postgres:postgres@localhost/postgres
  # test_uri: postgresql://postgres:postgres@localhost/lemur_test
  echo: false

migration:
  directory: %(root_path)s/migration
  ini: %(root_path)s/alembic.ini

jwt:
  secret: JWT-SECRET
  algorithm: HS256
  max_age: 86400

messaging:
  # default_messenger: restfulpy.messaging.postman.Postman
  default_messenger: restfulpy.messaging.console.ConsoleMessenger
  default_sender: restfulpy
  template_dirs:
    - %(restfulpy_dir)s/messaging/templates

worker:
  gap: 1
  number_of_threads: 4

api_documents:
  directory: %(data_dir)s/api-documents

smtp:
  host: smtp.example.com
  port: 587
  username: user@example.com
  password: password
  local_hostname: localhost

logging:
  loggers:

    default:
      handlers:
        - console
      level: debug
      formatter: default

    main:
      handlers:
        - console
        - main

    auth:
      handlers:
        - console
        - auth

    error:
      handlers:
        - console
        - error

    critical:
      handlers:
        - console
        - critical

  handlers:
    console:
     type: console
    debug:
     type: file
     filename: %(data_dir)s/logs/debug.log
    auth:
     type: file
     filename: %(data_dir)s/logs/auth.log
    error:
     type: file
     filename: %(data_dir)s/logs/error.log

    # console: !!python/object/new:logging.StreamHandler []
    # main: !!python/object/new:logging.StreamHandler [ %(data_dir)s/logs/debug.log ]
    # auth: !!python/object/new:logging.StreamHandler [ %(data_dir)s/logs/auth.log ]
    # error: !!python/object/new:logging.StreamHandler [ %(data_dir)s/logs/error.log ]

  formatters:
    default:
      format: "%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s"
      date_format: "%%Y-%%m-%%d %%H:%%M:%%S"

"""


def configure(config=None, directories=None, files=None, context=None, force=False):

    nanohttp_configure(init_value=__builtin_config, context=context, force=force)

    if config:
        settings.merge(config)

    if directories:
        settings.load_dirs(directories)

    if files:
        settings.load_files(files)
