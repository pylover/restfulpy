# restfulpy

A tool-chain for creating restful web applications.

[![PyPI](http://img.shields.io/pypi/v/restfulpy.svg)](https://pypi.python.org/pypi/restfulpy)
[![Build Status](https://travis-ci.org/Carrene/restfulpy.svg?branch=master)](https://travis-ci.org/Carrene/restfulpy)
[![Coverage Status](https://coveralls.io/repos/github/Carrene/restfulpy/badge.svg?branch=master)](https://coveralls.io/github/Carrene/restfulpy?branch=master)

### Goals:
 
- Automatically transform the SqlAlchemy models and queries into JSON with 
standard naming(camelCase).
- Http form validation based on SqlAlchemy models.
- Task Queue system


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
restfulpy completion install
```


