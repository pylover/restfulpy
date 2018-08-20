import re

from os.path import join, dirname
from setuptools import setup, find_packages


with open(join(dirname(__file__), '${project_name}', '__init__.py')) as v_file:
    package_version = re.compile('.*__version__ = \'(.*?)\'', re.S)\
        .match(v_file.read()).group(1)


dependencies = [
    'restfulpy >= 1.2.1b1',
]


setup(
    name='${project_name}',
    version=package_version,
    author='mohammad sheikhian',
    author_email='mohammadsheikhian70@gmail.com',
    install_requires=dependencies,
    packages=find_packages(),
    test_suite='${project_name}.tests',
    entry_points={
        'console_scripts': [
            '${project_name} = ${project_name}:${project_name}.cli_main'
        ]
    }
)

