# restfulpy

A tool-chain for creating restful web applications.

[![PyPI](http://img.shields.io/pypi/v/restfulpy.svg)](https://pypi.python.org/pypi/restfulpy)
[![Build Status](https://travis-ci.org/Carrene/restfulpy.svg?branch=master)](https://travis-ci.org/Carrene/restfulpy)
[![Coverage Status](https://coveralls.io/repos/github/Carrene/restfulpy/badge.svg?branch=master)](https://coveralls.io/github/Carrene/restfulpy?branch=master)
[![Join the chat at https://gitter.im/Carrene/restfulpy](https://badges.gitter.im/Carrene/restfulpy.svg)](https://gitter.im/Carrene/restfulpy?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

### Goals:
 
- Automatically transform the SqlAlchemy models and queries into JSON with 
standard naming(camelCase).
- Http form validation based on SqlAlchemy models.
- Scaffolding: `restfulpy scaffold -h`


### Install

#### PyPI

```bash
pip install restfulpy
```

#### Development

```bash
pip install -e .
pip install -r requirements-dev.txt
```

Run tests to ensure everything is ok:

```bash
pytest
```

### Command line interface

```bash
restfulpy -h
```

#### Autocompletion

```bash
restfulpy autocompletion install
```

### Scaffolding

```bash
restfulpy scaffold \
    --template full 
    --directory path/to/target \
    project1 \
    author@example.com
```

Follow the `path/to/target/README.md` to know how to use the newly created 
project.

#### Single file template

If you have generated your application by `--template singlefile` option, you can run it by:

```bash
nanohttp path/to/application/project1.py
```

Or you can make your application executable by following command:

```bash
chmod +x path/to/application/project1.py
```

Now run your application by:

```bash
path/to/application/project1.py
```

