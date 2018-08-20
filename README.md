# restfulpy

A tool-chain for creating restful web applications.

[![Build Status](http://img.shields.io/pypi/v/restfulpy.svg)](https://pypi.python.org/pypi/restfulpy)
[![Gitter](https://img.shields.io/gitter/room/Carrene/restfulpy.svg)](https://gitter.im/Carrene/restfulpy)
     
### Branches

#### master

[![Build Status](https://travis-ci.org/Carrene/restfulpy.svg?branch=master)](https://travis-ci.org/Carrene/restfulpy)
[![Coverage Status](https://coveralls.io/repos/github/Carrene/restfulpy/badge.svg?branch=master)](https://coveralls.io/github/Carrene/restfulpy?branch=master)

#### develop

[![Build Status](https://travis-ci.org/Carrene/restfulpy.svg?branch=develop)](https://travis-ci.org/Carrene/restfulpy)
[![Coverage Status](https://coveralls.io/repos/github/Carrene/restfulpy/badge.svg?branch=develop)](https://coveralls.io/github/Carrene/restfulpy?branch=develop)



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


