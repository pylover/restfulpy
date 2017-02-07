
from nanohttp import configure as nanohttp_configure, settings


__builtin_config = """

debug: true
pretty_json: true

db:
  uri: sqlite:///%(data_dir)s/devdata.db
  # uri: postgresql://postgres:postgres@localhost/restfulpy_demo_dev
  # administrative_uri: postgresql://postgres:postgres@localhost/postgres
  # test_uri: postgresql://postgres:postgres@localhost/restfulpy_test
  echo: false

migration:
  directory: %(root_path)s/migration
  ini: %(root_path)s/alembic.ini

jwt:
  secret: JWT-SECRET
  algorithm: HS256
  max_age: 86400  # 24 Hours
  refresh_token:
    secret: JWT-REFRESH-SECRET
    algorithm: HS256
    max_age: 2678400  # 30 Days

messaging:
  # default_messenger: restfulpy.messaging.postman.Postman
  default_messenger: restfulpy.messaging.ConsoleMessenger
  default_sender: restfulpy
  template_dirs:
    - %(restfulpy_dir)s/messaging/templates

worker:
  gap: 2
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
  version: 1
  disable_existing_loggers: false
  formatters:
    default:
      format: "%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s"
      date_format: "%%Y-%%m-%%d %%H:%%M:%%S"

  handlers:

    console:
      class: logging.StreamHandler
      stream: ext://sys.stdout
      formatter: default
      level: DEBUG

    main:
      class: logging.handlers.RotatingFileHandler
      filename: %(data_dir)s/logs/main.log
      maxBytes: 52428800
      formatter: default
      level: DEBUG

    error:
      class: logging.handlers.RotatingFileHandler
      filename: %(data_dir)s/logs/error.log
      maxBytes: 52428800
      formatter: default
      level: ERROR

  root:
    handlers:
      - console
      - main
      - error
    level: DEBUG
    formatter: default

"""


def configure(config=None, directories=None, files=None, context=None, force=False):

    nanohttp_configure(init_value=__builtin_config, context=context, force=force)

    if config:
        settings.merge(config)

    if directories:
        settings.load_dirs(directories)

    if files:
        settings.load_files(files)
