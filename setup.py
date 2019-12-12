import re
from os.path import join, dirname

from setuptools import setup, find_packages


# reading package version (without reloading it)
with open(join(dirname(__file__), 'restfulpy', '__init__.py')) as v_file:
    package_version = re.compile(r".*__version__ = '(.*?)'", re.S) \
        .match(v_file.read()) \
        .group(1)


dependencies = [
    'pymlconf >= 2, < 3',
    'nanohttp >= 1.11.10, < 2',
    'easycli >= 1.5, < 2',
    'argcomplete',
    'ujson',
    'sqlalchemy',
    'alembic',
    'itsdangerous',
    'psycopg2-binary',
    'redis',
    'python-dateutil',

    # Testing
    'pytest',
    'bddrest >= 2.5.7, < 3',
    'bddcli >= 2.5, < 3'
]


setup(
    name='restfulpy',
    version=package_version,
    description='A toolchain for developing REST APIs',
    author='Vahid Mardani',
    author_email='vahid.mardani@gmail.com',
    install_requires=dependencies,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    license='MIT',
    entry_points={
        'console_scripts': [
            'restfulpy = restfulpy.cli:main'
        ]
    },
)
